from datetime import datetime, timedelta
from bot.config import SEASON_DURATION_DAYS

SEASON_NUMBER = 1
SEASON_NAME = "فصل اول — طلوع فرقه‌ها"


def get_current_season_info():
    # شروع ثابت فصل اول
    start = datetime(2026, 8, 1, 0, 0, 0)
    end = start + timedelta(days=SEASON_DURATION_DAYS)
    return {
        "number": SEASON_NUMBER,
        "name": SEASON_NAME,
        "start": start,
        "end": end,
        "active": datetime.utcnow() < end,
    }


def season_text() -> str:
    info = get_current_season_info()
    return (
        f"🗓️ <b>{info['name']}</b>\n"
        f"شماره فصل: {info['number']}\n"
        f"شروع: {info['start'].date()}\n"
        f"پایان: {info['end'].date()}\n"
        f"وضعیت: {'فعال ✅' if info['active'] else 'پایان‌یافته'}\n\n"
        "مدال‌ها در پایان فصل حفظ می‌شوند.\n"
        "جدول رتبه در فصل بعد ریست می‌شود."
    )
