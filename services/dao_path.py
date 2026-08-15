"""مسیر معنوی: ارتدوکس / شیطانی / بیطرف — محدودیت یادگیری تکنیک"""
from __future__ import annotations
from services.persist import get_dict, save as _psave

PATHS = ("ارتدوکس", "شیطانی", "بیطرف")

# کلیدواژههای تشخیص مسیر تکنیک از نام/توضیح
DEMON_KEYS = (
    "شیطان", "اهریمن", "خون", "تاریکی", "سایه", "نفرین", "ممنوعه", "مرگ",
    "پوچی", "فساد", "زهر", "نیش", "دیو", "جهنم", "خونآشام", "نیش تاریکی",
    "سایه ابدی", "تنفس خلأ",
)
ORTHO_KEYS = (
    "ارتدوکس", "نور", "بهشت", "قدیس", "پاک", "مهر", "فرشته", "ایزد",
    "آناهیتا", "سیمرغ", "عدالت", "دیوار نور", "نفس نورانی", "بال نور",
    "فریدون", "جمشید",
)


def _map() -> dict:
    return get_dict("dao_paths")


def get_dao(tg: int) -> str:
    v = _map().get(str(int(tg)))
    if v in PATHS:
        return v
    return "بیطرف"  # پیشفرض


def set_dao(tg: int, name: str) -> str:
    name = (name or "").strip()
    aliases = {
        "orthodox": "ارتدوکس", "good": "ارتدوکس", "نور": "ارتدوکس",
        "demon": "شیطانی", "evil": "شیطانی", "dark": "شیطانی",
        "neutral": "بیطرف", "none": "بیطرف", "بیطرف": "بیطرف",
    }
    name = aliases.get(name, name)
    if name not in PATHS:
        for p in PATHS:
            if name in p or p in name:
                name = p
                break
    if name not in PATHS:
        return "مسیر نامعتبر. گزینهها: ارتدوکس | شیطانی | بیطرف\n/daopath ارتدوکس"
    m = _map()
    m[str(int(tg))] = name
    _psave("dao_paths")
    return (
        f"☯️ مسیر معنوی: <b>{name}</b>\n"
        + {
            "ارتدوکس": "فقط تکنیکهای ارتدوکس/نورانی قابل یادگیریاند.",
            "شیطانی": "فقط تکنیکهای شیطانی/تاریک قابل یادگیریاند.",
            "بیطرف": "میتوانی هر تکنیکی را یاد بگیری.",
        }[name]
    )


def detect_tech_path(name: str, description: str = "", grade: str = "") -> str:
    """تشخیص مسیر تکنیک از نام و توضیح"""
    blob = f"{name} {description} {grade}".lower()
    # صریح
    if "شیطان" in blob or "اهریمن" in name:
        return "شیطانی"
    if "ارتدوکس" in blob:
        return "ارتدوکس"
    if "بیطرف" in blob or "خنثی" in blob:
        return "بیطرف"
    demon_hit = any(k in name or k in (description or "") for k in DEMON_KEYS)
    ortho_hit = any(k in name or k in (description or "") for k in ORTHO_KEYS)
    if demon_hit and not ortho_hit:
        return "شیطانی"
    if ortho_hit and not demon_hit:
        return "ارتدوکس"
    # لیست صریح
    explicit = TECH_PATH_MAP.get(name)
    if explicit:
        return explicit
    return "بیطرف"


# نقشه صریح بعضی تکنیکها
TECH_PATH_MAP = {
    "پرورش ممنوعه": "شیطانی",
    "نیش تاریکی": "شیطانی",
    "سایه ابدی": "شیطانی",
    "تنفس خلأ": "شیطانی",
    "شعله خشم": "شیطانی",
    "همهمه روح رزمی": "شیطانی",
    "دیوار نور": "ارتدوکس",
    "نفس نورانی": "ارتدوکس",
    "تنفس بال نور": "ارتدوکس",
    "پیوند ارواح": "ارتدوکس",
    "ساخت جهان": "بیطرف",
    "تکنیک ساخت جهان": "بیطرف",
    "تنفس پایه": "بیطرف",
    "تنفس مهتاب": "بیطرف",
    "تنفس کوهستان": "بیطرف",
    "جریان پنجعنصر": "بیطرف",
    "ضربه اژدها": "بیطرف",
    "تیغ باد": "بیطرف",
    "سپراهآهنین": "بیطرف",
    "پوسته اژدها": "بیطرف",
    "موج دفاعی آب": "بیطرف",
}


def can_learn(tg: int, tech_name: str, description: str = "", grade: str = "") -> tuple[bool, str]:
    dao = get_dao(tg)
    tech_path = detect_tech_path(tech_name, description, grade)
    if dao == "بیطرف":
        return True, tech_path
    if tech_path == dao:
        return True, tech_path
    # سختگیرانه: فقط مسیر خود
    return False, (
        f"❌ مسیر تو <b>{dao}</b> است و فقط تکنیکهای {dao} را میتوانی یاد بگیری.\n"
        f"تکنیک «{tech_name}» از مسیر <b>{tech_path}</b> است.\n"
        f"تغییر مسیر: /daopath بیطرف|ارتدوکس|شیطانی"
    )


def list_help() -> str:
    return (
        "☯️ <b>مسیر معنوی</b>\n"
        "• ارتدوکس — فقط تکنیک ارتدوکس/نور\n"
        "• شیطانی — فقط تکنیک شیطانی/تاریک\n"
        "• بیطرف — همه تکنیکها\n\n"
        "/daopath — وضعیت\n"
        "/daopath ارتدوکس|شیطانی|بیطرف — انتخاب"
    )
