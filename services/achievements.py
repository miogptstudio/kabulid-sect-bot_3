"""سیستم دستاوردها — پایدار"""
from __future__ import annotations
from datetime import datetime
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from services.persist import get_dict, save as _psave

ACHIEVEMENTS = {
    "first_win": {"title": "اولین برد", "description": "اولین دوئل را بردی", "icon": "🏅", "reward_xp": 10},
    "win_streak_10": {"title": "۱۰ برد پیاپی", "description": "۱۰ دوئل متوالی", "icon": "🔥", "reward_xp": 50},
    "beat_arjomand": {"title": "شکست ارجمند", "description": "یک ارجمند را شکست دادی", "icon": "👑", "reward_xp": 30},
    "season_champion": {"title": "قهرمان فصل", "description": "قهرمان یک فصل", "icon": "🏆", "reward_xp": 100},
    "guardian_master": {"title": "فاتح نگهبان", "description": "پیروزی در نگهبان", "icon": "🛡️", "reward_xp": 20},
    "first_hunt": {"title": "شکارچی تازهکار", "description": "اولین شکار موفق", "icon": "🌲", "reward_xp": 15},
    "first_tame": {"title": "رامکننده", "description": "اولین حیوان رامشده", "icon": "🐺", "reward_xp": 20},
    "gather_100": {"title": "تذهیبگر", "description": "۱۰۰ بار جمع چی", "icon": "🌀", "reward_xp": 25},
}


def _unlocked() -> dict:
    return get_dict("achievements_unlocked")


def has(tg: int, code: str) -> bool:
    return code in (_unlocked().get(str(int(tg))) or [])


def list_user(tg: int) -> str:
    got = set(_unlocked().get(str(int(tg))) or [])
    lines = ["🏆 <b>دستاوردها</b>", ""]
    for code, info in ACHIEVEMENTS.items():
        mark = "✅" if code in got else "⬜"
        lines.append(f"{mark} {info['icon']} <b>{info['title']}</b> — {info['description']}")
    lines.append(f"\nباز شده: {len(got)}/{len(ACHIEVEMENTS)}")
    return "\n".join(lines)


async def check_and_award(session: AsyncSession, user, code: str) -> str | None:
    """اعطای دستاورد؛ متن جایزه یا None"""
    if code not in ACHIEVEMENTS:
        return None
    tg = int(getattr(user, "telegram_id", 0) or 0)
    if not tg:
        return None
    if has(tg, code):
        return None
    m = _unlocked()
    sk = str(tg)
    arr = list(m.get(sk) or [])
    arr.append(code)
    m[sk] = arr
    _psave("achievements_unlocked")
    info = ACHIEVEMENTS[code]
    try:
        user.xp = int(user.xp or 0) + int(info.get("reward_xp") or 0)
        # جدول DB هم اگر باشد
        try:
            from database.models import Achievement, UserAchievement
            r = await session.execute(select(Achievement).where(Achievement.code == code))
            ach = r.scalar_one_or_none()
            if not ach:
                ach = Achievement(
                    code=code,
                    title=info["title"],
                    description=info.get("description") or "",
                )
                session.add(ach)
                await session.flush()
            ua = UserAchievement(user_id=user.id, achievement_id=ach.id)
            session.add(ua)
        except Exception:
            pass
        await session.commit()
    except Exception:
        pass
    return f"{info['icon']} دستاورد باز شد: <b>{info['title']}</b> (+{info.get('reward_xp', 0)} XP)"


async def ensure_achievement_rows(session: AsyncSession):
    try:
        from database.models import Achievement
        r = await session.execute(select(Achievement))
        existing = {a.code for a in r.scalars().all()}
        for code, info in ACHIEVEMENTS.items():
            if code not in existing:
                session.add(Achievement(code=code, title=info["title"], description=info.get("description") or ""))
        await session.commit()
    except Exception:
        pass
