from aiogram.types import FSInputFile
from aiogram.utils.keyboard import InlineKeyboardBuilder
from bot.servant_images import get_servant_image_by_id


def servant_keyboard(index: int):
    """کیبورد خدمتکار خریداری‌شده (مالک)."""
    kb = InlineKeyboardBuilder()
    kb.button(text="🛒 خرید", callback_data=f"servbuy:{index}")
    kb.button(text="📋 وضعیت", callback_data=f"servstatus:{index}")
    kb.button(text="❤️ وفاداری", callback_data=f"servloyal:{index}")
    kb.button(text="🧘 پرورش", callback_data=f"servtrain:{index}")
    kb.button(text="💍 ازدواج", callback_data=f"servmarry:{index}")
    kb.button(text="⚔️ دوئل خدمتکار", callback_data=f"servduelguide:{index}")
    kb.button(text="⬅️ بازار", callback_data="servmarket")
    kb.adjust(2, 2, 2, 1)
    return kb.as_markup()


def market_keyboard(position: int, total: int, servant_id: int):
    """کیبورد مرور بازار: قبلی / بعدی + خرید."""
    kb = InlineKeyboardBuilder()
    prev_pos = (position - 1) % total
    next_pos = (position + 1) % total
    kb.button(text="◀️ قبلی", callback_data=f"servpage:{prev_pos}")
    kb.button(text=f"{position + 1}/{total}", callback_data=f"servpage:{position}")
    kb.button(text="بعدی ▶️", callback_data=f"servpage:{next_pos}")
    kb.button(text="🛒 خرید این خدمتکار", callback_data=f"servbuy:{servant_id}")
    kb.button(text="📦 خدمتکارهای من", callback_data="servmylist")
    kb.adjust(3, 1, 1)
    return kb.as_markup()


def owned_browse_keyboard(position: int, total: int, bag_index: int):
    """مرور خدمتکارهای خریداری‌شده (bag_index یک‌پایه)."""
    kb = InlineKeyboardBuilder()
    prev_pos = (position - 1) % total
    next_pos = (position + 1) % total
    kb.button(text="◀️ قبلی", callback_data=f"servownpage:{prev_pos}")
    kb.button(text=f"{position + 1}/{total}", callback_data=f"servownpage:{position}")
    kb.button(text="بعدی ▶️", callback_data=f"servownpage:{next_pos}")
    kb.button(text="📋 وضعیت", callback_data=f"servstatus:{bag_index}")
    kb.button(text="❤️ وفاداری", callback_data=f"servloyal:{bag_index}")
    kb.button(text="🧘 پرورش", callback_data=f"servtrain:{bag_index}")
    kb.button(text="💍 ازدواج", callback_data=f"servmarry:{bag_index}")
    kb.button(text="🏪 بازگشت به بازار", callback_data="servmarket")
    kb.adjust(3, 2, 2, 1)
    return kb.as_markup()


def servant_image(index: int):
    p = get_servant_image_by_id(index)
    return FSInputFile(p) if p and p.exists() else None


def market_caption(item: dict, position: int, total: int) -> str:
    price = int(item.get("price") or 0)
    return (
        f"🧑🤝🧑 <b>بازار خدمتکاران</b>\n"
        f"📄 {position + 1} از {total}\n\n"
        f"🎴 <b>{item.get('name', '—')}</b>\n"
        f"🔢 شماره: <code>{item.get('id')}</code>\n"
        f"🧬 تبار: {item.get('race', '—')}\n"
        f"⚧ جنسیت: {item.get('gender', '—')}\n"
        f"💰 قیمت: <b>{price:,}</b> سکه\n"
        f"📜 {item.get('desc', '—')}\n\n"
        f"◀️ ▶️ برای ورق زدن · خرید با دکمه پایین"
    )
