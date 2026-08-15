"""قفل پنل اینلاین برای صاحبش — دیگران بدون هیچ پیام عمومی رد میشوند"""

from aiogram.types import CallbackQuery


async def ensure_owner(callback: CallbackQuery, owner_id: int, label: str = "این پنل") -> bool:
    """اگر کلیککننده صاحب نباشد: بدون متن در چت، فقط کلیک را بیاثر میکند."""
    if callback.from_user and callback.from_user.id == owner_id:
        return True
    # هیچ پیامی در گروه/چت نوشته نمیشود
    try:
        await callback.answer()
    except Exception:
        pass
    return False


def parse_owner_data(data: str, prefix: str) -> tuple[int | None, str]:
    if not data.startswith(prefix):
        return None, ""
    parts = data.split(":", 2)
    if len(parts) < 3:
        return None, ""
    try:
        owner_id = int(parts[1])
    except ValueError:
        return None, ""
    return owner_id, parts[2]


async def silent_deny(callback: CallbackQuery) -> None:
    """رد بیصدا — بدون آلرت و بدون پیام در چت"""
    try:
        await callback.answer()
    except Exception:
        pass
