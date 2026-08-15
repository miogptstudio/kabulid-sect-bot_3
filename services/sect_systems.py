"""خزانه، برج تهذیب، کتابخانه تکنیک، ارتقای رهبری و مأموریت فرقه"""
from __future__ import annotations
from datetime import datetime, timedelta
from services.persist import get_dict, save as _psave

# ---------- خزانه ----------
def _treasury() -> dict:
    return get_dict("sect_treasury")


def get_treasury(sect_id: int) -> dict:
    m = _treasury()
    sk = str(int(sect_id))
    if sk not in m:
        m[sk] = {"coins": 0, "spirit": 0, "heavenly": 0, "materials": 0}
        _psave("sect_treasury")
    return m[sk]


def deposit(sect_id: int, currency: str, amount: int) -> str:
    amount = int(amount)
    if amount <= 0:
        return "مقدار نامعتبر."
    cur = currency.lower().strip()
    alias = {
        "سکه": "coins", "coins": "coins", "coin": "coins",
        "روحی": "spirit", "spirit": "spirit", "سنگروحی": "spirit",
        "بهشتی": "heavenly", "heavenly": "heavenly",
        "مواد": "materials", "material": "materials", "resources": "materials",
    }
    key = alias.get(cur)
    if not key:
        return "ارز: coins | spirit | heavenly | materials"
    t = get_treasury(sect_id)
    t[key] = int(t.get(key) or 0) + amount
    m = _treasury(); m[str(int(sect_id))] = t; _psave("sect_treasury")
    return f"✅ واریز {amount:,} {key} به خزانه. موجودی {key}: {t[key]:,}"


def withdraw(sect_id: int, currency: str, amount: int) -> tuple[bool, str]:
    amount = int(amount)
    alias = {
        "سکه": "coins", "coins": "coins", "coin": "coins",
        "روحی": "spirit", "spirit": "spirit",
        "بهشتی": "heavenly", "heavenly": "heavenly",
        "مواد": "materials", "materials": "materials",
    }
    key = alias.get(currency.lower().strip())
    if not key:
        return False, "ارز نامعتبر."
    t = get_treasury(sect_id)
    if int(t.get(key) or 0) < amount:
        return False, f"خزانه کافی نیست ({t.get(key,0):,})."
    t[key] = int(t.get(key) or 0) - amount
    m = _treasury(); m[str(int(sect_id))] = t; _psave("sect_treasury")
    return True, f"برداشت {amount:,} {key}."


def treasury_text(sect_id: int, sect_name: str = "") -> str:
    t = get_treasury(sect_id)
    return (
        f"🏦 <b>خزانه فرقه {sect_name}</b>" + chr(10)
        + f"🪙 سکه: {int(t.get('coins') or 0):,}" + chr(10)
        + f"💎 روحی: {int(t.get('spirit') or 0):,}" + chr(10)
        + f"✨ بهشتی: {int(t.get('heavenly') or 0):,}" + chr(10)
        + f"📦 مواد: {int(t.get('materials') or 0):,}" + chr(10)
        + chr(10) + "/sectdeposit نوع مقدار — واریز از کیف خودت"
        + chr(10) + "/sectwithdraw نوع مقدار — برداشت (رهبر/ارجمند)"
    )


# ---------- ساختمانهای فرقه ----------
BUILDINGS = {
    "tower": {
        "name": "برج تهذیب",
        "max_level": 10,
        "cost_key": "spirit",
        "base_cost": 50,
        "effect": "بونوس انرژی تذهیب اعضا",
    },
    "library": {
        "name": "کتابخانه تکنیک",
        "max_level": 10,
        "cost_key": "heavenly",
        "base_cost": 20,
        "effect": "یادگیری تکنیک فرقهای",
    },
    "forge": {
        "name": "آهنگری فرقه",
        "max_level": 10,
        "cost_key": "materials",
        "base_cost": 30,
        "effect": "ساخت سلاح/ابزار با مواد خزانه",
    },
}


def _buildings() -> dict:
    return get_dict("sect_buildings")


