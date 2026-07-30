import os
from dotenv import load_dotenv

load_dotenv()

BOT_TOKEN = os.getenv("BOT_TOKEN")
ADMIN_IDS = [int(x) for x in os.getenv("ADMIN_IDS", "").split(",") if x.strip()]
DATABASE_URL = os.getenv("DATABASE_URL", "sqlite+aiosqlite:///./bot.db")

# Ranking settings
WINS_FOR_SAME_RANK_PROMOTE = 10
CONSECUTIVE_LOSSES_FOR_DEMOTE = 3
GUARDIAN_WIN_PROMOTE = 1
GUARDIAN_LOSS_DEMOTE = 2

# XP settings
XP_PER_WIN = 15
XP_PER_LOSS = 5
XP_PER_GUARDIAN_WIN = 25
XP_NEEDED_PER_LEVEL = 100  # برای هر سطح داخل رتبه

# Season settings (in days)
SEASON_DURATION_DAYS = 90
