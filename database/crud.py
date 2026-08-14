from datetime import datetime
from sqlalchemy import select, update
from sqlalchemy.sql import func
from sqlalchemy.ext.asyncio import AsyncSession
from database.models import User, Duel, Medal, Achievement, UserAchievement, Season, Question


# ==================== USER ====================

async def get_user_by_telegram_id(session: AsyncSession, telegram_id: int) -> User | None:
    result = await session.execute(select(User).where(User.telegram_id == telegram_id))
    return result.scalar_one_or_none()


async def create_user(session: AsyncSession, telegram_id: int, full_name: str, username: str | None = None) -> User:
    user = User(
        telegram_id=telegram_id,
        full_name=full_name,
        username=username
    )
    session.add(user)
    await session.commit()
    await session.refresh(user)
    return user


async def get_or_create_user(session: AsyncSession, telegram_id: int, full_name: str, username: str | None = None) -> User:
    user = await get_user_by_telegram_id(session, telegram_id)
    if user:
        user.last_active = datetime.utcnow()
        user.full_name = full_name
        if username:
            user.username = username
        await session.commit()
        return user
    return await create_user(session, telegram_id, full_name, username)


async def update_user_stats(session: AsyncSession, user: User, won: bool):
    user.total_duels += 1
    user.last_duel_at = datetime.utcnow()
    
    if won:
        user.wins += 1
        user.win_streak += 1
        user.loss_streak = 0
    else:
        user.losses += 1
        user.loss_streak += 1
        user.win_streak = 0
    
    await session.commit()


# ==================== DUEL ====================

async def create_duel(session: AsyncSession, challenger_id: int, opponent_id: int, is_guardian: bool = False) -> Duel:
    duel = Duel(
        challenger_id=challenger_id,
        opponent_id=opponent_id,
        is_guardian=is_guardian,
        status="pending"
    )
    session.add(duel)
    await session.commit()
    await session.refresh(duel)
    return duel


async def finish_duel(session: AsyncSession, duel: Duel, winner_id: int):
    duel.winner_id = winner_id
    duel.status = "finished"
    duel.finished_at = datetime.utcnow()
    await session.commit()


# ==================== QUESTIONS ====================

async def get_random_question(session: AsyncSession, difficulty: int, category: str | None = None) -> Question | None:
    query = select(Question).where(Question.difficulty <= difficulty)
    if category:
        query = query.where(Question.category == category)
    result = await session.execute(query.order_by(func.random()).limit(1))
    return result.scalar_one_or_none()
