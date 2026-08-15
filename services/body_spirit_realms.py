"""قلمروهای پرورش بدن و روح"""
from __future__ import annotations

BODY_REALMS = [
    "جسم خام", "پوستآهن", "استخوانفولاد", "عضلهٔ حیوان", "خونجاری",
    "تاندونابریشم", "مغز استخوان بیدار", "اندام درونی محکم", "بدن اژدها",
    "بدن ققنوس", "بدن تایتان", "بدن نیمهخدا", "بدن خدا", "بدن ازلی", "بدن مطلق",
]

SPIRIT_REALMS = [
    "روح خفته", "جرقه آگاهی", "شعله درون", "رود روح", "اقیانوس ذهن",
    "آسمان روحی", "ستارهروان", "کهکشان روان", "روح جاودان", "روح ابدی",
    "روح پوچی", "روح خالق", "روح واحد", "روح بینام", "روح مطلق",
]

# tg -> {realm_index, stage, xp}
from services.persist import get_dict, save as _psave
def _bp():
    return get_dict("body_prog")
def _sp():
    return get_dict("spirit_prog")


STAGES = 10
# XP لازم برای هر مرحله در قلمرو i
def xp_need(realm_i: int, stage: int) -> int:
    return int(100 * (1.5 ** realm_i) * (1 + stage * 0.4))


def get_body_prog(tg: int) -> dict:
    m = _bp(); sk = str(int(tg))
    if sk not in m:
        m[sk] = {"realm": 0, "stage": 1, "xp": 0}
        _psave("body_prog")
    return m[sk]


def get_spirit_prog(tg: int) -> dict:
    m = _sp(); sk = str(int(tg))
    if sk not in m:
        m[sk] = {"realm": 0, "stage": 1, "xp": 0}
        _psave("spirit_prog")
    return m[sk]


def _advance(prog: dict, realms: list, amount: int) -> list[str]:
    msgs = []
    prog["xp"] = int(prog.get("xp") or 0) + int(amount)
    while True:
        ri = int(prog.get("realm") or 0)
        st = int(prog.get("stage") or 1)
        need = xp_need(ri, st)
        if prog["xp"] < need:
            break
        prog["xp"] -= need
        prog["stage"] = st + 1
        if prog["stage"] > STAGES:
            prog["stage"] = 1
            if ri < len(realms) - 1:
                prog["realm"] = ri + 1
                msgs.append(f"🌟 قلمرو → «{realms[prog['realm']]}»")
            else:
                prog["stage"] = STAGES
                prog["xp"] = need - 1
                break
        msgs.append(f"⬆️ مرحله {prog['stage']}/{STAGES} | {realms[int(prog['realm'])]}")
    # caller saves via get_* which shares dict in map — save both
    _psave("body_prog"); _psave("spirit_prog")
    return msgs


def add_body_realm_xp(tg: int, amount: int = 15) -> str:
    p = get_body_prog(tg)
    msgs = _advance(p, BODY_REALMS, amount)
    ri, st = int(p["realm"]), int(p["stage"])
    need = xp_need(ri, st)
    lines = [
        f"💪 قلمرو بدن: <b>{BODY_REALMS[ri]}</b> | مرحله {st}/{STAGES}",
        f"XP: {p['xp']}/{need} (+{amount})",
    ]
    if msgs:
        lines += msgs
    return chr(10).join(lines)


def add_spirit_realm_xp(tg: int, amount: int = 15) -> str:
    p = get_spirit_prog(tg)
    msgs = _advance(p, SPIRIT_REALMS, amount)
    ri, st = int(p["realm"]), int(p["stage"])
    need = xp_need(ri, st)
    lines = [
        f"👻 قلمرو روح: <b>{SPIRIT_REALMS[ri]}</b> | مرحله {st}/{STAGES}",
        f"XP: {p['xp']}/{need} (+{amount})",
    ]
    if msgs:
        lines += msgs
    return chr(10).join(lines)


def body_realm_status(tg: int) -> str:
    p = get_body_prog(tg)
    ri, st = int(p["realm"]), int(p["stage"])
    lines = [
        "💪 <b>قلمروهای پرورش بدن</b>",
        f"فعلی: <b>{BODY_REALMS[ri]}</b> — مرحله {st}/{STAGES}",
        f"XP: {p['xp']}/{xp_need(ri, st)}",
        "",
    ]
    for i, name in enumerate(BODY_REALMS):
        mark = " ←" if i == ri else ""
        lines.append(f"{i+1}. {name}{mark}")
    lines += ["", "با /bodycult یا «پرورش پوست» XP قلمرو بدن میگیری."]
    return chr(10).join(lines)


def spirit_realm_status(tg: int) -> str:
    p = get_spirit_prog(tg)
    ri, st = int(p["realm"]), int(p["stage"])
    lines = [
        "👻 <b>قلمروهای پرورش روح</b>",
        f"فعلی: <b>{SPIRIT_REALMS[ri]}</b> — مرحله {st}/{STAGES}",
        f"XP: {p['xp']}/{xp_need(ri, st)}",
        "",
    ]
    for i, name in enumerate(SPIRIT_REALMS):
        mark = " ←" if i == ri else ""
        lines.append(f"{i+1}. {name}{mark}")
    lines += ["", "با /trainspirit XP قلمرو روح میگیری."]
    return chr(10).join(lines)


def body_realm_power_bonus(tg: int) -> int:
    p = get_body_prog(tg)
    return int(p.get("realm", 0)) * 15 + int(p.get("stage", 1)) * 2


def spirit_realm_power_bonus(tg: int) -> int:
    p = get_spirit_prog(tg)
    return int(p.get("realm", 0)) * 12 + int(p.get("stage", 1)) * 2
