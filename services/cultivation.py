from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from database.models_v2 import Cultivation, CULTIVATION_REALMS
from database.models_v3 import CultivationTechnique, UserTechnique
from database.models import User

ENERGY_PER_STAGE = 100
ROOT_UNLOCK_ENERGY = 200  # انرژی لازم برای رسیدن به ریشه پنج‌عنصر


DEFAULT_TECHNIQUES = [
    {
        "name": "تنفس پایه",
        "description": "تکنیک ساده تذهیب برای مبتدیان",
        "grade": "پایه",
        "energy_bonus": 0,
        "is_starter": True
    },
    {
        "name": "جریان پنج‌عنصر",
        "description": "تکنیک متوسط بر پایه پنج عنصر",
        "grade": "متوسط",
        "energy_bonus": 8,
        "required_root": "ریشه پنج‌عنصر"
    },
    {
        "name": "شعله‌ی درونی",
        "description": "تکنیک آتشین برای ریشه آتش",
        "grade": "متوسط",
        "energy_bonus": 12,
        "required_root": "ریشه آتش"
    },
]


async def ensure_default_techniques(session: AsyncSession):
    result = await session.execute(select(CultivationTechnique))
    if result.scalars().first():
        return
    for t in DEFAULT_TECHNIQUES:
        session.add(CultivationTechnique(**t))
    await session.commit()


async def get_or_create_cultivation(session: AsyncSession, user_id: int) -> Cultivation:
    result = await session.execute(
        select(Cultivation).where(Cultivation.user_id == user_id)
    )
    cult = result.scalar_one_or_none()
    if cult:
        return cult
    
    cult = Cultivation(
        user_id=user_id,
        spiritual_root="بدون ریشه"  # همه بدون ریشه شروع می‌کنن
    )
    session.add(cult)
    await session.commit()
    await session.refresh(cult)
    return cult


async def get_active_technique(session: AsyncSession, user_id: int) -> CultivationTechnique | None:
    result = await session.execute(
        select(UserTechnique, CultivationTechnique)
        .join(CultivationTechnique, UserTechnique.technique_id == CultivationTechnique.id)
        .where(UserTechnique.user_id == user_id, UserTechnique.is_active == True)
    )
    row = result.first()
    if row:
        return row[1]
    return None


async def learn_technique(session: AsyncSession, user_id: int, technique: CultivationTechnique, from_user_id: int | None = None) -> str:
    # چک تکراری
    existing = await session.execute(
        select(UserTechnique).where(
            UserTechnique.user_id == user_id,
            UserTechnique.technique_id == technique.id
        )
    )
    if existing.scalar_one_or_none():
        return "این تکنیک رو قبلاً بلدی."
    
    cult = await get_or_create_cultivation(session, user_id)
    
    # چک ریشه مورد نیاز
    if technique.required_root and cult.spiritual_root != technique.required_root:
        if cult.spiritual_root == "بدون ریشه":
            return "هنوز ریشه معنوی نداری. باید به ریشه پنج‌عنصر برسی."
        return f"این تکنیک نیاز به «{technique.required_root}» داره."
    
    ut = UserTechnique(
        user_id=user_id,
        technique_id=technique.id,
        is_active=False,
        learned_from=from_user_id
    )
    session.add(ut)
    
    # اگر اولین تکنیکشه، فعالش کن
    any_active = await get_active_technique(session, user_id)
    if not any_active:
        ut.is_active = True
    
    await session.commit()
    return f"✅ تکنیک «{technique.name}» یاد گرفته شد."


async def set_active_technique(session: AsyncSession, user_id: int, technique_id: int) -> str:
    # غیرفعال کردن بقیه
    result = await session.execute(
        select(UserTechnique).where(UserTechnique.user_id == user_id)
    )
    for ut in result.scalars().all():
        ut.is_active = (ut.technique_id == technique_id)
    await session.commit()
    return "تکنیک فعال تغییر کرد."


async def add_energy(session: AsyncSession, user_id: int, amount: int) -> dict:
    cult = await get_or_create_cultivation(session, user_id)
    
    # بدون ریشه → فقط تا رسیدن به ریشه پنج‌عنصر می‌تونه جمع کنه
    if cult.spiritual_root == "بدون ریشه":
        # هنوز تکنیک لازم نیست، اما انرژی محدود برای باز کردن ریشه
        cult.energy += amount
        messages = []
        
        if cult.energy >= ROOT_UNLOCK_ENERGY:
            cult.spiritual_root = "ریشه پنج‌عنصر"
            cult.energy = 0
            messages.append("🌟 ریشه معنوی پنج‌عنصر بیدار شد! حالا می‌تونی تکنیک یاد بگیری و تذهیب واقعی کنی.")
        
        await session.commit()
        return {
            "leveled": False,
            "realm": cult.realm,
            "stage": cult.stage,
            "energy": cult.energy,
            "root": cult.spiritual_root,
            "messages": messages or [f"در حال بیدار کردن ریشه... ({cult.energy}/{ROOT_UNLOCK_ENERGY})"]
        }
    
    # با ریشه → باید تکنیک فعال داشته باشه
    tech = await get_active_technique(session, user_id)
    if not tech:
        return {
            "leveled": False,
            "realm": cult.realm,
            "stage": cult.stage,
            "energy": cult.energy,
            "root": cult.spiritual_root,
            "messages": ["❌ تکنیک تذهیب فعالی نداری! اول یک تکنیک یاد بگیر یا فعال کن."]
        }
    
    # بونوس تکنیک
    total = amount + (tech.energy_bonus or 0)
    cult.energy += total
    messages = []
    leveled = False
    
    while cult.energy >= ENERGY_PER_STAGE:
        cult.energy -= ENERGY_PER_STAGE
        cult.stage += 1
        leveled = True
        
        if cult.stage > 3:
            cult.stage = 1
            try:
                idx = CULTIVATION_REALMS.index(cult.realm)
                if idx < len(CULTIVATION_REALMS) - 1:
                    cult.realm = CULTIVATION_REALMS[idx + 1]
                    messages.append(f"🌟 قلمرو تذهیب به «{cult.realm}» ارتقا یافت!")
                else:
                    cult.stage = 3
                    cult.energy = ENERGY_PER_STAGE - 1
            except ValueError:
                pass
        
        messages.append(f"⬆️ سطح تذهیب به {cult.stage} رسید (قلمرو: {cult.realm})")
    
    await session.commit()
    return {
        "leveled": leveled,
        "realm": cult.realm,
        "stage": cult.stage,
        "energy": cult.energy,
        "root": cult.spiritual_root,
        "messages": messages
    }
