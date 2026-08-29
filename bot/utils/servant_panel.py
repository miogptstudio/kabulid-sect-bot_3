from aiogram.types import FSInputFile
from aiogram.utils.keyboard import InlineKeyboardBuilder
from bot.servant_images import get_servant_image_by_id


def servant_keyboard(index: int, owner_id: int):
    """کیبورد خدمتکار خریداری‌شده (مالک)."""
    kb = InlineKeyboardBuilder()
    kb.button(text="📋 وضعیت", callback_data=f"servstatus:{owner_id}:{index}")
    kb.button(text="❤️ وفاداری", callback_data=f"servloyal:{owner_id}:{index}")
    kb.button(text="🧘 پرورش", callback_data=f"servtrain:{owner_id}:{index}")
    kb.button(text="💍 ازدواج", callback_data=f"servmarry:{owner_id}:{index}")
    kb.button(text="⚔️ دوئل خدمتکار", callback_data=f"servduelguide:{owner_id}:{index}")
    kb.button(text="⬅️ بازار", callback_data=f"servmarket:{owner_id}")
    kb.adjust(2, 2, 2, 1)
    return kb.as_markup()


def market_keyboard(position: int, total: int, servant_id: int, owner_id: int):
    """کیبورد مرور بازار: قبلی / بعدی + خرید."""
    kb = InlineKeyboardBuilder()
    prev_pos = (position - 1) % total
    next_pos = (position + 1) % total
    kb.button(text="◀️ قبلی", callback_data=f"servpage:{owner_id}:{prev_pos}")
    kb.button(text=f"{position + 1}/{total}", callback_data=f"servpage:{owner_id}:{position}")
    kb.button(text="بعدی ▶️", callback_data=f"servpage:{owner_id}:{next_pos}")
    kb.button(text="🛒 خرید این خدمتکار", callback_data=f"servbuy:{owner_id}:{servant_id}")
    kb.button(text="📦 خدمتکارهای من", callback_data=f"servmylist:{owner_id}")
    kb.adjust(3, 1, 1)
    return kb.as_markup()


def owned_browse_keyboard(position: int, total: int, bag_index: int, owner_id: int):
    """مرور خدمتکارهای خریداری‌شده (bag_index یک‌پایه)."""
    kb = InlineKeyboardBuilder()
    prev_pos = (position - 1) % total
    next_pos = (position + 1) % total
    kb.button(text="◀️ قبلی", callback_data=f"servownpage:{owner_id}:{prev_pos}")
    kb.button(text=f"{position + 1}/{total}", callback_data=f"servownpage:{owner_id}:{position}")
    kb.button(text="بعدی ▶️", callback_data=f"servownpage:{owner_id}:{next_pos}")
    kb.button(text="📋 وضعیت", callback_data=f"servstatus:{owner_id}:{bag_index}")
    kb.button(text="❤️ وفاداری", callback_data=f"servloyal:{owner_id}:{bag_index}")
    kb.button(text="🧘 پرورش", callback_data=f"servtrain:{owner_id}:{bag_index}")
    kb.button(text="💍 ازدواج", callback_data=f"servmarry:{owner_id}:{bag_index}")
    kb.button(text="🏪 بازگشت به بازار", callback_data=f"servmarket:{owner_id}")
    kb.adjust(3, 2, 2, 1)
    return kb.as_markup()


def servant_image(index: int):
    p = get_servant_image_by_id(index)
    return FSInputFile(p) if p and p.exists() else None


def market_caption(item: dict, position: int, total: int) -> str:
    karma_price = int(item.get("karma_price") or 0)
    price = int(item.get("price") or 0)
    if karma_price > 0:
        price_line = f"☯️ قیمت: <b>{karma_price}</b> کارما"
    else:
        price_line = f"💰 قیمت: <b>{price:,}</b> سکه"
    stock_line = ""
    try:
        from services.servants import weekly_stock_remaining, SPECIAL_WEEKLY_STOCK_LIMITS
        sid = int(item.get("id") or 0)
        st = weekly_stock_remaining(sid)
        if st is not None:
            used, remaining = st
            limit = SPECIAL_WEEKLY_STOCK_LIMITS.get(sid, 3)
            stock_line = f"\n📦 موجودی این هفته: <b>{remaining}</b> از {limit}"
    except Exception:
        if item.get("special_weekly_stock"):
            stock_line = f"\n📦 موجودی هفتگی: حداکثر {item.get('special_weekly_stock', 3)} عدد"
    return (
        f"🧑🤝🧑 <b>بازار خدمتکاران</b>\n"
        f"📄 {position + 1} از {total}\n\n"
        f"🎴 <b>{item.get('name', '—')}</b>\n"
        f"🔢 شماره: <code>{item.get('id')}</code>\n"
        f"🧬 تبار: {item.get('race', '—')}\n"
        f"⚧ جنسیت: {item.get('gender', '—')}\n"
        f"{price_line}{stock_line}\n"
        f"📜 {item.get('desc', '—')}\n\n"
        f"◀️ ▶️ برای ورق زدن · خرید با دکمه پایین"
    )