def get_buildings(sect_id: int) -> dict:
    m = _buildings()
    sk = str(int(sect_id))
    if sk not in m:
        m[sk] = {"tower": 1, "library": 1, "forge": 1}
        _psave("sect_buildings")
    return m[sk]


def upgrade_building(sect_id: int, bkey: str) -> str:
    if bkey not in BUILDINGS:
        return "ساختمان: tower | library | forge"
    info = BUILDINGS[bkey]
    b = get_buildings(sect_id)
    lvl = int(b.get(bkey) or 1)
    if lvl >= info["max_level"]:
        return f"{info['name']} در سقف سطح است."
    cost = info["base_cost"] * lvl * lvl
    ok, msg = withdraw(sect_id, info["cost_key"], cost)
    if not ok:
        return f"برای ارتقا به سطح {lvl+1} نیاز به {cost} {info['cost_key']}. {msg}"
    b[bkey] = lvl + 1
    m = _buildings(); m[str(int(sect_id))] = b; _psave("sect_buildings")
    return f"🏗 {info['name']} → سطح <b>{lvl+1}</b> (هزینه {cost} {info['cost_key']})"


def buildings_text(sect_id: int) -> str:
    b = get_buildings(sect_id)
    lines = ["🏛 <b>ساختمانهای فرقه</b>", ""]
    for k, info in BUILDINGS.items():
        lvl = int(b.get(k) or 1)
        cost = info["base_cost"] * lvl * lvl
        lines.append(f"• {info['name']}: سطح {lvl}/{info['max_level']}")
        lines.append(f"  {info['effect']}")
        lines.append(f"  ارتقا: {cost} {info['cost_key']} — /sectupgrade {k}")
    return chr(10).join(lines)


def tower_bonus(sect_id: int) -> float:
    lvl = int(get_buildings(sect_id).get("tower") or 1)
    return 1.0 + lvl * 0.03  # تا +30%


def library_level(sect_id: int) -> int:
    return int(get_buildings(sect_id).get("library") or 1)


def forge_level(sect_id: int) -> int:
    return int(get_buildings(sect_id).get("forge") or 1)


# تکنیکهای کتابخانه بر اساس سطح
LIBRARY_TECHS = {
    1: [("تنفس فرقهای", 5)],
    2: [("تیغه هماهنگ", 8)],
    3: [("سپر جمعی", 10)],
    4: [("جریان چی گروهی", 12)],
    5: [("نگاه رهبر", 15)],
    6: [("ضربه همصدا", 18)],
    7: [("حفاظت ارجمند", 22)],
    8: [("عروج جمعی", 28)],
    9: [("قانون فرقه", 35)],
    10: [("اراده بنیانگذار", 50)],
}


def list_library_techs(sect_id: int) -> str:
    lvl = library_level(sect_id)
    lines = [f"📚 <b>کتابخانه تکنیک</b> (سطح {lvl})", ""]
    for L in range(1, lvl + 1):
        for name, pwr in LIBRARY_TECHS.get(L, []):
            lines.append(f"Lv{L}: {name} (+{pwr} قدرت)")
    lines += ["", "/learnsecttech نام — یادگیری (نیاز امتیاز مشارکت)"]
    return chr(10).join(lines)


def _learned() -> dict:
    return get_dict("sect_tech_learned")


def learn_sect_tech(tg_id: int, sect_id: int, tech_name: str, contribution: int) -> str:
    lvl = library_level(sect_id)
    found = None
    need_contrib = 20
    for L in range(1, lvl + 1):
        for name, pwr in LIBRARY_TECHS.get(L, []):
            if name == tech_name or tech_name in name:
                found = (name, pwr, L)
                need_contrib = 10 + L * 5
    if not found:
        return "تکنیک در سطح کتابخانه فعلی نیست."
    if contribution < need_contrib:
        return f"امتیاز مشارکت کم است (نیاز {need_contrib})."
    m = _learned()
    sk = str(int(tg_id))
    bag = list(m.get(sk) or [])
    if found[0] in bag:
        return "قبلاً یاد گرفتهای."
    bag.append(found[0])
    m[sk] = bag
    _psave("sect_tech_learned")
    return f"📖 تکنیک <b>{found[0]}</b> یاد گرفته شد (+{found[1]} قدرت). امتیاز لازم بود: {need_contrib}"


