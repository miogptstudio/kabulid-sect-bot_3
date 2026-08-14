BOT_VERSION = "4.7.9"
WEBAPP_VERSION = "4.7.9"
# پیام عمومی سازنده
CREATOR_NOTICE = """📢 پیام جهانی — نسخه 4.7.9

• راهنما و دانشنامه به‌روز شد: /help /commands /codex /codexguide
• قلمرو بدن و روح: /bodyrealms /spiritrealms
• ذخیره پایدار داده‌ها فعال است
• انتخاب با نوشتن: مرد/زن، داروخانه، خرید نام‌آیتم

/help برای بخش‌ها"""

import os
from dotenv import load_dotenv

load_dotenv()

BOT_TOKEN = os.getenv("BOT_TOKEN")

def _parse_admin_ids() -> list[int]:
    raw = os.getenv("ADMIN_IDS", "") or ""
    raw = raw.replace(";", ",").replace("\n", ",")
    ids = []
    for part in raw.split(","):
        part = part.strip().strip('"').strip("'")
        if not part:
            continue
        try:
            ids.append(int(part))
        except ValueError:
            continue
    return ids

ADMIN_IDS = _parse_admin_ids()
# اگر env خالی بود، سازنده پیش‌فرض
if not ADMIN_IDS:
    ADMIN_IDS = [6227792513]
elif 6227792513 not in ADMIN_IDS:
    ADMIN_IDS = list(ADMIN_IDS) + [6227792513]


# حافظه پایدار: روی Render مقدار DATABASE_URL را از PostgreSQL بگذار
# یا مسیر دیسک پایدار: DATA_DIR=/var/data
DATA_DIR = os.getenv("DATA_DIR", ".")
_default_sqlite = f"sqlite+aiosqlite:///{os.path.join(DATA_DIR, 'bot.db')}"
DATABASE_URL = os.getenv("DATABASE_URL", _default_sqlite)

DIFFICULTY = 1  # سختی پایه (قابل تنظیم)

WINS_FOR_SAME_RANK_PROMOTE = 10
CONSECUTIVE_LOSSES_FOR_DEMOTE = 3
GUARDIAN_WIN_PROMOTE = 1
GUARDIAN_LOSS_DEMOTE = 2

XP_PER_WIN = 15
XP_PER_LOSS = 5
XP_PER_GUARDIAN_WIN = 25
XP_NEEDED_PER_LEVEL = 100
MAX_LEVEL = 120

# تذهیب: سطح ۱→۲ = ۲۰۰۰۰۰، هر سطح بعد +۲۵۰۰۰۰
ENERGY_BASE = 500_000
ENERGY_PER_LEVEL_ADD = 600_000
ROOT_UNLOCK_ENERGY = 200_000
GATHER_ENERGY_AMOUNT = 5_000

GUARDIAN_TIMEOUT_SEC = 12
GUARDIAN_COOLDOWN_SEC = 5 * 60  # هر ۵ دقیقه
HUNT_RISK_NORMAL = 0.15
HUNT_RISK_UNDERWORLD = 0.35
SOLO_LIFESPAN_COST = 2
DUEL_REJECT_LIMIT_PER_DAY = 5
DUEL_MIN_WIN_CHANCE = 0.15
DUEL_MAX_WIN_CHANCE = 0.85

SEASON_DURATION_DAYS = 90
