import random
from datetime import datetime
from sqlalchemy import select, desc
from sqlalchemy.ext.asyncio import AsyncSession
from database.models_v2 import ArenaProfile, ArenaMatch
from database.models import User
from services.power import calc_power, win_chance
from services.economy import get_or_create_wallet

# درجه‌ها از پایین به بالا
ARENA_TIERS_FULL = ["برنز", "نقره", "طلا", "الماس", "بهشتی", "آسمانی", "خدایان"]

# امتیاز لازم برای نگه داشتن/رسیدن به درجه
TIER_POINTS = {
    "برنز": 0,
    "نقره": 100,
    "طلا": 250,
    "الماس": 500,
    "بهشتی": 1000,
    "آسمانی": 2000,
    "خدایان": 4000,
}

# هزینه ورود به هر آرنا: (نوع ارز, مقدار)
# spirit=سنگ روحی, heavenly=بهشتی, celestial=آسمانی, god=خدا, coins=سکه
ENTRY_COST = {
    "برنز": ("spirit", 1),          # ۱ سنگ روحی (جایگزین: ۱۰۰۰ سکه در کد)
    "نقره": ("spirit", 500),        # ۵۰۰ سنگ روحی
    "طلا": ("heavenly", 1),         # ۱ سنگ بهشتی
    "الماس": ("heavenly", 500),     # ۵۰۰ سنگ بهشتی
    "بهشتی": ("celestial", 1),      # ۱ سنگ آسمانی
    "آسمانی": ("celestial", 500),   # ۵۰۰ سنگ آسمانی
    "خدایان": ("god", 1),           # ۱ سنگ خدا
}

BRONZE_COIN_ALT = 1000  # اگر سنگ روحی نداشت، ۱۰۰۰ سکه برای برنز


def entry_cost_text(tier: str) -> str:
    kind, amount = ENTRY_COST.get(tier, ("spirit", 1))
    names = {
        "spirit": "سنگ روحی",
        "heavenly": "سنگ بهشتی",
        "celestial": "سنگ آسمانی",
        "god": "سنگ خدا",
        "coins": "سکه",
    }
    t = f"{amount} {names.get(kind, kind)}"
    if tier == "برنز":
        t += f" (یا {BRONZE_COIN_ALT} سکه)"
    return t


async def can_pay_entry(session: AsyncSession, user_id: int, tier: str) -> tuple[bool, str]:
    w = await get_or_create_wallet(session, user_id)
    kind, amount = ENTRY_COST.get(tier, ("spirit", 1))
    if kind == "spirit":
        if (w.spirit_stones or 0) >= amount:
            return True, ""
        if tier == "برنز" and (w.coins or 0) >= BRONZE_COIN_ALT:
            return True, ""
        return False, f"نیاز: {entry_cost_text(tier)} | روحی: {w.spirit_stones} | سکه: {w.coins}"
    if kind == "heavenly":
        if (w.heavenly_stones or 0) >= amount:
            return True, ""
        return False, f"نیاز: {entry_cost_text(tier)} | بهشتی: {w.heavenly_stones or 0}"
    if kind == "celestial":
        if (w.celestial_stones or 0) >= amount:
            return True, ""
        return False, f"نیاز: {entry_cost_text(tier)} | آسمانی: {w.celestial_stones or 0}"
    if kind == "god":
        if (w.god_stones or 0) >= amount:
            return True, ""
        return False, f"نیاز: {entry_cost_text(tier)} | خدا: {w.god_stones or 0}"
    return False, "هزینه نامعتبر"


async def charge_entry(session: AsyncSession, user_id: int, tier: str) -> str:
    """کم کردن هزینه ورود. در صورت موفقیت پیام خالی یا توضیح."""
    w = await get_or_create_wallet(session, user_id)
    kind, amount = ENTRY_COST.get(tier, ("spirit", 1))
    if kind == "spirit":
        if (w.spirit_stones or 0) >= amount:
            w.spirit_stones -= amount
            return f"−{amount} سنگ روحی"
        if tier == "برنز" and w.coins >= BRONZE_COIN_ALT:
            w.coins -= BRONZE_COIN_ALT
            return f"−{BRONZE_COIN_ALT} سکه"
        raise ValueError("هزینه ورود پرداخت نشد")
    if kind == "heavenly":
        if (w.heavenly_stones or 0) < amount:
            raise ValueError("سنگ بهشتی کافی نیست")
        w.heavenly_stones -= amount
        return f"−{amount} سنگ بهشتی"
    if kind == "celestial":
        if (w.celestial_stones or 0) < amount:
            raise ValueError("سنگ آسمانی کافی نیست")
        w.celestial_stones -= amount
        return f"−{amount} سنگ آسمانی"
    if kind == "god":
        if (w.god_stones or 0) < amount:
            raise ValueError("سنگ خدا کافی نیست")
        w.god_stones -= amount
        return f"−{amount} سنگ خدا"
    raise ValueError("نوع هزینه نامعتبر")


