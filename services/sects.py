from datetime import datetime, timedelta
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from database.models_v2 import Sect, SectMember, SECT_STATUS, SECT_TYPES
from database.models_v3 import Territory, LeadershipChallenge, BetrayalLog
from database.models import User
from services.cultivation import get_or_create_cultivation

# فقط از قلمرو «بالا» به بعد می‌تونه فرقه بسازه
MIN_REALM_TO_CREATE_SECT = "بالا"
REALM_ORDER = ["پایه", "متوسط", "بالا", "پیشرفته", "خدا"]

# شمشیرهای مخصوص رتبه
RANK_SWORDS = {
    "ارجمند": "شمشیر پوچی و خلقت",
    "ارشد": "شمشیر آذرخش",
    "عضو داخلی": "شمشیر ریشه",  # بعداً با ریشه شخصی‌سازی می‌شه
}

# فاصله چالش رهبری: ۳۰ روز
LEADER_CHALLENGE_COOLDOWN_DAYS = 30


async def can_create_sect(session: AsyncSession, user: User) -> tuple[bool, str]:
    cult = await get_or_create_cultivation(session, user.id)
    try:
        if REALM_ORDER.index(cult.realm) < REALM_ORDER.index(MIN_REALM_TO_CREATE_SECT):
            return False, f"برای ساخت فرقه باید حداقل قلمرو «{MIN_REALM_TO_CREATE_SECT}» باشی (الان: {cult.realm})"
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
    symbol: str = "⚜️"
) -> Sect:
    if sect_type not in SECT_TYPES:
        raise ValueError("نوع فرقه نامعتبر است")
    
    ok, msg = await can_create_sect(session, leader)
    if not ok:
        raise ValueError(msg)
    
    sect = Sect(
        name=name,
        sect_type=sect_type,
        description=description or f"فرقه {name}",
        leader_id=leader.id,
        member_count=1
    )
    # اگر فیلد symbol در مدل نبود، در description نگه می‌داریم
    session.add(sect)
    await session.flush()
    
    member = SectMember(
        user_id=leader.id,
        sect_id=sect.id,
        status="عضو داخلی فرقه"
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


async def join_sect(session: AsyncSession, user: User, sect: Sect) -> SectMember:
    existing = await session.execute(
        select(SectMember).where(SectMember.user_id == user.id)
    )
    if existing.scalar_one_or_none():
        raise ValueError("قبلاً عضو یک فرقه هستی")
    
    member = SectMember(
        user_id=user.id,
        sect_id=sect.id,
        status="عضو دسته‌های پایین‌تر"
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
        return "فقط اعضای همین فرقه می‌تونن چالش بدن."
    
    # فقط یک چالش در ماه
    month_ago = datetime.utcnow() - timedelta(days=LEADER_CHALLENGE_COOLDOWN_DAYS)
    recent = await session.execute(
        select(LeadershipChallenge).where(
            LeadershipChallenge.sect_id == sect.id,
            LeadershipChallenge.challenger_id == challenger.id,
            LeadershipChallenge.created_at >= month_ago
        )
    )
    if recent.scalar_one_or_none():
        return f"هر {LEADER_CHALLENGE_COOLDOWN_DAYS} روز فقط یک‌بار می‌تونی چالش رهبری بدی."
    
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
        return "⚔️ چالش موفق! رهبر جدید فرقه شدی. (فقط رهبری فرقه عوض شد، نه کل ربات)"
    else:
        challenge.status = "lost"
        await session.commit()
        return "چالش شکست خورد. رهبر سر جاش ماند."


async def betray_sect(session: AsyncSession, user: User, reason: str = None) -> str:
    membership = await get_user_sect(session, user.id)
    if not membership:
        return "عضو هیچ فرقه‌ای نیستی."
    
    sect = await session.get(Sect, membership.sect_id)
    if sect and sect.leader_id == user.id:
        return "رهبر نمی‌تونه خیانت کنه. اول رهبری رو واگذار کن."
    
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
    return f"🗡️ به فرقه خیانت کردی و خارج شدی. حالا تذهیب‌کننده دوره‌گرد هستی."


async def conquer_territory(session: AsyncSession, attacker_sect: Sect, territory: Territory) -> str:
    if territory.owner_sect_id == attacker_sect.id:
        return "این قلمرو مال خودته."
    
    # ساده: اگر امتیاز فرقه مهاجم بیشتر باشه، تصاحب می‌شه
    if attacker_sect.total_points >= territory.defense_points:
        old = territory.owner_sect_id
        territory.owner_sect_id = attacker_sect.id
        territory.defense_points += 20
        await session.commit()
        return f"🏰 قلمرو «{territory.name}» تصاحب شد!"
    return f"دفاع قلمرو قوی‌تر از امتیاز فرقه توست (نیاز: {territory.defense_points} امتیاز)."
