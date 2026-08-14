import os
import logging
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession
from sqlalchemy import text
from bot.config import DATABASE_URL, DATA_DIR

logger = logging.getLogger(__name__)


def _normalize_url(url: str) -> str:
    if url.startswith("postgres://"):
        url = url.replace("postgres://", "postgresql+asyncpg://", 1)
    elif url.startswith("postgresql://") and "+asyncpg" not in url:
        url = url.replace("postgresql://", "postgresql+asyncpg://", 1)
    return url


os.makedirs(DATA_DIR, exist_ok=True)
_url = _normalize_url(DATABASE_URL)
engine = create_async_engine(_url, echo=False)
async_session = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)


async def get_session() -> AsyncSession:
    async with async_session() as session:
        yield session


# ستون‌هایی که ممکن است در دیتابیس قدیمی نباشند
USER_COLUMNS = [
    ("solo_count", "INTEGER DEFAULT 0"),
    ("blood", "INTEGER DEFAULT 100"),
    ("poisoned_until", "TIMESTAMP NULL"),
    ("equipped_weapon_id", "INTEGER NULL"),
    ("has_cyrus_sword", "BOOLEAN DEFAULT FALSE"),
    ("first_cities", "TEXT NULL"),
    ("city", "VARCHAR(64) DEFAULT 'tehran'"),
    ("world", "VARCHAR(64) DEFAULT 'فانی'"),
    ("lifespan", "INTEGER DEFAULT 100"),
    ("is_spirit_raiser", "BOOLEAN DEFAULT FALSE"),
    ("gender", "VARCHAR(16) DEFAULT 'نامشخص'"),
    ("yang", "INTEGER DEFAULT 100"),
    ("yin", "INTEGER DEFAULT 0"),
    ("is_virgin", "BOOLEAN DEFAULT TRUE"),
    ("is_dead", "BOOLEAN DEFAULT FALSE"),
    ("race", "VARCHAR(32) DEFAULT 'انسان'"),
    ("language", "VARCHAR(8) DEFAULT 'fa'"),
    ("garden_slots", "INTEGER DEFAULT 10"),
    ("last_plant_at", "TIMESTAMP NULL"),
    ("pet_slots", "INTEGER DEFAULT 10"),
    ("last_hunt_at", "TIMESTAMP NULL"),
    ("restricted_until", "TIMESTAMP NULL"),
    ("restriction_reason", "TEXT NULL"),
]

CULT_COLUMNS = [
    ("body_type", "VARCHAR(64) DEFAULT 'بدن معمولی'"),
    ("afk_until", "TIMESTAMP NULL"),
    ("spiritual_root", "VARCHAR(64) NULL"),
    ("talent", "VARCHAR(64) NULL"),
    ("energy", "INTEGER DEFAULT 0"),
    ("stage", "INTEGER DEFAULT 1"),
    ("realm", "VARCHAR(32) DEFAULT 'بیداری'"),
]

WALLET_COLUMNS = [
    ("coins", "INTEGER DEFAULT 0"),
    ("spirit_stones", "INTEGER DEFAULT 0"),
    ("last_daily_coin", "TIMESTAMP NULL"),
    ("heavenly_stones", "INTEGER DEFAULT 0"),
    ("celestial_stones", "INTEGER DEFAULT 0"),
    ("god_stones", "INTEGER DEFAULT 0"),
    ("chaos_stones", "INTEGER DEFAULT 0"),
    ("void_stones", "INTEGER DEFAULT 0"),
    ("origin_stones", "INTEGER DEFAULT 0"),
    ("karma_points", "INTEGER DEFAULT 0"),
    ("destiny_stones", "INTEGER DEFAULT 0"),
    ("immortal_stones", "INTEGER DEFAULT 0"),
    ("creation_stones", "INTEGER DEFAULT 0"),
    ("absolute_stones", "INTEGER DEFAULT 0"),
    ("faith_stones", "INTEGER DEFAULT 0"),
    ("dragon_coins", "INTEGER DEFAULT 0"),
]

TECH_COLUMNS = [
    ("is_starter", "BOOLEAN DEFAULT FALSE"),
    ("energy_bonus", "INTEGER DEFAULT 0"),
    ("required_root", "VARCHAR(64) NULL"),
    ("grade", "VARCHAR(32) NULL"),
    ("description", "TEXT NULL"),
]


async def migrate_schema():
    """اجباری: اضافه کردن ستون‌های گمشده به PostgreSQL / SQLite"""
    added = 0
    async with engine.begin() as conn:
        dialect = conn.dialect.name
        logger.info("Running migrate_schema on dialect=%s", dialect)

        async def add_col(table: str, col: str, typedef: str):
            nonlocal added
            try:
                if dialect == "postgresql":
                    sql = f'ALTER TABLE "{table}" ADD COLUMN IF NOT EXISTS "{col}" {typedef}'
                    await conn.execute(text(sql))
                    added += 1
                    logger.info("OK column %s.%s", table, col)
                else:
                    r = await conn.execute(text(f"PRAGMA table_info({table})"))
                    existing = {row[1] for row in r.fetchall()}
                    if col in existing:
                        return
                    await conn.execute(text(f"ALTER TABLE {table} ADD COLUMN {col} {typedef}"))
                    added += 1
                    logger.info("OK sqlite column %s.%s", table, col)
            except Exception as e:
                logger.warning("skip %s.%s: %s", table, col, e)

        for col, td in USER_COLUMNS:
            await add_col("users", col, td)
        for col, td in CULT_COLUMNS:
            await add_col("cultivations", col, td)
        for col, td in WALLET_COLUMNS:
            await add_col("user_wallets", col, td)
        for col, td in TECH_COLUMNS:
            await add_col("cultivation_techniques", col, td)

        # user_techniques
        for col, td in [
            ("is_active", "BOOLEAN DEFAULT FALSE"),
            ("learned_at", "TIMESTAMP NULL"),
        ]:
            await add_col("user_techniques", col, td)

        # جدول کلید-مقدار پایدار
        try:
            await conn.execute(text(
                "CREATE TABLE IF NOT EXISTS persist_kv ("
                "ns VARCHAR(64) PRIMARY KEY, payload TEXT NOT NULL, "
                "updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP)"
            ))
            logger.info("OK table persist_kv")
        except Exception as e:
            logger.warning("persist_kv: %s", e)

    logger.info("migrate_schema finished, attempted adds=%s", added)
