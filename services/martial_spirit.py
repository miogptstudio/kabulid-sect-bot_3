"""روح رزمی — بیدارسازی، رشد، اثر در دوئل"""
from datetime import datetime, timedelta
import random

SPIRIT_TYPES = {
    "شمشیر روح": {"elem": "فلز", "atk": 1.2, "def": 0.9, "desc": "برش تیز — حمله بالا"},
    "نیزه رعد": {"elem": "رعد", "atk": 1.25, "def": 0.85, "desc": "سرعت و نفوذ"},
    "سپر کوه": {"elem": "خاک", "atk": 0.9, "def": 1.3, "desc": "دفاع سنگین"},
    "شعله ققنوس": {"elem": "آتش", "atk": 1.3, "def": 0.8, "desc": "سوخت و آسیب"},
    "موج سیمرغ": {"elem": "باد", "atk": 1.15, "def": 1.1, "desc": "حکمت و تعادل ایرانی"},
    "سایه دیو": {"elem": "تاریکی", "atk": 1.35, "def": 0.75, "desc": "حمله وحشی"},
    "نور آناهیتا": {"elem": "آب", "atk": 1.0, "def": 1.25, "desc": "شفا و پایداری"},
    "چنگال اژدها": {"elem": "اژدها", "atk": 1.4, "def": 1.0, "desc": "قدرت اژدها"},
    "کمان رخش": {"elem": "سرعت", "atk": 1.2, "def": 1.0, "desc": "دقت و سرعت پهلوانی"},
    "گرز کاوه": {"elem": "آهن", "atk": 1.15, "def": 1.15, "desc": "ضربه قیام"},
}

# tg_id -> spirit state
_spirits: dict[int, dict] = {}
_last_train: dict[int, datetime] = {}
TRAIN_CD = timedelta(minutes=30)


def get_spirit(tg_id: int) -> dict | None:
    return _spirits.get(tg_id)


def awaken(tg_id: int, preferred: str | None = None) -> tuple[bool, str]:
    if tg_id in _spirits:
        s = _spirits[tg_id]
        return False, f"روح رزمی داری: <b>{s['type']}</b> Lv.{s['level']}"
    if preferred and preferred in SPIRIT_TYPES:
        st = preferred
    else:
        st = random.choice(list(SPIRIT_TYPES.keys()))
    _spirits[tg_id] = {
        "type": st,
        "level": 1,
        "exp": 0,
        "exp_need": 50,
        "active": True,
    }
    info = SPIRIT_TYPES[st]
    return True, (
        f"👻 روح رزمی بیدار شد: <b>{st}</b>" + chr(10)
        + f"عنصر: {info['elem']}" + chr(10)
        + f"{info['desc']}" + chr(10)
        + f"حمله ×{info['atk']} | دفاع ×{info['def']}" + chr(10)
        + "/spirit · /trainspirit · /spiritmode"
    )


def status_text(tg_id: int) -> str:
    s = get_spirit(tg_id)
    if not s:
        return "روح رزمی نداری. /awaken یا /بیدار‌روح"
    info = SPIRIT_TYPES.get(s["type"], {})
    on = "فعال ✅" if s.get("active", True) else "خاموش ⏸"
    return (
        f"👻 <b>روح رزمی</b>" + chr(10)
        + f"نوع: <b>{s['type']}</b>" + chr(10)
        + f"سطح: {s['level']}" + chr(10)
        + f"تجربه: {s['exp']}/{s['exp_need']}" + chr(10)
        + f"وضعیت در دوئل: {on}" + chr(10)
        + f"عنصر: {info.get('elem')}" + chr(10)
        + f"{info.get('desc')}" + chr(10)
        + f"ضریب حمله ×{info.get('atk')} | دفاع ×{info.get('def')}" + chr(10)
        + "/trainspirit — تمرین | /spiritmode — روشن/خاموش"
    )


def train(tg_id: int) -> str:
    s = get_spirit(tg_id)
    if not s:
        return "اول /awaken"
    now = datetime.utcnow()
    last = _last_train.get(tg_id)
    if last and now - last < TRAIN_CD:
        left = int((TRAIN_CD - (now - last)).total_seconds() // 60) + 1
        return f"⏳ تمرین بعدی حدود {left} دقیقه دیگر"
    _last_train[tg_id] = now
    gain = random.randint(8, 20) + s["level"]
    s["exp"] += gain
    msg = f"🏋️ روح رزمی تمرین کرد: +{gain} EXP"
    while s["exp"] >= s["exp_need"]:
        s["exp"] -= s["exp_need"]
        s["level"] += 1
        s["exp_need"] = 50 + s["level"] * 25
        msg += chr(10) + f"⬆ سطح روح رزمی → {s['level']}"
    return msg + chr(10) + f"الان Lv.{s['level']} | {s['exp']}/{s['exp_need']}"


def toggle(tg_id: int) -> str:
    s = get_spirit(tg_id)
    if not s:
        return "اول /awaken"
    s["active"] = not s.get("active", True)
    return "روح رزمی در دوئل: " + ("فعال ✅" if s["active"] else "خاموش ⏸")


def power_bonus(tg_id: int) -> int:
    """بونوس قدرت عددی برای calc_power / duel"""
    s = get_spirit(tg_id)
    if not s or not s.get("active", True):
        return 0
    info = SPIRIT_TYPES.get(s["type"], {})
    atk = float(info.get("atk", 1.0))
    # سطح * ضریب حمله
    return int(s["level"] * 6 * atk)


def on_duel_win(tg_id: int, amount: int = 5):
    s = get_spirit(tg_id)
    if not s:
        return
    s["exp"] += amount
    while s["exp"] >= s["exp_need"]:
        s["exp"] -= s["exp_need"]
        s["level"] += 1
        s["exp_need"] = 50 + s["level"] * 25
