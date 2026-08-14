"""سیستم‌های توسعه‌یافته: تبار، قدرت رزمی، خاندان و حکومت."""
from __future__ import annotations
from services.persist import get_dict, save

BLOODLINES = {
    "فانی": (1.0, "تبار عادی"),
    "روحی": (1.15, "تبار وابسته به روح"),
    "آسمانی": (1.35, "تبار آسمانی"),
    "الهی": (1.7, "تبار الهی"),
    "باستانی": (2.0, "تبار باستانی"),
    "هرج‌ومرج": (2.3, "تبار هرج‌ومرج"),
    "خلقت": (2.7, "تبار خلقت"),
    "ازلی": (3.2, "تبار ازلی"),
    "مطلق": (4.0, "تبار مطلق"),
}

def _row(ns, tg):
    d = get_dict(ns); k = str(int(tg))
    if k not in d: d[k] = {}
    return d[k], d

def get_bloodline(tg):
    row, _ = _row("bloodlines", tg)
    return row.get("name", "فانی")

def set_bloodline(tg, name):
    key = next((k for k in BLOODLINES if k == name or k in name or name in k), None)
    if not key: return None
    row, d = _row("bloodlines", tg); row["name"] = key; d[str(int(tg))] = row; save("bloodlines")
    return key

def bloodline_bonus(tg):
    name = get_bloodline(tg)
    return BLOODLINES.get(name, (1.0, ""))[0]

def add_stat(tg, stat, amount):
    row, d = _row("advanced_power", tg)
    row[stat] = int(row.get(stat, 0)) + int(amount)
    d[str(int(tg))] = row; save("advanced_power")
    return row

def get_stats(tg):
    row, _ = _row("advanced_power", tg)
    return {k:int(v or 0) for k,v in row.items()}

def family_note(tg, text):
    row, d = _row("family", tg); row["note"] = text; d[str(int(tg))] = row; save("family"); return row

def get_kingdom(tg):
    d=get_dict("kingdoms"); return d.get(str(int(tg)), {"name":"قلمرو بی‌نام","capital":"پایتخت","treasury":0,"tax":0,"army":0,"population":0,"cities":[]})

def set_kingdom(tg, **kwargs):
    d=get_dict("kingdoms"); k=str(int(tg)); row=d.get(k) or get_kingdom(tg); row.update(kwargs); d[k]=row; save("kingdoms"); return row

def kingdom_add_city(tg, city):
    row=get_kingdom(tg); cities=list(row.get("cities") or []); 
    if city not in cities: cities.append(city)
    return set_kingdom(tg, cities=cities)
