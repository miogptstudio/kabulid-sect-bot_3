"""تکنیک‌های پرورش بدن — با اجبار تعادل"""
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

# حداکثر اختلاف سطح بین تکنیک‌ها (اجبار تعادل)
MAX_LEVEL_GAP = 2
# سقف قدرت مؤثر بدن (جلوگیری از اسپم یک تکنیک)
MAX_EFFECTIVE_POWER = 2500

# persistent
from services.persist import get_dict, save as _psave
def _body_map() -> dict:
    return get_dict("body_cult")
def _body_save():
    _psave("body_cult")
# compat: module-level proxy
class _BodyProxy(dict):
    def __getitem__(self, k):
        return _body_map()[str(k)] if str(k) in _body_map() else _body_map()[k]
    def __setitem__(self, k, v):
        d = _body_map(); d[str(k)] = v; _body_save()
    def __contains__(self, k):
        d = _body_map(); return str(k) in d or k in d
    def get(self, k, default=None):
        d = _body_map()
        if str(k) in d: return d[str(k)]
        return d.get(k, default)
    def setdefault(self, k, default=None):
        d = _body_map()
        sk = str(k)
        if sk not in d:
            d[sk] = default if default is not None else {}
            _body_save()
        return d[sk]
_body = _BodyProxy()

CD = timedelta(minutes=3)


def list_techs() -> str:
    lines = ["💪 <b>تکنیک‌های پرورش بدن</b>", ""]
    for n, i in BODY_TECHS.items():
        lines.append(f"• <b>{n}</b> — {i['desc']}")
        lines.append(f"  قدرت+{i['power']} | هزینه {i['energy_cost']} انرژی")
    lines += [
        "",
        "⚠️ باید تکنیک‌ها را <b>متعادل</b> پرورش دهی.",
        f"اختلاف سطح بیشتر از {MAX_LEVEL_GAP} مجاز نیست.",
        "",
        "/bodycult نام — پرورش",
        "یا بنویس: پرورش پوست / پرورش عضله / ...",
        "/mybody — وضعیت بدن",
        "/bodytechs — همین لیست",
    ]
    return chr(10).join(lines)


def get_body(tg_id: int) -> dict:
    d = _body_map()
    sk = str(tg_id)
    if sk not in d:
        d[sk] = {"techs": {}, "total_power": 0, "last": None, "sessions": 0}
        _body_save()
    return d[sk]


def effective_power(tg_id: int) -> int:
    """قدرت مؤثر: حداقل سطح‌ها × تعداد + جریمه عدم تعادل"""
    d = get_body(tg_id)
    techs = d.get("techs") or {}
    if not techs:
        return 0
    levels = list(techs.values())
    mn, mx = min(levels), max(levels)
    # فقط سطوحی که از min بیش از MAX_LEVEL_GAP بالاترند در محاسبه کامل حساب نمی‌شوند
    effective_sum = 0
    for name, lv in techs.items():
        base = BODY_TECHS.get(name, {}).get("power", 10)
        # سطح مؤثر سقف: min+MAX_LEVEL_GAP
        eff_lv = min(lv, mn + MAX_LEVEL_GAP)
        effective_sum += base * eff_lv
    # جریمه اختلاف زیاد
    if mx - mn > MAX_LEVEL_GAP:
        effective_sum = int(effective_sum * 0.5)
    return min(MAX_EFFECTIVE_POWER, int(effective_sum))


def body_power_bonus(tg_id: int) -> int:
    return effective_power(tg_id)


def _can_train(techs: dict, tech_name: str) -> tuple[bool, str]:
    if not techs:
        return True, ""
    levels = list(techs.values())
    mn = min(levels) if levels else 0
    cur = techs.get(tech_name, 0)
    # نمی‌توانی یک تکنیک را خیلی جلو ببری
    if cur >= mn + MAX_LEVEL_GAP and len(techs) >= 1:
        # باید اول بقیه را بالا بیاوری
        lagging = [n for n, lv in techs.items() if lv < cur]
        if lagging or cur > mn + MAX_LEVEL_GAP - 1:
            need = [n for n, lv in techs.items() if lv <= mn]
            if not need:
                need = lagging
            # اگر این تکنیک از قبل جلو است
            if cur - mn >= MAX_LEVEL_GAP:
                return False, (
                    f"⚠️ تعادل بدن لازم است." + chr(10)
                    + f"«{tech_name}» سطح {cur} است؛ حداقل بقیه {mn}." + chr(10)
                    + f"اول این‌ها را پرورش بده: " + "، ".join(need[:5]) + chr(10)
                    + f"حداکثر اختلاف سطح: {MAX_LEVEL_GAP}"
                )
    return True, ""


