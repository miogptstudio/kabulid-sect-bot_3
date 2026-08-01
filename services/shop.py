from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from database.models_v3 import Building, ShopItem, UserInventory
from database.models import User


# آیتم‌های پیش‌فرض: قرص، طلسم، مواد، گیاه، سلاح
DEFAULT_ITEMS = [
    # ===== داروخانه =====
    {
        "building_type": "داروخانه",
        "name": "قرص انرژی پایه",
        "item_type": "pill",
        "description": "۲۵ انرژی تذهیب می‌دهد",
        "price": 30,
        "effect": {"energy": 25}
    },
    {
        "building_type": "داروخانه",
        "name": "قرص بهبودی",
        "item_type": "pill",
        "description": "کمی XP می‌دهد",
        "price": 50,
        "effect": {"xp": 20}
    },
    # ===== طلسم‌خانه =====
    {
        "building_type": "طلسم‌خانه",
        "name": "طلسم محافظ ضعیف",
        "item_type": "talisman",
        "description": "یک بار از باخت سنگین جلوگیری می‌کند",
        "price": 100,
        "effect": {"protect": 1}
    },
    {
        "building_type": "طلسم‌خانه",
        "name": "کاغذ طلسم معمولی",
        "item_type": "talisman_paper",
        "description": "کاغذ پایه برای کشیدن طلسم",
        "price": 25,
        "effect": {}
    },
    {
        "building_type": "طلسم‌خانه",
        "name": "کاغذ طلسم معنوی",
        "item_type": "talisman_paper",
        "description": "کاغذ نادر با جوهر روح برای طلسم‌های قوی",
        "price": 90,
        "effect": {}
    },
    {
        "building_type": "طلسم‌خانه",
        "name": "جوهر روح",
        "item_type": "material",
        "description": "جوهر مخصوص نوشتن طلسم‌های معنوی",
        "price": 60,
        "effect": {}
    },
    # ===== کیمیاگری =====
    {
        "building_type": "کیمیاگری",
        "name": "مواد اولیه کیمیا",
        "item_type": "material",
        "description": "بسته پایه مواد کیمیاگری",
        "price": 20,
        "effect": {}
    },
    {
        "building_type": "کیمیاگری",
        "name": "پودر گوگرد",
        "item_type": "material",
        "description": "ماده شیمیایی برای معجون‌های آتشین",
        "price": 35,
        "effect": {}
    },
    {
        "building_type": "کیمیاگری",
        "name": "شیشه کیمیا",
        "item_type": "material",
        "description": "شیشه مخصوص نگهداری معجون",
        "price": 15,
        "effect": {}
    },
    {
        "building_type": "کیمیاگری",
        "name": "کریستال خالص",
        "item_type": "material",
        "description": "کریستال کمیاب برای معجون‌های پیشرفته",
        "price": 100,
        "effect": {}
    },
    # ===== باغ گیاهان =====
    {
        "building_type": "باغ گیاهان",
        "name": "گیاه معمولی - گل بهار",
        "item_type": "herb_normal",
        "description": "گیاه معمولی برای معجون‌های پایه",
        "price": 15,
        "effect": {}
    },
    {
        "building_type": "باغ گیاهان",
        "name": "گیاه معمولی - ریشه کوهی",
        "item_type": "herb_normal",
        "description": "ریشه مقاوم برای معجون‌های متوسط",
        "price": 25,
        "effect": {}
    },
    {
        "building_type": "باغ گیاهان",
        "name": "گیاه معنوی - برگ روح",
        "item_type": "herb_spiritual",
        "description": "گیاه معنوی کمیاب",
        "price": 80,
        "effect": {"energy": 10}
    },
    {
        "building_type": "باغ گیاهان",
        "name": "گیاه معنوی - گل ماه",
        "item_type": "herb_spiritual",
        "description": "گل معنوی نادر برای طلسم‌های قوی",
        "price": 120,
        "effect": {}
    },
    # ===== آهنگری =====
    {
        "building_type": "آهنگری",
        "name": "شمشیر آهنی",
        "item_type": "weapon",
        "description": "سلاح پایه",
        "price": 150,
        "effect": {"duel_power": 5}
    },
    {
        "building_type": "آهنگری",
        "name": "نیزه فولادی",
        "item_type": "weapon",
        "description": "سلاح متوسط",
        "price": 280,
        "effect": {"duel_power": 12}
    },
    {
        "building_type": "آهنگری",
        "name": "شمشیر روح‌دار",
        "item_type": "weapon",
        "description": "سلاح معنوی قوی",
        "price": 500,
        "effect": {"duel_power": 25}
    },
    {
        "building_type": "آهنگری",
        "name": "آهن خام",
        "item_type": "material",
        "description": "ماده اولیه برای ساخت سلاح",
        "price": 40,
        "effect": {}
    },
    {
        "building_type": "آهنگری",
        "name": "فولاد تصفیه‌شده",
        "item_type": "material",
        "description": "فولاد باکیفیت برای سلاح‌های بهتر",
        "price": 90,
        "effect": {}
    },
    {
        "building_type": "آهنگری",
        "name": "سنگ روح",
        "item_type": "material",
        "description": "سنگ معنوی برای ساخت سلاح روح‌دار",
        "price": 150,
        "effect": {}
    },

    {"building_type": "سالن تکنیک", "name": "کتاب تنفس پایه", "item_type": "tech_book", "description": "یادگیری تنفس پایه", "price": 100, "effect": {"learn_tech": "تنفس پایه"}},
    {"building_type": "سالن تکنیک", "name": "کتاب جریان پنج‌عنصر", "item_type": "tech_book", "description": "تکنیک پنج‌عنصر", "price": 250, "effect": {"learn_tech": "جریان پنج‌عنصر"}},
    {"building_type": "سالن تکنیک", "name": "کتاب شعله درونی", "item_type": "tech_book", "description": "تکنیک آتش", "price": 300, "effect": {"learn_tech": "شعله‌ی درونی"}},
    {"building_type": "سالن تکنیک", "name": "کتاب طوفان روح", "item_type": "tech_book", "description": "باد و روح", "price": 400, "effect": {"learn_tech": "طوفان روح"}},
    {"building_type": "سالن تکنیک", "name": "کتاب زره سنگی", "item_type": "tech_book", "description": "دفاع", "price": 280, "effect": {"learn_tech": "زره سنگی"}},
    {"building_type": "سالن تکنیک", "name": "کتاب چشم حقیقت", "item_type": "tech_book", "description": "درک انرژی", "price": 320, "effect": {"learn_tech": "چشم حقیقت"}},
    {"building_type": "سالن تکنیک", "name": "کتاب پنجه ببر", "item_type": "tech_book", "description": "حمله", "price": 450, "effect": {"learn_tech": "پنجه ببر"}},
    {"building_type": "سالن تکنیک", "name": "کتاب موج آسمانی", "item_type": "tech_book", "description": "پیشرفته", "price": 800, "effect": {"learn_tech": "موج آسمانی"}},
    {"building_type": "سالن تکنیک", "name": "کتاب نفس یخ", "item_type": "tech_book", "description": "یخ", "price": 400, "effect": {"learn_tech": "نفس یخ"}},
    {"building_type": "سالن تکنیک", "name": "کتاب تنفس اژدها", "item_type": "tech_book", "description": "اژدها", "price": 600, "effect": {"learn_tech": "تنفس اژدها"}},
    {"building_type": "سالن تکنیک", "name": "کتاب جریان آسمانی", "item_type": "tech_book", "description": "آسمانی", "price": 700, "effect": {"learn_tech": "جریان آسمانی"}},
    {"building_type": "سالن تکنیک", "name": "کتاب سکوت مرگ", "item_type": "tech_book", "description": "زیرین", "price": 900, "effect": {"learn_tech": "سکوت مرگ"}},
    {"building_type": "آهنگری", "name": "شمشیر آسمانی", "item_type": "weapon", "description": "سلاح قلمرو آسمان", "price": 2000, "effect": {"duel_power": 40}},
    {"building_type": "آهنگری", "name": "نیزه ای‌تری", "item_type": "weapon", "description": "سلاح ای‌تری", "price": 5000, "effect": {"duel_power": 80}},
    {"building_type": "آهنگری", "name": "خنجر شیطانی", "item_type": "weapon", "description": "مسیر شیطانی", "price": 1500, "effect": {"duel_power": 35}},
    {"building_type": "طلسم‌خانه", "name": "طلسم محافظ", "item_type": "talisman", "description": "کاهش آسیب", "price": 200, "effect": {}},
    {"building_type": "طلسم‌خانه", "name": "طلسم آتش", "item_type": "talisman", "description": "حمله آتشین", "price": 350, "effect": {"duel_power": 8}},
    {"building_type": "طلسم‌خانه", "name": "طلسم ای‌تری", "item_type": "talisman", "description": "قدرت اتر", "price": 2000, "effect": {"duel_power": 25}},
    {"building_type": "داروخانه", "name": "قرص عمر", "item_type": "pill", "description": "+۱۰ عمر", "price": 300, "effect": {"lifespan": 10}},
    {"building_type": "داروخانه", "name": "قرص چی بزرگ", "item_type": "pill", "description": "+۵۰۰۰ انرژی", "price": 400, "effect": {"energy": 5000}},
    {"building_type": "داروخانه", "name": "قرص خدا", "item_type": "pill", "description": "کمیاب", "price": 10000, "effect": {"energy": 20000}},
    {"building_type": "کیمیاگری", "name": "دستور معجون سرعت", "item_type": "recipe", "description": "دستور ساخت", "price": 150, "effect": {}},
    {"building_type": "کیمیاگری", "name": "دستور معجون قدرت", "item_type": "recipe", "description": "دستور ساخت", "price": 200, "effect": {}},
{"building_type": "آهنگری", "name": "شمشیر نور", "item_type": "weapon", "description": "سلاح ریشه نور", "price": 2500, "effect": {"duel_power": 45}},
    {"building_type": "آهنگری", "name": "خنجر تاریکی", "item_type": "weapon", "description": "سلاح تاریکی", "price": 2500, "effect": {"duel_power": 45}},
    {"building_type": "آهنگری", "name": "نیزه روح", "item_type": "weapon", "description": "سلاح روحی", "price": 3000, "effect": {"duel_power": 55}},
    {"building_type": "آهنگری", "name": "تیغ الهی", "item_type": "weapon", "description": "کمیاب", "price": 15000, "effect": {"duel_power": 120}},
    {"building_type": "طلسم‌خانه", "name": "طلسم نور", "item_type": "talisman", "description": "محافظ نورانی", "price": 500, "effect": {"duel_power": 12}},
    {"building_type": "طلسم‌خانه", "name": "طلسم تاریکی", "item_type": "talisman", "description": "قدرت تاریک", "price": 500, "effect": {"duel_power": 12}},
    {"building_type": "طلسم‌خانه", "name": "طلسم تسخیر", "item_type": "talisman", "description": "برای ارواح", "price": 2000, "effect": {}},
    {"building_type": "داروخانه", "name": "قرص ریشه", "item_type": "pill", "description": "کمک بیداری ریشه", "price": 800, "effect": {"energy": 10000}},
    {"building_type": "داروخانه", "name": "قرص روحی", "item_type": "pill", "description": "انرژی روح", "price": 1200, "effect": {"energy": 15000}},
    {"building_type": "داروخانه", "name": "قرص نور", "item_type": "pill", "description": "پاکسازی", "price": 900, "effect": {"energy": 8000}},
    {"building_type": "کیمیاگری", "name": "گرد نور", "item_type": "material", "description": "ماده کیمیاگری نور", "price": 200, "effect": {}},
    {"building_type": "کیمیاگری", "name": "گرد تاریکی", "item_type": "material", "description": "ماده تاریک", "price": 200, "effect": {}},
    {"building_type": "کیمیاگری", "name": "خون روح", "item_type": "material", "description": "ماده کمیاب", "price": 600, "effect": {}},
    {"building_type": "کیمیاگری", "name": "گرد ای‌تری", "item_type": "material", "description": "ماده ای‌تری", "price": 1000, "effect": {}},
    {"building_type": "سالن تکنیک", "name": "کتاب نفس نورانی", "item_type": "tech_book", "description": "تکنیک نور", "price": 500, "effect": {"learn_tech": "نفس نورانی"}},
    {"building_type": "سالن تکنیک", "name": "کتاب سایه ابدی", "item_type": "tech_book", "description": "تکنیک تاریکی", "price": 500, "effect": {"learn_tech": "سایه ابدی"}},
    {"building_type": "سالن تکنیک", "name": "کتاب همهمه روح", "item_type": "tech_book", "description": "تکنیک روحی", "price": 700, "effect": {"learn_tech": "همهمه روح"}},
    {"building_type": "آهنگری", "name": "شمشیر ذوالفقار", "item_type": "weapon_unique", "description": "شمشیر ایرانی افسانه‌ای — فقط یکی در کل بازی", "price": 999999, "effect": {"duel_power": 500, "unique": "zulfiqar"}},
    {"building_type": "آهنگری", "name": "زره اژدها", "item_type": "armor", "description": "کاهش آسیب عجیب — پوست اژدها", "price": 4000, "effect": {"duel_power": 30, "armor": 40}},
    {"building_type": "آهنگری", "name": "زره غیب", "item_type": "armor", "description": "گاهی ضربه را محو می‌کند", "price": 6000, "effect": {"duel_power": 20, "armor": 50, "weird": "vanish"}},
    {"building_type": "آهنگری", "name": "زره خدایان", "item_type": "armor", "description": "بدن را سخت‌تر می‌کند", "price": 20000, "effect": {"duel_power": 60, "armor": 100}},
    {"building_type": "آهنگری", "name": "زره نفرین", "item_type": "armor", "description": "قدرت می‌دهد اما عمر می‌گیرد", "price": 3000, "effect": {"duel_power": 45, "armor": 25, "weird": "curse"}},
    {"building_type": "آهنگری", "name": "نیزه رستم", "item_type": "weapon", "description": "سلاح حماسی ایرانی", "price": 8000, "effect": {"duel_power": 90}},
    {"building_type": "آهنگری", "name": "گرز گرشاسب", "item_type": "weapon", "description": "گرز افسانه‌ای", "price": 7000, "effect": {"duel_power": 85}},
    {"building_type": "آهنگری", "name": "شمشیر کوروش بزرگ", "item_type": "weapon_unique", "description": "شمشیر شاه ایران — فقط یکی؛ صاحب نمی‌میرد؛ یک ضربه = نابودی ابدی دشمن", "price": 5000000, "effect": {"duel_power": 999, "unique": "cyrus"}},
    {"building_type": "داروخانه", "name": "قرص سلامتی", "item_type": "pill", "description": "پاک کردن سم و ترمیم خون", "price": 150, "effect": {"heal": 1}},
    {"building_type": "داروخانه", "name": "پادزهر", "item_type": "pill", "description": "سم را خنثی می‌کند", "price": 200, "effect": {"heal": 1}},
    {"building_type": "آهنگری", "name": "کلت پنهان", "item_type": "weapon", "description": "سلاح گرم", "price": 3000, "effect": {"duel_power": 25}},
    {"building_type": "آهنگری", "name": "کلاشنیکف کهنه", "item_type": "weapon", "description": "سلاح گرم سنگین", "price": 5000, "effect": {"duel_power": 40}},
    {"building_type": "داروخانه", "name": "قرص سلامتی", "item_type": "pill", "description": "پاک کردن سم و ترمیم خون", "price": 150, "effect": {"heal": 1}},
    {"building_type": "داروخانه", "name": "پادزهر", "item_type": "pill", "description": "خنثی کردن سم", "price": 200, "effect": {"heal": 1}},
    {"building_type": "آهنگری", "name": "کلت پنهان", "item_type": "weapon", "description": "سلاح گرم", "price": 3000, "effect": {"duel_power": 25}},
    {"building_type": "آهنگری", "name": "کلاشنیکف کهنه", "item_type": "weapon", "description": "سلاح گرم سنگین", "price": 5000, "effect": {"duel_power": 40}},
]


