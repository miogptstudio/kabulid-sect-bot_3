import random
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from database.models_v3 import Pet
from database.models import User

DEFAULT_PET_SLOTS = 10
MAX_PET_SLOTS = 50
PALACE_UPGRADE_SLOTS = 5
PALACE_UPGRADE_COST = 8000
HUNT_COOLDOWN_HOURS = 1

WILD_SPECIES = [
    ("گرگ وحشی", 12, 8),
    ("روباه آتشین", 10, 6),
    ("مار سمی", 14, 5),
    ("عقاب کوهی", 11, 7),
    ("خوک جنگلی", 8, 12),
    ("سیمرغ", 40, 35),
    ("اژدهای ایرانی", 45, 40),
    ("همای سعادت", 30, 25),
    ("مردآزمای دریایی", 28, 22),
    ("اژدهای غربی", 42, 38),
    ("ققنوس غربی", 38, 30),
    ("یونیکورن", 25, 28),
    ("گریفین", 35, 32),
    ("اژدهای شرقی", 48, 42),
    ("کیرین", 36, 34),
    ("نه دم روباه", 33, 27),
    ("بایزه", 30, 28),
]

DOMESTIC_SPECIES = [
    ("گربه روح", 6, 6),
    ("سگ نگهبان", 9, 10),
    ("خرگوش ماه", 4, 5),
    ("پرنده خوش‌خوان", 5, 4),
    ("آهو بهشتی", 15, 12),
    ("اسب باد", 18, 14),
    ("لاک‌پشت زرین", 7, 15),
    ("جغد دانش", 8, 9),
]


def pet_capacity(user: User) -> int:
    return int(getattr(user, "pet_slots", None) or DEFAULT_PET_SLOTS)


async def spawn_wild(session: AsyncSession) -> Pet:
    species, atk, deff = random.choice(WILD_SPECIES)
    pet = Pet(
        name=species,
        pet_type="wild",
        species=species,
        description=f"حیوان وحشی: {species}",
        attack=atk + random.randint(0, 5),
        defense=deff + random.randint(0, 5),
        loyalty=10,
        is_wild=True,
        owner_id=None,
    )
    session.add(pet)
    await session.commit()
    await session.refresh(pet)
    return pet


async def get_user_pets(session: AsyncSession, user_id: int) -> list:
    result = await session.execute(
        select(Pet).where(Pet.owner_id == user_id).order_by(Pet.id)
    )
    return list(result.scalars().all())


async def can_own_more(session: AsyncSession, user: User):
    pets = await get_user_pets(session, user.id)
    cap = pet_capacity(user)
    if len(pets) >= cap:
        return False, (
            f"🏰 کاخ رام‌شدگان پر است ({len(pets)}/{cap})."
            + chr(10)
            + f"با /petpalace ارتقا بده (سقف {MAX_PET_SLOTS})."
        )
    return True, ""


async def tame_pet(session: AsyncSession, user: User, pet: Pet) -> str:
    if not pet or not pet.is_wild or pet.owner_id:
        return "این حیوان قابل رام کردن نیست."

    ok, msg = await can_own_more(session, user)
    if not ok:
        return msg

    chance = min(40 + (user.level or 1) * 5, 85)
    if random.randint(1, 100) > chance:
        await session.delete(pet)
        await session.commit()
        return f"❌ رام کردن شکست خورد و {pet.species} فرار کرد. (شانس: {chance}%)"

    pet.is_wild = False
    pet.pet_type = "domestic"
    pet.owner_id = user.id
    pet.loyalty = 40
    pet.name = f"{pet.species}"
    await session.commit()
    return (
        f"✅ {pet.species} رام شد!"
        + chr(10)
        + f"حمله: {pet.attack} | دفاع: {pet.defense} | وفاداری: {pet.loyalty}"
    )


async def buy_domestic(session: AsyncSession, user: User, cost_coins: int = 100) -> str:
    from services.economy import get_or_create_wallet, pay_any_currency

    ok, msg = await can_own_more(session, user)
    if not ok:
        return msg

    w = await get_or_create_wallet(session, user.id)
    ok, pay_msg = pay_any_currency(w, cost_coins)
    if not ok:
        return pay_msg

    species, atk, deff = random.choice(DOMESTIC_SPECIES)
    pet = Pet(
        name=species,
        pet_type="domestic",
        species=species,
        description="حیوان خونگی خریداری‌شده",
        attack=atk,
        defense=deff,
        loyalty=70,
        is_wild=False,
        owner_id=user.id,
    )
    session.add(pet)
    await session.commit()
    return (
        f"✅ {species} خریداری شد!"
        + chr(10)
        + f"حمله: {atk} | دفاع: {deff} | وفاداری: ۷۰"
        + chr(10)
        + pay_msg
    )


async def feed_pet(session: AsyncSession, pet: Pet, cost: int = 20) -> str:
    from services.economy import get_or_create_wallet, pay_any_currency

    if not pet.owner_id:
        return "این حیوان مال کسی نیست."
    w = await get_or_create_wallet(session, pet.owner_id)
    ok, pay_msg = pay_any_currency(w, cost)
    if not ok:
        return pay_msg
    pet.loyalty = min(100, (pet.loyalty or 0) + random.randint(5, 15))
    pet.attack = (pet.attack or 0) + random.randint(0, 1)
    await session.commit()
    return (
        f"🍖 {pet.name} غذا خورد. وفاداری: {pet.loyalty} | حمله: {pet.attack}"
        + chr(10)
        + pay_msg
    )


async def train_pet(session: AsyncSession, pet: Pet, cost: int = 50) -> str:
    from services.economy import get_or_create_wallet, pay_any_currency

    if not pet.owner_id:
        return "این حیوان مال کسی نیست."
    w = await get_or_create_wallet(session, pet.owner_id)
    ok, pay_msg = pay_any_currency(w, cost)
    if not ok:
        return pay_msg
    pet.attack = (pet.attack or 0) + random.randint(1, 3)
    pet.defense = (pet.defense or 0) + random.randint(1, 3)
    pet.loyalty = min(100, (pet.loyalty or 0) + random.randint(1, 5))
    await session.commit()
    return (
        f"🏋️ {pet.name} آموزش دید!"
        + chr(10)
        + f"حمله: {pet.attack} | دفاع: {pet.defense} | وفاداری: {pet.loyalty}"
        + chr(10)
        + pay_msg
    )
