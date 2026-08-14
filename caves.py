"""غارهای هر شهر — غنیمت پر"""
import random
from datetime import datetime, timedelta

CAVE_TYPES = [
    ("غار تاریک", "معمولی"),
    ("غار بلور", "نادر"),
    ("غار اژدها", "افسانه‌ای"),
    ("غار سیمرغ", "افسانه‌ای"),
    ("غار متروکه", "معمولی"),
    ("غار رعد", "نادر"),
    ("غار گنج", "نادر"),
    ("غار باستانی", "افسانه‌ای"),
    ("غار زیرآبی", "نادر"),
    ("غار یخی", "نادر"),
    ("غار آتشین", "نادر"),
    ("غار روح", "افسانه‌ای"),
]

# هر شهر حداقل یک غار اختصاصی دارد
def city_cave_name(city_name: str) -> str:
    return f"غار {city_name}"

_last_cave: dict[int, datetime] = {}
CD = timedelta(minutes=30)  # کمی سریع‌تر


def explore(tg_id: int, city_name: str):
    """همیشه غنیمت — غار پر از چیزهای مختلف"""
    now = datetime.utcnow()
    last = _last_cave.get(tg_id)
    if last and now - last < CD:
        left = int((CD - (now - last)).total_seconds() // 60) + 1
        return f"⏳ تا غار بعدی حدود {left} دقیقه"

    _last_cave[tg_id] = now
    # غار اختصاصی شهر + نوع تصادفی
    dedicated = city_cave_name(city_name)
    cave, rarity = random.choice(CAVE_TYPES)
    if random.random() < 0.5:
        cave = dedicated
        rarity = "شهری"

    # همیشه حداقل یک پاداش؛ گاهی چندتایی
    roll = random.random()
    rewards = []
    # سکه تقریباً همیشه
    coins = random.randint(80, 350)
    rewards.append(("coins", coins))
    if roll < 0.55 or rarity in ("نادر", "افسانه‌ای", "شهری"):
        rewards.append(("spirit", random.randint(1, 3)))
    if roll < 0.7:
        rewards.append(("energy", random.randint(400, 1500)))
    if rarity == "افسانه‌ای" and random.random() < 0.4:
        rewards.append(("spirit", random.randint(2, 5)))
        rewards.append(("coins", random.randint(200, 600)))
    if random.random() < 0.12:
        rewards.append(("danger", random.randint(3, 12)))

    return ("multi", rewards, cave, rarity)
