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
DATABASE_URL = os.getenv("DATABASE_URL", "sqlite+aiosqlite:///./bot.db")

# ========== سختی ×۱۰۰۰۰۰ ==========
DIFFICULTY = 100_000

WINS_FOR_SAME_RANK_PROMOTE = 10 * DIFFICULTY  # ۱۰ × ۱۰۰۰۰۰ برد هم‌رتبه
CONSECUTIVE_LOSSES_FOR_DEMOTE = 3  # سقوط همچنان با ۳ باخت متوالی
GUARDIAN_WIN_PROMOTE = 1 * DIFFICULTY
GUARDIAN_LOSS_DEMOTE = 2

# XP خیلی سخت
XP_PER_WIN = 1
XP_PER_LOSS = 0
XP_PER_GUARDIAN_WIN = 1
XP_NEEDED_PER_LEVEL = 100 * DIFFICULTY  # ۱۰٬۰۰۰٬۰۰۰ XP برای هر سطح

# تذهیب
ENERGY_PER_STAGE = 100 * DIFFICULTY      # ۱۰٬۰۰۰٬۰۰۰
ROOT_UNLOCK_ENERGY = 200 * DIFFICULTY    # ۲۰٬۰۰۰٬۰۰۰
GATHER_ENERGY_AMOUNT = 1                 # هر جمع‌آوری فقط ۱ انرژی
GUARDIAN_TIMEOUT_SEC = 8                 # قبلاً ۲۰
HUNT_RISK_NORMAL = 0.45                  # خطر شکار خیلی بالا
HUNT_RISK_UNDERWORLD = 0.85
SOLO_LIFESPAN_COST = 5                   # هر خودارضایی ۵٪ عمر

SEASON_DURATION_DAYS = 90

# دوئل: بازیکن ضعیف‌تر شانس خیلی کم
DUEL_MIN_WIN_CHANCE = 0.02
DUEL_MAX_WIN_CHANCE = 0.60
