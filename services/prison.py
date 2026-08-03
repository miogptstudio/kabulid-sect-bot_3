from datetime import datetime, timedelta
from sqlalchemy.ext.asyncio import AsyncSession
from database.models import User

PRISON_HOURS = 5
KILL_LIMIT_PER_DAY = 3
BAIL_HEAVENLY = 50

_daily_kills: dict = {}


def _day_key(uid: int):
    return (uid, datetime.utcnow().date().isoformat())


def record_kill(user_id: int) -> int:
    k = _day_key(user_id)
    _daily_kills[k] = _daily_kills.get(k, 0) + 1
    return _daily_kills[k]


def kills_today(user_id: int) -> int:
    return _daily_kills.get(_day_key(user_id), 0)


async def put_in_prison(session: AsyncSession, user: User) -> str:
    user.restricted_until = datetime.utcnow() + timedelta(hours=PRISON_HOURS)
    user.restriction_reason = "زندان"
    await session.commit()
    return (
        f"🔒 به زندان افتادی ({PRISON_HOURS} ساعت)." + chr(10)
        + f"بیش از {KILL_LIMIT_PER_DAY} قتل در یک روز." + chr(10)
        + "تا آزادی خدمات ربات محدود است." + chr(10)
        + f"آزادی زودتر: /bail با {BAIL_HEAVENLY} سنگ بهشتی"
    )


def is_in_prison(user: User) -> bool:
    if getattr(user, "restriction_reason", None) != "زندان":
        return False
    until = getattr(user, "restricted_until", None)
    if not until:
        return False
    return datetime.utcnow() < until


async def try_bail(session: AsyncSession, user: User) -> str:
    from services.economy import get_or_create_wallet
    if not is_in_prison(user):
        return "در زندان نیستی."
    w = await get_or_create_wallet(session, user.id)
    if (w.heavenly_stones or 0) < BAIL_HEAVENLY:
        return f"نیاز به {BAIL_HEAVENLY} سنگ بهشتی (داری: {w.heavenly_stones or 0})"
    w.heavenly_stones -= BAIL_HEAVENLY
    user.restricted_until = None
    user.restriction_reason = None
    await session.commit()
    return f"✅ با {BAIL_HEAVENLY} سنگ بهشتی آزاد شدی."


async def check_prison_block(session: AsyncSession, user: User):
    if is_in_prison(user):
        left = user.restricted_until - datetime.utcnow()
        h = int(left.total_seconds() // 3600)
        m = int((left.total_seconds() % 3600) // 60)
        return (
            f"🔒 در زندانی ({h}س {m}د مانده)." + chr(10)
            + f"/bail — آزادی با {BAIL_HEAVENLY} سنگ بهشتی"
        )
    if getattr(user, "restriction_reason", None) == "زندان":
        user.restricted_until = None
        user.restriction_reason = None
        await session.commit()
    return None
