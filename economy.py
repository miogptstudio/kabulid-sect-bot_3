
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from database.models_v3 import UserWallet

COINS_PER_STONE = 1000
STONE_PER_HEAVENLY = 1000
HEAVENLY_PER_CELESTIAL = 1000
CELESTIAL_PER_GOD = 1_000_000_000  # ۱ سنگ خدا = ۱ میلیارد سنگ آسمانی
GOD_PER_CHAOS = 1000
CHAOS_PER_VOID = 1000
VOID_PER_ORIGIN = 1000
ORIGIN_PER_DESTINY = 1000       # ۱ تقدیر = ۱۰۰۰ ازلی
DESTINY_PER_IMMORTAL = 1000     # ۱ جاودان = ۱۰۰۰ تقدیر
IMMORTAL_PER_CREATION = 1000    # ۱ خلقت = ۱۰۰۰ جاودان
CREATION_PER_ABSOLUTE = 1000    # ۱ مطلق = ۱۰۰۰ خلقت
FAITH_PER_DRAGON = 100          # ۱ سکه اژدها = ۱۰۰ ایمان (ارز موازی)
GOD_PER_CHAOS = 1000  # ۱ هرج‌ومرج = ۱۰۰۰ خدا
CHAOS_PER_VOID = 1000
VOID_PER_ORIGIN = 1000


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
    stones = max(1, int(stones))
    w = await get_or_create_wallet(session, user_id)
    cost = stones * COINS_PER_STONE
    coins = int(w.coins or 0)
    if coins < cost:
        return f"❌ سکه کافی نیست. نیاز: {cost} (داری: {coins})"
    w.coins = coins - cost
    w.spirit_stones = int(w.spirit_stones or 0) + stones
    await session.commit()
    return f"✅ +{stones} سنگ روحی | سکه: {w.coins} | روحی: {w.spirit_stones}"


async def exchange_to_coins(session: AsyncSession, user_id: int, stones: int = 1) -> str:
    stones = max(1, int(stones))
    w = await get_or_create_wallet(session, user_id)
    have = int(w.spirit_stones or 0)
    if have < stones:
        return f"❌ سنگ روحی کافی نیست (داری: {have})"
    w.spirit_stones = have - stones
    w.coins = int(w.coins or 0) + stones * COINS_PER_STONE
    await session.commit()
    return f"✅ +{stones * COINS_PER_STONE} سکه | سکه: {w.coins} | روحی: {w.spirit_stones}"


async def exchange_up(session: AsyncSession, user_id: int, kind: str, amount: int = 1) -> str:
    """ارتقای ارز: spirit→heavenly→celestial→god"""
    w = await get_or_create_wallet(session, user_id)
    if kind == "heavenly":
        cost = amount * STONE_PER_HEAVENLY
        if int(w.spirit_stones or 0) < cost:
            return f"نیاز {cost} سنگ روحی"
        w.spirit_stones = int(w.spirit_stones or 0) - cost
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
    if kind == "chaos":
        cost = amount * GOD_PER_CHAOS
        if int(getattr(w, "god_stones", 0) or 0) < cost:
            return f"نیاز {cost} سنگ خدا"
        w.god_stones = int(w.god_stones or 0) - cost
        w.chaos_stones = int(getattr(w, "chaos_stones", 0) or 0) + amount
        await session.commit()
        return f"✅ +{amount} سنگ هرج‌ومرج"
    if kind == "void":
        cost = amount * CHAOS_PER_VOID
        if int(getattr(w, "chaos_stones", 0) or 0) < cost:
            return f"نیاز {cost} سنگ هرج‌ومرج"
        w.chaos_stones = int(w.chaos_stones or 0) - cost
        w.void_stones = int(getattr(w, "void_stones", 0) or 0) + amount
        await session.commit()
        return f"✅ +{amount} سنگ پوچی"
    if kind == "origin":
        cost = amount * VOID_PER_ORIGIN
        if int(getattr(w, "void_stones", 0) or 0) < cost:
            return f"نیاز {cost} سنگ پوچی"
        w.void_stones = int(w.void_stones or 0) - cost
        w.origin_stones = int(getattr(w, "origin_stones", 0) or 0) + amount
        await session.commit()
        return f"✅ +{amount} سنگ ازلی"
    if kind == "destiny":
        cost = amount * ORIGIN_PER_DESTINY
        if int(getattr(w, "origin_stones", 0) or 0) < cost:
            return f"نیاز {cost} سنگ ازلی"
        w.origin_stones = int(w.origin_stones or 0) - cost
        w.destiny_stones = int(getattr(w, "destiny_stones", 0) or 0) + amount
        await session.commit()
        return f"✅ +{amount} سنگ تقدیر"
    if kind == "immortal":
        cost = amount * DESTINY_PER_IMMORTAL
        if int(getattr(w, "destiny_stones", 0) or 0) < cost:
            return f"نیاز {cost} سنگ تقدیر"
        w.destiny_stones = int(w.destiny_stones or 0) - cost
        w.immortal_stones = int(getattr(w, "immortal_stones", 0) or 0) + amount
        await session.commit()
        return f"✅ +{amount} سنگ جاودان"
    if kind == "creation":
        cost = amount * IMMORTAL_PER_CREATION
        if int(getattr(w, "immortal_stones", 0) or 0) < cost:
            return f"نیاز {cost} سنگ جاودان"
        w.immortal_stones = int(w.immortal_stones or 0) - cost
        w.creation_stones = int(getattr(w, "creation_stones", 0) or 0) + amount
        await session.commit()
        return f"✅ +{amount} سنگ خلقت"
    if kind == "absolute":
        cost = amount * CREATION_PER_ABSOLUTE
        if int(getattr(w, "creation_stones", 0) or 0) < cost:
            return f"نیاز {cost} سنگ خلقت"
        w.creation_stones = int(w.creation_stones or 0) - cost
        w.absolute_stones = int(getattr(w, "absolute_stones", 0) or 0) + amount
        await session.commit()
        return f"✅ +{amount} سنگ مطلق"
    if kind == "faith":
        # از سکه اژدها یا کارما
        cost = amount * 10
        if int(getattr(w, "karma_points", 0) or 0) >= cost:
            w.karma_points = int(w.karma_points or 0) - cost
        elif int(w.coins or 0) >= cost * 1000:
            w.coins = int(w.coins or 0) - cost * 1000
        else:
            return f"نیاز {cost} کارما یا {cost*1000} سکه"
        w.faith_stones = int(getattr(w, "faith_stones", 0) or 0) + amount
        await session.commit()
        return f"✅ +{amount} سنگ ایمان"
    if kind == "dragon":
        cost = amount * FAITH_PER_DRAGON
        if int(getattr(w, "faith_stones", 0) or 0) < cost:
            return f"نیاز {cost} سنگ ایمان"
        w.faith_stones = int(w.faith_stones or 0) - cost
        w.dragon_coins = int(getattr(w, "dragon_coins", 0) or 0) + amount
        await session.commit()
        return f"✅ +{amount} سکه اژدها"
    return "نوع: heavenly celestial god chaos void origin destiny immortal creation absolute faith dragon"


