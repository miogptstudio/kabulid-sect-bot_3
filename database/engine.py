import os
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession
from bot.config import DATABASE_URL, DATA_DIR

def _normalize_url(url: str) -> str:
    # Render / Heroku style postgres
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


async def migrate_schema():
    """اضافه کردن ستون‌های جدید به جداول موجود (create_all ستون جدید نمی‌سازد)"""
    from sqlalchemy import text

    # users
    user_cols = [
        ("solo_count", "INTEGER DEFAULT 0"),
        ("blood", "INTEGER DEFAULT 100"),
        ("poisoned_until", "TIMESTAMP"),
        ("equipped_weapon_id", "INTEGER"),
        ("has_cyrus_sword", "BOOLEAN DEFAULT FALSE"),
        ("first_cities", "TEXT"),
        ("city", "VARCHAR(32) DEFAULT 'tehran'"),
        ("world", "VARCHAR(32) DEFAULT 'فانی'"),
        ("lifespan", "INTEGER DEFAULT 100"),
        ("is_spirit_raiser", "BOOLEAN DEFAULT FALSE"),
        ("gender", "VARCHAR(16) DEFAULT 'نامشخص'"),
        ("yang", "INTEGER DEFAULT 100"),
        ("yin", "INTEGER DEFAULT 0"),
        ("is_virgin", "BOOLEAN DEFAULT TRUE"),
        ("is_dead", "BOOLEAN DEFAULT FALSE"),
    ]
    # cultivations
    cult_cols = [
        ("body_type", "VARCHAR(64) DEFAULT 'بدن معمولی'"),
        ("afk_until", "TIMESTAMP"),
        ("spiritual_root", "VARCHAR(64)"),
        ("talent", "VARCHAR(64)"),
    ]
    # wallets if separate
    wallet_cols = [
        ("heavenly_stones", "INTEGER DEFAULT 0"),
        ("celestial_stones", "INTEGER DEFAULT 0"),
        ("god_stones", "INTEGER DEFAULT 0"),
        ("last_daily_coin", "TIMESTAMP"),
    ]

    async with engine.begin() as conn:
        dialect = conn.dialect.name  # postgresql or sqlite

        async def add_col(table: str, col: str, typedef: str):
            if dialect == "postgresql":
                sql = f'ALTER TABLE {table} ADD COLUMN IF NOT EXISTS {col} {typedef}'
            else:
                # SQLite: check pragma
                r = await conn.execute(text(f"PRAGMA table_info({table})"))
                existing = {row[1] for row in r.fetchall()}
                if col in existing:
                    return
                sql = f"ALTER TABLE {table} ADD COLUMN {col} {typedef}"
            try:
                await conn.execute(text(sql))
            except Exception:
                pass  # جدول ممکن است هنوز نباشد

        for col, td in user_cols:
            await add_col("users", col, td)
        for col, td in cult_cols:
            await add_col("cultivations", col, td)
        for col, td in wallet_cols:
            await add_col("user_wallets", col, td)
            await add_col("wallets", col, td)

        # cultivations کامل
        for col, td in [
            ("energy", "INTEGER DEFAULT 0"),
            ("stage", "INTEGER DEFAULT 1"),
            ("realm", "VARCHAR(32) DEFAULT 'بیداری'"),
            ("updated_at", "TIMESTAMP"),
        ]:
            await add_col("cultivations", col, td)

        # techniques
        for col, td in [
            ("is_starter", "BOOLEAN DEFAULT FALSE"),
            ("energy_bonus", "INTEGER DEFAULT 0"),
            ("required_root", "VARCHAR(64)"),
            ("grade", "VARCHAR(32)"),
            ("description", "TEXT"),
        ]:
            await add_col("cultivation_techniques", col, td)

        for col, td in [
            ("is_active", "BOOLEAN DEFAULT FALSE"),
            ("learned_at", "TIMESTAMP"),
        ]:
            await add_col("user_techniques", col, td)
