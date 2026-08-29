"""ناوبری متنی: کاربر میتواند نام بخش را بدون / بنویسد."""
from aiogram import Router, F
from aiogram.types import Message

router = Router()


def _norm(text: str) -> str:
    t = (text or "").strip().lower()
    # حذف فاصله‌های صفرعرض و نرمال‌سازی ساده
    for ch in ("\u200c", "\u200f", "\u200e", "\ufeff"):
        t = t.replace(ch, "")
    return " ".join(t.split())


# نامهای قابل تایپ برای ورود مستقیم به بخشها
ALIASES = {
    "👤 پروفایل": "profile",
    "🧘 تزکیه": "cultivation",
    "⚔️ نبرد": "duel",
    "🎒 کوله بار": "inventory",
    "🎒 کولهبار": "inventory",
    "⚗ کیمیاگری": "craft",
    "🏛 فرقه": "sects",
    "🏪 بازار": "shop",
    "🎁 گنجینه": "codex",
    "📜 ماموریت ها": "missions",
    "📜 مأموریتها": "missions",
    "🏆 دستاوردها": "achievements",
    "📊 رتبه بندی": "ranking",
    "📊 رتبهبندی": "ranking",
    "🌍 رویدادها": "events",
    "🎁 پاداش روزانه": "daily",
    "🎲 تاس شانس": "luckdice",
    "💼 شغل": "jobs",
    "📖 راهنما": "help",
    "پروفایل": "profile",
    "پروفایل من": "profile",
    "تذهیب": "cultivation",
    "تزکیه": "cultivation",
    "تذهیب و قلمرو": "cultivation",
    "قلمرو": "cultivation",
    "نبرد": "duel",
    "دوئل": "duel",
    "دوئل خدمتکار": "servantduel",
    "دوئل خدمتکاران": "servantduel",
    "دوئل کاراکتر": "charduel",
    "دوئل کاراکترها": "charduel",
    "کوله بار": "inventory",
    "کولهبار": "inventory",
    "کیف": "inventory",
    "کیمیاگری": "craft",
    "ساخت": "craft",
    "فرقه": "sects",
    "فرقه ها": "sects",
    "فرقهها": "sects",
    "بازار": "market",
    "مغازه": "shop",
    "فروشگاه": "shop",
    "گنجینه": "codex",
    "دانشنامه": "codex",
    "ماموریت": "missions",
    "مأموریت": "missions",
    "ماموریت ها": "missions",
    "مأموریتها": "missions",
    "دستاوردها": "achievements",
    "رتبه بندی": "ranking",
    "رتبهبندی": "ranking",
    "رتبه ها": "ranking",
    "رتبهها": "ranking",
    "رویدادها": "events",
    "رویداد": "events",
    "پاداش روزانه": "daily",
    "ورود روزانه": "daily",
    "تاس شانس": "luckdice",
    "تاس شانسی": "luckdice",
    "شغل": "jobs",
    "شغل ها": "jobs",
    "شغلها": "jobs",
    "راهنما": "help",
    "دستورات": "commands",
    "قوانین": "rules",
    "آرنا": "arena",
    "نگهبان": "guardian",
    "خدمتکار": "servants",
    "خدمتکارها": "servants",
    "خدمتکار ها": "servants",
    "لیست خدمتکار": "myservants",
    "لیست خدمتکارها": "myservants",
    "ازدواج": "marry",
    "همسران": "wives",
    "خانواده": "wives",
    "کاراکتر": "pullchar",
    "کاراکتر جدید": "pullchar",
    "کاراکترها": "mychars",
    "کاراکتر ها": "mychars",
    "لیست کاراکتر": "mychars",
    "لیست کاراکترها": "mychars",
    "شکار": "hunt",
    "🐾 شکار": "hunt",
    "حیوانات و شکار": "hunt",
    "بهترین کاراکتر": "bestchar",
    "جرم": "crime",
    "تحت تعقیب": "crime",
    "نقشه": "worldmap",
    "نقشه جهان": "worldmap",
    "جنگ فرقه": "sectwar",
    "باس جهانی": "worldboss",
    "باس جهان": "worldboss",
    "حمله به باس": "bossattack",
    "رویداد جهان": "worldevent",
    "رویداد جدید": "worldevent",
    "موقعیت": "world",
    "مختصات": "world",
    "جهان جدید": "world",
    "فروشگاه صندوق": "chests",
    "خرید صندوق": "chests",
    "زیرمجموعه فرقه": "subsects",
    "۹ آسمان": "skies",
    "۹آسمان": "skies",
    "نه آسمان": "skies",
    "آسمان": "skies",
    "پلکان بهشت": "heavenstair",
    "پلکانبهشت": "heavenstair",
    "پلکان": "heavenstair",
    "صعود": "heavenstair",
    "مکان های آسمان": "landmarks",
    "مکانهای آسمان": "landmarks",
    "مکان های جدید": "landmarks",
    "شهرهای جهان": "worldcities",
    "شهرها": "worldcities",
    "قلمروهای جهان": "worldcities",
    "ساخت شهر": "newcity",
    "ساخت کشور": "newcountry",
    "غذا": "eat",
    "آب": "drink",
    "شمال": "north", "جنوب": "south", "شرق": "east", "غرب": "west",
    "صندوق": "chest",
    "ماموریت زنجیره": "chainmission",
    "اتحاد": "alliance",
    "بانک": "bank",
    "سرمایه گذاری": "bank",
    "صندوق روزانه": "chest",
    "خرید صندوق": "chests",
    "گنجینه روزانه": "chest",
    "کاراکتر شانسی": "pullchar",
    "کاراکتر شانسی جدید": "pullchar",
    "خدمتکارهای من": "myservants",
    "خدمتکار من": "myservants",
    "خرید خدمتکار": "buyservant",
    "رویداد جهان": "worldevent",
    "تکنیک کنترل پوچی": "voidtech",
    "کنترل پوچی": "voidtech",
}


