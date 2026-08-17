"""هشت جهان اولیه — مناطق نامدار و مجازات نام اشتباه"""
from __future__ import annotations

WORLD_NAME = "هشت جهان اولیه"

# ترتیب مناطق: عددها + اسلات «ایتری» بین ۷ و ۸
# id برای پیشرفت داخلی؛ label برای نمایش شماره
REGION_ORDER = [
    {"id": 1, "label": "1", "name": "نیک"},
    {"id": 2, "label": "2", "name": "مین"},
    {"id": 3, "label": "3", "name": "والا مقام"},
    {"id": 4, "label": "4", "name": "بلند مرتبه"},
    {"id": 5, "label": "5", "name": None},
    {"id": 6, "label": "6", "name": None},
    {"id": 7, "label": "7", "name": None},
    {"id": 8, "label": "ایتری", "name": None},  # عدد/اسلات بین ۷ و ۸ — نام منطقه نیست
    {"id": 9, "label": "8", "name": None},
]

MAX_INDEX = len(REGION_ORDER) - 1  # 0-based last index

# tg_id -> index در REGION_ORDER (0..MAX_INDEX)، -1 = وارد نشده
from services.persist import get_dict, save as _psave
def _idx_map():
    return get_dict("eight_worlds")



def current_index(tg_id: int) -> int:
    return int(_idx_map().get(str(int(tg_id)), -1))


def current_region_info(tg_id: int) -> dict | None:
    i = current_index(tg_id)
    if i < 0 or i > MAX_INDEX:
        return None
    return REGION_ORDER[i]


def status_text(tg_id: int) -> str:
    i = current_index(tg_id)
    lines = [
        f"🌌 <b>{WORLD_NAME}</b>",
        "",
        "شمارهها: ۱…۷ · <b>ایتری</b> · ۸",
        "نام مناطق: نیک، مین، والا مقام، بلند مرتبه — بقیه بینام",
        "«ایتری» عدد/اسلات بین ۷ و ۸ است، نه نام منطقه.",
        "نام اشتباه برای رفتن به بعد = حذف دائمی اکانت.",
        "",
    ]
    for idx, reg in enumerate(REGION_ORDER):
        mark = " ← تو" if idx == i else ""
        label = reg["label"]
        if reg["name"]:
            lines.append(f"{label}. {reg['name']}{mark}")
        else:
            lines.append(f"{label}. (بینام){mark}")
    if i < 0:
        lines += ["", "هنوز وارد نشدهای. /enter8 — ورود به منطقه ۱ (نیک)"]
    elif i >= MAX_INDEX:
        lines += ["", "به آخرین منطقه رسیدهای."]
    else:
        nxt = REGION_ORDER[i + 1]
        if nxt["name"]:
            lines += ["", f"منطقه بعد ({nxt['label']}) نام دارد. /goregion نامدقیق"]
        else:
            # برای اسلات ایتری و بینامها
            if nxt["label"] == "ایتری":
                lines += ["", "منطقه بعد اسلات <b>ایتری</b> است. /goregion ایتری"]
            else:
                lines += ["", f"منطقه بعد ({nxt['label']}) بینام است. /goregion بینام"]
    lines += ["", "/enter8 — ورود", "/goregion نامیاعدد", "/region8 — وضعیت"]
    return chr(10).join(lines)


def enter(tg_id: int) -> str:
    _idx_map()[str(int(tg_id))] = 0; _psave("eight_worlds")
    return (
        f"وارد {WORLD_NAME} شدی." + chr(10)
        + "منطقه ۱: <b>نیک</b>" + chr(10)
        + "ترتیب اعداد: ۱…۷ → ایتری → ۸" + chr(10)
        + "برای منطقه بعد: /goregion …"
    )


def try_advance(tg_id: int, name_attempt: str) -> tuple[str, bool]:
    """returns (message, wipe_account)"""
    name_attempt = (name_attempt or "").strip()
    i = current_index(tg_id)
    if i < 0:
        return "اول /enter8 بزن.", False
    if i >= MAX_INDEX:
        return "دیگر منطقهای جلوتر نیست.", False
    nxt = REGION_ORDER[i + 1]
    ok = False

    # نرمالسازی
    raw = name_attempt.replace(" ", "").replace("‌", "").replace("-", "")
    low = name_attempt.lower().strip()

    if nxt["name"]:
        # منطقه نامدار: فقط نام درست
        cnorm = nxt["name"].replace(" ", "").replace("‌", "")
        if raw == cnorm or name_attempt == nxt["name"]:
            ok = True
    else:
        # بینام یا اسلات ایتری
        if nxt["label"] == "ایتری":
            # باید خود عدد/اسلات ایتری را بنویسد
            if raw in ("ایتری", "ایتری") or low in ("etree", "e tree", "e-tree", "etri"):
                ok = True
        else:
            # مناطق بینام با شماره معمولی
            if name_attempt in ("بینام", "بينام", "بدون نام", "هیچ", "none", "-"):
                ok = True
            # قبول شماره label هم
            if name_attempt == nxt["label"] or raw == nxt["label"]:
                ok = True

    if not ok:
        return (
            f"ورودی اشتباه برای منطقه بعد ({nxt['label']})." + chr(10)
            + "اکانت برای همیشه پاک میشود.",
            True,
        )
    _idx_map()[str(int(tg_id))] = i + 1; _psave("eight_worlds")
    if nxt["name"]:
        shown = nxt["name"]
    elif nxt["label"] == "ایتری":
        shown = "اسلات ایتری (بین ۷ و ۸)"
    else:
        shown = f"(بینام — شماره {nxt['label']})"
    return f"✅ وارد منطقه <b>{nxt['label']}</b> شدی: {shown}", False
