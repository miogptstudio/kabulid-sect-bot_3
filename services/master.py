from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from database.models_v2 import MasterDisciple
from database.models import User


async def take_disciple(session: AsyncSession, master: User, disciple: User) -> MasterDisciple:
    # چک کن شاگرد قبلاً استاد نداشته باشه
    existing = await session.execute(
        select(MasterDisciple).where(
            MasterDisciple.disciple_id == disciple.id,
            MasterDisciple.status == "active"
        )
    )
    if existing.scalar_one_or_none():
        raise ValueError("این نفر قبلاً استاد داره")
    
    # چک کن خودش شاگرد نباشه
    as_disciple = await session.execute(
        select(MasterDisciple).where(
            MasterDisciple.disciple_id == master.id,
            MasterDisciple.status == "active"
        )
    )
    if as_disciple.scalar_one_or_none():
        raise ValueError("تو خودت شاگرد هستی و نمی‌تونی استاد بشی")
    
    relation = MasterDisciple(
        master_id=master.id,
        disciple_id=disciple.id
    )
    session.add(relation)
    await session.commit()
    await session.refresh(relation)
    return relation


async def get_disciples(session: AsyncSession, master_id: int) -> list:
    result = await session.execute(
        select(MasterDisciple).where(
            MasterDisciple.master_id == master_id,
            MasterDisciple.status == "active"
        )
    )
    return result.scalars().all()


async def get_master(session: AsyncSession, disciple_id: int) -> MasterDisciple | None:
    result = await session.execute(
        select(MasterDisciple).where(
            MasterDisciple.disciple_id == disciple_id,
            MasterDisciple.status == "active"
        )
    )
    return result.scalar_one_or_none()
