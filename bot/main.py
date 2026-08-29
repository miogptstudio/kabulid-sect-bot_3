import asyncio
import logging
import os
from html import escape
import re
from aiogram import Bot, Dispatcher
from aiogram.types import ErrorEvent
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode
from aiogram.fsm.storage.memory import MemoryStorage

from bot.config import BOT_TOKEN
from database.engine import engine, migrate_schema, async_session as async_session_for_portal
from database.models import Base
import database.models_v2  # noqa: F401
import database.models_v3  # noqa: F401
from bot.handlers import spirit as spirit  # noqa
from bot.handlers import selftest as selftest  # noqa
from bot.handlers import text_navigation as text_navigation  # noqa
from bot.handlers import open_world as open_world  # noqa
from bot.handlers import characters as characters  # noqa
from bot.handlers import retention as retention  # noqa
from bot.handlers import (
    start, profile, duel, guardian, ranking, admin, missions, advanced_systems,
    sects, cultivation, master, arena, accounts, shop, crafting, dual, marriage, pets, death, world, help_menu, combat, engagement, games, garden, social, creatures, combat_extra, race, spirit, society_extra, lang, jobs_events, codex_items, prison_market, fallback
)
from bot.health import start_health_server
from bot.middlewares.service_lock import ServiceLockMiddleware
from bot.middlewares.auto_reply import AutoReplyMiddleware
from bot.middlewares.panel_owner import PanelOwnerMiddleware
from bot.middlewares.text_commands import TextCommandMiddleware

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


_ALLOWED_HTML_TAGS = {
    "b", "strong", "i", "em", "u", "ins", "s", "strike", "del",
    "code", "pre", "blockquote", "tg-spoiler", "a", "tg-emoji"
}
_TAG_RE = re.compile(r"</?([A-Za-z][A-Za-z0-9_-]*)(?:\s[^>]*)?>")


def _safe_html_text(value: str) -> str:
    """Keep Telegram-supported HTML, escape unknown tags, and fail safe on bad nesting."""
    if not isinstance(value, str) or "<" not in value:
        return value

    def repl(m):
        tag = m.group(1).lower()
        if tag in _ALLOWED_HTML_TAGS:
            return m.group(0)
        return escape(m.group(0))

    value = _TAG_RE.sub(repl, value)

    # Telegram rejects malformed/unbalanced HTML. If that happens, strip markup
    # completely rather than letting a harmless user-visible message crash a handler.
    stack = []
    token_re = re.compile(r"<(b|strong|i|em|u|ins|s|strike|del|code|pre|blockquote|tg-spoiler|a|tg-emoji)(?:\s[^>]*)?>(.*?)</\1>", re.I | re.S)
    # A conservative balance check: every opening/closing supported tag must pair.
    for m in re.finditer(r"<(\/)?(b|strong|i|em|u|ins|s|strike|del|code|pre|blockquote|tg-spoiler|a|tg-emoji)(?:\s[^>]*)?>", value, re.I):
        closing = bool(m.group(1))
        tag = m.group(2).lower()
        if not closing:
            stack.append(tag)
        elif not stack or stack[-1] != tag:
            return re.sub(r"<[^>]+>", "", value)
        else:
            stack.pop()
    if stack:
        return re.sub(r"<[^>]+>", "", value)
    return value


class SafeHTMLBot(Bot):
    """Bot wrapper that prevents malformed dynamic HTML from breaking handlers."""
    async def __call__(self, method, request_timeout=None):
        # TelegramMethod objects expose text/caption for the methods where the
        # global default parse mode is applied. Sanitize only those fields.
        for field in ("text", "caption"):
            if hasattr(method, field):
                value = getattr(method, field)
                if isinstance(value, str):
                    setattr(method, field, _safe_html_text(value))
        return await super().__call__(method, request_timeout=request_timeout)