async def ensure_default_buildings_and_items(session: AsyncSession):
    """ساختمان‌ها و آیتم‌های پیش‌فرض را در صورت نبودن اضافه می‌کند"""
    types = ["داروخانه", "کیمیاگری", "طلسم‌خانه", "باغ گیاهان", "آهنگری", "سالن تکنیک"]
    result = await session.execute(select(Building))
    existing = {b.building_type: b for b in result.scalars().all()}
    buildings = dict(existing)
    for btype in types:
        if btype not in buildings:
            b = Building(name=btype, building_type=btype, description=f"ساختمان {btype}")
            session.add(b)
            await session.flush()
            buildings[btype] = b

    # آیتم‌های موجود
    result = await session.execute(select(ShopItem))
    existing_names = {i.name for i in result.scalars().all()}
    for item_data in DEFAULT_ITEMS:
        if item_data["name"] in existing_names:
            continue
        b = buildings.get(item_data["building_type"])
        if not b:
            continue
        item = ShopItem(
            building_id=b.id,
            name=item_data["name"],
            item_type=item_data["item_type"],
            description=item_data["description"],
            price=item_data["price"],
            effect=item_data["effect"],
        )
        session.add(item)
    await session.commit()


async def get_buildings(session: AsyncSession):
    result = await session.execute(select(Building).where(Building.is_active == True))
    return result.scalars().all()


