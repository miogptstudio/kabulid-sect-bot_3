
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


# معادل سکه برای هر واحد ارز (از پایین به بالا)
# 1 spirit = 1000 coins
# 1 heavenly = 1000 spirit = 1_000_000 coins
# 1 celestial = 1000 heavenly = 1_000_000_000 coins
# 1 god = 1_000_000_000 celestial


def currency_to_coins(w: UserWallet) -> int:
    """کل دارایی به معادل سکه"""
    c = int(w.coins or 0)
    c += int(w.spirit_stones or 0) * COINS_PER_STONE
    c += int(getattr(w, "heavenly_stones", 0) or 0) * COINS_PER_STONE * STONE_PER_HEAVENLY
    c += int(getattr(w, "celestial_stones", 0) or 0) * COINS_PER_STONE * STONE_PER_HEAVENLY * HEAVENLY_PER_CELESTIAL
    # god stones: هر واحد = CELESTIAL_PER_GOD آسمانی
    c += int(getattr(w, "god_stones", 0) or 0) * COINS_PER_STONE * STONE_PER_HEAVENLY * HEAVENLY_PER_CELESTIAL * CELESTIAL_PER_GOD
    return c


def pay_any_currency(w: UserWallet, price_coins: int) -> tuple[bool, str]:
    """
    پرداخت قیمت (به سکه) با هر ارزی.
    اول از سکه؛ اگر کم بود از سنگ روحی، بهشتی، آسمانی، خدا به‌ترتیب کم می‌شود.
    """
    if price_coins <= 0:
        return True, "رایگان"

    total = currency_to_coins(w)
    if total < price_coins:
        return False, (
            f"❌ موجودی کافی نیست.\n"
            f"نیاز: {price_coins:,} سکه (یا معادل)\n"
            f"کل دارایی معادل: {total:,} سکه\n"
            f"سکه:{w.coins} | روحی:{w.spirit_stones or 0} | بهشتی:{getattr(w,'heavenly_stones',0) or 0} | "
            f"آسمانی:{getattr(w,'celestial_stones',0) or 0} | خدا:{getattr(w,'god_stones',0) or 0}"
        )

    remaining = price_coins
    paid_parts = []

    # 1) سکه
    take = min(int(w.coins or 0), remaining)
    if take:
        w.coins = int(w.coins or 0) - take
        remaining -= take
        paid_parts.append(f"{take:,} سکه")

    # 2) سنگ روحی
    if remaining > 0:
        spirit = int(w.spirit_stones or 0)
        need_spirit = (remaining + COINS_PER_STONE - 1) // COINS_PER_STONE  # ceil
        take_s = min(spirit, need_spirit)
        if take_s:
            w.spirit_stones = spirit - take_s
            # ارزش به سکه
            value = take_s * COINS_PER_STONE
            remaining -= value
            paid_parts.append(f"{take_s} سنگ روحی")
            # اگر بیش از نیاز بود، باقی را به سکه برگردان
            if remaining < 0:
                w.coins = int(w.coins or 0) + (-remaining)
                remaining = 0

    # 3) سنگ بهشتی
    if remaining > 0:
        unit = COINS_PER_STONE * STONE_PER_HEAVENLY  # 1e6
        have = int(getattr(w, "heavenly_stones", 0) or 0)
        need = (remaining + unit - 1) // unit
        take_h = min(have, need)
        if take_h:
            w.heavenly_stones = have - take_h
            value = take_h * unit
            remaining -= value
            paid_parts.append(f"{take_h} سنگ بهشتی")
            if remaining < 0:
                # باقی را به روحی/سکه نشکنیم ساده: به سکه
                w.coins = int(w.coins or 0) + (-remaining)
                remaining = 0

    # 4) سنگ آسمانی
    if remaining > 0:
        unit = COINS_PER_STONE * STONE_PER_HEAVENLY * HEAVENLY_PER_CELESTIAL  # 1e9
        have = int(getattr(w, "celestial_stones", 0) or 0)
        need = (remaining + unit - 1) // unit
        take_c = min(have, need)
        if take_c:
            w.celestial_stones = have - take_c
            value = take_c * unit
            remaining -= value
            paid_parts.append(f"{take_c} سنگ آسمانی")
            if remaining < 0:
                w.coins = int(w.coins or 0) + (-remaining)
                remaining = 0

    # 5) سنگ خدا
    if remaining > 0:
        unit = COINS_PER_STONE * STONE_PER_HEAVENLY * HEAVENLY_PER_CELESTIAL * CELESTIAL_PER_GOD
        have = int(getattr(w, "god_stones", 0) or 0)
        need = (remaining + unit - 1) // unit
        take_g = min(have, need)
        if take_g:
            w.god_stones = have - take_g
            value = take_g * unit
            remaining -= value
            paid_parts.append(f"{take_g} سنگ خدا")
            if remaining < 0:
                w.coins = int(w.coins or 0) + (-remaining)
                remaining = 0

    if remaining > 0:
        return False, "خطا در محاسبه پرداخت."

    detail = " + ".join(paid_parts) if paid_parts else "۰"
    return True, (
        f"پرداخت: {detail}\n"
        f"مانده → سکه:{w.coins} | روحی:{w.spirit_stones or 0} | "
        f"بهشتی:{getattr(w,'heavenly_stones',0) or 0} | "
        f"آسمانی:{getattr(w,'celestial_stones',0) or 0} | "
        f"خدا:{getattr(w,'god_stones',0) or 0}"
    )
