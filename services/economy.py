
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
GOD_PER_CHAOS = 1000  # ۱ هرجومرج = ۱۰۰۰ خدا
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
    """ارتقای ارز در کل زنجیره"""
    amount = max(1, int(amount))
    w = await get_or_create_wallet(session, user_id)
    kind = (kind or "").strip().lower()
    aliases = {
        "heavenly": "heavenly", "بهشتی": "heavenly", "heaven": "heavenly",
        "celestial": "celestial", "آسمانی": "celestial", "sky": "celestial",
        "god": "god", "خدا": "god",
        "chaos": "chaos", "هرجومرج": "chaos",
        "void": "void", "پوچی": "void",
        "origin": "origin", "ازلی": "origin",
        "destiny": "destiny", "تقدیر": "destiny",
        "immortal": "immortal", "جاودان": "immortal",
        "creation": "creation", "خلقت": "creation",
        "absolute": "absolute", "مطلق": "absolute",
        "faith": "faith", "ایمان": "faith",
        "dragon": "dragon", "اژدها": "dragon",
    }
    kind = aliases.get(kind, kind)
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
        return f"✅ +{amount} سنگ هرجومرج"
    if kind == "void":
        cost = amount * CHAOS_PER_VOID
        if int(getattr(w, "chaos_stones", 0) or 0) < cost:
            return f"نیاز {cost} سنگ هرجومرج"
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
    """تبدیل ارز بالاتر به یک پله پایین‌تر — کل زنجیره پشتیبانی می‌شود.
    spirit→سکه | heavenly→spirit | celestial→heavenly | god→celestial |
    chaos→god | void→chaos | origin→void | destiny→origin |
    immortal→destiny | creation→immortal | absolute→creation
    """
    amount = max(1, int(amount))
    w = await get_or_create_wallet(session, user_id)
    kind = (kind or "").strip().lower()
    aliases = {
        "spirit": "spirit", "روحی": "spirit", "سنگروحی": "spirit", "stone": "spirit",
        "heavenly": "heavenly", "بهشتی": "heavenly", "heaven": "heavenly",
        "celestial": "celestial", "آسمانی": "celestial", "sky": "celestial",
        "god": "god", "خدا": "god", "godstone": "god",
        "chaos": "chaos", "هرجومرج": "chaos", "chaos_stones": "chaos",
        "void": "void", "پوچی": "void", "void_stones": "void",
        "origin": "origin", "ازلی": "origin", "origin_stones": "origin",
        "destiny": "destiny", "تقدیر": "destiny", "destiny_stones": "destiny",
        "immortal": "immortal", "جاودان": "immortal", "immortal_stones": "immortal",
        "creation": "creation", "خلقت": "creation", "creation_stones": "creation",
        "absolute": "absolute", "مطلق": "absolute", "absolute_stones": "absolute",
        "dragon": "dragon", "اژدها": "dragon", "dragon_coins": "dragon",
        "faith": "faith", "ایمان": "faith", "faith_stones": "faith",
        "coin": "spirit", "سکه": "spirit",
    }
    kind = aliases.get(kind, kind)

    # (attr, lower_attr, rate, label, lower_label)
    chain = {
        "spirit": ("spirit_stones", "coins", COINS_PER_STONE, "سنگ روحی", "سکه"),
        "heavenly": ("heavenly_stones", "spirit_stones", STONE_PER_HEAVENLY, "سنگ بهشتی", "سنگ روحی"),
        "celestial": ("celestial_stones", "heavenly_stones", HEAVENLY_PER_CELESTIAL, "سنگ آسمانی", "سنگ بهشتی"),
        "god": ("god_stones", "celestial_stones", CELESTIAL_PER_GOD, "سنگ خدا", "سنگ آسمانی"),
        "chaos": ("chaos_stones", "god_stones", GOD_PER_CHAOS, "سنگ هرجومرج", "سنگ خدا"),
        "void": ("void_stones", "chaos_stones", CHAOS_PER_VOID, "سنگ پوچی", "سنگ هرجومرج"),
        "origin": ("origin_stones", "void_stones", VOID_PER_ORIGIN, "سنگ ازلی", "سنگ پوچی"),
        "destiny": ("destiny_stones", "origin_stones", ORIGIN_PER_DESTINY, "سنگ تقدیر", "سنگ ازلی"),
        "immortal": ("immortal_stones", "destiny_stones", DESTINY_PER_IMMORTAL, "سنگ جاودان", "سنگ تقدیر"),
        "creation": ("creation_stones", "immortal_stones", IMMORTAL_PER_CREATION, "سنگ خلقت", "سنگ جاودان"),
        "absolute": ("absolute_stones", "creation_stones", CREATION_PER_ABSOLUTE, "سنگ مطلق", "سنگ خلقت"),
        "dragon": ("dragon_coins", "faith_stones", FAITH_PER_DRAGON, "سکه اژدها", "سنگ ایمان"),
        "faith": ("faith_stones", "coins", 1000, "سنگ ایمان", "سکه"),
    }
    if kind not in chain:
        return (
            "نوع نامعتبر.\n"
            "فرمت: /exchangedown spirit|heavenly|celestial|god|chaos|void|origin|destiny|immortal|creation|absolute|dragon|faith [n]\n"
            "مثال: /exchangedown absolute 1  → مطلق به خلقت"
        )
    attr, lower, rate, label, lower_label = chain[kind]
    have = int(getattr(w, attr, 0) or 0)
    if have < amount:
        return f"❌ {label} کافی نیست (داری: {have:,})"
    setattr(w, attr, have - amount)
    gain = amount * rate
    setattr(w, lower, int(getattr(w, lower, 0) or 0) + gain)
    await session.commit()
    new_high = int(getattr(w, attr, 0) or 0)
    new_low = int(getattr(w, lower, 0) or 0)
    return (
        f"⬇️ تبدیل شد: −{amount:,} {label} → +{gain:,} {lower_label}" + chr(10)
        + f"{label}: {new_high:,} | {lower_label}: {new_low:,}"
    )




