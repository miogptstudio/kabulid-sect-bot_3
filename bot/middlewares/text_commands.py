"""اجرای دستورات ربات بدون اسلش.

نام Commandهای ثبت‌شده + نام‌های فارسی منو را به /command تبدیل می‌کند
تا بدون / هم کار کنند.
"""
from __future__ import annotations

import ast
import logging
from pathlib import Path
from typing import Any, Awaitable, Callable

from aiogram import BaseMiddleware
from aiogram.types import Message

logger = logging.getLogger(__name__)

_ZERO_WIDTH = "\u200c\u200d\u200e\u200f\ufeff"
_EMOJI_PREFIXES = (
    "👤", "🧘", "⚔️", "🎒", "⚗", "🏛", "🏪", "🎁", "📜", "🏆", "📊", "🌍",
    "🎲", "💼", "📖", "⚙️", "🐾", "💍", "🪙", "💎", "🛠", "🎮", "🗺", "⭐",
)


def normalize(value: str) -> str:
    value = (value or "").strip().lower()
    for ch in _ZERO_WIDTH:
        value = value.replace(ch, "")
    for em in _EMOJI_PREFIXES:
        value = value.replace(em, "")
    return "".join(value.split())


def load_command_aliases() -> dict[str, str]:
    handlers_dir = Path(__file__).resolve().parents[1] / "handlers"
    aliases: dict[str, str] = {
        normalize("شروع"): "start",
        normalize("شروع بازی"): "start",
        normalize("کمک"): "help",
        normalize("راهنما"): "help",
        normalize("منو"): "help",
    }
    for path in handlers_dir.glob("*.py"):
        try:
            tree = ast.parse(path.read_text(encoding="utf-8"))
        except Exception:
            continue
        for node in ast.walk(tree):
            if not isinstance(node, ast.Call):
                continue
            if not isinstance(node.func, ast.Name) or node.func.id != "Command":
                continue
            values = [
                a.value
                for a in node.args
                if isinstance(a, ast.Constant) and isinstance(a.value, str)
            ]
            if not values:
                continue
            canonical = values[0]
            for value in values:
                key = normalize(value)
                if key:
                    aliases.setdefault(key, canonical)

    try:
        from bot.handlers import text_navigation as tn
        for fa, cmd in getattr(tn, "ALIASES", {}).items():
            key = normalize(fa)
            if key and cmd:
                aliases.setdefault(key, cmd)
    except Exception as e:
        logger.warning("could not load text_navigation aliases: %s", e)

    aliases.update({
        normalize("مقاممن"): "iamadmin",
        normalize("مقام من"): "iamadmin",
        normalize("شهرها"): "worldcities",
        normalize("قلمروها"): "territories",
        normalize("کیف پول"): "wallet",
        normalize("کیف"): "wallet",
        normalize("پروفایل"): "profile",
        normalize("وضعیت"): "profile",
        normalize("تزکیه"): "cultivation",
        normalize("تذهیب"): "cultivation",
        normalize("دوئل"): "duel",
        normalize("نبرد"): "duel",
        normalize("رتبه"): "ranking",
        normalize("فرقه"): "sects",
        normalize("فروشگاه"): "shop",
        normalize("روزانه"): "daily",
        normalize("بدن"): "body",
        normalize("روح"): "spirit",
        normalize("آرنا"): "arena",
        normalize("شغل"): "jobs",
        normalize("مأموریت"): "quests",
        normalize("ماموریت"): "quests",
    })
    return aliases


class TextCommandMiddleware(BaseMiddleware):
    def __init__(self) -> None:
        super().__init__()
        self.aliases = load_command_aliases()
        self._sorted = sorted(self.aliases, key=len, reverse=True)
        logger.info("TextCommandMiddleware loaded %s aliases", len(self.aliases))

    def _rewrite(self, text: str) -> str | None:
        raw = (text or "").strip()
        if not raw or raw.startswith("/"):
            return None
        words = raw.split()
        for count in range(min(5, len(words)), 0, -1):
            head = " ".join(words[:count])
            key = normalize(head)
            canonical = self.aliases.get(key)
            if canonical:
                args = " ".join(words[count:])
                return "/" + canonical + ((" " + args) if args else "")
        key = normalize(raw)
        canonical = self.aliases.get(key)
        if canonical:
            return "/" + canonical
        return None

    async def __call__(
        self,
        handler: Callable[[Any, dict], Awaitable[Any]],
        event: Any,
        data: dict,
    ) -> Any:
        if isinstance(event, Message) and event.text and not event.text.lstrip().startswith("/"):
            rewritten = self._rewrite(event.text)
            if rewritten:
                event = event.model_copy(update={"text": rewritten})
        return await handler(event, data)
