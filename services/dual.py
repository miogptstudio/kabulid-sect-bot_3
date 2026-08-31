import random
from datetime import datetime, timedelta
from services.persist import get_dict as _dual_get, save as _dual_save

DUAL_COOLDOWN_MINUTES = 30
DUAL_EVOLVE_THRESHOLD = 7
from datetime import datetime
from sqlalchemy import select, or_
from sqlalchemy.ext.asyncio import AsyncSession
from database.models import User
from database.models_v3 import DualCultivation
from services.cultivation import get_or_create_cultivation, add_energy, get_active_technique

# شانس بچهدار شدن در تذهیب دوگانه
CHILD_CHANCE = 0.10  # ۱۰٪


async def request_dual(session: AsyncSession, user1: User, user2: User) -> DualCultivation | str:
    if user1.id == user2.id:
        return "نمیتونی با خودت تذهیب دوگانه کنی."
    
    # جنسیت مشخص باشد — مرد/زن، زن/زن و مرد/مرد مجاز
    g1 = user1.gender or "نامشخص"
    g2 = user2.gender or "نامشخص"

    if g1 == "نامشخص" or g2 == "نامشخص":
        return "هر دو نفر باید جنسیت خود را با /gender مشخص کرده باشند."

    if g1 not in ("مرد", "زن") or g2 not in ("مرد", "زن"):
        return "جنسیت نامعتبر. /gender"
    
    # تذهیب دوگانه هر ۳۰ دقیقه یک‌بار برای هر بازیکن؛ زمان در persist ذخیره می‌شود.
    cooldowns = _dual_get("dual_cooldowns")
    now = datetime.utcnow()
    for uid in (user1.id, user2.id):
        raw = cooldowns.get(str(uid))
        if raw:
            try:
                last = datetime.fromisoformat(raw)
                remain = timedelta(minutes=DUAL_COOLDOWN_MINUTES) - (now - last)
                if remain.total_seconds() > 0:
                    mins_total = max(1, int((remain.total_seconds() + 59) // 60))
                    hours, mins = divmod(mins_total, 60)
                    time_text = f"{hours}ساعت و {mins}دقیقه" if hours else f"{mins}دقیقه"
                    return f"⏳ تذهیب دوگانه برای {user1.full_name if uid == user1.id else user2.full_name} هنوز آماده نیست. زمان باقی‌مانده: {time_text}."
            except (ValueError, TypeError):
                cooldowns.pop(str(uid), None)

    cult1 = await get_or_create_cultivation(session, user1.id)
    cult2 = await get_or_create_cultivation(session, user2.id)
    
    if cult1.spiritual_root == "بدون ریشه":
        return "تو هنوز ریشه معنوی نداری."
    if cult2.spiritual_root == "بدون ریشه":
        return f"{user2.full_name} هنوز ریشه معنوی نداره."
    
    tech1 = await get_active_technique(session, user1.id)
    tech2 = await get_active_technique(session, user2.id)
    if not tech1:
        return "تکنیک تذهیب فعالی نداری."
    if not tech2:
        return f"{user2.full_name} تکنیک فعالی نداره."
    
    # پاک کردن درخواستهای pending قدیمیتر از ۱ ساعت
    try:
        from datetime import timedelta
        old = datetime.utcnow() - timedelta(hours=1)
        old_rows = await session.execute(
            select(DualCultivation).where(
                DualCultivation.status == "pending",
                DualCultivation.created_at < old,
            )
        )
        for row in old_rows.scalars().all():
            row.status = "expired"
        await session.commit()
    except Exception:
        pass

    existing = await session.execute(
        select(DualCultivation).where(
            DualCultivation.status.in_(["pending", "active"]),
            or_(
                DualCultivation.user1_id == user1.id,
                DualCultivation.user2_id == user1.id,
                DualCultivation.user1_id == user2.id,
                DualCultivation.user2_id == user2.id,
            )
        )
    )
    if existing.scalar_one_or_none():
        return "یکی از شما الان در تذهیب دوگانه یا درخواست باز هست. /canceldual برای لغو درخواست خودت."
    
    dual = DualCultivation(
        user1_id=user1.id,
        user2_id=user2.id,
        status="pending"
    )
    session.add(dual)
    await session.commit()
    await session.refresh(dual)
    return dual


async def accept_dual(session: AsyncSession, dual: DualCultivation, accepter_id: int) -> str:
    if dual.user2_id != accepter_id:
        return "فقط طرف مقابل میتونه قبول کنه."
    if dual.status != "pending":
        return "این درخواست دیگه معتبر نیست."
    
    dual.status = "active"
    await session.commit()

    r1, r2 = {"messages": []}, {"messages": []}
    try:
        r1 = await add_energy(session, dual.user1_id, 80)
    except Exception as e:
        r1 = {"messages": [f"خطا انرژی1: {type(e).__name__}"]}
    try:
        r2 = await add_energy(session, dual.user2_id, 80)
    except Exception as e:
        r2 = {"messages": [f"خطا انرژی2: {type(e).__name__}"]}

    dual.energy_shared = 160
    # ثبت cooldown فقط پس از موفقیت واقعی
    cooldowns = _dual_get("dual_cooldowns")
    now = datetime.utcnow()
    cooldowns[str(dual.user1_id)] = now.isoformat()
    cooldowns[str(dual.user2_id)] = now.isoformat()
    _dual_save("dual_cooldowns")
    dual.status = "finished"
    dual.finished_at = datetime.utcnow()
    await session.commit()
    
    msg = "☯️ تذهیب دوگانه انجام شد! هر دو +۸۰ انرژی گرفتند.\n"
    if r1.get("messages"):
        msg += "نفر اول: " + " | ".join(r1["messages"]) + "\n"
    if r2.get("messages"):
        msg += "نفر دوم: " + " | ".join(r2["messages"])
    
    # هر ۷ تذهیب موفق، یک تکامل ریشه ثبت می‌کند.
    progress = _dual_get("dual_evolution")
    for uid in (dual.user1_id, dual.user2_id):
        key = str(uid)
        row = progress.setdefault(key, {"count": 0, "evolution": 0})
        row["count"] = int(row.get("count", 0)) + 1
        if row["count"] % DUAL_EVOLVE_THRESHOLD == 0:
            row["evolution"] = int(row.get("evolution", 0)) + 1
            msg += f"\n🌱 <b>تکامل ریشه!</b> سطح تکامل تذهیب دوگانه: {row['evolution']}"
    _dual_save("dual_evolution")

    return msg


async def reject_dual(session: AsyncSession, dual: DualCultivation, rejecter_id: int) -> str:
    if dual.user2_id != rejecter_id and dual.user1_id != rejecter_id:
        return "دسترسی نداری."
    dual.status = "finished"
    dual.finished_at = datetime.utcnow()
    await session.commit()
    return "تذهیب دوگانه رد شد."


async def cancel_dual(session: AsyncSession, user_id: int) -> str:
    result = await session.execute(
        select(DualCultivation).where(
            DualCultivation.status == "pending",
            or_(
                DualCultivation.user1_id == user_id,
                DualCultivation.user2_id == user_id,
            )
        )
    )
    rows = list(result.scalars().all())
    if not rows:
        return "درخواست باز نداری."
    for d in rows:
        d.status = "cancelled"
    await session.commit()
    return f"✅ {len(rows)} درخواست تذهیب دوگانه لغو شد."
