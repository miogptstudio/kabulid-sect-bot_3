from datetime import datetime, timedelta
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from database.models_v2 import Sect, SectMember, SECT_STATUS, SECT_TYPES
from database.models_v3 import Territory, LeadershipChallenge, BetrayalLog
from database.models import User
from services.cultivation import get_or_create_cultivation

# فقط از قلمرو «بالا» به بعد میتونه فرقه بسازه
MIN_REALM_TO_CREATE_SECT = "پیشرفته"  # بالاتر از «بالا»
REALM_ORDER = [
    "بیداری", "پایه", "متوسط", "بالا", "پیشرفته", "هسته", "روح",
    "نیمهخدا", "خدا", "آسمان", "ایتری", "جاودان", "ابدی",
    "خلقت", "پوچی", "فراپوچی", "مطلق",
]

# شمشیرهای مخصوص رتبه
RANK_SWORDS = {
    "ارجمند": "شمشیر پوچی و خلقت",
    "ارشد": "شمشیر آذرخش",
    "عضو داخلی": "شمشیر ریشه",  # بعداً با ریشه شخصیسازی میشه
}

# فاصله چالش رهبری: ۳۰ روز
LEADER_CHALLENGE_COOLDOWN_DAYS = 30
LEADER_CHALLENGE_COOLDOWN_HOURS = 1  # چالش رهبری هر ۱ ساعت


async def can_create_sect(session: AsyncSession, user: User) -> tuple[bool, str]:
    cult = await get_or_create_cultivation(session, user.id)
    try:
        order = REALM_ORDER
        try:
            from database.models_v2 import CULTIVATION_REALMS
            if cult.realm in CULTIVATION_REALMS:
                order = list(CULTIVATION_REALMS)
        except Exception:
            pass
        if order.index(cult.realm) < order.index(MIN_REALM_TO_CREATE_SECT):
            return False, f"برای ساخت فرقه باید بالاتر از «بالا» باشی (حداقل «{MIN_REALM_TO_CREATE_SECT}») — الان: {cult.realm}"
    except ValueError:
        return False, "قلمرو تذهیب نامعتبر است."
    
    existing = await get_user_sect(session, user.id)
    if existing:
        return False, "قبلاً عضو یک فرقه هستی."
    return True, ""


async def create_sect(
    session: AsyncSession,
    name: str,
    sect_type: str,
    leader: User,
    description: str = None,
    symbol: str = "⚜️",
    parent_sect: Sect | None = None
) -> Sect:
    if sect_type not in SECT_TYPES:
        raise ValueError("نوع فرقه نامعتبر است")
    
    ok, msg = await can_create_sect(session, leader)
    if not ok:
        raise ValueError(msg)
    
    from services.power import calc_power
    leader_power_data = await calc_power(session, leader)
    leader_power = int(leader_power_data.get("total") or 0)
    if parent_sect is not None:
        if not parent_sect.is_active:
            raise ValueError("فرقه مادر فعال نیست.")
        if int(parent_sect.power_level or 0) <= leader_power:
            raise ValueError("فرقه زیرمجموعه باید از فرقه مادر ضعیف‌تر باشد.")
    sect = Sect(
        name=name[:64],
        sect_type=sect_type,
        description=description or f"فرقه {name}",
        leader_id=leader.id,
        member_count=1,
        parent_sect_id=(parent_sect.id if parent_sect else None),
        leader_power=leader_power,
        power_level=max(1, leader_power),
    )
    # اگر فیلد symbol در مدل نبود، در description نگه میداریم
    session.add(sect)
    await session.flush()
    
    member = SectMember(
        user_id=leader.id,
        sect_id=sect.id,
        status="رهبر"
    )
    session.add(member)
    
    # قلمرو اولیه فرقه
    territory = Territory(
        name=f"قلمرو {name}",
        description=f"سرزمین اصلی فرقه {name}",
        owner_sect_id=sect.id,
        defense_points=100
    )
    session.add(territory)
    
    await session.commit()
    await session.refresh(sect)
    return sect


