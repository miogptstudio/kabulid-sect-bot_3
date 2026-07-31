from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from database.models_v3 import GroupDimension, VengefulSpirit
from database.models import User

DIM_TYPES = ["فانی", "بهشتی", "زیرین"]


async def get_or_create_group_dim(session: AsyncSession, chat_id: int, title: str | None = None) -> GroupDimension:
    result = await session.execute(
        select(GroupDimension).where(GroupDimension.chat_id == chat_id)
    )
    g = result.scalar_one_or_none()
    if g:
        return g
    # private chat = personal dimension
    dtype = "فانی"
    g = GroupDimension(
        chat_id=chat_id,
        name=(title or "بُعد شخصی")[:64],
        dimension_type=dtype,
    )
    session.add(g)
    await session.commit()
    await session.refresh(g)
    return g


async def set_group_dimension(session: AsyncSession, chat_id: int, dtype: str) -> GroupDimension:
    if dtype not in DIM_TYPES:
        raise ValueError("نوع نامعتبر")
    g = await get_or_create_group_dim(session, chat_id)
    g.dimension_type = dtype
    await session.commit()
    return g


async def become_vengeful(session: AsyncSession, user: User, target_id: int | None = None, reason: str = "مرگ در شکار") -> VengefulSpirit:
    # غیرفعال کردن قبلی
    result = await session.execute(
        select(VengefulSpirit).where(VengefulSpirit.user_id == user.id, VengefulSpirit.is_active == True)
    )
    for s in result.scalars().all():
        s.is_active = False
    spirit = VengefulSpirit(
        user_id=user.id,
        target_user_id=target_id,
        power=30 + (user.level or 1) * 2,
        reason=reason,
        is_active=True,
    )
    user.world = "زیرین"
    user.is_spirit_raiser = True
    user.is_dead = False  # روح فعال است
    session.add(spirit)
    await session.commit()
    await session.refresh(spirit)
    return spirit


async def release_spirit(session: AsyncSession, user: User) -> str:
    result = await session.execute(
        select(VengefulSpirit).where(VengefulSpirit.user_id == user.id, VengefulSpirit.is_active == True)
    )
    s = result.scalar_one_or_none()
    if not s:
        return "روح انتقام‌جوی فعالی نداری."
    s.is_active = False
    user.world = "فانی"
    await session.commit()
    return "از مسیر انتقام خارج شدی و به دنیای فانی برگشتی."
