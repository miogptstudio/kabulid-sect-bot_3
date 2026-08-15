"""فروش عمومی شمشیر کوروش — بسته شده"""
from datetime import datetime, timedelta

SALE_START = datetime(2020, 1, 1)
SALE_DAYS = 0
PUBLIC_PRICE = 50000
_bought: set[int] = set()


def sale_active() -> bool:
    return False


def sale_info() -> str:
    return (
        "⚔️ فروش عمومی شمشیر کوروش <b>بسته</b> است." + chr(10)
        + "فقط سازنده از /adshop میتواند بدهد."
    )


def can_buy(tg_id: int) -> tuple[bool, str]:
    return False, "فروش عمومی بسته است."