async def get_or_create_arena_profile(session: AsyncSession, user_id: int) -> ArenaProfile:
    result = await session.execute(
        select(ArenaProfile).where(ArenaProfile.user_id == user_id)
    )
    profile = result.scalar_one_or_none()
    if profile:
        return profile
    profile = ArenaProfile(user_id=user_id, tier="برنز", points=0)
    session.add(profile)
    await session.commit()
    await session.refresh(profile)
    return profile


def _update_tier(profile: ArenaProfile) -> str | None:
    old = profile.tier if profile.tier in ARENA_TIERS_FULL else "برنز"
    pts = profile.points
    new_tier = "برنز"
    for tier in ARENA_TIERS_FULL:
        if pts >= TIER_POINTS[tier]:
            new_tier = tier
    profile.tier = new_tier
    if new_tier != old:
        try:
            if ARENA_TIERS_FULL.index(new_tier) > ARENA_TIERS_FULL.index(old):
                return f"🎖️ ارتقا آرنا: {old} → <b>{new_tier}</b>!"
            return f"📉 سقوط آرنا: {old} → <b>{new_tier}</b>"
        except ValueError:
            return f"درجه: <b>{new_tier}</b>"
    return None


def match_tier(tier_a: str, tier_b: str) -> str:
    """درجه مسابقه = بالاترین درجه بین دو نفر (سخت‌گیرتر)"""
    try:
        ia = ARENA_TIERS_FULL.index(tier_a if tier_a in ARENA_TIERS_FULL else "برنز")
        ib = ARENA_TIERS_FULL.index(tier_b if tier_b in ARENA_TIERS_FULL else "برنز")
        return ARENA_TIERS_FULL[max(ia, ib)]
    except ValueError:
        return "برنز"


async def process_arena_result(
    session: AsyncSession,
    winner: User,
    loser: User,
) -> tuple[str, ArenaProfile, ArenaProfile]:
    wp = await get_or_create_arena_profile(session, winner.id)
    lp = await get_or_create_arena_profile(session, loser.id)

    wp.wins += 1
    wp.points += 15
    wp.season_points += 15
    lp.losses += 1
    lp.points = max(0, lp.points - 8)

    msgs = []
    m1 = _update_tier(wp)
    m2 = _update_tier(lp)
    if m1:
        msgs.append(m1)
    if m2:
        msgs.append(m2)

    reward = {
        "برنز": 20, "نقره": 40, "طلا": 70, "الماس": 100,
        "بهشتی": 150, "آسمانی": 250, "خدایان": 500,
    }.get(wp.tier, 20)
    try:
        w = await get_or_create_wallet(session, winner.id)
        w.coins += reward
        msgs.append(f"🪙 جایزه: +{reward} سکه")
    except Exception:
        pass

    session.add(ArenaMatch(
        player1_id=winner.id,
        player2_id=loser.id,
        winner_id=winner.id,
        tier=wp.tier,
        finished_at=datetime.utcnow(),
    ))
    await session.commit()
    return "\n".join(msgs), wp, lp


async def run_arena_fight(session: AsyncSession, p1: User, p2: User) -> str:
    power1 = await calc_power(session, p1)
    power2 = await calc_power(session, p2)
    # بر اساس قدرت — بدون شانس تصادفی
    if power1["total"] > power2["total"]:
        winner, loser = p1, p2
    elif power2["total"] > power1["total"]:
        winner, loser = p2, p1
    else:
        winner, loser = (p1, p2) if random.random() < 0.5 else (p2, p1)

    extra, wprof, lprof = await process_arena_result(session, winner, loser)
    text = (
        "🏟️ <b>نتیجه آرنا</b>" + chr(10) + chr(10)
        + f"{p1.full_name} ({power1['total']}) vs {p2.full_name} ({power2['total']})" + chr(10)
        + "⚖️ بر اساس قدرت" + chr(10) + chr(10)
        + f"🏆 برنده: <b>{winner.full_name}</b>" + chr(10)
        + f"درجه: {wprof.tier} | امتیاز: {wprof.points}" + chr(10)
        + f"بازنده: {loser.full_name} ({lprof.tier} | {lprof.points})" + chr(10)
    )
    if extra:
        text += chr(10) + str(extra)
    return text



