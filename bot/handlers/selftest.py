"""دستور تست جامع: /testall
همه مسیرهای مهم را بدون خراب کردن بازی چک می‌کند و خطاها را گزارش می‌دهد.
فقط سازنده / ادمین / ویژه.
"""
from __future__ import annotations
import importlib
import inspect
import re
import traceback
from aiogram import Router
from aiogram.types import Message
from aiogram.filters import Command

router = Router()


def _ok(msg: str) -> str:
    return f"✅ {msg}"


def _fail(msg: str, err: BaseException | None = None) -> str:
    if err is None:
        return f"❌ {msg}"
    tb = traceback.format_exception_only(type(err), err)
    detail = "".join(tb).strip()
    return f"❌ {msg}\n   → {detail}"


def _check_text_navigation_imports() -> list[str]:
    lines = []
    try:
        import bot.handlers.text_navigation as tn
        src = inspect.getsource(tn)
    except Exception as e:
        return [_fail("خواندن text_navigation", e)]

    # from bot.handlers.X import Y  then await Y(
    pattern = re.compile(
        r"from bot\.handlers\.(\w+) import (\w+)\s*\n\s*await (\w+)\("
    )
    for mod, imported, awaited in pattern.findall(src):
        name = imported
        try:
            m = importlib.import_module(f"bot.handlers.{mod}")
            fn = getattr(m, name, None)
            if fn is None:
                lines.append(_fail(f"text_nav: bot.handlers.{mod}.{name} وجود ندارد"))
            elif not callable(fn):
                lines.append(_fail(f"text_nav: bot.handlers.{mod}.{name} قابل فراخوانی نیست"))
            elif imported != awaited:
                lines.append(_fail(f"text_nav: import {imported} ولی await {awaited}"))
            else:
                lines.append(_ok(f"text_nav → {mod}.{name}"))
        except Exception as e:
            lines.append(_fail(f"text_nav import {mod}.{name}", e))
    if not lines:
        lines.append(_fail("هیچ importی در text_navigation پیدا نشد"))
    return lines


def _check_handler_modules() -> list[str]:
    lines = []
    import pkgutil
    import bot.handlers as handlers_pkg
    for info in pkgutil.iter_modules(handlers_pkg.__path__):
        name = info.name
        if name.startswith("_"):
            continue
        try:
            mod = importlib.import_module(f"bot.handlers.{name}")
            # count Command handlers roughly
            n = 0
            for attr in dir(mod):
                obj = getattr(mod, attr, None)
                if callable(obj) and attr.startswith("cmd_"):
                    n += 1
            lines.append(_ok(f"module handlers.{name} (cmd_* ≈ {n})"))
        except Exception as e:
            lines.append(_fail(f"import handlers.{name}", e))
    return lines


def _check_services() -> list[str]:
    lines = []
    services = [
        "services.staff",
        "services.servants",
        "services.economy",
        "services.sect_systems",
        "services.immortal",
        "services.power",
        "services.cultivation",
        "services.dual",
        "services.prison",
        "bot.servant_images",
        "bot.panel_images",
        "bot.utils.servant_panel",
    ]
    for s in services:
        try:
            importlib.import_module(s)
            lines.append(_ok(f"import {s}"))
        except Exception as e:
            lines.append(_fail(f"import {s}", e))
    return lines


def _check_servant_images() -> list[str]:
    lines = []
    try:
        from pathlib import Path
        from bot.servant_images import get_servant_image_by_id
        missing = []
        for i in range(1, 37):
            p = get_servant_image_by_id(i)
            if not p or not Path(p).exists():
                missing.append(str(i))
        if missing:
            lines.append(_fail(f"عکس خدمتکار نیست برای id: {', '.join(missing)}"))
        else:
            lines.append(_ok("عکس خدمتکارها ۱ تا ۳۶ موجود است"))
    except Exception as e:
        lines.append(_fail("بررسی عکس خدمتکار", e))
    return lines


def _check_staff_api() -> list[str]:
    lines = []
    try:
        from services.staff import get_staff, has_perm, PERM_DIAG, list_staff, money_limit
        r = get_staff(0)
        has_perm(0, PERM_DIAG)
        money_limit(0)
        list_staff()
        lines.append(_ok(f"staff API (get_staff(0)={r})"))
    except Exception as e:
        lines.append(_fail("staff API", e))
    return lines


def _check_servants_buy_signature() -> list[str]:
    lines = []
    try:
        from services import servants as s
        import inspect
        sig = inspect.signature(s.buy)
        params = list(sig.parameters)
        if "karma" not in params:
            lines.append(_fail(f"servants.buy پارامتر karma ندارد: {params}"))
        else:
            lines.append(_ok(f"servants.buy signature OK {params}"))
        # unique train
        from services.servants import _train_cooldown_seconds, UNIQUE_SERVANT_IDS
        cd = _train_cooldown_seconds(1, next(iter(UNIQUE_SERVANT_IDS)))
        if cd != 30:
            lines.append(_fail(f"کولداون بی‌همتا باید ۳۰ باشد نه {cd}"))
        else:
            lines.append(_ok("کولداون پرورش بی‌همتا = ۳۰ث"))
    except Exception as e:
        lines.append(_fail("servants API", e))
    return lines


