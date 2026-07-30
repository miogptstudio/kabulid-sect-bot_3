from datetime import datetime, timedelta
from bot.config import SEASON_DURATION_DAYS

# مدیریت فصل‌ها - نسخه اولیه

def get_current_season_info():
    # فعلاً ساده
    return {
        "name": "فصل اول",
        "start": datetime.utcnow() - timedelta(days=10),
        "end": datetime.utcnow() + timedelta(days=SEASON_DURATION_DAYS - 10)
    }
