"""سیستمهای توسعهیافته: تبار، قدرت رزمی، خاندان و حکومت."""
from __future__ import annotations
from services.persist import get_dict, save

BLOODLINES = {
    "فانی": (1.0, "تبار عادی"),
    "روحی": (1.15, "تبار وابسته به روح"),
    "آسمانی": (1.35, "تبار آسمانی"),
    "الهی": (1.7, "تبار الهی"),
    "باستانی": (2.0, "تبار باستانی"),
    "هرجومرج": (2.3, "تبار هرجومرج"),
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
    d=get_dict("kingdoms"); return d.get(str(int(tg)), {"name":"قلمرو بینام","capital":"پایتخت","treasury":0,"tax":0,"army":0,"population":0,"cities":[]})

def set_kingdom(tg, **kwargs):
    d=get_dict("kingdoms"); k=str(int(tg)); row=d.get(k) or get_kingdom(tg); row.update(kwargs); d[k]=row; save("kingdoms"); return row

def kingdom_add_city(tg, city):
    row=get_kingdom(tg); cities=list(row.get("cities") or []); 
    if city not in cities: cities.append(city)
    return set_kingdom(tg, cities=cities)

# ==================== سیستمهای جدید V32 ====================
from datetime import datetime, timedelta
import random

CURRENCY_CHAIN = ["سکه", "روحی", "بهشتی", "آسمانی", "خدا", "هرجومرج", "پوچی", "خلقت", "ازلی", "مطلق"]

def _ns_row(ns, tg, default=None):
    d = get_dict(ns); k = str(int(tg))
    if k not in d:
        d[k] = default.copy() if isinstance(default, dict) else (default if default is not None else {})
    return d[k], d

def crime_status(tg):
    row, _ = _ns_row("crime", tg, {"wanted": 0, "jail_until": None, "bounty": 0})
    return row

def commit_crime(tg, severity=1, bounty=0):
    row, d = _ns_row("crime", tg, {"wanted": 0, "jail_until": None, "bounty": 0})
    row["wanted"] = min(100, int(row.get("wanted", 0)) + int(severity))
    row["bounty"] = max(0, int(row.get("bounty", 0)) + int(bounty))
    d[str(int(tg))] = row; save("crime"); return row

def set_jail(tg, hours=1):
    row, d = _ns_row("crime", tg, {"wanted": 0, "jail_until": None, "bounty": 0})
    row["jail_until"] = (datetime.utcnow() + timedelta(hours=max(1, int(hours)))).isoformat()
    d[str(int(tg))] = row; save("crime"); return row

def is_jailed(tg):
    x = crime_status(tg).get("jail_until")
    if not x: return False
    try: return datetime.utcnow() < datetime.fromisoformat(x)
    except Exception: return False

def world_state():
    d = get_dict("world_map")
    if not d:
        d.update({"seasons": "آرام", "danger": 10, "treasure": 0, "regions": {}}); save("world_map")
    return d

def discover_region(tg, name=None):
    d = world_state(); regions = d.setdefault("regions", {})
    name = name or random.choice(["جنگل ارواح", "دشت اژدها", "ویرانه باستانی", "دره آسمانی", "دریای پوچی"])
    regions.setdefault(name, {"owner": None, "danger": random.randint(1, 100), "resources": random.randint(100, 10000)})
    save("world_map"); return name, regions[name]

def kingdom_upgrade(tg, stat="army", amount=1):
    row = get_kingdom(tg)
    aliases={"ارتش":"army","جمعیت":"population","مالیات":"tax","خزانه":"treasury"}
    stat=aliases.get(stat,stat)
    if stat not in {"army","population","tax","treasury"}: return row
    row[stat]=max(0,int(row.get(stat,0))+int(amount)); return set_kingdom(tg, **{stat:row[stat]})

def sect_war(a, b):
    d=get_dict("sect_wars"); key=f"{int(a)}:{int(b)}:{datetime.utcnow().date().isoformat()}"
    if key in d: return d[key]
    score_a=random.randint(1,100); score_b=random.randint(1,100)
    winner=a if score_a>=score_b else b
    d[key]={"a":a,"b":b,"score_a":score_a,"score_b":score_b,"winner":winner,"at":datetime.utcnow().isoformat()}; save("sect_wars"); return d[key]

def world_boss():
    d=get_dict("world_boss")
    if not d or d.get("hp",0)<=0:
        d={"name":random.choice(["اژدهای باستانی","نگهبان خلقت","غول پوچی"]),"hp":random.randint(100000,500000),"max_hp":0,"reward":random.randint(1000,100000),"participants":{}}
        d["max_hp"]=d["hp"]; save("world_boss")
    return d

def hit_world_boss(tg, damage):
    d=world_boss(); dmg=max(1,int(damage)); dmg=min(dmg,d["hp"]); d["hp"]-=dmg
    p=d.setdefault("participants",{}); p[str(int(tg))]=int(p.get(str(int(tg)),0))+dmg; save("world_boss"); return d,dmg

def open_chest(tg, grade="معمولی"):
    """باز کردن صندوق با محدودیت یک‌بار در هر ۲۴ ساعت برای هر بازیکن.

    داده‌های قدیمی chests حفظ می‌شوند؛ فقط last_open_at به رکورد اضافه می‌شود.
    """
    rewards={"معمولی":(100,1000),"نادر":(1000,10000),"افسانهای":(10000,100000),"الهی":(100000,1000000),"مطلق":(1000000,10000000)}
    if grade not in rewards:
        grade = "معمولی"

    d=get_dict("chests")
    key=str(int(tg))
    row=d.setdefault(key,{"opened":0,"coins":0})

    # محدودیت سراسری صندوق: هر ۲۴ ساعت یک بار، مستقل از نوع صندوق.
    now=datetime.utcnow()
    last=row.get("last_open_at")
    if last:
        try:
            last_dt=datetime.fromisoformat(str(last))
            remaining=timedelta(hours=24)-(now-last_dt)
            if remaining.total_seconds()>0:
                return None, int(remaining.total_seconds())
        except (TypeError, ValueError):
            # رکوردهای قدیمی یا خراب مانع استفاده بازیکن نمی‌شوند.
            pass

    lo,hi=rewards[grade]
    amount=random.randint(lo,hi)
    row["opened"]=int(row.get("opened",0))+1
    row["coins"]=int(row.get("coins",0))+amount
    row["last_open_at"]=now.isoformat()
    row["last_grade"]=grade
    d[key]=row
    save("chests")
    return amount, 0

def chain_mission(tg):
    d=get_dict("chain_missions"); k=str(int(tg)); row=d.setdefault(k,{"step":1,"done":0,"reward":0})
    steps=[("شکار",1),("دوئل",1),("کاوش",1),("باس جهانی",1)]
    return row, steps[min(row["step"]-1,len(steps)-1)]

def advance_chain_mission(tg):
    row,_=chain_mission(tg); row["done"]+=1
    if row["done"]>=1:
        row["step"]+=1; row["done"]=0; row["reward"]+=1
    save("chain_missions"); return row

def random_event():
    events=["بارش گنج", "ظهور قلمرو باستانی", "حمله هیولاها", "تخفیف بازار", "رونق مشاغل"]
    d=get_dict("events_state"); d["current"]={"name":random.choice(events),"at":datetime.utcnow().isoformat()}; save("events_state"); return d["current"]

def alliance_create(tg, name):
    d=get_dict("alliances"); key=str(int(tg))
    if key in d: return d[key]
    row={"name":name[:40],"leader":int(tg),"members":[int(tg)],"treasury":0}; d[key]=row; save("alliances"); return row

def alliance_join(leader_tg, member_tg):
    d=get_dict("alliances"); row=d.get(str(int(leader_tg)))
    if not row: return None
    if int(member_tg) not in row["members"]: row["members"].append(int(member_tg))
    save("alliances"); return row

def alliance_list(): return list(get_dict("alliances").values())

def bank(tg):
    d=get_dict("bank"); return d.setdefault(str(int(tg)),{"deposit":0,"invest":0,"last":None})

def bank_deposit(tg, amount):
    row=bank(tg); row["deposit"]+=max(0,int(amount)); row["last"]=datetime.utcnow().isoformat(); save("bank"); return row

def bank_invest(tg, amount):
    row=bank(tg); row["invest"]+=max(0,int(amount)); row["last"]=datetime.utcnow().isoformat(); save("bank"); return row

def bank_balance(tg): return bank(tg)
