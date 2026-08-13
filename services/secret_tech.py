"""تکنیک مخفی کنترل پوچی — پایدار"""
from __future__ import annotations
from services.persist import get_dict, save as _psave

TECH_NAME = "کنترل پوچی اطراف بخش اول"
PRICE_GOD = 999999999
SECRET_TEXT = '📜 <b>کنترل پوچی اطراف بخش اول</b>\n\nبرای اینکه بتوانید پوچی اطراف را کنترل کنید، به یک <b>کانال پوچی</b> نیاز دارید که می\u200cتوانید داخل بدنتان بسازید.\n\nبرای ساخت کانال باید کمی از پوچی\u200cای که در بدنتان هست استفاده کنید. حس آن مثل کنترل کردن قلبتان است و می\u200cتوانید راحت بسازید.\n\nمحل قرارگیری این کانال را باید جایی بگذارید که آسیب نبیند؛ وگرنه کارتان نابود کردن خودتان به دست خودتان است.\n\n<b>آموزش تکنیک</b>\nباید حواسی که در بدن و اطراف\u200cتان است را کنترل کنید — آسان است. همهٔ انسان\u200cها می\u200cتوانند خیلی جزئی اطراف\u200cشان را کنترل کنند، ولی گسترش نمی\u200cدهند. هدف این تکنیک همان گسترش است.\n\n<b>مراحل</b>\n۱) از یک عنصر پاک استفاده کنید.\n۲) دست\u200cتان را مشت کنید.\n۳) جریان رگ\u200cها و پوچی اطراف را در دست\u200cتان حس کنید.\n۴) آن را گسترش دهید.\n\nهمین — چیز خاصی نیست؛ تمرکز و گسترش پیوسته.'


def _owners() -> set[int]:
    d = get_dict("void_owners")
    return set(int(x) for x in d.get("ids", []))


def _save_owners(s: set[int]) -> None:
    get_dict("void_owners")["ids"] = list(s)
    _psave("void_owners")


def _learned() -> set[int]:
    d = get_dict("void_learned")
    return set(int(x) for x in d.get("ids", []))


def _save_learned(s: set[int]) -> None:
    get_dict("void_learned")["ids"] = list(s)
    _psave("void_learned")


def _text_map() -> dict:
    return get_dict("void_text")


def has_manuscript(tg_id: int) -> bool:
    return int(tg_id) in _owners()


def has_learned(tg_id: int) -> bool:
    return int(tg_id) in _learned()


def buy(tg_id: int) -> tuple[bool, str]:
    tg = int(tg_id)
    if tg in _owners() or tg in _learned():
        return False, "قبلاً خریده یا یاد گرفته‌ای."
    o = _owners(); o.add(tg); _save_owners(o)
    tm = _text_map(); tm[str(tg)] = True; _psave("void_text")
    return True, (
        f"✅ خرید <b>{TECH_NAME}</b> موفق." + chr(10)
        + "دکمه یا /showvoidtech برای دیدن متن (فقط تو)."
    )


def show_text(tg_id: int) -> str:
    tg = int(tg_id)
    if tg not in _owners() and tg not in _learned():
        return "نسخه خطی نداری. /buyvoidtech"
    return SECRET_TEXT


def consume_and_learn(tg_id: int) -> str:
    tg = int(tg_id)
    if tg not in _owners():
        if tg in _learned():
            return "قبلاً یاد گرفته‌ای."
        return "نسخه خطی نداری."
    o = _owners(); o.discard(tg); _save_owners(o)
    L = _learned(); L.add(tg); _save_learned(L)
    tm = _text_map(); tm.pop(str(tg), None); _psave("void_text")
    return (
        f"✅ <b>{TECH_NAME}</b> را یاد گرفتی." + chr(10)
        + "متن نسخه خطی مصرف و حذف شد."
    )


def public_list_line() -> str:
    return f"🌀 {TECH_NAME} — فقط نام؛ متن بعد از خرید"


# سازگاری با هندلرها
def is_owner(tg_id: int) -> bool:
    return has_manuscript(tg_id) or has_learned(tg_id)

def get_secret_text(tg_id: int) -> str:
    return show_text(tg_id)

def shop_line() -> str:
    return public_list_line()

def status(tg_id: int) -> str:
    if has_learned(tg_id):
        return f"✅ {TECH_NAME} — یاد گرفته شده"
    if has_manuscript(tg_id):
        return f"📜 {TECH_NAME} — نسخه خطی داری (/showvoidtech /learnvoidtech)"
    return f"🌀 {TECH_NAME} — /buyvoidtech ({PRICE_GOD} سنگ خدا)"