async def join_sect(session: AsyncSession, user: User, sect: Sect, tg_id: int | None = None) -> SectMember:
    # آزمون عضویت
    try:
        from services.sect_exam import has_passed
        tid = int(tg_id or getattr(user, 'telegram_id', 0) or 0)
        if tid and not has_passed(tid, sect.id):
            raise ValueError(
                f"اول آزمون عضویت را بگذران: /sectrules {sect.name} سپس /sectexam {sect.name}"
            )
    except ValueError:
        raise
    except Exception:
        pass
    existing = await session.execute(
        select(SectMember).where(SectMember.user_id == user.id)
    )
    if existing.scalar_one_or_none():
        raise ValueError("قبلاً عضو یک فرقه هستی")
    
    member = SectMember(
        user_id=user.id,
        sect_id=sect.id,
        status="عضو دستههای پایینتر"
    )
    session.add(member)
    sect.member_count += 1
    await session.commit()
    return member


async def promote_sect_status(session: AsyncSession, member: SectMember) -> str | None:
    try:
        idx = SECT_STATUS.index(member.status)
        if idx < len(SECT_STATUS) - 1:
            member.status = SECT_STATUS[idx + 1]
            await session.commit()
            return member.status
    except ValueError:
        pass
    return None


async def get_user_sect(session: AsyncSession, user_id: int) -> SectMember | None:
    result = await session.execute(
        select(SectMember).where(SectMember.user_id == user_id)
    )
    return result.scalar_one_or_none()


async def add_contribution(session: AsyncSession, user_id: int, points: int) -> int:
    membership = await get_user_sect(session, user_id)
    if not membership:
        return 0
    membership.contribution_points += points
    sect = await session.get(Sect, membership.sect_id)
    if sect:
        sect.total_points += points
    await session.commit()
    return membership.contribution_points


async def get_rank_sword(user: User, cult_root: str | None = None) -> str | None:
    """شمشیر مخصوص بر اساس رتبه"""
    if user.rank == "ارجمند":
        return RANK_SWORDS["ارجمند"]
    if user.rank == "ارشد":
        return RANK_SWORDS["ارشد"]
    if user.rank in ("عضو داخلی",) or "داخلی" in (user.rank or ""):
        root = cult_root or "معمولی"
        return f"شمشیر {root}"
    return None


async def challenge_leader(session: AsyncSession, challenger: User, sect: Sect) -> LeadershipChallenge | str:
    if sect.leader_id == challenger.id:
        return "تو خودت رهبر هستی."
    
    membership = await get_user_sect(session, challenger.id)
    if not membership or membership.sect_id != sect.id:
        return "فقط اعضای همین فرقه میتونن چالش بدن."
    
    # فقط یک چالش در ماه
    hour_ago = datetime.utcnow() - timedelta(hours=LEADER_CHALLENGE_COOLDOWN_HOURS)
    recent = await session.execute(
        select(LeadershipChallenge).where(
            LeadershipChallenge.sect_id == sect.id,
            LeadershipChallenge.challenger_id == challenger.id,
            LeadershipChallenge.created_at >= hour_ago
        )
    )
    if recent.scalar_one_or_none():
        return f"هر {LEADER_CHALLENGE_COOLDOWN_HOURS} ساعت فقط یکبار میتونی چالش رهبری بدی."
    
    challenge = LeadershipChallenge(
        sect_id=sect.id,
        challenger_id=challenger.id,
        leader_id=sect.leader_id,
        status="pending"
    )
    session.add(challenge)
    await session.commit()
    await session.refresh(challenge)
    return challenge


