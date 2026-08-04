"""فروش عمومی شمشیر کوروش — ۳ روز از زمان فعال‌سازی"""
from datetime import datetime, timedelta

# شروع فروش: از اولین Deploy بعد از این آپدیت — یا ثابت
SALE_START = datetime.utcnow()
SALE_DAYS = 3
PUBLIC_PRICE = 50000  # سنگ روحی — قیمت عمومی محدود


def sale_active() -> bool:
    return datetime.utcnow() < SALE_START + timedelta(days=SALE_DAYS)


def sale_info() -> str:
    end = SALE_START + timedelta(days=SALE_DAYS)
    left = end - datetime.utcnow()
    if left.total_seconds() <= 0:
        return "فروش عمومی شمشیر کوروش به پایان رسیده. فقط /adshop ادمین."
    h = int(left.total_seconds() // 3600)
    return (
        f"⚔️ <b>فروش عمومی شمشیر کوروش</b>" + chr(10)
        + f"مدت: ۳ روز | باقی‌مانده حدود {h} ساعت" + chr(10)
        + f"قیمت: {PUBLIC_PRICE} سنگ روحی" + chr(10)
        + "هر نفر حداکثر ۱ عدد" + chr(10)
        + "/buycyrus — خرید"
    )


_bought: set[int] = set()


def can_buy(tg_id: int) -> tuple[bool, str]:
    if not sale_active():
        return False, "فروش تمام شده."
    if tg_id in _bought:
        return False, "قبلاً خریدی (حداکثر ۱)."
    return True, "ok"
