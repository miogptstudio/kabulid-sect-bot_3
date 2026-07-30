from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from database.models_v2 import ArenaProfile, ArenaMatch, ARENA_TIERS
from database.models import User


async def get_or_create_arena_profile(session: AsyncSession, user_id: int) -> ArenaProfile:
    result = await session.execute(
        select(ArenaProfile).where(ArenaProfile.user_id == user_id)
    )
    profile = result.scalar_one_or_none()
    if profile:
        return profile
    
    profile = ArenaProfile(user_id=user_id)
    session.add(profile)
    await session.commit()
    await session.refresh(profile)
    return profile


async def process_arena_result(session: AsyncSession, winner_id: int, loser_id: int, tier: str = "برنز"):
    winner = await get_or_create_arena_profile(session, winner_id)
    loser = await get_or_create_arena_profile(session, loser_id)
    
    winner.wins += 1
    winner.points += 15
    winner.season_points += 15
    
    loser.losses += 1
    loser.points = max(0, loser.points - 8)
    
    # ارتقای درجه
    if winner.points >= 100 and winner.tier == "برنز":
        winner.tier = "نقره"
    elif winner.points >= 250 and winner.tier == "نقره":
        winner.tier = "طلا"
    
    await session.commit()
    return winner, loser