def sect_tech_power(tg_id: int) -> int:
    bag = _learned().get(str(int(tg_id))) or []
    total = 0
    for L, techs in LIBRARY_TECHS.items():
        for name, pwr in techs:
            if name in bag:
                total += pwr
    return total


# ---------- ارتقای مقام رهبری ----------
LEADER_RANKS = [
    ("رهبر نوپا", 0),
    ("رهبر تثبیتشده", 100),
    ("رهبر کهن", 300),
    ("رهبر اعظم", 700),
    ("پیر فرقه", 1500),
    ("اسطوره فرقه", 3000),
]


def _leader_xp() -> dict:
    return get_dict("sect_leader_xp")


def leader_xp(sect_id: int) -> int:
    return int(_leader_xp().get(str(int(sect_id)), 0) or 0)


def add_leader_xp(sect_id: int, amount: int) -> str:
    m = _leader_xp()
    sk = str(int(sect_id))
    m[sk] = leader_xp(sect_id) + int(amount)
    _psave("sect_leader_xp")
    return leader_rank_text(sect_id)


def leader_rank_name(sect_id: int) -> str:
    xp = leader_xp(sect_id)
    cur = LEADER_RANKS[0][0]
    for name, need in LEADER_RANKS:
        if xp >= need:
            cur = name
    return cur


def leader_rank_text(sect_id: int) -> str:
    xp = leader_xp(sect_id)
    cur = leader_rank_name(sect_id)
    nxt = None
    for name, need in LEADER_RANKS:
        if need > xp:
            nxt = (name, need)
            break
    lines = [
        f"👑 مقام رهبری: <b>{cur}</b>",
        f"XP رهبری: {xp}",
    ]
    if nxt:
        lines.append(f"بعدی: {nxt[0]} (نیاز {nxt[1]} XP)")
    else:
        lines.append("سقف مقام رهبری")
    return chr(10).join(lines)


# ---------- مأموریت فرقه ----------
MISSION_TEMPLATES = [
    {"id": "gather_herb", "title": "جمعآوری گیاه روحی", "contrib": 8, "coins": 40, "materials": 2, "leader_xp": 3},
    {"id": "patrol", "title": "گشتزنی قلمرو", "contrib": 10, "coins": 50, "materials": 1, "leader_xp": 4},
    {"id": "forge_aid", "title": "کمک در آهنگری فرقه", "contrib": 12, "coins": 30, "materials": 4, "leader_xp": 5},
    {"id": "library_copy", "title": "رونویسی کتاب تکنیک", "contrib": 15, "coins": 20, "spirit": 2, "leader_xp": 6},
    {"id": "tower_meditate", "title": "مدیتیشن گروهی در برج", "contrib": 14, "spirit": 5, "coins": 25, "leader_xp": 5},
    {"id": "recruit", "title": "جذب عضو جدید", "contrib": 20, "coins": 80, "materials": 3, "leader_xp": 8},
    {"id": "defend", "title": "دفاع از مرز", "contrib": 18, "coins": 60, "materials": 2, "leader_xp": 7},
]


def _missions() -> dict:
    return get_dict("sect_missions")


def _contrib() -> dict:
    return get_dict("sect_contribution")


def get_contrib(tg_id: int) -> int:
    return int(_contrib().get(str(int(tg_id)), 0) or 0)


def add_contrib(tg_id: int, amount: int) -> int:
    m = _contrib()
    sk = str(int(tg_id))
    m[sk] = get_contrib(tg_id) + int(amount)
    _psave("sect_contribution")
    return int(m[sk])