def wallet_text(w: UserWallet) -> str:
    nl = chr(10)
    return (
        f"💰 <b>کیف پول</b>{nl}{nl}"
        f"🪙 سکه: <b>{int(w.coins or 0):,}</b>{nl}"
        f"💎 سنگ روحی: <b>{int(w.spirit_stones or 0):,}</b>{nl}"
        f"✨ سنگ بهشتی: <b>{int(getattr(w, 'heavenly_stones', 0) or 0):,}</b>{nl}"
        f"🌌 سنگ آسمانی: <b>{int(getattr(w, 'celestial_stones', 0) or 0):,}</b>{nl}"
        f"👑 سنگ خدا: <b>{int(getattr(w, 'god_stones', 0) or 0):,}</b>{nl}"
        f"🌪 سنگ هرجومرج: <b>{int(getattr(w, 'chaos_stones', 0) or 0):,}</b>{nl}"
        f"🕳 سنگ پوچی: <b>{int(getattr(w, 'void_stones', 0) or 0):,}</b>{nl}"
        f"🌌 سنگ ازلی: <b>{int(getattr(w, 'origin_stones', 0) or 0):,}</b>{nl}"
        f"🔮 سنگ تقدیر: <b>{int(getattr(w, 'destiny_stones', 0) or 0):,}</b>{nl}"
        f"♾️ سنگ جاودان: <b>{int(getattr(w, 'immortal_stones', 0) or 0):,}</b>{nl}"
        f"🌀 سنگ خلقت: <b>{int(getattr(w, 'creation_stones', 0) or 0):,}</b>{nl}"
        f"💠 سنگ مطلق: <b>{int(getattr(w, 'absolute_stones', 0) or 0):,}</b>{nl}"
        f"🙏 سنگ ایمان: <b>{int(getattr(w, 'faith_stones', 0) or 0):,}</b>{nl}"
        f"🐉 سکه اژدها: <b>{int(getattr(w, 'dragon_coins', 0) or 0):,}</b>{nl}"
        f"🪶 جوهر ازلی: <b>{int(getattr(w, 'eternal_ink', 0) or 0):,}</b>{nl}{nl}"
        f"تبدیل: /convert up|down نوع تعداد{nl}"
        f"/exchangeup · /exchangedown{nl}"
        f"زنجیره: سکه↔روحی↔بهشتی↔آسمانی↔خدا↔هرجومرج↔پوچی↔ازلی↔تقدیر↔جاودان↔خلقت↔مطلق"
    )




