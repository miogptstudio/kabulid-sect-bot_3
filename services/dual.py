import random
from datetime import datetime
from sqlalchemy import select, or_
from sqlalchemy.ext.asyncio import AsyncSession
from database.models import User
from database.models_v3 import DualCultivation
from services.cultivation import get_or_create_cultivation, add_energy, get_active_technique

# شانس بچه‌دار شدن در تذهیب دوگانه
CHILD_CHANCE = 0.000009  # ۰/۰۰۰۰۰۹


async def request_dual(session: AsyncSession, user1: User, user2: User) -> DualCultivation | str:
    if user1.id == user2.id:
        return "نمی‌تونی با خودت تذهیب دوگانه کنی."
    
    # جنسیت: باید یکی مرد و یکی زن باشه
    g1 = user1.gender or "نامشخص"
    g2 = user2.gender or "نامشخص"
    
    if g1 == "نامشخص" or g2 == "نامشخص":
        return "هر دو نفر باید جنسیت خود را با /gender مشخص کرده باشند."
    
    if g1 == g2:
        return "تذهیب دوگانه فقط بین مرد و زن ممکن است."
    
    if {g1, g2} != {"مرد", "زن"}:
        return "تذهیب دوگانه فقط بین یک مرد و یک زن قبول می‌شود."
    
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
        return "یکی از شما الان در تذهیب دوگانه یا درخواست باز هست."
    
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
        return "فقط طرف مقابل می‌تونه قبول کنه."
    if dual.status != "pending":
        return "این درخواست دیگه معتبر نیست."
    
    dual.status = "active"
    await session.commit()
    
    r1 = await add_energy(session, dual.user1_id, 40)
    r2 = await add_energy(session, dual.user2_id, 40)
    
    dual.energy_shared = 80
    # از دست دادن باکرگی
    u1 = await session.get(User, dual.user1_id)
    u2 = await session.get(User, dual.user2_id)
    if u1:
        u1.is_virgin = False
    if u2:
        u2.is_virgin = False
    dual.status = "finished"
    dual.finished_at = datetime.utcnow()
    await session.commit()
    
    msg = "☯️ تذهیب دوگانه انجام شد! هر دو +۴۰ انرژی گرفتن.\n"
    if r1.get("messages"):
        msg += "نفر اول: " + " | ".join(r1["messages"]) + "\n"
    if r2.get("messages"):
        msg += "نفر دوم: " + " | ".join(r2["messages"])
    
    # شانس بچه‌دار شدن
    if random.random() < CHILD_CHANCE:
        from database.models import User
        u1 = await session.get(User, dual.user1_id)
        u2 = await session.get(User, dual.user2_id)
        child_name = f"فرزند {u1.full_name[:8]} و {u2.full_name[:8]}"
        
        # ثبت یک یوزر مجازی به عنوان فرزند (telegram_id منفی برای غیرواقعی بودن)
        child = User(
            telegram_id=-(dual.user1_id * 100000 + dual.user2_id),  # آیدی مصنوعی یکتا
            full_name=child_name,
            gender=random.choice(["مرد", "زن"]),
            rank="عضو دسته‌های پایین‌تر"
        )
        session.add(child)
        await session.commit()
        
        msg += (
            f"\n\n👶✨ <b>معجزه رخ داد!</b>\n"
            f"با شانس بسیار نادر، فرزندی متولد شد: <b>{child_name}</b>\n"
            f"جنسیت: {child.gender}"
        )
    
    return msg


async def reject_dual(session: AsyncSession, dual: DualCultivation, rejecter_id: int) -> str:
    if dual.user2_id != rejecter_id and dual.user1_id != rejecter_id:
        return "دسترسی نداری."
    dual.status = "finished"
    dual.finished_at = datetime.utcnow()
    await session.commit()
    return "تذهیب دوگانه رد شد."
