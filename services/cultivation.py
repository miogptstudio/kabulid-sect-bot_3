import random
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from database.models_v2 import Cultivation, CULTIVATION_REALMS
from database.models_v3 import CultivationTechnique, UserTechnique
from database.models import User

from bot.config import ROOT_UNLOCK_ENERGY, ENERGY_BASE, ENERGY_PER_LEVEL_ADD

MAX_STAGE = 10

# هرچه ریشه کمیاب‌تر، بازدهی تذهیب بالاتر؛ چندعنصری سخت‌تر (ضریب انرژی لازم)
ROOT_CULT_MULT = {
    "بدون ریشه": 0.5,
    "ریشه پنج‌عنصر": 1.0,
    "ریشه آتش": 1.1, "ریشه آب": 1.1, "ریشه چوب": 1.1, "ریشه فلز": 1.15, "ریشه خاک": 1.1,
    "ریشه دو‌عنصری آتش‌آب": 1.25, "ریشه دو‌عنصری چوب‌خاک": 1.25, "ریشه دو‌عنصری فلز‌آتش": 1.3,
    "ریشه سه‌عنصری": 1.45, "ریشه چهار‌عنصری": 1.7,
    "ریشه نور": 1.4, "ریشه تاریکی": 1.4, "ریشه روحی": 1.5, "ریشه روح": 1.55,
    "ریشه بهشتی": 1.7, "ریشه آسمانی": 1.9, "ریشه الهی": 2.2, "ریشه پوچی": 2.0,
    "ریشه ای‌تری": 1.85, "ریشه دوگانه": 1.6,
}
ROOT_HARD_MULT = {
    "ریشه دو‌عنصری آتش‌آب": 1.3, "ریشه دو‌عنصری چوب‌خاک": 1.3, "ریشه دو‌عنصری فلز‌آتش": 1.35,
    "ریشه سه‌عنصری": 1.6, "ریشه چهار‌عنصری": 2.0,
}

BODY_TYPES = [
    "بدن معمولی", "بدن چوب زمینی", "بدن بهشتی", "بدن اژدهای اعظم",
    "بدن خدایان", "بدن خدای غبطه‌انگیز", "بدن نورانی", "بدن تاریک", "بدن روحی",
]
BODY_BONUS = {
    "بدن معمولی": 1.0,
    "بدن چوب زمینی": 1.15,
    "بدن بهشتی": 1.4,
    "بدن اژدهای اعظم": 1.6,
    "بدن خدایان": 1.8,
    "بدن خدای غبطه‌انگیز": 2.0,
    "بدن نورانی": 1.35,
    "بدن تاریک": 1.35,
    "بدن روحی": 1.5,
}


def energy_needed_for_stage(stage: int, realm: str | None = None, root: str | None = None) -> int:
    """هر مرحله سخت‌تر؛ قلمروهای بالاتر گنجایش بیشتر"""
    from database.models_v2 import CULTIVATION_REALMS
    s = max(1, stage or 1)
    base = ENERGY_BASE + (s - 1) * ENERGY_PER_LEVEL_ADD
    # ضریب قلمرو
    try:
        ri = CULTIVATION_REALMS.index(realm) if realm in CULTIVATION_REALMS else 0
    except Exception:
        ri = 0
    mult = 1.0 + ri * 0.35
    hard = ROOT_HARD_MULT.get(root or '', 1.0)
    return int(base * mult * hard)




DEFAULT_TECHNIQUES = [
    {"name": "تنفس اژدها", "description": "تنفس قوی برای قلمرو بالا", "grade": "بالا", "energy_bonus": 45000, "required_root": None},
    {"name": "جریان آسمانی", "description": "تکنیک قلمرو پیشرفته", "grade": "پیشرفته", "energy_bonus": 1000, "required_root": None},
    {"name": "سکوت مرگ", "description": "تکنیک دنیای زیرین", "grade": "بالا", "energy_bonus": 45000, "required_root": "ریشه روح"},

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
        "energy_bonus": 0,
        "required_root": "ریشه پنج‌عنصر"
    },
    {
        "name": "شعله‌ی درونی",
        "description": "تکنیک آتشین برای ریشه آتش",
        "grade": "متوسط",
        "energy_bonus": 0,
        "required_root": "ریشه آتش"
    },
]


