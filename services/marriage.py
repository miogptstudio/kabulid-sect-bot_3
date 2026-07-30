from datetime import datetime, timedelta
from sqlalchemy import select, or_, and_
from sqlalchemy.ext.asyncio import AsyncSession
from database.models import User
from database.models_v3 import Marriage

ENGAGE_HOURS = 48  # مهلت نامزدی
LEVEL_DIFF_WARN = 2  # اختلاف سطح برای هشدار


async def get_wives(session: AsyncSession, husband_id: int) -> list:
    result = await session.execute(
        select(Marriage).where(
            Marriage.husband_id == husband_id,
            Marriage.status == "married"
        )
    )
    return result.scalars().all()


async def get_husband(session: AsyncSession, wife_id: int) -> Marriage | None:
    result = await session.execute(
        select(Marriage).where(
            Marriage.wife_id == wife_id,
            Marriage.status == "married"
        )
    )
    return result.scalar_one_or_none()


async def get_active_relation(session: AsyncSession, user_id: int) -> list[Marriage]:
    """همه روابط pending/engaged/married مربوط به کاربر"""
    result = await session.execute(
        select(Marriage).where(
            or_(Marriage.husband_id == user_id, Marriage.wife_id == user_id),
            Marriage.status.in_(["pending", "engaged", "married"])
        )
    )
    return list(result.scalars().all())


async def _sect_info(session: AsyncSession, user_id: int):
    try:
        from services.sects import get_user_sect
        from database.models_v2 import Sect
        membership = await get_user_sect(session, user_id)
        if not membership:
            return None, None
        sect = await session.get(Sect, membership.sect_id)
        return membership, sect
    except Exception:
        return None, None


async def propose(session: AsyncSession, proposer: User, target: User) -> tuple[Marriage | None, str, list[str]]:
    """
    برمی‌گرداند: (marriage یا None, پیام خطا یا خالی, لیست هشدارها)
    """
    warnings: list[str] = []

    if proposer.id == target.id:
        return None, "نمی‌تونی با خودت ازدواج کنی.", []

    g1 = proposer.gender or "نامشخص"
    g2 = target.gender or "نامشخص"

    if g1 == "نامشخص" or g2 == "نامشخص":
        return None, "هر دو باید با /gender جنسیت مشخص کرده باشن.", []

    if g1 != "مرد":
        return None, "فعلاً فقط مرد می‌تونه درخواست ازدواج بده.", []
    if g2 != "زن":
        return None, "فقط می‌تونی از یک زن درخواست ازدواج کنی.", []

    existing_wife = await get_husband(session, target.id)
    if existing_wife:
        return None, f"{target.full_name} قبلاً متاهل است.", []

    # درخواست/نامزدی باز قبلی
    pending = await session.execute(
        select(Marriage).where(
            Marriage.husband_id == proposer.id,
            Marriage.wife_id == target.id,
            Marriage.status.in_(["pending", "engaged"])
        )
    )
    if pending.scalar_one_or_none():
        return None, "درخواست یا نامزدی باز بین شما وجود داره.", []

    # هشدار اختلاف سطح (بدون اجبار) — هرچه اختلاف بیشتر، هشدار جدی‌تر
    level_diff = abs((proposer.level or 1) - (target.level or 1))
    level_warn = level_diff >= LEVEL_DIFF_WARN
    if level_diff >= 5:
        warnings.append(
            f"🚨🚨 <b>هشدار بسیار جدی اختلاف سطح</b>\n"
            f"{proposer.full_name}: سطح {proposer.level} | {target.full_name}: سطح {target.level}\n"
            f"اختلاف: <b>{level_diff} سطح</b>\n"
            f"این فاصله خیلی زیاد است. ریسک نارضایتی و فشار اجتماعی بالاست.\n"
            f"با این حال ازدواج <b>فقط با رضایت آزادانه دو طرف</b> ممکن است — هیچ اجباری وجود ندارد."
        )
    elif level_diff > 2:
        warnings.append(
            f"🚨 <b>هشدار جدی اختلاف سطح</b>\n"
            f"{proposer.full_name}: سطح {proposer.level} | {target.full_name}: سطح {target.level}\n"
            f"اختلاف: <b>{level_diff} سطح</b> (بیش از ۲ سطح)\n"
            f"لطفاً با دقت تصمیم بگیرید. ازدواج فقط با رضایت دو طرف است."
        )
    elif level_diff == 2:
        warnings.append(
            f"⚠️ هشدار اختلاف سطح: {proposer.full_name} (سطح {proposer.level}) و "
            f"{target.full_name} (سطح {target.level}) — اختلاف ۲ سطح.\n"
            f"ازدواج همچنان فقط با رضایت دو طرف است."
        )

    # محدودیت / هشدار فرقه‌ای
    cross_sect = False
    m1, s1 = await _sect_info(session, proposer.id)
    m2, s2 = await _sect_info(session, target.id)
    if s1 and s2:
        if s1.id != s2.id:
            cross_sect = True
            warnings.append(
                f"⚠️ ازدواج بین‌فرقه‌ای: «{s1.name}» ({s1.sect_type}) و «{s2.name}» ({s2.sect_type})."
            )
            if s1.sect_type == "شیطانی" and s2.sect_type == "ارتدوکس":
                warnings.append("⚠️ تضاد شدید نوعی فرقه‌ها (شیطانی / ارتدوکس). بزرگان ممکن است مخالفت کنند — باز هم فقط با رضایت ممکن است.")
            elif s1.sect_type == "ارتدوکس" and s2.sect_type == "شیطانی":
                warnings.append("⚠️ تضاد شدید نوعی فرقه‌ها (ارتدوکس / شیطانی). باز هم فقط با رضایت ممکن است.")
        else:
            warnings.append(f"✅ هر دو عضو فرقه «{s1.name}» هستید.")
    elif not s1 and not s2:
        warnings.append("هر دو بدون فرقه (تذهیب‌کننده دوره‌گرد) هستید.")
    else:
        cross_sect = True
        warnings.append("⚠️ یکی عضو فرقه است و دیگری نیست.")

    expires = datetime.utcnow() + timedelta(hours=ENGAGE_HOURS)
    m = Marriage(
        husband_id=proposer.id,
        wife_id=target.id,
        status="engaged",  # نامزدی با مهلت
        invited_guests=[],
        level_warning=level_warn,
        cross_sect_warning=cross_sect,
        engage_expires_at=expires,
    )
    session.add(m)
    await session.commit()
    await session.refresh(m)
    return m, "", warnings