async def resolve_challenge(session: AsyncSession, challenge: LeadershipChallenge, challenger_won: bool) -> str:
    if challenge.status != "pending":
        return "این چالش دیگه معتبر نیست."
    
    challenge.resolved_at = datetime.utcnow()
    if challenger_won:
        challenge.status = "won"
        sect = await session.get(Sect, challenge.sect_id)
        if sect:
            sect.leader_id = challenge.challenger_id
        await session.commit()
        return "⚔️ چالش موفق! رهبر جدید فرقه شدی."
    else:
        challenge.status = "lost"
        await session.commit()
        # اگر چالشگر از نظر قلمرو ضعیفتر باشد → مرگ معلق تا بخشش رهبر
        from database.models_v3 import Territory
        from sqlalchemy import select, func
        sect = await session.get(Sect, challenge.sect_id)
        terr = await session.execute(
            select(func.count()).select_from(Territory).where(Territory.owner_sect_id == challenge.sect_id)
        )
        # mark challenger for death unless pardoned - return special code
        return "LOST_NEED_PARDON"


async def betray_sect(session: AsyncSession, user: User, reason: str = None) -> str:
    membership = await get_user_sect(session, user.id)
    if not membership:
        return "عضو هیچ فرقهای نیستی."
    
    sect = await session.get(Sect, membership.sect_id)
    if sect and sect.leader_id == user.id:
        return "رهبر نمیتونه خیانت کنه. اول رهبری رو واگذار کن."
    
    log = BetrayalLog(
        user_id=user.id,
        from_sect_id=membership.sect_id,
        reason=reason
    )
    session.add(log)
    
    if sect:
        sect.member_count = max(0, sect.member_count - 1)
    
    await session.delete(membership)
    await session.commit()
    return f"🗡️ به فرقه خیانت کردی و خارج شدی. حالا تذهیبکننده دورهگرد هستی."


async def conquer_territory(session: AsyncSession, attacker_sect: Sect, territory: Territory) -> str:
    if territory.owner_sect_id == attacker_sect.id:
        return "این قلمرو مال خودته."
    
    # ساده: اگر امتیاز فرقه مهاجم بیشتر باشه، تصاحب میشه
    if attacker_sect.total_points >= territory.defense_points:
        old = territory.owner_sect_id
        territory.owner_sect_id = attacker_sect.id
        territory.defense_points += 20
        await session.commit()
        return f"🏰 قلمرو «{territory.name}» تصاحب شد!"
    return f"دفاع قلمرو قویتر از امتیاز فرقه توست (نیاز: {territory.defense_points} امتیاز)."


async def transfer_leadership(session: AsyncSession, leader: User, new_leader: User) -> str:
    membership_l = await get_user_sect(session, leader.id)
    membership_n = await get_user_sect(session, new_leader.id)
    if not membership_l:
        return "عضو فرقه نیستی."
    sect = await session.get(Sect, membership_l.sect_id)
    if not sect or sect.leader_id != leader.id:
        return "فقط رهبر فعلی میتواند رهبری را واگذار کند."
    if not membership_n or membership_n.sect_id != sect.id:
        return "فرد جدید باید عضو همین فرقه باشد."
    sect.leader_id = new_leader.id
    await session.commit()
    return f"👑 رهبری فرقه «{sect.name}» به {new_leader.full_name} واگذار شد."


async def refresh_sect_power(session: AsyncSession, sect: Sect) -> int:
    """قدرت فرقه از قدرت رهبر + مشارکت اعضا مشتق می‌شود."""
    leader = await session.get(User, sect.leader_id) if sect.leader_id else None
    leader_power = 0
    if leader:
        from services.power import calc_power
        leader_power = int((await calc_power(session, leader)).get("total") or 0)
    sect.leader_power = leader_power
    sect.power_level = max(1, leader_power + int(sect.total_points or 0))
    await session.commit()
    return int(sect.power_level)


async def list_subsects(session: AsyncSession, parent_id: int):
    result = await session.execute(select(Sect).where(Sect.parent_sect_id == int(parent_id), Sect.is_active == True))
    return result.scalars().all()
