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
]


async def ensure_default_buildings_and_items(session: AsyncSession):
    """اگر ساختمون و آیتمی نبود، بساز"""
    result = await session.execute(select(Building))
    if result.scalars().first():
        return
    
    buildings = {}
    for btype in ["داروخانه", "کیمیاگری", "طلسم‌خانه", "باغ گیاهان", "آهنگری"]:
        b = Building(name=btype, building_type=btype, description=f"ساختمان {btype}")
        session.add(b)
        await session.flush()
        buildings[btype] = b
    
    for item_data in DEFAULT_ITEMS:
        b = buildings.get(item_data["building_type"])
        if not b:
            continue
        item = ShopItem(
            building_id=b.id,
            name=item_data["name"],
            item_type=item_data["item_type"],
            description=item_data["description"],
            price=item_data["price"],
            effect=item_data["effect"]
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
    if user.xp < item.price:
        return f"❌ XP کافی نداری (نیاز: {item.price})"
    
    user.xp -= item.price
    
    result = await session.execute(
        select(UserInventory).where(
            UserInventory.user_id == user.id,
            UserInventory.item_id == item.id
        )
    )
    inv = result.scalar_one_or_none()
    if inv:
        inv.quantity += 1
    else:
        inv = UserInventory(user_id=user.id, item_id=item.id, quantity=1)
        session.add(inv)
    
    await session.commit()
    return f"✅ «{item.name}» خریداری شد. XP باقی‌مانده: {user.xp}"