async def on_startup():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    await migrate_schema()
    try:
        from services.open_world import launch_portal_once, portal_story
        async with async_session_for_portal() as _portal_session:
            launched = await launch_portal_once(_portal_session)
        if launched:
            logger.info("WORLD PORTAL: all players moved to the new open world")
    except Exception as e:
        logger.warning("world portal init: %s", e)
    try:
        from services.persist import preload_all, load_from_db, sync_to_db
        # PostgreSQL منبع اصلی دادههای پایدار است؛ فایل محلی فقط fallback است.
        n = await load_from_db()
        preload_all()
        logger.info("Persist loaded from DB: %s namespaces", n)
        await sync_to_db()
    except Exception as e:
        logger.warning("persist init: %s", e)
    logger.info("Database tables created + migrated (v1 + v2 + v3).")


async def main():
    if not BOT_TOKEN:
        raise ValueError("BOT_TOKEN is not set in .env")

    port = int(os.getenv("PORT", 8080))
    await start_health_server(port)

    bot = SafeHTMLBot(
        token=BOT_TOKEN,
        default=DefaultBotProperties(parse_mode=ParseMode.HTML)
    )
    dp = Dispatcher(storage=MemoryStorage())
    dp.message.middleware(ServiceLockMiddleware())
    dp.message.middleware(TextCommandMiddleware())
    # AutoReplyMiddleware موقتاً غیرفعال — باعث می‌شد جواب‌ها ارسال نشوند
    # dp.message.middleware(AutoReplyMiddleware())
    dp.callback_query.middleware(ServiceLockMiddleware())
    dp.callback_query.middleware(PanelOwnerMiddleware())

    # ورود به بخشها با نوشتن نامشان، بدون نیاز به /command
    dp.include_router(open_world.router)
    dp.include_router(start.router)
    dp.include_router(advanced_systems.router)
    dp.include_router(profile.router)
    dp.include_router(duel.router)
    dp.include_router(guardian.router)
    dp.include_router(ranking.router)
    dp.include_router(missions.router)
    dp.include_router(sects.router)
    dp.include_router(cultivation.router)
    dp.include_router(master.router)
    dp.include_router(arena.router)
    dp.include_router(accounts.router)
    dp.include_router(shop.router)
    dp.include_router(crafting.router)
    dp.include_router(dual.router)
    dp.include_router(marriage.router)
    dp.include_router(pets.router)
    dp.include_router(death.router)
    dp.include_router(world.router)
    dp.include_router(help_menu.router)
    dp.include_router(combat.router)
    dp.include_router(engagement.router)
    dp.include_router(retention.router)
    dp.include_router(games.router)
    dp.include_router(garden.router)
    dp.include_router(social.router)
    dp.include_router(creatures.router)
    dp.include_router(combat_extra.router)
    dp.include_router(race.router)
    dp.include_router(spirit.router)
    dp.include_router(lang.router)
    dp.include_router(jobs_events.router)
    dp.include_router(characters.router)
    dp.include_router(society_extra.router)
    dp.include_router(codex_items.router)
    dp.include_router(prison_market.router)
    dp.include_router(admin.router)
    dp.include_router(selftest.router)
    # ناوبری متنی بعد از handlerهای اصلی؛ تا دکمه‌های متنی قبلی مسدود نشوند.
    dp.include_router(text_navigation.router)
    dp.include_router(fallback.router)

    @dp.errors()
    async def _on_error(event: ErrorEvent):
        logger.exception("Update error: %s", event.exception)
        try:
            upd = event.update
            msg = None
            if upd.message:
                msg = upd.message
            elif upd.callback_query and upd.callback_query.message:
                msg = upd.callback_query.message
            if msg:
                err = event.exception
                err_text = (
                    "⚠️ خطا در اجرای دستور: "
                    + type(err).__name__
                    + "\n"
                    + escape(str(err)[:180])
                    + "\n/help"
                )
                await msg.answer(err_text[:3900])
        except Exception:
            pass
        return True

    await on_startup()
    logger.info("Bot starting...")
    await bot.delete_webhook(drop_pending_updates=True)
    logger.info("Webhook cleared; polling...")
    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())