def list_open_missions(sect_id: int) -> str:
    m = _missions()
    sk = str(int(sect_id))
    open_m = m.get(sk) or {"active": [], "done_today": {}}
    lines = ["📜 <b>مأموریتهای فرقه</b>", ""]
    if not open_m.get("active"):
        lines.append("مأموریت فعالی نیست. رهبر/ارجمند: /assignsectmission")
    else:
        for i, mid in enumerate(open_m["active"], 1):
            tpl = next((t for t in MISSION_TEMPLATES if t["id"] == mid), None)
            if tpl:
                lines.append(
                    f"{i}. {tpl['title']} — مشارکت +{tpl['contrib']} | "
                    f"پاداش منابع"
                )
    lines += [
        "",
        "/assignsectmission — صدور مأموریت (رهبر/ارجمند)",
        "/dosectmission شماره — انجام مأموریت (اعضا)",
        f"امتیاز مشارکت تو: {get_contrib(0)} (با /mysectmission ببین)",
    ]
    return chr(10).join(lines)


def assign_missions(sect_id: int, count: int = 3) -> str:
    import random
    m = _missions()
    sk = str(int(sect_id))
    data = m.get(sk) or {"active": [], "done_today": {}}
    picks = random.sample(MISSION_TEMPLATES, k=min(count, len(MISSION_TEMPLATES)))
    data["active"] = [p["id"] for p in picks]
    m[sk] = data
    _psave("sect_missions")
    lines = ["✅ مأموریتهای جدید صادر شد:", ""]
    for i, p in enumerate(picks, 1):
        lines.append(f"{i}. {p['title']} (+{p['contrib']} مشارکت)")
    lines.append("اعضا: /dosectmission شماره")
    return chr(10).join(lines)


def do_mission(tg_id: int, sect_id: int, index: int) -> str:
    m = _missions()
    sk = str(int(sect_id))
    data = m.get(sk) or {"active": [], "done_today": {}}
    active = list(data.get("active") or [])
    if index < 1 or index > len(active):
        return "شماره مأموریت نامعتبر. /sectmissions"
    mid = active[index - 1]
    # روزانه یکبار هر مأموریت برای هر نفر
    day = datetime.utcnow().strftime("%Y-%m-%d")
    done = data.setdefault("done_today", {})
    ukey = f"{tg_id}:{mid}:{day}"
    if done.get(ukey):
        return "این مأموریت را امروز انجام دادهای."
    tpl = next((t for t in MISSION_TEMPLATES if t["id"] == mid), None)
    if not tpl:
        return "مأموریت نامعتبر."
    done[ukey] = True
    data["done_today"] = done
    m[sk] = data
    _psave("sect_missions")
    # پاداش
    c = add_contrib(tg_id, tpl["contrib"])
    t = get_treasury(sect_id)
    t["coins"] = int(t.get("coins") or 0) + int(tpl.get("coins") or 0)
    t["spirit"] = int(t.get("spirit") or 0) + int(tpl.get("spirit") or 0)
    t["materials"] = int(t.get("materials") or 0) + int(tpl.get("materials") or 0)
    tm = _treasury(); tm[str(int(sect_id))] = t; _psave("sect_treasury")
    add_leader_xp(sect_id, int(tpl.get("leader_xp") or 0))
    try:
        from services.sect_exam import add_promo_score
        add_promo_score(sect_id, tg_id, int(tpl.get("contrib") or 1))
    except Exception:
        pass
    # پاداش شخصی سکه
    personal = int(tpl.get("coins") or 0) // 2
    return (
        f"✅ مأموریت <b>{tpl['title']}</b> انجام شد." + chr(10)
        + f"🏅 مشارکت تو: +{tpl['contrib']} (جمع {c})" + chr(10)
        + f"🏦 خزانه: +{tpl.get('coins',0)} سکه / +{tpl.get('spirit',0)} روحی / +{tpl.get('materials',0)} مواد" + chr(10)
        + f"🎁 پاداش شخصی: +{personal} سکه (با /claimsectreward بعداً یا خودکار در ولت)" + chr(10)
        + f"👑 XP رهبری فرقه: +{tpl.get('leader_xp',0)}"
    )


def claim_personal_hint() -> int:
    return 0
