"""ذخیره‌سازی پایدار داده‌های حافظه‌ای روی دیسک + دیتابیس"""
from __future__ import annotations
import json
import os
import logging
import threading
from pathlib import Path
from typing import Any

from bot.config import DATA_DIR

logger = logging.getLogger(__name__)
_lock = threading.RLock()
_dir = Path(DATA_DIR) / "persist"
_dir.mkdir(parents=True, exist_ok=True)

# cache in process
_cache: dict[str, Any] = {}


def _path(ns: str) -> Path:
    safe = "".join(c if c.isalnum() or c in "-_" else "_" for c in ns)
    return _dir / f"{safe}.json"


def _json_default(o):
    if hasattr(o, "isoformat"):
        return o.isoformat()
    if isinstance(o, set):
        return {"__set__": list(o)}
    return str(o)


def _revive(obj):
    if isinstance(obj, dict):
        if "__set__" in obj and len(obj) == 1:
            return set(obj["__set__"])
        return {k: _revive(v) for k, v in obj.items()}
    if isinstance(obj, list):
        return [_revive(x) for x in obj]
    return obj


def load(ns: str, default: Any = None) -> Any:
    """بارگذاری namespace؛ اگر نبود default (یا {})"""
    if default is None:
        default = {}
    with _lock:
        if ns in _cache:
            return _cache[ns]
        p = _path(ns)
        if p.exists():
            try:
                data = json.loads(p.read_text(encoding="utf-8"))
                data = _revive(data)
                _cache[ns] = data
                return data
            except Exception as e:
                logger.warning("persist load %s failed: %s", ns, e)
        # copy default
        if isinstance(default, (dict, list, set)):
            import copy
            data = copy.deepcopy(default)
        else:
            data = default
        _cache[ns] = data
        return data


def save(ns: str, data: Any = None) -> None:
    """ذخیره فوری روی دیسک"""
    with _lock:
        if data is not None:
            _cache[ns] = data
        payload = _cache.get(ns)
        if payload is None:
            return
        p = _path(ns)
        try:
            tmp = p.with_suffix(".tmp")
            tmp.write_text(
                json.dumps(payload, ensure_ascii=False, indent=0, default=_json_default),
                encoding="utf-8",
            )
            tmp.replace(p)
        except Exception as e:
            logger.warning("persist save %s failed: %s", ns, e)


def get_dict(ns: str) -> dict:
    d = load(ns, {})
    if not isinstance(d, dict):
        d = {}
        _cache[ns] = d
    return d


def set_dict(ns: str, d: dict) -> None:
    save(ns, d)


def update_key(ns: str, key: str | int, value: Any) -> None:
    d = get_dict(ns)
    d[str(key)] = value
    save(ns, d)


def delete_key(ns: str, key: str | int) -> None:
    d = get_dict(ns)
    d.pop(str(key), None)
    save(ns, d)


async def sync_to_db() -> int:
    """همه namespaceها را در جدول persist_kv ذخیره کن"""
    try:
        from database.engine import async_session
        from sqlalchemy import text
        n = 0
        async with async_session() as session:
            # ensure table
            await session.execute(text(
                """
                CREATE TABLE IF NOT EXISTS persist_kv (
                    ns VARCHAR(64) PRIMARY KEY,
                    payload TEXT NOT NULL,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
                """
            ))
            with _lock:
                items = list(_cache.items())
                # also dump files not in cache
                for p in _dir.glob("*.json"):
                    ns = p.stem
                    if ns not in _cache:
                        try:
                            items.append((ns, json.loads(p.read_text(encoding="utf-8"))))
                        except Exception:
                            pass
            for ns, payload in items:
                raw = json.dumps(payload, ensure_ascii=False, default=_json_default)
                # upsert
                await session.execute(
                    text(
                        """
                        INSERT INTO persist_kv (ns, payload)
                        VALUES (:ns, :payload)
                        ON CONFLICT(ns) DO UPDATE SET payload = :payload,
                            updated_at = CURRENT_TIMESTAMP
                        """
                    ),
                    {"ns": ns, "payload": raw},
                )
                n += 1
            await session.commit()
        return n
    except Exception as e:
        # SQLite upsert syntax differs — fallback
        try:
            from database.engine import async_session
            from sqlalchemy import text
            n = 0
            async with async_session() as session:
                await session.execute(text(
                    "CREATE TABLE IF NOT EXISTS persist_kv ("
                    "ns VARCHAR(64) PRIMARY KEY, payload TEXT NOT NULL, "
                    "updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP)"
                ))
                with _lock:
                    items = list(_cache.items())
                for ns, payload in items:
                    raw = json.dumps(payload, ensure_ascii=False, default=_json_default)
                    await session.execute(
                        text("DELETE FROM persist_kv WHERE ns = :ns"),
                        {"ns": ns},
                    )
                    await session.execute(
                        text("INSERT INTO persist_kv (ns, payload) VALUES (:ns, :payload)"),
                        {"ns": ns, "payload": raw},
                    )
                    n += 1
                await session.commit()
            return n
        except Exception as e2:
            logger.warning("sync_to_db failed: %s / %s", e, e2)
            return 0


async def load_from_db() -> int:
    """DB منبع اصلی داده‌های پایدار است؛ داده‌های بازیکن با آپدیت ربات پاک نمی‌شوند."""
    try:
        from database.engine import async_session
        from sqlalchemy import text
        async with async_session() as session:
            await session.execute(text(
                "CREATE TABLE IF NOT EXISTS persist_kv ("
                "ns VARCHAR(64) PRIMARY KEY, payload TEXT NOT NULL, "
                "updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP)"
            ))
            r = await session.execute(text("SELECT ns, payload FROM persist_kv"))
            rows = r.fetchall()
            n = 0
            for ns, payload in rows:
                # اگر DB داده دارد، همان داده مرجع است. این کار جلوی جایگزین‌شدن
                # دیتای جدید بازیکنان با فایل قدیمی هنگام deploy/update را می‌گیرد.
                try:
                    data = _revive(json.loads(payload))
                    with _lock:
                        _cache[ns] = data
                    save(ns, data)
                    n += 1
                except Exception:
                    pass
            return n
    except Exception as e:
        logger.warning("load_from_db: %s", e)
        return 0


def preload_all() -> None:
    """همه فایل‌های persist را در کش بیاور"""
    for p in _dir.glob("*.json"):
        try:
            load(p.stem)
        except Exception:
            pass