async def _check_db(message: Message) -> list[str]:
    lines = []
    try:
        from database.engine import async_session
        from database.crud import get_or_create_user
        from services.economy import get_or_create_wallet
        async with async_session() as session:
            u = await get_or_create_user(
                session,
                message.from_user.id,
                message.from_user.full_name,
                message.from_user.username,
            )
            w = await get_or_create_wallet(session, u.id)
            lines.append(_ok(f"DB user id={u.id} coins={getattr(w,'coins',0)}"))
    except Exception as e:
        lines.append(_fail("اتصال دیتابیس / کاربر", e))
    return lines


def _check_main_routers() -> list[str]:
    lines = []
    try:
        src = open("bot/main.py", encoding="utf-8").read()
        needed = [
            "text_navigation", "start", "admin", "sects", "social",
            "cultivation", "shop", "dual", "marriage", "combat", "selftest",
        ]
        for n in needed:
            if n in src:
                lines.append(_ok(f"main.py includes/mentions {n}"))
            else:
                lines.append(_fail(f"main.py به {n} اشاره ندارد"))
    except Exception as e:
        lines.append(_fail("خواندن main.py", e))
    return lines


@router.message(Command("testall", "تست‌همه", "تستهمه", "checkall", "بررسی‌کامل"))
async def cmd_testall(message: Message):
    from services.staff import has_perm, PERM_DIAG
    if not has_perm(message.from_user.id, PERM_DIAG):
        await message.answer("⛔️ فقط ویژه / مدیر / ادمین / سازنده.")
        return

    await message.answer("🔎 شروع تست جامع... چند لحظه صبر کن.")

    report: list[str] = ["🧪 <b>گزارش /testall</b>", ""]
    fails = 0

    sections = [
        ("ماژول‌ها", _check_handler_modules()),
        ("سرویس‌ها", _check_services()),
        ("ناوبری متنی", _check_text_navigation_imports()),
        ("عکس خدمتکار", _check_servant_images()),
        ("مقامات", _check_staff_api()),
        ("خدمتکار API", _check_servants_buy_signature()),
        ("روترها", _check_main_routers()),
        ("دیتابیس", await _check_db(message)),
    ]

    for title, lines in sections:
        report.append(f"<b>▸ {title}</b>")
        for line in lines:
            report.append(line)
            if line.startswith("❌"):
                fails += 1
        report.append("")

    report.append(f"——————————\nجمع خطاها: <b>{fails}</b>")
    if fails:
        report.append("متن کامل خطاها را کپی کن و بفرست تا درست شوند.")
    else:
        report.append("همه چک‌های استاتیک OK بودند.")

    # ارسال تکه‌تکه (محدودیت تلگرام)
    text = "\n".join(report)
    for i in range(0, len(text), 3900):
        await message.answer(text[i:i + 3900])


@router.message(Command("testrun", "اجرا‌تست", "اجراتست"))
async def cmd_testrun(message: Message):
    """چند دستور امن را واقعاً اجرا می‌کند و خطا را نشان می‌دهد."""
    from services.staff import has_perm, PERM_DIAG
    if not has_perm(message.from_user.id, PERM_DIAG):
        await message.answer("⛔️ فقط ویژه و بالاتر.")
        return

    await message.answer("▶️ اجرای واقعی چند دستور امن...")
    results = []

    async def run(label, coro):
        try:
            await coro
            results.append(f"✅ {label}")
        except Exception as e:
            results.append(f"❌ {label}: {type(e).__name__}: {e}")

    # دستورات نسبتاً امن (فقط نمایش)
    try:
        from bot.handlers.profile import cmd_profile
        await run("/profile", cmd_profile(message))
    except Exception as e:
        results.append(f"❌ /profile setup: {e}")

    try:
        from bot.handlers.cultivation import cmd_cultivation
        await run("/cultivation", cmd_cultivation(message))
    except Exception as e:
        results.append(f"❌ /cultivation setup: {e}")

    try:
        from bot.handlers.help_menu import cmd_help
        await run("/help", cmd_help(message))
    except Exception as e:
        results.append(f"❌ /help setup: {e}")

    try:
        from bot.handlers.codex_items import cmd_item_codex
        await run("/codex", cmd_item_codex(message))
    except Exception as e:
        results.append(f"❌ /codex setup: {e}")

    try:
        from bot.handlers.social import cmd_servants_v2
        await run("/servants", cmd_servants_v2(message))
    except Exception as e:
        results.append(f"❌ /servants setup: {e}")

    try:
        from bot.handlers.start import cmd_ping
        await run("/ping", cmd_ping(message))
    except Exception as e:
        results.append(f"❌ /ping setup: {e}")

    fails = sum(1 for r in results if r.startswith("❌"))
    results.append(f"\nخطاهای اجرا: <b>{fails}</b>")
    await message.answer("\n".join(results))