async def exchange_down(session: AsyncSession, user_id: int, kind: str, amount: int = 1) -> str:
    """تبدیل ارز بالاتر به پایین‌تر
    kind: spirit (روحی→سکه) | heavenly (بهشتی→روحی) | celestial (آسمانی→بهشتی) | god (خدا→آسمانی)
    """
    amount = max(1, int(amount))
    w = await get_or_create_wallet(session, user_id)
    kind = (kind or "").strip().lower()
    aliases = {
        "spirit": "spirit", "روحی": "spirit", "سنگ‌روحی": "spirit", "stone": "spirit",
        "heavenly": "heavenly", "بهشتی": "heavenly", "heaven": "heavenly",
        "celestial": "celestial", "آسمانی": "celestial", "sky": "celestial",
        "god": "god", "خدا": "god", "godstone": "god",
        "coin": "spirit", "سکه": "spirit",  # روحی→سکه
    }
    kind = aliases.get(kind, kind)

    if kind == "spirit":
        have = int(w.spirit_stones or 0)
        if have < amount:
            return f"❌ سنگ روحی کافی نیست (داری: {have})"
        w.spirit_stones = have - amount
        gain = amount * COINS_PER_STONE
        w.coins = int(w.coins or 0) + gain
        await session.commit()
        return f"⬇️ +{gain:,} سکه (از {amount} سنگ روحی) | سکه: {w.coins} | روحی: {w.spirit_stones}"

    if kind == "heavenly":
        have = int(getattr(w, "heavenly_stones", 0) or 0)
        if have < amount:
            return f"❌ سنگ بهشتی کافی نیست (داری: {have})"
        w.heavenly_stones = have - amount
        gain = amount * STONE_PER_HEAVENLY
        w.spirit_stones = int(w.spirit_stones or 0) + gain
        await session.commit()
        return f"⬇️ +{gain:,} سنگ روحی (از {amount} بهشتی) | روحی: {w.spirit_stones} | بهشتی: {w.heavenly_stones}"

    if kind == "celestial":
        have = int(getattr(w, "celestial_stones", 0) or 0)
        if have < amount:
            return f"❌ سنگ آسمانی کافی نیست (داری: {have})"
        w.celestial_stones = have - amount
        gain = amount * HEAVENLY_PER_CELESTIAL
        w.heavenly_stones = int(getattr(w, "heavenly_stones", 0) or 0) + gain
        await session.commit()
        return f"⬇️ +{gain:,} سنگ بهشتی (از {amount} آسمانی) | بهشتی: {w.heavenly_stones} | آسمانی: {w.celestial_stones}"

    if kind == "god":
        have = int(getattr(w, "god_stones", 0) or 0)
        if have < amount:
            return f"❌ سنگ خدا کافی نیست (داری: {have})"
        w.god_stones = have - amount
        gain = amount * CELESTIAL_PER_GOD
        w.celestial_stones = int(getattr(w, "celestial_stones", 0) or 0) + gain
        await session.commit()
        return f"⬇️ +{gain:,} سنگ آسمانی (از {amount} خدا) | آسمانی: {w.celestial_stones} | خدا: {w.god_stones}"

    if kind == "chaos":
        have = int(getattr(w, "chaos_stones", 0) or 0)
        if have < amount:
            return f"❌ هرج‌ومرج کافی نیست (داری: {have})"
        w.chaos_stones = have - amount
        gain = amount * GOD_PER_CHAOS
        w.god_stones = int(getattr(w, "god_stones", 0) or 0) + gain
        await session.commit()
        return f"⬇️ +{gain:,} سنگ خدا (از {amount} هرج‌ومرج)"
    if kind == "void":
        have = int(getattr(w, "void_stones", 0) or 0)
        if have < amount:
            return f"❌ پوچی کافی نیست (داری: {have})"
        w.void_stones = have - amount
        gain = amount * CHAOS_PER_VOID
        w.chaos_stones = int(getattr(w, "chaos_stones", 0) or 0) + gain
        await session.commit()
        return f"⬇️ +{gain:,} هرج‌ومرج (از {amount} پوچی)"
    if kind == "origin":
        have = int(getattr(w, "origin_stones", 0) or 0)
        if have < amount:
            return f"❌ ازلی کافی نیست (داری: {have})"
        w.origin_stones = have - amount
        gain = amount * VOID_PER_ORIGIN
        w.void_stones = int(getattr(w, "void_stones", 0) or 0) + gain
        await session.commit()
        return f"⬇️ +{gain:,} پوچی (از {amount} ازلی)"
    return (
        "نوع نامعتبر." + chr(10)
        + "فرمت: /exchangedown spirit|heavenly|celestial|god|chaos|void|origin [n]"
    )