async def arena_leaderboard(session: AsyncSession, limit: int = 10) -> str:
    result = await session.execute(
        select(ArenaProfile, User)
        .join(User, ArenaProfile.user_id == User.id)
        .order_by(desc(ArenaProfile.points))
        .limit(limit)
    )
    rows = result.all()
    if not rows:
        return "هنوز کسی در آرنا امتیاز ندارد."
    text = "🏟️ <b>لیدربورد آرنا</b>\n\n"
    for i, (prof, user) in enumerate(rows, 1):
        text += f"{i}. {user.full_name} — {prof.tier} | {prof.points} ({prof.wins}W/{prof.losses}L)\n"
    return text


# --- آرنای چندنفره باز ---
_open_rooms: dict[int, dict] = {}  # room_id -> {host, players: [user_ids], names: {}, tier, started}


def create_open_room(host_id: int, host_name: str, tier: str = "برنز") -> int:
    rid = host_id  # یک اتاق باز به ازای هر میزبان
    _open_rooms[rid] = {
        "host": host_id,
        "players": [host_id],
        "names": {host_id: host_name},
        "tier": tier if tier in ARENA_TIERS_FULL else "برنز",
        "started": False,
    }
    return rid


def join_open_room(room_id: int, user_id: int, name: str) -> str:
    room = _open_rooms.get(room_id)
    if not room:
        return "اتاق پیدا نشد."
    if room["started"]:
        return "مسابقه شروع شده."
    if user_id in room["players"]:
        return "قبلاً داخل هستی."
    if len(room["players"]) >= 10:
        return "ظرفیت پر است (حداکثر ۱۰)."
    room["players"].append(user_id)
    room["names"][user_id] = name
    return f"وارد شدی. نفرات: {len(room['players'])}/10"


def list_open_rooms() -> str:
    if not _open_rooms:
        return "اتاق بازی بازی نیست. /arenaopen برای ساخت."
    text = "🏟️ <b>اتاق‌های آرنای چندنفره</b>\n\n"
    for rid, r in _open_rooms.items():
        if r["started"]:
            continue
        text += (
            f"#{rid} — {r['tier']} | {len(r['players'])}/10 نفر\n"
            f"میزبان: {r['names'].get(r['host'], rid)}\n"
            f"ورود: /arenajoin {rid}\n\n"
        )
    return text or "اتاقی باز نیست."


async def start_open_arena(session: AsyncSession, room_id: int, starter_id: int) -> str:
    room = _open_rooms.get(room_id)
    if not room:
        return "اتاق نیست."
    if room["host"] != starter_id:
        return "فقط میزبان می‌تواند شروع کند."
    if len(room["players"]) < 3:
        return f"حداقل ۳ نفر لازم است (الان {len(room['players'])})."
    if len(room["players"]) > 10:
        return "حداکثر ۱۰ نفر."
    tier = room["tier"]
    # هزینه ورود همه
    for uid in room["players"]:
        ok, err = await can_pay_entry(session, uid, tier)
        if not ok:
            name = room["names"].get(uid, str(uid))
            return f"{name} هزینه ورود ندارد:\n{err}"
    fees = []
    for uid in room["players"]:
        fees.append(await charge_entry(session, uid, tier))
    await session.commit()

    # شبیه‌سازی مسابقه: بر اساس قدرت، یک برنده
    from database.models import User
    fighters = []
    for uid in room["players"]:
        u = await session.get(User, uid)
        if u:
            pw = await calc_power(session, u)
            fighters.append((u, pw["total"]))
    if len(fighters) < 3:
        return "بازیکن معتبر کافی نیست."
    fighters.sort(key=lambda x: x[1], reverse=True)
    # فقط قدرت — بدون شانس
    winner = fighters[0][0]
    # امتیاز
    wp = await get_or_create_arena_profile(session, winner.id)
    wp.wins += 1
    wp.points += 25
    wp.season_points += 25
    msg_tier = _update_tier(wp)
    for u, _ in fighters[1:]:
        lp = await get_or_create_arena_profile(session, u.id)
        lp.losses += 1
        lp.points = max(0, lp.points - 5)
        _update_tier(lp)
    try:
        w = await get_or_create_wallet(session, winner.id)
        w.coins += 50
    except Exception:
        pass
    await session.commit()
    room["started"] = True
    del _open_rooms[room_id]
    ranking = "\n".join(
        f"{i}. {u.full_name} ({pwr})" for i, (u, pwr) in enumerate(fighters, 1)
    )
    text = (
        f"🏟️ <b>آرنای چندنفره تمام شد</b>\n"
        f"درجه: {tier}\n\n"
        f"🏆 برنده: <b>{winner.full_name}</b> +۲۵ امتیاز +۵۰ سکه\n"
    )
    if msg_tier:
        text += msg_tier + "\n"
    text += f"\nترتیب قدرت:\n{ranking}"
    return text
