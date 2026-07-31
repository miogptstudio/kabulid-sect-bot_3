from sqlalchemy.ext.asyncio import AsyncSession
from database.models import User

CITIES = [
    {"id": "tehran", "name": "تهران", "desc": "پایتخت و مرکز قدرت"},
    {"id": "mashhad", "name": "مشهد", "desc": "زیارت و آرامش روح"},
    {"id": "isfahan", "name": "اصفهان", "desc": "هنر و طلسم‌سازی"},
    {"id": "shiraz", "name": "شیراز", "desc": "ادبیات و شعر"},
    {"id": "tabriz", "name": "تبریز", "desc": "تجارت و سکه"},
    {"id": "yazd", "name": "یزد", "desc": "تذهیب کویری"},
    {"id": "kerman", "name": "کرمان", "desc": "شکار و بیابان"},
    {"id": "rasht", "name": "رشت", "desc": "باران و گیاه معنوی"},
]

NAME_TO_ID = {c["name"]: c["id"] for c in CITIES}
NAME_TO_ID.update({c["id"]: c["id"] for c in CITIES})


async def ensure_user_city(session: AsyncSession, user: User) -> str:
    if not getattr(user, "city", None):
        user.city = "tehran"
        await session.commit()
    return user.city or "tehran"


def get_city(city_id: str) -> dict:
    for c in CITIES:
        if c["id"] == city_id:
            return c
    return CITIES[0]


def list_cities_text(current_id: str) -> str:
    lines = ["🏙️ <b>شهرهای ایران</b>\n"]
    for c in CITIES:
        mark = " ✅" if c["id"] == current_id else ""
        lines.append(f"• <b>{c['name']}</b>{mark}\n  {c['desc']}")
    lines.append("\nسفر: /travel نام‌شهر\nمثال: /travel شیراز")
    return "\n".join(lines)
