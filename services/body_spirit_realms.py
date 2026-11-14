"""قلمروهای پرورش بدن و روح — نسخه پاک و منسجم"""
from __future__ import annotations

# فقط قلمروهای فعال و کامل (قلمروهای قدیمی/ناقص حذف شدند)
BODY_REALMS = [
    "جسم خام",
    "پوست آهن",
    "استخوان فولاد",
    "عضله حیوان",
    "خون جاری",
    "تاندون ابریشم",
    "مغز استخوان بیدار",
    "اندام درونی محکم",
    "بدن اژدها",
    "بدن ققنوس",
    "بدن تایتان",
    "بدن نیمه‌خدا",
    "بدن خدا",
    "بدن ازلی",
    "بدن مطلق",
]

SPIRIT_REALMS = [
    "روح خفته",
    "جرقه آگاهی",
    "شعله درون",
    "رود روح",
    "اقیانوس ذهن",
    "آسمان روحی",
    "ستاره روان",
    "کهکشان روان",
    "روح جاودان",
    "روح ابدی",
    "روح پوچی",
    "روح خالق",
    "روح واحد",
    "روح بی‌نام",
    "روح مطلق",
]

from services.persist import get_dict, save as _psave


def _bp():
    return get_dict("body_prog")


def _sp():
    return get_dict("spirit_prog")


STAGES = 10


def xp_need(realm_i: int, stage: int) -> int:
    return int(100 * (1.5 ** realm_i) * (1 + stage * 0.4))


def get_body_prog(tg: int) -> dict:
    m = _bp()
    sk = str(int(tg))
    if sk not in m:
        m[sk] = {"realm": 0, "stage": 1, "xp": 0}
        _psave("body_prog")
    # clamp به قلمروهای موجود
    prog = m[sk]
    if int(prog.get("realm") or 0) >= len(BODY_REALMS):
        prog["realm"] = len(BODY_REALMS) - 1
        prog["stage"] = STAGES
        _psave("body_prog")
    return prog


def get_spirit_prog(tg: int) -> dict:
    m = _sp()
    sk = str(int(tg))
    if sk not in m:
        m[sk] = {"realm": 0, "stage": 1, "xp": 0}
        _psave("spirit_prog")
    prog = m[sk]
    if int(prog.get("realm") or 0) >= len(SPIRIT_REALMS):
        prog["realm"] = len(SPIRIT_REALMS) - 1
        prog["stage"] = STAGES
        _psave("spirit_prog")
    return prog


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
                msgs.append(f"⬆ ورود به قلمرو: <b>{realms[prog['realm']]}</b>")
            else:
                prog["stage"] = STAGES
                prog["xp"] = 0
                msgs.append("✨ به نهایت این مسیر رسیدی.")
                break
        else:
            msgs.append(f"📈 مرحله {prog['stage']}/{STAGES} در {realms[ri]}")
    return msgs


def train_body(tg: int, amount: int = 20) -> str:
    prog = get_body_prog(tg)
    msgs = _advance(prog, BODY_REALMS, amount)
    _psave("body_prog")
    ri = int(prog.get("realm") or 0)
    st = int(prog.get("stage") or 1)
    head = f"💪 بدن: <b>{BODY_REALMS[ri]}</b> — مرحله {st}/{STAGES} | XP {prog.get('xp', 0)}"
    return head + (("\n" + "\n".join(msgs)) if msgs else "")


def train_spirit(tg: int, amount: int = 20) -> str:
    prog = get_spirit_prog(tg)
    msgs = _advance(prog, SPIRIT_REALMS, amount)
    _psave("spirit_prog")
    ri = int(prog.get("realm") or 0)
    st = int(prog.get("stage") or 1)
    head = f"🌀 روح: <b>{SPIRIT_REALMS[ri]}</b> — مرحله {st}/{STAGES} | XP {prog.get('xp', 0)}"
    return head + (("\n" + "\n".join(msgs)) if msgs else "")


def body_power_bonus(tg: int) -> int:
    prog = get_body_prog(tg)
    ri = int(prog.get("realm") or 0)
    st = int(prog.get("stage") or 1)
    return int(ri * 120 + st * 15)


def spirit_power_bonus(tg: int) -> int:
    prog = get_spirit_prog(tg)
    ri = int(prog.get("realm") or 0)
    st = int(prog.get("stage") or 1)
    return int(ri * 100 + st * 12)


def status_text(tg: int) -> str:
    bp = get_body_prog(tg)
    sp = get_spirit_prog(tg)
    br = BODY_REALMS[int(bp.get("realm") or 0)]
    sr = SPIRIT_REALMS[int(sp.get("realm") or 0)]
    return (
        f"💪 بدن: <b>{br}</b> — مرحله {bp.get('stage', 1)}/{STAGES}\n"
        f"🌀 روح: <b>{sr}</b> — مرحله {sp.get('stage', 1)}/{STAGES}\n"
        f"⚡ بونوس قدرت بدن: +{body_power_bonus(tg):,}\n"
        f"✨ بونوس قدرت روح: +{spirit_power_bonus(tg):,}"
    )
