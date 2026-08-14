"""پیشرفت خودکار مأموریت‌ها بر اساس اکشن‌ها"""
from datetime import datetime
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from database.models import UserMission, Mission


async def bump_mission(session: AsyncSession, user_id: int, target_type: str, amount: int = 1) -> list[str]:
    messages = []
    result = await session.execute(
        select(UserMission).where(
            UserMission.user_id == user_id,
            UserMission.is_completed == False,
        )
    )
    for um in result.scalars().all():
        mission = await session.get(Mission, um.mission_id)
        if not mission or mission.target_type != target_type:
            continue
        um.progress = (um.progress or 0) + amount
        if um.progress >= mission.target_value:
            um.is_completed = True
            um.completed_at = datetime.utcnow()
            um.reward_claimed = True
            try:
                from database.models import User as _U
                u = await session.get(_U, user_id)
                if u:
                    u.xp = int(u.xp or 0) + int(mission.reward_xp or 0)
            except Exception:
                pass
            messages.append(
                f"✅ مأموریت «{mission.title}» تمام شد! +{mission.reward_xp or 0} XP"
            )
            # reward coins/stones if description mentions - simple fixed
            try:
                from services.economy import get_or_create_wallet
                w = await get_or_create_wallet(session, user_id)
                w.coins += 50
                w.spirit_stones += 1
                messages.append("🪙 +۵۰ سکه | 💎 +۱ سنگ روحی")
            except Exception:
                pass
    await session.commit()
    return messages
