import random
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from database.models_v3 import Recipe, CraftingSkill, UserInventory, ShopItem
from database.models import User
from services.cultivation import get_or_create_cultivation


DEFAULT_RECIPES = [
    # کیمیاگری
    {
        "name": "معجون انرژی کوچک",
        "recipe_type": "alchemy",
        "required_materials": {
            "گیاه معمولی - گل بهار": 1,
            "مواد اولیه کیمیا": 1,
            "شیشه کیمیا": 1
        },
        "result_item_name": "قرص انرژی پایه",
        "result_effect": {"energy": 40},
        "min_cultivation_realm": "پایه",
        "success_rate": 80
    },
    {
        "name": "معجون انرژی متوسط",
        "recipe_type": "alchemy",
        "required_materials": {
            "گیاه معمولی - ریشه کوهی": 1,
            "پودر گوگرد": 1,
            "شیشه کیمیا": 1
        },
        "result_item_name": "قرص انرژی متوسط",
        "result_effect": {"energy": 80},
        "min_cultivation_realm": "متوسط",
        "success_rate": 65
    },
    {
        "name": "معجون روح",
        "recipe_type": "alchemy",
        "required_materials": {
            "گیاه معنوی - برگ روح": 1,
            "کریستال خالص": 1,
            "شیشه کیمیا": 1
        },
        "result_item_name": "معجون روح",
        "result_effect": {"energy": 120, "xp": 30},
        "min_cultivation_realm": "بالا",
        "success_rate": 55
    },
    # طلسمسازی
    {
        "name": "طلسم محافظ پایه",
        "recipe_type": "talisman",
        "required_materials": {
            "کاغذ طلسم معمولی": 1,
            "گیاه معمولی - گل بهار": 1
        },
        "result_item_name": "طلسم محافظ ضعیف",
        "result_effect": {"protect": 1},
        "min_cultivation_realm": "پایه",
        "success_rate": 75
    },
    {
        "name": "طلسم قدرت",
        "recipe_type": "talisman",
        "required_materials": {
            "کاغذ طلسم معنوی": 1,
            "جوهر روح": 1,
            "گیاه معنوی - گل ماه": 1
        },
        "result_item_name": "طلسم قدرت",
        "result_effect": {"xp_bonus": 15, "duel_power": 8},
        "min_cultivation_realm": "متوسط",
        "success_rate": 60
    },
    # آهنگری (ساخت سلاح)
    {
        "name": "ساخت شمشیر آهنی",
        "recipe_type": "smithing",
        "required_materials": {
            "آهن خام": 2
        },
        "result_item_name": "شمشیر آهنی",
        "result_effect": {"duel_power": 5},
        "min_cultivation_realm": "پایه",
        "success_rate": 85
    },
    {
        "name": "ساخت نیزه فولادی",
        "recipe_type": "smithing",
        "required_materials": {
            "فولاد تصفیهشده": 2,
            "آهن خام": 1
        },
        "result_item_name": "نیزه فولادی",
        "result_effect": {"duel_power": 12},
        "min_cultivation_realm": "متوسط",
        "success_rate": 70
    },
    {
        "name": "ساخت شمشیر روحدار",
        "recipe_type": "smithing",
        "required_materials": {
            "فولاد تصفیهشده": 1,
            "سنگ روح": 1,
            "کریستال خالص": 1
        },
        "result_item_name": "شمشیر روحدار",
        "result_effect": {"duel_power": 25},
        "min_cultivation_realm": "بالا",
        "success_rate": 50
    },
]


async def ensure_default_recipes(session: AsyncSession):
    result = await session.execute(select(Recipe))
    if result.scalars().first():
        return
    for r in DEFAULT_RECIPES:
        session.add(Recipe(**r))
    await session.commit()


async def get_or_create_skill(session: AsyncSession, user_id: int, skill_type: str) -> CraftingSkill:
    result = await session.execute(
        select(CraftingSkill).where(
            CraftingSkill.user_id == user_id,
            CraftingSkill.skill_type == skill_type
        )
    )
    skill = result.scalar_one_or_none()
    if skill:
        return skill
    skill = CraftingSkill(user_id=user_id, skill_type=skill_type)
    session.add(skill)
    await session.commit()
    await session.refresh(skill)
    return skill