def wallet_text(w: UserWallet) -> str:
    return (
        f"💰 <b>کیف پول</b>\n\n"
        f"🪙 سکه: <b>{w.coins}</b>\n"
        f"💎 سنگ روحی: <b>{w.spirit_stones}</b>\n"
        f"✨ سنگ بهشتی: <b>{getattr(w, 'heavenly_stones', 0) or 0}</b>\n"
        f"🌌 سنگ آسمانی: <b>{getattr(w, 'celestial_stones', 0) or 0}</b>\n"
        f"👑 سنگ خدا: <b>{getattr(w, 'god_stones', 0) or 0}</b>\n"        f"🌪 سنگ هرج‌ومرج: <b>{getattr(w, 'chaos_stones', 0) or 0}</b>\n"        f"🕳 سنگ پوچی: <b>{getattr(w, 'void_stones', 0) or 0}</b>\n"        f"🌌 سنگ ازلی: <b>{getattr(w, 'origin_stones', 0) or 0}</b>\n"        f"☯️ کارما: <b>{getattr(w, 'karma_points', 0) or 0}</b>\n"
        f"🔮 سنگ تقدیر: <b>{getattr(w, 'destiny_stones', 0) or 0}</b>\n"
        f"♾️ سنگ جاودان: <b>{getattr(w, 'immortal_stones', 0) or 0}</b>\n"
        f"🌀 سنگ خلقت: <b>{getattr(w, 'creation_stones', 0) or 0}</b>\n"
        f"💠 سنگ مطلق: <b>{getattr(w, 'absolute_stones', 0) or 0}</b>\n"
        f"🙏 سنگ ایمان: <b>{getattr(w, 'faith_stones', 0) or 0}</b>\n"
        f"🐉 سکه اژدها: <b>{getattr(w, 'dragon_coins', 0) or 0}</b>\n\n"
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
    # سطوح بالاتر — با سقف برای جلوگیری از overflow
    try:
        unit = COINS_PER_STONE * STONE_PER_HEAVENLY * HEAVENLY_PER_CELESTIAL * CELESTIAL_PER_GOD
        c += int(getattr(w, "chaos_stones", 0) or 0) * unit * 1000
        c += int(getattr(w, "void_stones", 0) or 0) * unit * 1000 * 1000
        c += int(getattr(w, "origin_stones", 0) or 0) * unit * 1000 ** 3
        c += int(getattr(w, "destiny_stones", 0) or 0) * unit * 1000 ** 4
        c += int(getattr(w, "immortal_stones", 0) or 0) * unit * 1000 ** 5
        c += int(getattr(w, "creation_stones", 0) or 0) * unit * 1000 ** 6
        c += int(getattr(w, "absolute_stones", 0) or 0) * unit * 1000 ** 7
        c += int(getattr(w, "dragon_coins", 0) or 0) * 100_000
        c += int(getattr(w, "faith_stones", 0) or 0) * 1000
    except Exception:
        pass
    return int(c) if c < 10**18 else 10**18


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
