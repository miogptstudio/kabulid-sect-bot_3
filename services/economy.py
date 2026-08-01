
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from database.models_v3 import UserWallet

COINS_PER_STONE = 1000
STONE_PER_HEAVENLY = 1000
HEAVENLY_PER_CELESTIAL = 1000
CELESTIAL_PER_GOD = 1_000_000_000  # ۱ سنگ خدا = ۱ میلیارد سنگ آسمانی


async def get_or_create_wallet(session: AsyncSession, user_id: int) -> UserWallet:
    result = await session.execute(
        select(UserWallet).where(UserWallet.user_id == user_id)
    )
    w = result.scalar_one_or_none()
    if w:
        return w
    w = UserWallet(user_id=user_id, coins=50)
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
        return f"❌ سکه کافی نیست. نیاز: {cost} (داری: {w.coins})"
    w.coins -= cost
    w.spirit_stones += stones
    await session.commit()
    return f"✅ +{stones} سنگ روحی | سکه: {w.coins} | روحی: {w.spirit_stones}"


async def exchange_to_coins(session: AsyncSession, user_id: int, stones: int = 1) -> str:
    w = await get_or_create_wallet(session, user_id)
    if w.spirit_stones < stones:
        return f"❌ سنگ روحی کافی نیست (داری: {w.spirit_stones})"
    w.spirit_stones -= stones
    w.coins += stones * COINS_PER_STONE
    await session.commit()
    return f"✅ +{stones * COINS_PER_STONE} سکه | سکه: {w.coins} | روحی: {w.spirit_stones}"


async def exchange_up(session: AsyncSession, user_id: int, kind: str, amount: int = 1) -> str:
    """ارتقای ارز: spirit→heavenly→celestial→god"""
    w = await get_or_create_wallet(session, user_id)
    if kind == "heavenly":
        cost = amount * STONE_PER_HEAVENLY
        if (w.spirit_stones or 0) < cost:
            return f"نیاز {cost} سنگ روحی"
        w.spirit_stones -= cost
        w.heavenly_stones = (w.heavenly_stones or 0) + amount
        await session.commit()
        return f"✅ +{amount} سنگ بهشتی"
    if kind == "celestial":
        cost = amount * HEAVENLY_PER_CELESTIAL
        if (w.heavenly_stones or 0) < cost:
            return f"نیاز {cost} سنگ بهشتی"
        w.heavenly_stones -= cost
        w.celestial_stones = (w.celestial_stones or 0) + amount
        await session.commit()
        return f"✅ +{amount} سنگ آسمانی"
    if kind == "god":
        cost = amount * CELESTIAL_PER_GOD
        if (w.celestial_stones or 0) < cost:
            return f"نیاز {cost} سنگ آسمانی (۱ سنگ خدا = ۱٬۰۰۰٬۰۰۰٬۰۰۰ آسمانی)"
        w.celestial_stones -= cost
        w.god_stones = (w.god_stones or 0) + amount
        await session.commit()
        return f"✅ +{amount} سنگ خدا"
    return "نوع نامعتبر: heavenly | celestial | god"


def wallet_text(w: UserWallet) -> str:
    return (
        f"💰 <b>کیف پول</b>\n\n"
        f"🪙 سکه: <b>{w.coins}</b>\n"
        f"💎 سنگ روحی: <b>{w.spirit_stones}</b>\n"
        f"✨ سنگ بهشتی: <b>{getattr(w, 'heavenly_stones', 0) or 0}</b>\n"
        f"🌌 سنگ آسمانی: <b>{getattr(w, 'celestial_stones', 0) or 0}</b>\n"
        f"👑 سنگ خدا: <b>{getattr(w, 'god_stones', 0) or 0}</b>\n\n"
        f"تبدیل:\n"
        f"۱۰۰۰ سکه → ۱ روحی\n"
        f"۱۰۰۰ روحی → ۱ بهشتی\n"
        f"۱۰۰۰ بهشتی → ۱ آسمانی\n"
        f"۱٬۰۰۰٬۰۰۰٬۰۰۰ آسمانی → ۱ خدا\n"
        f"/exchangestone · /exchangeup heavenly|celestial|god"
    )