async def get_items_of_building(session: AsyncSession, building_id: int):
    result = await session.execute(
        select(ShopItem).where(ShopItem.building_id == building_id, ShopItem.is_active == True)
    )
    return result.scalars().all()


async def buy_item(session: AsyncSession, user: User, item: ShopItem) -> str:
    if item.item_type == "weapon_unique" or (isinstance(item.effect, dict) and item.effect.get("unique")):
        from sqlalchemy import select as sel
        owned = await session.execute(
            sel(UserInventory).join(ShopItem, UserInventory.item_id == ShopItem.id).where(
                ShopItem.name == item.name
            )
        )
        if owned.first():
            return "❌ این آیتم یکتاست و قبلاً کسی آن را دارد."

    from services.economy import get_or_create_wallet
    w = await get_or_create_wallet(session, user.id)
    if w.coins < item.price:
        return f"❌ سکه کافی نداری (نیاز: {item.price} | داری: {w.coins})"

    w.coins -= item.price
    effect = item.effect or {}
    extra = ""

    # کتاب تکنیک → یادگیری مستقیم
    if item.item_type == "tech_book" or (isinstance(effect, dict) and effect.get("learn_tech")):
        tech_name = effect.get("learn_tech") if isinstance(effect, dict) else None
        if tech_name:
            from services.cultivation import ensure_default_techniques, learn_technique
            from database.models_v3 import CultivationTechnique
            from sqlalchemy import select as sel
            await ensure_default_techniques(session)
            r = await session.execute(
                sel(CultivationTechnique).where(CultivationTechnique.name == tech_name)
            )
            tech = r.scalar_one_or_none()
            if tech:
                extra = await learn_technique(session, user.id, tech)
            else:
                extra = f"تکنیک «{tech_name}» در دیتابیس نبود."
        await session.commit()
        return f"✅ «{item.name}» خریداری شد.\n{extra}\nسکه باقی: {w.coins}"

    result = await session.execute(
        select(UserInventory).where(
            UserInventory.user_id == user.id,
            UserInventory.item_id == item.id,
        )
    )
    inv = result.scalar_one_or_none()
    if inv:
        inv.quantity += 1
    else:
        inv = UserInventory(user_id=user.id, item_id=item.id, quantity=1)
        session.add(inv)

    await session.commit()
    return f"✅ «{item.name}» خریداری شد. سکه باقی: {w.coins}"