import random
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from database.models_v3 import Pet
from database.models import User

WILD_SPECIES = [
    ("گرگ وحشی", 12, 8),
    ("روباه آتشین", 10, 6),
    ("مار سمی", 14, 5),
    ("عقاب کوهی", 11, 7),
    ("خوک جنگلی", 8, 12),
]

DOMESTIC_SPECIES = [
    ("گربه روح", 6, 6),
    ("سگ نگهبان", 9, 10),
    ("خرگوش ماه", 4, 5),
    ("پرنده خوش‌خوان", 5, 4),
]


async def spawn_wild(session: AsyncSession) -> Pet:
    species, atk, deff = random.choice(WILD_SPECIES)
    pet = Pet(
        name=species,
        pet_type="wild",
        species=species,
        description=f"حیوان وحشی: {species}",
        attack=atk,
        defense=deff,
        loyalty=10,
        is_wild=True,
        owner_id=None
    )
    session.add(pet)
    await session.commit()
    await session.refresh(pet)
    return pet


async def get_user_pets(session: AsyncSession, user_id: int) -> list:
    result = await session.execute(
        select(Pet).where(Pet.owner_id == user_id)
    )
    return result.scalars().all()


async def tame_pet(session: AsyncSession, user: User, pet: Pet) -> str:
    if not pet.is_wild or pet.owner_id:
        return "این حیوان قابل رام کردن نیست."
    
    # شانس رام کردن بر اساس XP ساده
    chance = min(40 + (user.level * 5), 85)
    if random.randint(1, 100) > chance:
        await session.delete(pet)
        await session.commit()
        return f"❌ رام کردن شکست خورد و {pet.species} فرار کرد. (شانس: {chance}%)"
    
    pet.is_wild = False
    pet.pet_type = "domestic"
    pet.owner_id = user.id
    pet.loyalty = 40
    pet.name = f"{pet.species} {user.full_name[:6]}"
    await session.commit()
    return f"✅ {pet.species} رام شد و حیوان خونگی تو شد!\nحمله: {pet.attack} | دفاع: {pet.defense}"


async def buy_domestic(session: AsyncSession, user: User, cost_coins: int = 100) -> str:
    from services.economy import get_or_create_wallet
    w = await get_or_create_wallet(session, user.id)
    if w.coins < cost_coins:
        return f"❌ نیاز به {cost_coins} سکه داری (داری: {w.coins})"
    
    species, atk, deff = random.choice(DOMESTIC_SPECIES)
    w.coins -= cost_coins
    pet = Pet(
        name=f"{species}",
        pet_type="domestic",
        species=species,
        description="حیوان خونگی خریداری‌شده",
        attack=atk,
        defense=deff,
        loyalty=70,
        is_wild=False,
        owner_id=user.id
    )
    session.add(pet)
    await session.commit()
    return f"✅ {species} خریداری شد!\nحمله: {atk} | دفاع: {deff}\nسکه باقی: {w.coins}"
