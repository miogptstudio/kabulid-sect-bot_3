from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from database.models_v3 import UserWallet

COINS_PER_STONE = 1000


async def get_or_create_wallet(session: AsyncSession, user_id: int) -> UserWallet:
    result = await session.execute(
        select(UserWallet).where(UserWallet.user_id == user_id)
    )
    w = result.scalar_one_or_none()
    if w:
        return w
    w = UserWallet(user_id=user_id, coins=50)  # سکه شروع
    session.add(w)
    await session.commit()
    await session.refresh(w)
    return w


async def add_coins(session: AsyncSession, user_id: int, amount: int) -> int:
    w = await get_or_create_wallet(session, user_id)
    w.coins += amount
    await session.commit()
    return w.coins


async def exchange_to_stones(session: AsyncSession, user_id: int, stones: int = 1) -> str:
    w = await get_or_create_wallet(session, user_id)
    cost = stones * COINS_PER_STONE
    if w.coins < cost:
        return f"❌ سکه کافی نیست. نیاز: {cost} سکه (داری: {w.coins})"
    w.coins -= cost
    w.spirit_stones += stones
    await session.commit()
    return f"✅ {stones} سنگ روحی گرفتی.\nسکه باقی: {w.coins} | سنگ روحی: {w.spirit_stones}"


async def exchange_to_coins(session: AsyncSession, user_id: int, stones: int = 1) -> str:
    w = await get_or_create_wallet(session, user_id)
    if w.spirit_stones < stones:
        return f"❌ سنگ روحی کافی نیست (داری: {w.spirit_stones})"
    w.spirit_stones -= stones
    w.coins += stones * COINS_PER_STONE
    await session.commit()
    return f"✅ {stones * COINS_PER_STONE} سکه گرفتی.\nسکه: {w.coins} | سنگ: {w.spirit_stones}"
