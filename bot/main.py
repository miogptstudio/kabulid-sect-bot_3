import asyncio
import logging
import os
from aiogram import Bot, Dispatcher
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode
from aiogram.fsm.storage.memory import MemoryStorage

from bot.config import BOT_TOKEN
from database.engine import engine, migrate_schema
from database.models import Base
import database.models_v2  # noqa: F401
import database.models_v3  # noqa: F401
from bot.handlers import (
    start, profile, duel, guardian, ranking, admin, missions,
    sects, cultivation, master, arena, accounts, shop, crafting, dual, marriage, pets, death, world, help_menu, combat, engagement, games, garden, social, creatures, combat_extra, fallback
)
from bot.health import start_health_server

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


async def on_startup():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    await migrate_schema()
    logger.info("Database tables created + migrated (v1 + v2 + v3).")


async def main():
    if not BOT_TOKEN:
        raise ValueError("BOT_TOKEN is not set in .env")

    port = int(os.getenv("PORT", 8080))
    await start_health_server(port)

    bot = Bot(
        token=BOT_TOKEN,
        default=DefaultBotProperties(parse_mode=ParseMode.HTML)
    )
    dp = Dispatcher(storage=MemoryStorage())

    # بدون چک اجباری کانال

    dp.include_router(start.router)
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
    dp.include_router(games.router)
    dp.include_router(garden.router)
    dp.include_router(social.router)
    dp.include_router(creatures.router)
    dp.include_router(combat_extra.router)
    dp.include_router(admin.router)
    dp.include_router(fallback.router)  # آخر — دستور ناشناخته

    @dp.errors()
    async def _global_error(event, exception):
        logger.exception("Handler error: %s", exception)
        try:
            update = event.update
            msg = update.message or (update.callback_query.message if update.callback_query else None)
            if msg:
                await msg.answer(f"⚠️ خطا: {type(exception).__name__}")
        except Exception:
            pass
        return True

    await on_startup()
    logger.info("Bot starting (no channel lock)...")
    logger.info("Routers registered: start, profile, duel, cultivation, shop, dual, ...")
    # قطع webhook و نمونه قبلی تا Conflict نماند
    await bot.delete_webhook(drop_pending_updates=True)
    logger.info("Webhook cleared; starting polling...")
    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())