@router.message(F.text, ~F.text.startswith("/"))
async def text_section_navigation(message: Message):
    # فقط پیامهای متنی ساده (دکمه کیبورد و نام بخش).
    # دستورات /command عمداً از فیلتر حذف شده‌اند تا روترهای دیگر آن‌ها را بگیرند.
    raw = (message.text or "").strip()
    if not raw:
        return

    norm = _norm(raw)

    # اجرای «دستور» بدون اسلش، حتی وقتی آرگومان دارد.
    if norm.startswith("ساخت شهر ") or norm.startswith("ساختشهر "):
        from bot.handlers.open_world import cmd_new_city
        msg = message.model_copy(update={"text": "/newcity " + raw.split(maxsplit=2)[-1]})
        await cmd_new_city(msg)
        return
    if norm.startswith("ساخت کشور ") or norm.startswith("ساختکشور "):
        from bot.handlers.open_world import cmd_new_country
        msg = message.model_copy(update={"text": "/newcountry " + raw.split(maxsplit=2)[-1]})
        await cmd_new_country(msg)
        return
    if norm.startswith("ساخت فرقه ") or norm.startswith("ساختفرقه "):
        from bot.handlers.sects import cmd_create_sect
        msg = message.model_copy(update={"text": "/createsect " + raw.split(maxsplit=2)[-1]})
        await cmd_create_sect(msg)
        return
    if norm.startswith("قدرت بده ") or norm.startswith("قدرتبده "):
        from bot.handlers.admin import cmd_give_power
        msg = message.model_copy(update={"text": "/givepower " + raw.split(maxsplit=2)[-1]})
        await cmd_give_power(msg)
        return
    if norm.startswith("حذف قدرت ") or norm.startswith("حذفقدرت ") or norm.startswith("کم کردن قدرت "):
        from bot.handlers.admin import cmd_take_power
        msg = message.model_copy(update={"text": "/takepower " + raw.split(maxsplit=2)[-1]})
        await cmd_take_power(msg)
        return
    if norm.startswith("پلکان بهشت") or norm == "صعود":
        from bot.handlers.open_world import cmd_heaven_stair
        await cmd_heaven_stair(message)
        return

    key = ALIASES.get(norm)
    if not key:
        return

    try:
        if key == "profile":
            from bot.handlers.profile import cmd_profile
            await cmd_profile(message)
        elif key == "cultivation":
            from bot.handlers.cultivation import cmd_cultivation
            await cmd_cultivation(message)
        elif key == "duel":
            await message.answer(
                "⚔️ <b>بخش نبرد و دوئل</b>\n\n"
                "برای دوئل، روی پیام بازیکن موردنظر ریپلای کن و بنویس:\n"
                "<code>/duel</code>\n\n"
                "برای دوئل رندوم هم میتوانی بنویسی:\n"
                "<code>/randomduel</code>"
            )
        elif key == "servantduel":
            await message.answer(
                "🧑🤝🧑 <b>دوئل خدمتکاران</b>\n\n"
                "روی پیام حریف ریپلای کن و بنویس:\n"
                "<code>/servantduel شماره_خدمتکار_من شماره_خدمتکار_حریف</code>\n"
                "یا با آیدی حریف:\n"
                "<code>/servantduel آیدی شماره_من شماره_حریف</code>\n\n"
                "این نبرد فقط قدرت خود خدمتکارها را مقایسه میکند."
            )
        elif key == "charduel":
            await message.answer(
                "🎴 <b>دوئل کاراکترها</b>\n\n"
                "روی پیام حریف ریپلای کن و بنویس:\n"
                "<code>/charduel شماره_کاراکتر_من شماره_کاراکتر_حریف</code>\n"
                "یا از آیدی حریف استفاده کن.\n\n"
                "نبرد بر اساس قدرت کاراکتر و ستارههای آن انجام میشود."
            )
        elif key == "inventory":
            from bot.handlers.shop import cmd_inventory
            await cmd_inventory(message)
        elif key == "craft":
            from bot.handlers.crafting import cmd_craft
            await cmd_craft(message)
        elif key == "sects":
            from bot.handlers.sects import cmd_sects
            await cmd_sects(message)
        elif key == "market":
            from bot.handlers.social import cmd_market
            await cmd_market(message)
        elif key == "shop":
            from bot.handlers.shop import cmd_buildings
            await cmd_buildings(message)
        elif key == "codex":
            from bot.handlers.codex_items import cmd_item_codex
            await cmd_item_codex(message)
        elif key == "missions":
            from bot.handlers.missions import cmd_missions
            await cmd_missions(message)
        elif key == "achievements":
            from bot.handlers.ranking import cmd_achievements
            await cmd_achievements(message)
        elif key == "ranking":
            from bot.handlers.ranking import cmd_ranking
            await cmd_ranking(message)
        elif key == "events":
            from bot.handlers.jobs_events import cmd_events
            await cmd_events(message)
        elif key == "daily":
            from bot.handlers.retention import cmd_daily
            await cmd_daily(message)
        elif key == "luckdice":
            from bot.handlers.jobs_events import cmd_luck_dice
            await cmd_luck_dice(message)
        elif key == "jobs":
            from bot.handlers.jobs_events import cmd_jobs
            await cmd_jobs(message)
        elif key == "help":
            from bot.handlers.help_menu import cmd_help
            await cmd_help(message)
        elif key == "commands":
            from bot.handlers.help_menu import cmd_commands
            await cmd_commands(message)
        elif key == "rules":
            from bot.handlers.help_menu import cmd_rules
            await cmd_rules(message)
        elif key == "voidtech":
            from bot.handlers.cultivation import cmd_void_control
            await cmd_void_control(message)
        elif key == "arena":
            from bot.handlers.arena import cmd_arena
            await cmd_arena(message)
        elif key == "guardian":
            from bot.handlers.guardian import cmd_guardian
            await cmd_guardian(message)
        elif key == "servants":
            from bot.handlers.social import cmd_servants_v2
            await cmd_servants_v2(message)
        elif key == "myservants":
            from bot.handlers.social import cmd_my_servants_v2
            await cmd_my_servants_v2(message)
        elif key == "marry":
            from bot.handlers.marriage import cmd_marry
            await cmd_marry(message)
        elif key == "wives":
            from bot.handlers.marriage import cmd_wives
            await cmd_wives(message)
        elif key == "pullchar":
            from bot.handlers.characters import cmd_pull
            await cmd_pull(message)
        elif key == "mychars":
            from bot.handlers.characters import cmd_list
            await cmd_list(message)
        elif key == "hunt":
            from bot.handlers.pets import cmd_hunt
            await cmd_hunt(message)
        elif key == "bestchar":
            from bot.handlers.characters import cmd_best
            await cmd_best(message)
        elif key == "crime":
            from bot.handlers.advanced_systems import crime_cmd
            await crime_cmd(message)
        elif key == "skies":
            from bot.handlers.open_world import cmd_skies
            await cmd_skies(message)
        elif key == "heavenstair":
            from bot.handlers.open_world import cmd_heaven_stair
            await cmd_heaven_stair(message)
        elif key == "worldcities":
            from bot.handlers.open_world import cmd_world_cities
            await cmd_world_cities(message)
        elif key == "landmarks":
            from bot.handlers.open_world import cmd_landmarks
            await cmd_landmarks(message)
        elif key == "worldmap":
            from bot.handlers.open_world import cmd_world
            await cmd_world(message)
        elif key == "sectwar":
            from bot.handlers.advanced_systems import sectwar_cmd
            await sectwar_cmd(message)
        elif key == "worldboss":
            from bot.handlers.open_world import cmd_world_boss
            await cmd_world_boss(message)
        elif key == "chest":
            from bot.handlers.advanced_systems import chest_cmd
            await chest_cmd(message)
        elif key == "world":
            from bot.handlers.open_world import cmd_world
            await cmd_world(message)
        elif key in ("north", "south", "east", "west"):
            from bot.handlers.open_world import cmd_move
            # همان تابع با متن بدون اسلش هم جهت را می‌خواند.
            await cmd_move(message)
        elif key == "worldevent":
            from bot.handlers.open_world import cmd_world_event
            await cmd_world_event(message)
        elif key == "bossattack":
            from bot.handlers.open_world import cmd_boss_attack
            await cmd_boss_attack(message)
        elif key == "newcity":
            await message.answer("برای ساخت شهر بنویس: /newcity نام شهر")
        elif key == "newcountry":
            await message.answer("برای ساخت کشور بنویس: /newcountry نام کشور")
        elif key == "eat":
            from bot.handlers.open_world import cmd_eat
            await cmd_eat(message)
        elif key == "drink":
            from bot.handlers.open_world import cmd_drink
            await cmd_drink(message)
        elif key == "chests":
            from bot.handlers.advanced_systems import chest_shop_cmd
            await chest_shop_cmd(message)
        elif key == "subsects":
            await message.answer("برای دیدن زیرمجموعه: /subsects شناسه_فرقه")
        elif key == "chainmission":
            from bot.handlers.advanced_systems import chainmission_cmd
            await chainmission_cmd(message)
        elif key == "event":
            from bot.handlers.advanced_systems import event_cmd
            await event_cmd(message)
        elif key == "alliance":
            from bot.handlers.advanced_systems import alliance_cmd
            await alliance_cmd(message)
        elif key == "bank":
            from bot.handlers.advanced_systems import bank_cmd
            await bank_cmd(message)
    except Exception as e:
        import logging, traceback
        logging.getLogger(__name__).exception("text_nav error key=%s: %s", key, e)
        tb = traceback.format_exc()
        await message.answer(
            f"⚠️ خطا در ورود به بخش: <code>{type(e).__name__}</code>\n"
            f"{str(e)[:300]}\n\n"
            f"<code>{tb[-400:]}</code>"
        )
