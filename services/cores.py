"""هسته‌های نژادی — پیدا کردن و تبدیل نژاد"""
import random
from datetime import datetime, timedelta

# هسته → نژاد مقصد
CORES = {
    "هسته انسان": {"race": "انسان", "rarity": "معمولی", "chance": 18},
    "هسته اژدها": {"race": "اژدهازاده", "rarity": "نادر", "chance": 6},
    "هسته ققنوس": {"race": "ققنوس‌زاده", "rarity": "نادر", "chance": 5},
    "هسته سیمرغ": {"race": "سیمرغ‌زاده", "rarity": "افسانه‌ای", "chance": 3},
    "هسته دیو": {"race": "دیوزاد", "rarity": "نادر", "chance": 5},
    "هسته پری": {"race": "پری‌ایرانی", "rarity": "نادر", "chance": 6},
    "هسته آناهیتا": {"race": "آناهیتا‌پیمان", "rarity": "افسانه‌ای", "chance": 2.5},
    "هسته رخش": {"race": "رخش‌تبار", "rarity": "نادر", "chance": 4},
    "هسته جمشید": {"race": "جمشید‌تبار", "rarity": "افسانه‌ای", "chance": 2.5},
    "هسته فریدون": {"race": "فریدون‌زاده", "rarity": "افسانه‌ای", "chance": 2.5},
    "هسته زال": {"race": "زال‌تبار", "rarity": "نادر", "chance": 4},
    "هسته رستم": {"race": "رستم‌تبار", "rarity": "افسانه‌ای", "chance": 2},
    "هسته هما": {"race": "هما‌زاده", "rarity": "افسانه‌ای", "chance": 3},
    "هسته کاوه": {"race": "کاوه‌تبار", "rarity": "نادر", "chance": 5},
    "هسته ضحاک": {"race": "ضحاک‌تبار", "rarity": "نادر", "chance": 4},
    "هسته فرشته": {"race": "فرشته", "rarity": "نادر", "chance": 5},
    "هسته اهریمن": {"race": "اهریمن", "rarity": "نادر", "chance": 5},
    "هسته جن": {"race": "جن", "rarity": "معمولی", "chance": 10},
    "هسته خون": {"race": "خون‌آشام", "rarity": "نادر", "chance": 5},
    "هسته روح": {"race": "روح‌پیمان", "rarity": "نادر", "chance": 5},
    "هسته غول": {"race": "غول", "rarity": "معمولی", "chance": 8},
    "هسته سایه": {"race": "سایه‌رو", "rarity": "نادر", "chance": 5},
    "هسته تایتان": {"race": "تایتان", "rarity": "افسانه‌ای", "chance": 2},
    "هسته رعد": {"race": "فرزند رعد", "rarity": "نادر", "chance": 4},
    "هسته یخ": {"race": "یخ‌زاد", "rarity": "نادر", "chance": 4},
    "هسته ستاره": {"race": "ستاره‌پیمان", "rarity": "افسانه‌ای", "chance": 2.5},
}

FIND_COOLDOWN = timedelta(hours=2)
_user_cores: dict[int, dict[str, int]] = {}  # tg_id -> {core_name: qty}
_last_find: dict[int, datetime] = {}


def list_cores_text() -> str:
    lines = ["💎 <b>هسته‌های نژادی</b>", ""]
    for name, info in CORES.items():
        lines.append(f"• {name} → <b>{info['race']}</b> ({info['rarity']})")
    lines.append("")
    lines.append("/findcore — جستجوی هسته (هر ۲ ساعت)")
    lines.append("/mycore — هسته‌های تو")
    lines.append("/usecore نام‌هسته — تبدیل نژاد")
    return chr(10).join(lines)


def get_user_cores(tg_id: int) -> dict[str, int]:
    return _user_cores.setdefault(tg_id, {})


def add_core(tg_id: int, name: str, qty: int = 1):
    bag = get_user_cores(tg_id)
    bag[name] = bag.get(name, 0) + qty


def find_core(tg_id: int) -> tuple[str | None, str]:
    now = datetime.utcnow()
    last = _last_find.get(tg_id)
    if last and now - last < FIND_COOLDOWN:
        left = int((FIND_COOLDOWN - (now - last)).total_seconds() // 60) + 1
        return None, f"⏳ تا جستجوی بعدی حدود {left} دقیقه"
    _last_find[tg_id] = now
    # weighted random
    names = list(CORES.keys())
    weights = [CORES[n]["chance"] for n in names]
    # 25% chance find nothing
    if random.random() < 0.25:
        return None, "هیچ هسته‌ای پیدا نشد. بعداً دوباره /findcore"
    name = random.choices(names, weights=weights, k=1)[0]
    add_core(tg_id, name, 1)
    info = CORES[name]
    return name, (
        f"💎 هسته پیدا شد: <b>{name}</b>" + chr(10)
        + f"نادر بودن: {info['rarity']}" + chr(10)
        + f"تبدیل به نژاد: <b>{info['race']}</b>" + chr(10)
        + f"/usecore {name}"
    )


def use_core(tg_id: int, core_name: str) -> tuple[str | None, str]:
    core_name = core_name.strip()
    # fuzzy match
    if core_name not in CORES:
        for k in CORES:
            if core_name in k or k in core_name:
                core_name = k
                break
    if core_name not in CORES:
        return None, "هسته نامعتبر. /cores"
    bag = get_user_cores(tg_id)
    if bag.get(core_name, 0) < 1:
        return None, f"این هسته را نداری. /findcore یا /mycore"
    bag[core_name] -= 1
    if bag[core_name] <= 0:
        del bag[core_name]
    race = CORES[core_name]["race"]
    return race, (
        f"✨ هسته «{core_name}» جذب شد!" + chr(10)
        + f"نژاد جدید: <b>{race}</b>"
    )