async def get_user_materials(session: AsyncSession, user_id: int) -> dict:
    result = await session.execute(
        select(UserInventory, ShopItem)
        .join(ShopItem, UserInventory.item_id == ShopItem.id)
        .where(UserInventory.user_id == user_id)
    )
    materials = {}
    for inv, item in result.all():
        materials[item.name] = inv.quantity
    return materials


async def craft(session: AsyncSession, user: User, recipe: Recipe) -> dict:
    cult = await get_or_create_cultivation(session, user.id)
    realms = ["بیداری", "پایه", "میانه", "متوسط", "هسته", "بالا", "روح", "پیشرفته", "آسمان", "پوچی", "کهکشانی", "اوج", "استاد", "ازلی", "خدا"]
    try:
        if realms.index(cult.realm) < realms.index(recipe.min_cultivation_realm):
            return {"success": False, "message": f"قلمرو تذهیب کافی نیست (نیاز: {recipe.min_cultivation_realm})"}
    except ValueError:
        pass

    materials = await get_user_materials(session, user.id)
    for mat_name, needed in mats.items():
        if materials.get(mat_name, 0) < needed:
            return {"success": False, "message": f"مواد کافی نداری (نیاز: {needed}× {mat_name})"}

    for mat_name, needed in mats.items():
        result = await session.execute(
            select(UserInventory, ShopItem)
            .join(ShopItem, UserInventory.item_id == ShopItem.id)
            .where(UserInventory.user_id == user.id, ShopItem.name == mat_name)
        )
        row = result.first()
        if row:
            inv, _ = row
            inv.quantity -= needed
            if inv.quantity <= 0:
                await session.delete(inv)

    skill = await get_or_create_skill(session, user.id, recipe.recipe_type)
    final_rate = min(recipe.success_rate + min(skill.level * 3, 20), 95)
    success = random.randint(1, 100) <= final_rate

    if success:
        skill.exp += 15
        if skill.exp >= 50:
            skill.exp = 0
            skill.level += 1
        # افزودن نتیجه به موجودی بازیکن
        try:
            rname = recipe.result_item_name or recipe.name
            ri = await session.execute(select(ShopItem).where(ShopItem.name == rname))
            item = ri.scalar_one_or_none()
            if not item:
                from database.models_v3 import Building
                b = await session.execute(select(Building).where(Building.building_type == "کیمیاگری"))
                bld = b.scalar_one_or_none()
                if not bld:
                    bld = Building(name="کیمیاگری", building_type="کیمیاگری", description="ساخت")
                    session.add(bld)
                    await session.flush()
                item = ShopItem(
                    building_id=bld.id,
                    name=rname,
                    item_type="crafted",
                    description=f"ساختهشده: {recipe.name}",
                    price=0,
                    effect=recipe.result_effect if isinstance(recipe.result_effect, dict) else {},
                )
                session.add(item)
                await session.flush()
            inv_r = await session.execute(
                select(UserInventory).where(
                    UserInventory.user_id == user.id,
                    UserInventory.item_id == item.id,
                )
            )
            inv = inv_r.scalar_one_or_none()
            if inv:
                inv.quantity = int(inv.quantity or 0) + 1
            else:
                session.add(UserInventory(user_id=user.id, item_id=item.id, quantity=1))
        except Exception:
            pass
        await session.commit()
        return {
            "success": True,
            "message": (
                f"✅ ساخت «{recipe.name}» موفق!"
                + chr(10)
                + f"مهارت {recipe.recipe_type} سطح {skill.level}"
                + chr(10)
                + f"آیتم «{recipe.result_item_name}» به کیف اضافه شد. /inventory"
            ),
            "result_name": recipe.result_item_name,
            "effect": recipe.result_effect,
        }
    else:
        await session.commit()
        return {
            "success": False,
            "message": f"❌ ساخت شکست خورد. مواد از بین رفت.\nشانس: {final_rate}%"
        }