# معادل سکه برای هر واحد ارز (از پایین به بالا)
# 1 spirit = 1000 coins
# 1 heavenly = 1000 spirit = 1_000_000 coins
# 1 celestial = 1000 heavenly = 1_000_000_000 coins
# 1 god = 1_000_000_000 celestial


def currency_to_coins(w: UserWallet) -> int:
    """ارزش کل کیف به معادل سکه؛ بدون سقف مصنوعی پایتونی."""
    c = int(w.coins or 0)
    c += int(w.spirit_stones or 0) * COINS_PER_STONE
    c += int(getattr(w, "heavenly_stones", 0) or 0) * COINS_PER_STONE * STONE_PER_HEAVENLY
    c += int(getattr(w, "celestial_stones", 0) or 0) * COINS_PER_STONE * STONE_PER_HEAVENLY * HEAVENLY_PER_CELESTIAL
    god_unit = COINS_PER_STONE * STONE_PER_HEAVENLY * HEAVENLY_PER_CELESTIAL * CELESTIAL_PER_GOD
    c += int(getattr(w, "god_stones", 0) or 0) * god_unit
    c += int(getattr(w, "chaos_stones", 0) or 0) * god_unit * GOD_PER_CHAOS
    c += int(getattr(w, "void_stones", 0) or 0) * god_unit * GOD_PER_CHAOS * CHAOS_PER_VOID
    c += int(getattr(w, "origin_stones", 0) or 0) * god_unit * GOD_PER_CHAOS * CHAOS_PER_VOID * VOID_PER_ORIGIN
    c += int(getattr(w, "destiny_stones", 0) or 0) * god_unit * 1000 ** 4
    c += int(getattr(w, "immortal_stones", 0) or 0) * god_unit * 1000 ** 5
    c += int(getattr(w, "creation_stones", 0) or 0) * god_unit * 1000 ** 6
    c += int(getattr(w, "absolute_stones", 0) or 0) * god_unit * 1000 ** 7
    c += int(getattr(w, "dragon_coins", 0) or 0) * 100_000
    c += int(getattr(w, "faith_stones", 0) or 0) * 1_000
    return int(c)


CURRENCY_ALIASES = {
    "coin": "coins", "coins": "coins", "سکه": "coins",
    "spirit": "spirit_stones", "spirit_stone": "spirit_stones", "روحی": "spirit_stones", "سنگ روحی": "spirit_stones",
    "heavenly": "heavenly_stones", "heaven": "heavenly_stones", "بهشتی": "heavenly_stones", "سنگ بهشتی": "heavenly_stones",
    "celestial": "celestial_stones", "sky": "celestial_stones", "آسمانی": "celestial_stones", "سنگ آسمانی": "celestial_stones",
    "god": "god_stones", "godstone": "god_stones", "خدا": "god_stones", "سنگ خدا": "god_stones",
    "chaos": "chaos_stones", "هرج و مرج": "chaos_stones", "هرجومرج": "chaos_stones", "سنگ هرج و مرج": "chaos_stones",
    "void": "void_stones", "پوچی": "void_stones", "سنگ پوچی": "void_stones",
    "origin": "origin_stones", "ازلی": "origin_stones", "سنگ ازلی": "origin_stones",
    "destiny": "destiny_stones", "تقدیر": "destiny_stones", "سنگ تقدیر": "destiny_stones",
    "immortal": "immortal_stones", "جاودان": "immortal_stones", "سنگ جاودان": "immortal_stones",
    "creation": "creation_stones", "خلقت": "creation_stones", "سنگ خلقت": "creation_stones",
    "absolute": "absolute_stones", "مطلق": "absolute_stones", "سنگ مطلق": "absolute_stones",
    "faith": "faith_stones", "ایمان": "faith_stones", "سنگ ایمان": "faith_stones",
    "dragon": "dragon_coins", "dragon_coin": "dragon_coins", "اژدها": "dragon_coins", "سکه اژدها": "dragon_coins", "ink": "eternal_ink", "جوهر": "eternal_ink", "جوهر ازلی": "eternal_ink",
}