async def ensure_default_techniques(session: AsyncSession):
    result = await session.execute(select(CultivationTechnique))
    existing = {x.name for x in result.scalars().all()}
    for data in DEFAULT_TECHNIQUES:
        if data["name"] in existing:
            continue
        # فقط فیلدهای مدل
        allowed = {k: v for k, v in data.items() if k in ("name", "description", "grade", "energy_bonus", "required_root")}
        session.add(CultivationTechnique(**allowed))
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
    messages = []
    root = cult.spiritual_root or "بدون ریشه"
    rmult = ROOT_CULT_MULT.get(root, 1.0)
    bmult = BODY_BONUS.get(getattr(cult, "body_type", None) or "بدن معمولی", 1.0)
    amount = max(1, int(amount * rmult * bmult))

    if root == "بدون ریشه":
        cult.energy += amount
        if cult.energy >= ROOT_UNLOCK_ENERGY:
            roots = [
                ("ریشه پنج‌عنصر", 18),
                ("ریشه آتش", 6), ("ریشه آب", 6), ("ریشه چوب", 6),
                ("ریشه فلز", 6), ("ریشه خاک", 6),
                ("ریشه دو‌عنصری آتش‌آب", 5), ("ریشه دو‌عنصری چوب‌خاک", 5),
                ("ریشه دو‌عنصری فلز‌آتش", 4),
                ("ریشه سه‌عنصری", 3), ("ریشه چهار‌عنصری", 2),
                ("ریشه نور", 4), ("ریشه تاریکی", 4),
                ("ریشه روحی", 3), ("ریشه روح", 3),
                ("ریشه بهشتی", 2), ("ریشه آسمانی", 2),
                ("ریشه الهی", 1), ("ریشه پوچی", 1),
                ("ریشه ای‌تری", 2), ("ریشه دوگانه", 2),
            ]
            names, weights = zip(*roots)
            chosen = random.choices(names, weights=weights, k=1)[0]
            cult.spiritual_root = chosen
            cult.energy = 0
            if cult.realm == "بیداری":
                cult.realm = "پایه"
                cult.stage = 1
            messages.append(f"🌟 ریشه «{chosen}» بیدار شد!")
            messages.append(f"قلمرو: {cult.realm}")
        await session.commit()
        return {
            "energy": cult.energy,
            "stage": cult.stage,
            "realm": cult.realm,
            "root": cult.spiritual_root,
            "messages": messages or [f"در حال بیدار کردن ریشه... ({cult.energy}/{ROOT_UNLOCK_ENERGY})"],
        }

    tech = await get_active_technique(session, user_id)
    if not tech:
        await session.commit()
        return {
            "energy": cult.energy,
            "stage": cult.stage,
            "realm": cult.realm,
            "root": cult.spiritual_root,
            "messages": ["تکنیک فعال نداری. /learntech یا سالن تکنیک"],
        }

    bonus = getattr(tech, "energy_bonus", 0) or 0
    amount = amount + int(bonus)
    cult.energy += amount
    messages.append(f"+{amount} انرژی (ریشه ×{rmult:.2f} | بدن ×{bmult:.2f})")

    leveled = False
    while cult.energy >= energy_needed_for_stage(cult.stage, cult.realm, cult.spiritual_root):
        need = energy_needed_for_stage(cult.stage, cult.realm, cult.spiritual_root)
        cult.energy -= need
        cult.stage += 1
        leveled = True
        if cult.stage > MAX_STAGE:
            cult.stage = 1
            try:
                idx = CULTIVATION_REALMS.index(cult.realm)
                if idx < len(CULTIVATION_REALMS) - 1:
                    cult.realm = CULTIVATION_REALMS[idx + 1]
                    messages.append(f"🌟 قلمرو → «{cult.realm}»")
                    try:
                        from services.economy import get_or_create_wallet
                        w = await get_or_create_wallet(session, cult.user_id)
                        import random as _r
                        reward = _r.choice([("coins", 150), ("spirit", 1), ("heavenly", 1)])
                        if reward[0] == "coins":
                            w.coins += reward[1]
                            messages.append(f"🎁 +{reward[1]} سکه")
                        elif reward[0] == "spirit":
                            w.spirit_stones += reward[1]
                            messages.append(f"🎁 +{reward[1]} سنگ روحی")
                        else:
                            w.heavenly_stones = (w.heavenly_stones or 0) + 1
                            messages.append("🎁 +۱ سنگ بهشتی")
                    except Exception:
                        pass
                else:
                    cult.stage = MAX_STAGE
                    cult.energy = energy_needed_for_stage(cult.stage, cult.realm, cult.spiritual_root) - 1
            except ValueError:
                pass
        messages.append(f"⬆️ مرحله {cult.stage}/{MAX_STAGE} | {cult.realm}")

    await session.commit()
    return {
        "energy": cult.energy,
        "stage": cult.stage,
        "realm": cult.realm,
        "root": cult.spiritual_root,
        "messages": messages,
    }
