from services.i18n import t_user, tr
from aiogram import Router
from aiogram.types import Message

router = Router()


@router.message()
async def unknown_command(message: Message):
    text = (message.text or "").strip()
    if not text.startswith("/"):
        return
    tip = t_user(message.from_user.id, "unknown_cmd")
    await message.answer(
        tip + chr(10) + chr(10)
        + "/start — شروع" + chr(10)
        + "/help — راهنما" + chr(10)
        + "/commands — همه دستورات" + chr(10)
        + "/ping — تست" + chr(10)
        + "/profile — پروفایل" + chr(10)
        + "/cultivation — تذهیب" + chr(10)
        + "/duel — دوئل" + chr(10)
        + "/buildings — فروشگاه"
    )