def normalize_currency(value: str | None) -> str | None:
    if not value:
        return None
    v = str(value).strip().lower()
    for ch in ("‌", "‏", "‎", "﻿"):
        v = v.replace(ch, "")
    v = " ".join(v.split())
    return CURRENCY_ALIASES.get(v, v)


def pay_specific_currency(w: UserWallet, amount: int, currency: str) -> tuple[bool, str]:
    """پرداخت دقیق با یک ارز؛ برای آیتمهایی که قیمتشان ارز خاص دارد."""
    amount = int(amount or 0)
    key = normalize_currency(currency)
    if amount <= 0:
        return True, "رایگان"
    if not key or not hasattr(w, key):
        return False, "❌ ارز پرداخت نامعتبر است."
    have = int(getattr(w, key) or 0)
    if have < amount:
        return False, f"❌ {currency} کافی نیست. نیاز: {amount:,} | داری: {have:,}"
    setattr(w, key, have - amount)
    return True, f"پرداخت: {amount:,} {currency}"


def pay_any_currency(w: UserWallet, price_coins: int) -> tuple[bool, str]:
    """پرداخت قیمت بر حسب سکه با امکان استفاده از ارزهای بالاتر.
    ارزهای زنجیرهای از سکه تا مطلق قابل خرد شدناند؛ ارزهای موازی نیز
    (ایمان/اژدها) با نرخ مستقل به سکه تبدیل میشوند تا باعث خطای خرید نشوند.
    """
    price_coins = int(price_coins or 0)
    if price_coins <= 0:
        return True, "رایگان"

    chain = [
        ("coins", 1, "سکه"),
        ("spirit_stones", COINS_PER_STONE, "سنگ روحی"),
        ("heavenly_stones", COINS_PER_STONE * STONE_PER_HEAVENLY, "سنگ بهشتی"),
        ("celestial_stones", COINS_PER_STONE * STONE_PER_HEAVENLY * HEAVENLY_PER_CELESTIAL, "سنگ آسمانی"),
        ("god_stones", COINS_PER_STONE * STONE_PER_HEAVENLY * HEAVENLY_PER_CELESTIAL * CELESTIAL_PER_GOD, "سنگ خدا"),
        ("chaos_stones", COINS_PER_STONE * STONE_PER_HEAVENLY * HEAVENLY_PER_CELESTIAL * CELESTIAL_PER_GOD * GOD_PER_CHAOS, "سنگ هرجومرج"),
        ("void_stones", COINS_PER_STONE * STONE_PER_HEAVENLY * HEAVENLY_PER_CELESTIAL * CELESTIAL_PER_GOD * GOD_PER_CHAOS * CHAOS_PER_VOID, "سنگ پوچی"),
        ("origin_stones", COINS_PER_STONE * STONE_PER_HEAVENLY * HEAVENLY_PER_CELESTIAL * CELESTIAL_PER_GOD * GOD_PER_CHAOS * CHAOS_PER_VOID * VOID_PER_ORIGIN, "سنگ ازلی"),
        ("destiny_stones", COINS_PER_STONE * STONE_PER_HEAVENLY * HEAVENLY_PER_CELESTIAL * CELESTIAL_PER_GOD * GOD_PER_CHAOS * CHAOS_PER_VOID * VOID_PER_ORIGIN * ORIGIN_PER_DESTINY, "سنگ تقدیر"),
        ("immortal_stones", COINS_PER_STONE * STONE_PER_HEAVENLY * HEAVENLY_PER_CELESTIAL * CELESTIAL_PER_GOD * GOD_PER_CHAOS * CHAOS_PER_VOID * VOID_PER_ORIGIN * ORIGIN_PER_DESTINY * DESTINY_PER_IMMORTAL, "سنگ جاودان"),
        ("creation_stones", COINS_PER_STONE * STONE_PER_HEAVENLY * HEAVENLY_PER_CELESTIAL * CELESTIAL_PER_GOD * GOD_PER_CHAOS * CHAOS_PER_VOID * VOID_PER_ORIGIN * ORIGIN_PER_DESTINY * DESTINY_PER_IMMORTAL * IMMORTAL_PER_CREATION, "سنگ خلقت"),
        ("absolute_stones", COINS_PER_STONE * STONE_PER_HEAVENLY * HEAVENLY_PER_CELESTIAL * CELESTIAL_PER_GOD * GOD_PER_CHAOS * CHAOS_PER_VOID * VOID_PER_ORIGIN * ORIGIN_PER_DESTINY * DESTINY_PER_IMMORTAL * IMMORTAL_PER_CREATION * CREATION_PER_ABSOLUTE, "سنگ مطلق"),
    ]
    parallel = [
        ("faith_stones", FAITH_PER_DRAGON * 1000, "سنگ ایمان"),
        ("dragon_coins", 100_000, "سکه اژدها"),
    ]
    total = sum(int(getattr(w,k,0) or 0) * unit for k,unit,_ in chain + parallel)
    if total < price_coins:
        return False, f"❌ موجودی کافی نیست. نیاز: {price_coins:,} سکه یا معادل ارزهای بالاتر | دارایی معادل: {total:,} سکه"

    # Pay the smallest denominations first, then consume one or more higher units.
    remaining = price_coins
    paid=[]
    # For exact payment, process low-to-high and break the first higher unit when needed.
    for i,(key,unit,label) in enumerate(chain):
        if remaining <= 0: break
        have=int(getattr(w,key,0) or 0)
        take=min(have, remaining//unit)
        if take:
            setattr(w,key,have-take); remaining-=take*unit; paid.append(f"{take:,} {label}")
        if remaining>0 and have-take>0 and remaining < unit:
            ratio=unit//chain[i-1][1] if i>0 else 0
            if ratio:
                # break exactly one higher unit into the previous denomination
                setattr(w,key,have-take-1)
                low_key,low_unit,low_label=chain[i-1]
                setattr(w,low_key,int(getattr(w,low_key,0) or 0)+ratio)
                low_have=int(getattr(w,low_key,0) or 0)
                low_take=(remaining+low_unit-1)//low_unit
                if low_take*low_unit > ratio and i==1:
                    low_take=ratio
                setattr(w,low_key,low_have-low_take)
                remaining=max(0, remaining-low_take*low_unit)
                paid.append(f"{low_take:,} {low_label} (تبدیل ۱ {label})")
    # Parallel currencies are consumed only if the main chain is insufficient.
    if remaining>0:
        for key,unit,label in parallel:
            have=int(getattr(w,key,0) or 0)
            if not have: continue
            take=(remaining+unit-1)//unit
            if take<=have:
                setattr(w,key,have-take); remaining=0
                paid.append(f"{take:,} {label}")
                break
    if remaining>0:
        # Rollback is safest: this function is called before commit, but callers may continue.
        return False, "❌ خطا در محاسبه پرداخت؛ خرید انجام نشد."
    return True, "پرداخت: " + " + ".join(paid)
