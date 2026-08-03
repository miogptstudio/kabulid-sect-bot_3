"""زمین تمرین — تا ۱ ساعت قطع خدمات ربات"""
from datetime import datetime, timedelta
from sqlalchemy.ext.asyncio import AsyncSession
from database.models import User

TRAIN_MAX_MINUTES = 60
TRAIN_MIN_MINUTES = 10
# پاداش تقریبی انرژی به ازای هر دقیقه
ENERGY_PER_MINUTE = 80


async def start_training(session: AsyncSession, user: User, minutes: int) -> str:
    minutes = max(TRAIN_MIN_MINUTES, min(TRAIN_MAX_MINUTES, int(minutes)))
    # اگر زندان است نمی‌تواند
    if getattr(user, "restriction_reason", None) == "زندان":
        until = getattr(user, "restricted_until", None)
        if until and datetime.utcnow() < until:
            return "در زندانی؛ نمی‌توانی تمرین کنی. /prison"
    if getattr(user, "restriction_reason", None) == "تمرین":
        until = getattr(user, "restricted_until", None)
        if until and datetime.utcnow() < until:
            left = until - datetime.utcnow()
            m = int(left.total_seconds() // 60) + 1
            return f"همین حالا در تمرین هستی. حدود {m} دقیقه مانده. /trainstatus"

    user.restricted_until = datetime.utcnow() + timedelta(minutes=minutes)
    user.restriction_reason = "تمرین"
    await session.commit()
    return (
        f"🏟 وارد زمین تمرین شدی ({minutes} دقیقه)." + chr(10)
        + "تا پایان تمرین هیچ خدمتی از ربات نمی‌گیری" + chr(10)
        + "(جمع‌آوری، دوئل، خرید، سفر و … قطع است)." + chr(10)
        + f"پایان تقریبی: {user.restricted_until.strftime('%H:%M')} UTC" + chr(10)
        + "/trainstatus — وضعیت | بعد از اتمام: /trainclaim"
    )


def is_training(user: User) -> bool:
    if getattr(user, "restriction_reason", None) != "تمرین":
        return False
    until = getattr(user, "restricted_until", None)
    if not until:
        return False
    return datetime.utcnow() < until


async def training_block_message(session: AsyncSession, user: User) -> str | None:
    """اگر در تمرین است پیام بده؛ اگر تمام شده None و فلگ بگذار برای claim"""
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
        return (
            f"🏟 در زمین تمرین هستی ({m}د {s}ث مانده)." + chr(10)
            + "خدمات ربات تا پایان تمرین قطع است." + chr(10)
            + "/trainstatus"
        )
    # تمام شده — هنوز reason تمرین است تا claim
    return None


async def claim_training(session: AsyncSession, user: User) -> str:
    if getattr(user, "restriction_reason", None) != "تمرین":
        return "تمرین فعالی نداری. /train"
    until = user.restricted_until
    if until and datetime.utcnow() < until:
        left = until - datetime.utcnow()
        m = int(left.total_seconds() // 60) + 1
        return f"هنوز تمرین تمام نشده ({m} دقیقه). صبر کن."

    # پاداش بر اساس حداکثر ۶۰ دقیقه (اگر until گذشته، فرض کامل)
    minutes = TRAIN_MAX_MINUTES
    if until:
        # نمی‌دانیم شروع کی بود؛ پاداش ثابت نسبی
        minutes = TRAIN_MAX_MINUTES
    # ذخیره start در reason ممکن نیست — پاداش متوسط
    gain = ENERGY_PER_MINUTE * 30  # پاداش پایه نیم‌ساعت معادل
    user.restricted_until = None
    user.restriction_reason = None
    await session.commit()

    try:
        from services.cultivation import add_energy
        res = await add_energy(session, user.id, gain)
        status = chr(10).join(res.get("messages") or [])
        return (
            f"✅ تمرین تمام شد. آزاد شدی." + chr(10)
            + f"+{gain} انرژی تمرین" + chr(10)
            + status
        )
    except Exception as e:
        return f"✅ تمرین تمام شد. آزاد شدی. (پاداش انرژی: خطا {type(e).__name__})"


async def train_status(session: AsyncSession, user: User) -> str:
    if getattr(user, "restriction_reason", None) != "تمرین":
        return "در تمرین نیستی. /train [دقیقه] — مثلاً /train 30 (حداکثر ۶۰)"
    until = user.restricted_until
    if not until:
        return "وضعیت تمرین نامعتبر. /trainclaim"
    now = datetime.utcnow()
    if now < until:
        left = until - now
        m = int(left.total_seconds() // 60)
        s = int(left.total_seconds() % 60)
        return (
            f"🏟 تمرین فعال" + chr(10)
            + f"مانده: {m}د {s}ث" + chr(10)
            + f"پایان: {until.strftime('%H:%M')} UTC" + chr(10)
            + "خدمات ربات قطع است."
        )
    return "تمرین تمام شده. /trainclaim بزن تا پاداش بگیری و آزاد شوی."
