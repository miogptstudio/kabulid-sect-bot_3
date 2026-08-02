from aiogram import Router
from aiogram.types import Message

router = Router()


@router.message()
async def unknown_command(message: Message):
    text = (message.text or "").strip()
    if not text.startswith("/"):
        return
    await message.answer(
        "دستور ناشناخته."
        + chr(10) + "/start — شروع"
        + chr(10) + "/help — راهنمای کامل"
        + chr(10) + "/ping — تست"
        + chr(10) + "/profile — پروفایل"
        + chr(10) + "/cultivation — تذهیب"
        + chr(10) + "/duel — دوئل"
        + chr(10) + "/buildings — فروشگاه"
    )
