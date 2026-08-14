"""مسیر تذهیب: قدرت / سرعت / دفاع و ترکیب‌ها"""
from __future__ import annotations
from services.persist import get_dict, save as _psave

PATHS = {
    "قدرت": {"power": 1.25, "speed": 0.9, "defense": 0.9, "desc": "حمله خام بیشتر"},
    "سرعت": {"power": 0.9, "speed": 1.3, "defense": 0.9, "desc": "جاخالی و نوبت بیشتر"},
    "دفاع": {"power": 0.9, "speed": 0.9, "defense": 1.3, "desc": "کاهش آسیب دریافتی"},
    "قدرت‌سرعت": {"power": 1.12, "speed": 1.12, "defense": 0.85, "desc": "حمله و جاخالی"},
    "قدرت‌دفاع": {"power": 1.12, "speed": 0.85, "defense": 1.12, "desc": "ضربه و سپر"},
    "سرعت‌دفاع": {"power": 0.85, "speed": 1.12, "defense": 1.12, "desc": "جاخالی و مقاومت"},
    "سه‌گانه": {"power": 1.08, "speed": 1.08, "defense": 1.08, "desc": "متعادل هر سه"},
    "خالص": {"power": 1.0, "speed": 1.0, "defense": 1.0, "desc": "بدون گرایش خاص"},
}


def _map() -> dict:
    return get_dict("cult_paths")


def get_path(tg: int) -> str:
    return str(_map().get(str(int(tg)), "خالص") or "خالص")


def set_path(tg: int, name: str) -> str:
    name = (name or "").strip()
    aliases = {
        "power": "قدرت", "atk": "قدرت", "attack": "قدرت",
        "speed": "سرعت", "spd": "سرعت", "dodge": "سرعت",
        "def": "دفاع", "defense": "دفاع", "tank": "دفاع",
        "ps": "قدرت‌سرعت", "قدرت سرعت": "قدرت‌سرعت",
        "pd": "قدرت‌دفاع", "قدرت دفاع": "قدرت‌دفاع",
        "sd": "سرعت‌دفاع", "سرعت دفاع": "سرعت‌دفاع",
        "all": "سه‌گانه", "triple": "سه‌گانه", "3": "سه‌گانه",
        "none": "خالص", "normal": "خالص",
    }
    name = aliases.get(name, name)
    if name not in PATHS:
        # fuzzy
        for k in PATHS:
            if name in k or k in name:
                name = k
                break
    if name not in PATHS:
        return "مسیر نامعتبر. /cultpath برای لیست"
    m = _map()
    m[str(int(tg))] = name
    _psave("cult_paths")
    info = PATHS[name]
    return (
        f"🛤️ مسیر تذهیب: <b>{name}</b>" + chr(10)
        + info["desc"] + chr(10)
        + f"ضریب قدرت ×{info['power']} | سرعت ×{info['speed']} | دفاع ×{info['defense']}"
    )


def mults(tg: int) -> dict:
    p = get_path(tg)
    return PATHS.get(p, PATHS["خالص"])


def list_paths() -> str:
    lines = ["🛤️ <b>مسیرهای تذهیب</b>", "یکی را انتخاب کن:", ""]
    for k, v in PATHS.items():
        lines.append(f"• <b>{k}</b> — {v['desc']}")
        lines.append(f"  قدرت×{v['power']} سرعت×{v['speed']} دفاع×{v['defense']}")
    lines += ["", "/cultpath نام — انتخاب", "مثال: /cultpath قدرت | /cultpath سه‌گانه"]
    return chr(10).join(lines)
