"""تکنیک‌های پرورش بدن"""
from datetime import datetime, timedelta
import random

BODY_TECHS = {
    "پرورش پوست": {"power": 8, "energy_cost": 500, "desc": "پوست سخت‌تر — دفاع سبک"},
    "پرورش استخوان": {"power": 12, "energy_cost": 800, "desc": "استخوان‌های فولادی"},
    "پرورش عضله": {"power": 15, "energy_cost": 1000, "desc": "قدرت ضربه بیشتر"},
    "پرورش خون": {"power": 10, "energy_cost": 700, "desc": "خون و حیات پایدارتر"},
    "پرورش تاندون": {"power": 14, "energy_cost": 900, "desc": "سرعت و انعطاف"},
    "پرورش مغز استخوان": {"power": 18, "energy_cost": 1500, "desc": "ریشه بدن عمیق"},
    "پرورش اندام درونی": {"power": 20, "energy_cost": 2000, "desc": "قلب و ریه قوی"},
    "پرورش بدن اژدها": {"power": 35, "energy_cost": 5000, "desc": "بدن افسانه‌ای"},
    "پرورش بدن خدا": {"power": 50, "energy_cost": 12000, "desc": "حد نهایی بدن فانی"},
}

# tg_id -> {tech: level, total_power, last}
_body: dict[int, dict] = {}
CD = timedelta(minutes=3)


def list_techs() -> str:
    lines = ["💪 <b>تکنیک‌های پرورش بدن</b>", ""]
    for n, i in BODY_TECHS.items():
        lines.append(f"• <b>{n}</b> — {i['desc']}")
        lines.append(f"  قدرت+{i['power']} | هزینه {i['energy_cost']} انرژی")
    lines += [
        "",
        "/bodycult نام — پرورش",
        "یا بنویس: پرورش بدن / پرورش دادن بدن",
        "/mybody — وضعیت بدن",
        "/bodytechs — همین لیست",
    ]
    return chr(10).join(lines)


def get_body(tg_id: int) -> dict:
    if tg_id not in _body:
        _body[tg_id] = {"techs": {}, "total_power": 0, "last": None, "sessions": 0}
    return _body[tg_id]


def body_power_bonus(tg_id: int) -> int:
    return int(get_body(tg_id).get("total_power", 0))


def train_body(tg_id: int, tech_name: str | None = None) -> tuple[bool, str, int]:
    """returns ok, message, energy_cost"""
    data = get_body(tg_id)
    now = datetime.utcnow()
    last = data.get("last")
    if last and now - last < CD:
        left = int((CD - (now - last)).total_seconds())
        return False, f"⏳ پرورش بدن هر ۳ دقیقه. {left}ث صبر کن.", 0

    if not tech_name or tech_name not in BODY_TECHS:
        # انتخاب تصادفی از تکنیک‌های یادگرفته یا پوست
        known = list(data["techs"].keys()) or ["پرورش پوست"]
        tech_name = random.choice(known) if known else "پرورش پوست"
        if tech_name not in BODY_TECHS:
            tech_name = "پرورش پوست"

    info = BODY_TECHS[tech_name]
    cost = info["energy_cost"]
    lvl = data["techs"].get(tech_name, 0) + 1
    # بازده با سطح کمی بیشتر
    gain = info["power"] + (lvl // 3)
    data["techs"][tech_name] = lvl
    data["total_power"] = int(data.get("total_power", 0)) + gain
    data["last"] = now
    data["sessions"] = int(data.get("sessions", 0)) + 1

    # شانس ارتقای نوع بدن در خدمات cultivation — پیام راهنما
    tip = ""
    if data["sessions"] % 10 == 0:
        tip = chr(10) + "✨ ۱۰ جلسه پرورش — بدن پایدارتر شد (قدرت دائمی)."
    msg = (
        f"💪 <b>{tech_name}</b> (سطح {lvl})" + chr(10)
        + f"+{gain} قدرت بدن | مجموع قدرت بدن: {data['total_power']}" + chr(10)
        + f"−{cost} انرژی" + tip
    )
    return True, msg, cost


def status(tg_id: int) -> str:
    d = get_body(tg_id)
    lines = [
        "💪 <b>وضعیت پرورش بدن</b>",
        f"قدرت بدن: {d.get('total_power', 0)}",
        f"جلسات: {d.get('sessions', 0)}",
        "",
    ]
    techs = d.get("techs") or {}
    if not techs:
        lines.append("هنوز تکنیکی تمرین نکردی. /bodycult یا بنویس: پرورش بدن")
    else:
        for n, lv in techs.items():
            lines.append(f"• {n}: سطح {lv}")
    lines += ["", "/bodytechs — لیست تکنیک‌ها"]
    return chr(10).join(lines)
