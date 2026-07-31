"""قفل پنل اینلاین برای صاحبش — دیگران نتوانند انگولک کنند"""

from aiogram.types import CallbackQuery


async def ensure_owner(callback: CallbackQuery, owner_id: int, label: str = "این پنل") -> bool:
    """اگر کلیک‌کننده صاحب پنل نباشد، هشدار می‌دهد و False برمی‌گرداند."""
    if callback.from_user and callback.from_user.id == owner_id:
        return True
    await callback.answer(f"❌ {label} مال تو نیست!", show_alert=True)
    return False


def parse_owner_data(data: str, prefix: str) -> tuple[int | None, str]:
    """
    فرمت: prefix:owner_id:rest
    مثال: buy:12345:7  → (12345, "7")
    """
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
