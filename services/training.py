"""زمین تمرین — پاداش به ازای هر دقیقه مثل AFK؛ امکان انصراف وسط کار"""
from __future__ import annotations
from datetime import datetime, timedelta
from sqlalchemy.ext.asyncio import AsyncSession
from database.models import User

TRAIN_MAX_MINUTES = 60
TRAIN_MIN_MINUTES = 10
ENERGY_PER_MINUTE = 6000
POWER_XP_PER_MINUTE = 15

_train_minutes: dict[int, int] = {}
_train_start: dict[int, datetime] = {}


async def start_training(session: AsyncSession, user: User, minutes: int) -> str:
    try:
        from services.prison import is_imprisoned
        if is_imprisoned(user):
            return "در زندانی؛ نمی‌توانی تمرین کنی. /prison"
    except Exception:
        pass
    if getattr(user, "restriction_reason", None) == "تمرین":
        until = user.restricted_until
        if until and datetime.utcnow() < until:
            left = until - datetime.utcnow()
            m = int(left.total_seconds() // 60) + 1
            return f"همین حالا در تمرین هستی. حدود {m} دقیقه مانده. /trainstatus | /trainstop"
    minutes = max(TRAIN_MIN_MINUTES, min(TRAIN_MAX_MINUTES, int(minutes)))
    now = datetime.utcnow()
    user.restricted_until = now + timedelta(minutes=minutes)
    user.restriction_reason = "تمرین"
    _train_minutes[user.id] = minutes
    _train_start[user.id] = now
    await session.commit()
    total_e = minutes * ENERGY_PER_MINUTE
    return (
        f"🏟 وارد زمین تمرین شدی ({minutes} دقیقه)." + chr(10)
        + f"پاداش تخمینی کامل: +{total_e} انرژی (+{minutes * POWER_XP_PER_MINUTE} قدرت)" + chr(10)
        + "تا پایان، خدمات ربات قطع است." + chr(10)
        + f"نرخ: هر دقیقه {ENERGY_PER_MINUTE} انرژی" + chr(10)
        + "/trainstatus — وضعیت" + chr(10)
        + "/trainstop — انصراف وسط تمرین (پاداش دقیقه‌های رفته)" + chr(10)
        + "/trainclaim — بعد از اتمام کامل"
    )


def is_training(user: User) -> bool:
    if getattr(user, "restriction_reason", None) != "تمرین":
        return False
    until = user.restricted_until
    if not until:
        return False
    return datetime.utcnow() < until


def _elapsed_minutes(user: User) -> int:
    started = _train_start.get(user.id)
    if not started:
        return 0
    sec = (datetime.utcnow() - started).total_seconds()
    return max(0, int(sec // 60))


async def training_block_message(session: AsyncSession, user: User) -> str | None:
    if getattr(user, "restriction_reason", None) != "تمرین":
        return None
    until = user.restricted_until
    if not until:
        return None
    now = datetime.utcnow()
    if now < until:
        left = until - now
        m = int(left.total_seconds() // 60)
        s = int(left.total_seconds() % 60)
        done = _elapsed_minutes(user)
        return (
            f"🏟 در زمین تمرین هستی ({m}د {s}ث مانده)." + chr(10)
            + f"تمرین‌شده تا الان: ~{done} دقیقه → حدود {done * ENERGY_PER_MINUTE} انرژی" + chr(10)
            + "خدمات قطع است. /trainstatus | /trainstop"
        )
    return None


async def _give_reward(session: AsyncSession, user: User, minutes: int, early: bool) -> str:
    minutes = max(0, min(TRAIN_MAX_MINUTES, int(minutes)))
    user.restriction_reason = None
    user.restricted_until = None
    _train_minutes.pop(user.id, None)
    _train_start.pop(user.id, None)
    if minutes <= 0:
        await session.commit()
        return "تمرین لغو شد؛ هنوز یک دقیقه کامل نگذشته بود. پاداشی نیست."
    gain = minutes * ENERGY_PER_MINUTE
    power_gain = minutes * POWER_XP_PER_MINUTE
    try:
        from services.cultivation import add_energy, get_or_create_cultivation
        result = await add_energy(session, user.id, gain)
        cult = await get_or_create_cultivation(session, user.id)
        try:
            if hasattr(cult, "body_power"):
                cult.body_power = int(getattr(cult, "body_power", 0) or 0) + power_gain
        except Exception:
            pass
        await session.commit()
        msgs = result.get("messages") or []
        tag = "انصراف وسط تمرین" if early else "تمرین کامل"
        return (
            f"✅ {tag} ({minutes} دقیقه)." + chr(10)
            + f"+{gain} انرژی" + chr(10)
            + f"+{power_gain} قدرت تمرین" + chr(10)
            + (chr(10).join(msgs) if msgs else "")
        )
    except Exception as e:
        await session.commit()
        return f"✅ آزاد شدی ({minutes}د). پاداش: خطا {type(e).__name__}"


async def claim_training(session: AsyncSession, user: User) -> str:
    if getattr(user, "restriction_reason", None) != "تمرین":
        return "تمرین فعالی نداری. /train"
    until = user.restricted_until
    if until and datetime.utcnow() < until:
        left = until - datetime.utcnow()
        m = int(left.total_seconds() // 60) + 1
        return (
            f"هنوز تمرین تمام نشده ({m} دقیقه)." + chr(10)
            + "اگر می‌خواهی الان خارج شوی: /trainstop"
        )
    planned = _train_minutes.get(user.id)
    started = _train_start.get(user.id)
    if planned:
        minutes = planned
    elif started and until:
        minutes = int((until - started).total_seconds() // 60)
    else:
        minutes = TRAIN_MIN_MINUTES
    return await _give_reward(session, user, minutes, early=False)


async def stop_training(session: AsyncSession, user: User) -> str:
    """انصراف وسط تمرین — پاداش دقیقه‌های واقعی گذشته"""
    if getattr(user, "restriction_reason", None) != "تمرین":
        return "تمرین فعالی نداری. /train"
    done = _elapsed_minutes(user)
    # حداقل ۰؛ اگر کمتر از ۱ دقیقه، بدون پاداش آزاد شو
    return await _give_reward(session, user, done, early=True)


async def train_status(session: AsyncSession, user: User) -> str:
    if getattr(user, "restriction_reason", None) != "تمرین":
        return (
            "در تمرین نیستی." + chr(10)
            + f"/train [دقیقه] — {TRAIN_MIN_MINUTES} تا {TRAIN_MAX_MINUTES}" + chr(10)
            + f"هر دقیقه ≈ {ENERGY_PER_MINUTE} انرژی"
        )
    until = user.restricted_until
    if not until:
        return "وضعیت نامعتبر. /trainstop یا /trainclaim"
    now = datetime.utcnow()
    planned = _train_minutes.get(user.id, TRAIN_MIN_MINUTES)
    done = _elapsed_minutes(user)
    if now < until:
        left = until - now
        m = int(left.total_seconds() // 60)
        s = int(left.total_seconds() % 60)
        return (
            f"🏟 تمرین فعال (قرارداد {planned} دقیقه)" + chr(10)
            + f"گذشته: ~{done} دقیقه → ~{done * ENERGY_PER_MINUTE} انرژی" + chr(10)
            + f"مانده: {m}د {s}ث" + chr(10)
            + "/trainstop — انصراف و گرفتن پاداش گذشته" + chr(10)
            + "/trainclaim — فقط بعد از اتمام"
        )
    return "تمرین تمام شده. /trainclaim بزن."
