"""تکنیک مخفی کنترل پوچی — پایدار"""
from __future__ import annotations
from services.persist import get_dict, save as _psave

TECH_NAME = "کنترل پوچی اطراف بخش اول"
PRICE_GOD = 999999999
SECRET_TEXT = '''📜 <b>کنترل پوچی اطراف — بخش اول</b>

<b>مرحلهٔ اول: ساخت رگ مصنوعی پوچی</b>

برای شروع، اول باید یک <b>رگ مصنوعی پوچی</b> با حواس خودتان بسازید. در این مرحله، تمرکز شما باید روی احساس جریان پوچی درون بدن و جریان اطرافتان باشد.

وقتی رگ مصنوعی شکل گرفت، باید فاصلهٔ بین پوست خودتان و جریان پوچی اطراف را حس کنید. هدف این مرحله این است که بتوانید ارتباط میان خودتان و جریان اطراف را درک و کنترل کنید.

<b>محدودیت آغازین</b>

در ابتدای مسیر، کنترل شما بسیار ناچیز است؛ در حد چیزی به کوچکی یک اتم. نباید انتظار داشته باشید که از همان ابتدا بتوانید حجم زیادی از پوچی اطراف را کنترل کنید.

برای قویتر شدن، باید همین تمرین را بهصورت پیوسته در دنیای بازی انجام دهید و کنترل خود را کمکم گسترش دهید. با پیشرفت، محدودهٔ کنترل از یک نقطهٔ بسیار کوچک به بخشهای بزرگتر اطراف شما میرسد.

<b>هدف بخش اول</b>

ساخت رگ مصنوعی، احساس جریان پوچی، ایجاد ارتباط با جریان اطراف و آغاز کنترل مقدار بسیار کمی از آن.

⚠️ <i>این تکنیک یک قابلیت فانتزی داخل بازی است و توضیحات بالا مربوط به قوانین دنیای بازی است؛ روش واقعی و اثباتشدهای برای کنترل «پوچی» در دنیای واقعی وجود ندارد.</i>

🔒 ادامهٔ تکنیک در بخش اول در دسترس نیست و مراحل بعدی هنوز کشف نشدهاند.'''


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


def buy(tg_id: int, god_stones: int) -> tuple[bool, str, int]:
    """خرید تکنیک مخفی با سنگ خدا و برگرداندن موجودی باقی‌مانده."""
    tg = int(tg_id)
    stones = max(0, int(god_stones or 0))
    if tg in _owners() or tg in _learned():
        return False, "قبلاً خریدی یا یاد گرفتی.", stones
    if stones < PRICE_GOD:
        return False, f"❌ سنگ خدا کافی نیست. نیاز: {PRICE_GOD:,} | موجودی: {stones:,}", stones
    o = _owners(); o.add(tg); _save_owners(o)
    tm = _text_map(); tm[str(tg)] = True; _psave("void_text")
    left = stones - PRICE_GOD
    return True, (
        f"✅ خرید <b>{TECH_NAME}</b> موفق." + chr(10)
        + "دکمه یا /showvoidtech برای دیدن متن (فقط تو)."
    ), left


def show_text(tg_id: int) -> str:
    tg = int(tg_id)
    if tg not in _owners() and tg not in _learned():
        return "نسخه خطی نداری. /buyvoidtech"
    return SECRET_TEXT


def consume_and_learn(tg_id: int) -> str:
    tg = int(tg_id)
    if tg not in _owners():
        if tg in _learned():
            return "قبلاً یاد گرفتهای."
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