async def accept_marriage(session: AsyncSession, marriage: Marriage, accepter_id: int) -> str:
    if marriage.wife_id != accepter_id:
        return "فقط طرف مقابل (زن) می‌تونه قبول کنه."

    if marriage.status not in ("pending", "engaged"):
        return "این درخواست دیگه معتبر نیست."

    # مهلت نامزدی
    if marriage.engage_expires_at and datetime.utcnow() > marriage.engage_expires_at:
        marriage.status = "expired"
        await session.commit()
        return "⏰ مهلت نامزدی تمام شده. درخواست منقضی شد."

    existing = await get_husband(session, accepter_id)
    if existing:
        return "تو قبلاً متاهل هستی."

    marriage.status = "married"
    marriage.married_at = datetime.utcnow()
    await session.commit()
    return "💍 عروسی انجام شد! حالا زن و شوهر هستید. (با رضایت دو طرف)"


async def reject_marriage(session: AsyncSession, marriage: Marriage, rejecter_id: int) -> str:
    if marriage.wife_id != rejecter_id and marriage.husband_id != rejecter_id:
        return "دسترسی نداری."
    if marriage.status not in ("pending", "engaged"):
        return "این درخواست معتبر نیست."
    marriage.status = "expired"
    await session.commit()
    return "درخواست / نامزدی رد شد. هیچ ازدواج اجباری وجود ندارد."


async def add_guest(session: AsyncSession, marriage: Marriage, guest_telegram_id: int) -> str:
    if marriage.status not in ("engaged", "married"):
        return "فقط برای نامزدی یا ازدواج فعال می‌توان مهمان دعوت کرد."
    guests = list(marriage.invited_guests or [])
    if guest_telegram_id in guests:
        return "این نفر قبلاً دعوت شده."
    guests.append(guest_telegram_id)
    marriage.invited_guests = guests
    await session.commit()
    return "✅ به لیست مهمان‌ها اضافه شد."


async def divorce(session: AsyncSession, user: User, partner_id: int) -> str:
    result = await session.execute(
        select(Marriage).where(
            Marriage.status == "married",
            or_(
                and_(Marriage.husband_id == user.id, Marriage.wife_id == partner_id),
                and_(Marriage.wife_id == user.id, Marriage.husband_id == partner_id),
            )
        )
    )
    m = result.scalar_one_or_none()
    if not m:
        return "ازدواجی با این شخص پیدا نشد."
    m.status = "divorced"
    m.divorced_at = datetime.utcnow()
    await session.commit()
    return "💔 ازدواج با رضایت فسخ شد. هر دو آزاد هستید."


async def expire_old_engagements(session: AsyncSession) -> int:
    """منقضی کردن نامزدی‌های تمام‌شده"""
    now = datetime.utcnow()
    result = await session.execute(
        select(Marriage).where(
            Marriage.status == "engaged",
            Marriage.engage_expires_at != None,
            Marriage.engage_expires_at < now,
        )
    )
    count = 0
    for m in result.scalars().all():
        m.status = "expired"
        count += 1
    if count:
        await session.commit()
    return count