def train_body(tg_id: int, tech_name: str | None = None) -> tuple[bool, str, int]:
    data = get_body(tg_id)
    now = datetime.utcnow()
    last = data.get("last")
    if last and now - last < CD:
        left = int((CD - (now - last)).total_seconds())
        return False, f"⏳ پرورش بدن هر ۳ دقیقه. {left}ث صبر کن.", 0

    techs = data.get("techs") or {}
    if not tech_name or tech_name not in BODY_TECHS:
        # انتخاب تصادفی از تکنیک‌هایی که مجازند
        candidates = []
        for n in BODY_TECHS:
            ok, _ = _can_train(techs, n)
            if ok:
                candidates.append(n)
        if not candidates:
            candidates = list(BODY_TECHS.keys())[:3]
        tech_name = random.choice(candidates)

    ok, why = _can_train(techs, tech_name)
    if not ok:
        return False, why, 0

    info = BODY_TECHS[tech_name]
    cost = info["energy_cost"]
    lvl = techs.get(tech_name, 0) + 1
    gain = info["power"] + (lvl // 3)
    data["techs"][tech_name] = lvl
    data["total_power"] = int(data.get("total_power", 0)) + gain
    data["last"] = now
    data["sessions"] = int(data.get("sessions", 0)) + 1
    _body_save()

    eff = effective_power(tg_id)
    tip = ""
    if data["sessions"] % 10 == 0:
        tip = chr(10) + "✨ ۱۰ جلسه پرورش — بدن پایدارتر شد."
    # هشدار تعادل
    levels = list(data["techs"].values())
    if levels and max(levels) - min(levels) >= MAX_LEVEL_GAP:
        tip += chr(10) + "⚖️ نزدیک سقف اختلاف سطح — بقیه تکنیک‌ها را هم پرورش بده."
    try:
        from services.body_spirit_realms import add_body_realm_xp
        realm_line = add_body_realm_xp(tg_id, 12 + lvl)
    except Exception:
        realm_line = ""
    msg = (
        f"💪 <b>{tech_name}</b> (سطح {lvl})" + chr(10)
        + f"+{gain} قدرت خام | مجموع خام: {data['total_power']}" + chr(10)
        + f"⚔️ قدرت مؤثر بدن: <b>{eff}</b> / {MAX_EFFECTIVE_POWER}" + chr(10)
        + f"−{cost} انرژی" + tip
        + ((chr(10) + chr(10) + realm_line) if realm_line else "")
    )
    return True, msg, cost


def status(tg_id: int) -> str:
    d = get_body(tg_id)
    eff = effective_power(tg_id)
    lines = [
        "💪 <b>وضعیت پرورش بدن</b>",
        f"قدرت خام: {d.get('total_power', 0)}",
        f"قدرت مؤثر (در نبرد): <b>{eff}</b> / {MAX_EFFECTIVE_POWER}",
        f"جلسات: {d.get('sessions', 0)}",
        f"قانون تعادل: اختلاف سطح ≤ {MAX_LEVEL_GAP}",
        "",
    ]
    techs = d.get("techs") or {}
    if not techs:
        lines.append("هنوز تکنیکی تمرین نکردی. بنویس: پرورش پوست")
    else:
        for n, lv in sorted(techs.items(), key=lambda x: -x[1]):
            lines.append(f"• {n}: سطح {lv}")
    lines += ["", "/bodytechs — لیست تکنیک‌ها"]
    return chr(10).join(lines)


def add_body_power(tg_id: int, amount: int) -> str:
    st = _state(int(tg_id))
    st["total_power"] = int(st.get("total_power") or 0) + int(amount)
    _body_save()
    return f"✅ قدرت بدن +{amount} (کل: {st['total_power']})"
