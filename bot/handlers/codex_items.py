from aiogram import Router
from aiogram.types import Message
from aiogram.filters import Command
from sqlalchemy import select

from database.engine import async_session
from database.crud import get_or_create_user
from database.models_v3 import ShopItem, Building
from services.shop import ensure_default_buildings_and_items

router = Router()

HOW_TO = {
    "pill": "داروخانه /buildings — خرید با سکه یا /use",
    "tea": "داروخانه — چای تذهیب +انرژی با کول‌داون",
    "weapon": "آهنگری — خرید؛ /equip برای تجهیز",
    "weapon_unique": "آهنگری — یکتا؛ فقط یک نفر",
    "armor": "آهنگری — زره در کیف قدرت می‌دهد",
    "material": "کیمیاگری / شکار / باغ — مواد ساخت",
    "herb_normal": "باغ گیاهان یا /garden",
    "herb_spiritual": "باغ / مأموریت نادر",
    "tech_book": "سالن تکنیک — یادگیری مستقیم",
    "talisman": "طلسم‌خانه — خرید یا /craft",
}


@router.message(Command("itemlist", "لیست‌آیتم", "codexitems", "دانشنامه‌آیتم", "انبارکل"))
async def cmd_item_codex(message: Message):
    async with async_session() as session:
        await ensure_default_buildings_and_items(session)
        result = await session.execute(select(ShopItem).where(ShopItem.is_active == True))
        items = result.scalars().all()
        buildings = {b.id: b for b in (await session.execute(select(Building))).scalars().all()}

    if not items:
        await message.answer("آیتمی نیست. /buildings")
        return

    by_type = {}
    for it in items:
        by_type.setdefault(it.item_type or "other", []).append(it)

    chunks = ["📚 <b>دانشنامه آیتم‌ها</b>" + chr(10) + "چطور به دست می‌آید:" + chr(10)]
    for itype, lst in sorted(by_type.items()):
        how = HOW_TO.get(itype, "فروشگاه /buildings یا مأموریت")
        line = f"{chr(10)}<b>▸ {itype}</b> — {how}" + chr(10)
        for it in lst[:20]:
            bname = ""
            if it.building_id and it.building_id in buildings:
                bname = buildings[it.building_id].name
            line += f"• {it.name} | {it.price} سکه | {bname}" + chr(10)
            if it.description:
                line += f"  {it.description[:60]}" + chr(10)
        chunks.append(line)

    text = ""
    for ch in chunks:
        if len(text) + len(ch) > 3500:
            await message.answer(text)
            text = ch
        else:
            text += ch
    if text:
        await message.answer(text)


@router.message(Command("buildingscodex", "ساختمان‌دانشنامه"))
async def cmd_building_codex(message: Message):
    await message.answer(
        "🏛 <b>ساختمان دانشنامه</b>" + chr(10)
        + "/itemlist — همه آیتم‌ها و روش تهیه" + chr(10)
        + "/buildings — خرید از ساختمان‌ها" + chr(10)
        + "/craft — ساخت معجون و طلسم" + chr(10)
        + "/inventory — کیف تو"
    )
