from aiogram import Router
from aiogram.types import Message
from aiogram.filters import Command
from bot.config import ADMIN_IDS
from database.engine import async_session
from database.crud import get_or_create_user, get_user_by_telegram_id
from services.power import calc_power
from services.advanced_systems import *

router = Router()

@router.message(Command("cultivationrules", "قوانین‌تذهیب", "قوانینتذهیب"))
async def cultivation_rules(message: Message):
    await message.answer("""🧘 <b>پایه‌ای‌ترین قوانین تذهیب</b>\n\n• تذهیب از قلمرو و مرحله تشکیل می‌شود.\n• هر قلمرو تا مرحله‌های تعریف‌شده پیش می‌رود؛ با رسیدن به اوج، ورود به قلمرو بعدی یک جهش بزرگ است.\n• انرژی معنوی سوخت اصلی پیشرفت است و ریشه معنوی بازدهی آن را تغییر می‌دهد.\n• تکنیک‌ها، رگ‌های معنوی، بدن، روح و تبار می‌توانند قدرت و سرعت رشد را افزایش دهند.\n• قلمرو بالاتر همیشه به معنی پیروزی قطعی نیست؛ تجهیزات، تکنیک، بدن، روح و قدرت رزمی هم محاسبه می‌شوند.\n• ادمین می‌تواند برای تست/مدیریت، تذهیب و قدرت را مستقیماً تنظیم کند.\n• مقادیر بسیار بزرگ برای انرژی و قدرت با عددهای بزرگ پشتیبانی می‌شوند.\n\nدستورات مفید: /cultivation /meditate /train /cultpath /vein /cores /powerstats""")

@router.message(Command("powerstats", "قدرترزمی", "قدرت_رزمی"))
async def power_stats(message: Message):
    async with async_session() as s:
        u=await get_or_create_user(s,message.from_user.id,message.from_user.full_name,message.from_user.username)
        p=await calc_power(s,u)
    st=get_stats(u.telegram_id); bl=get_bloodline(u.telegram_id)
    await message.answer(f"⚔️ <b>قدرت رزمی کامل</b>\n\nقدرت نهایی: <b>{p['total']:,}</b>\nقدرت پایه: {p.get('base',0):,}\nقدرت تذهیب: {p.get('realm',0):,}\nسلاح/زره: {p.get('weapon',0):,}\nبدن: {p.get('body',0):,}\nروح: {p.get('spirit',0):,}\nتبار: {bl}\nقدرت مستقیم ادمین: {p.get('admin',0):,}\n\n📌 قدرت نهایی از تذهیب، تجهیزات، بدن، روح، تکنیک‌ها، تبار و پاداش‌های مستقیم تشکیل می‌شود.")

@router.message(Command("bloodlines", "تبارها", "تبار"))
async def bloodlines(message: Message):
    text="🧬 <b>تبارها</b>\n\n"+"\n".join(f"• {k} — ضریب ×{v[0]} — {v[1]}" for k,v in BLOODLINES.items())
    await message.answer(text)

@router.message(Command("mybloodline", "تباری", "تبارمن"))
async def my_bloodline(message: Message):
    name=get_bloodline(message.from_user.id); await message.answer(f"🧬 تبار فعلی: <b>{name}</b>\nضریب تبار: ×{BLOODLINES[name][0]}")

@router.message(Command("setbloodline", "تنظیمتبار"))
async def set_bl(message: Message):
    if message.from_user.id not in ADMIN_IDS: return await message.answer("⛔ فقط سازنده.")
    parts=(message.text or '').split(maxsplit=2)
    target=message.reply_to_message.from_user.id if message.reply_to_message else (int(parts[1]) if len(parts)>2 else None)
    name=(parts[-1] if parts else '').strip()
    if target is None: return await message.answer("فرمت: /setbloodline TELEGRAM_ID تبار یا ریپلای + /setbloodline تبار")
    got=set_bloodline(target,name)
    await message.answer(f"✅ تبار {target} → {got}" if got else "❌ تبار پیدا نشد. /bloodlines")

@router.message(Command("familytree", "شجره", "شجره‌نامه"))
async def familytree(message: Message):
    async with async_session() as s:
        u=await get_or_create_user(s,message.from_user.id,message.from_user.full_name,message.from_user.username)
        from services.marriage import get_active_relation
        rels=await get_active_relation(s,u.id)
        lines=[]
        for r in rels:
            other_id=r.wife_id if r.husband_id==u.id else r.husband_id
            o=await s.get(type(u),other_id)
            if o: lines.append(f"• {o.full_name} — {r.status}")
    await message.answer("🌳 <b>شجره‌نامه/خانواده</b>\n\n"+('\n'.join(lines) if lines else 'هنوز رابطه خانوادگی ثبت‌شده‌ای نداری.')+"\n\nبرای فرزندان، از /mychildren استفاده کن.")

@router.message(Command("kingdom", "mykingdom", "قلمرومن", "حکومت"))
async def kingdom(message: Message):
    k=get_kingdom(message.from_user.id)
    await message.answer(f"👑 <b>{k['name']}</b>\n🏛 پایتخت: {k['capital']}\n👥 جمعیت: {k['population']:,}\n⚔️ ارتش: {k['army']:,}\n💰 خزانه: {k['treasury']:,}\n📈 مالیات: {k['tax']}٪\n🏙 شهرها: {', '.join(k['cities']) if k['cities'] else 'هنوز شهری ثبت نشده'}")

@router.message(Command("setkingdom", "تنظیمقلمرو"))
async def setkingdom(message: Message):
    if message.from_user.id not in ADMIN_IDS: return await message.answer("⛔ فقط سازنده.")
    parts=(message.text or '').split(maxsplit=2)
    if len(parts)<3: return await message.answer("فرمت: /setkingdom TELEGRAM_ID نام قلمرو")
    try: tg=int(parts[1])
    except: return await message.answer("آیدی باید عدد باشد.")
    k=set_kingdom(tg,name=parts[2])
    await message.answer(f"✅ نام قلمرو به «{k['name']}» تغییر کرد.")

@router.message(Command("kingdomcity", "افزودنشهر"))
async def kingdom_city(message: Message):
    if message.from_user.id not in ADMIN_IDS: return await message.answer("⛔ فقط سازنده.")
    parts=(message.text or '').split(maxsplit=2)
    if len(parts)<3: return await message.answer("فرمت: /kingdomcity TELEGRAM_ID نام شهر")
    k=kingdom_add_city(int(parts[1]),parts[2]); await message.answer(f"✅ شهر «{parts[2]}» به قلمرو اضافه شد.")

@router.message(Command("setkingdomstat", "آمارقلمرو"))
async def kingdom_stat(message: Message):
    if message.from_user.id not in ADMIN_IDS: return await message.answer("⛔ فقط سازنده.")
    p=(message.text or '').split()
    if len(p)<4: return await message.answer("فرمت: /setkingdomstat TELEGRAM_ID treasury|army|population|tax مقدار")
    tg=int(p[1]); key=p[2]; val=int(p[3]); aliases={'خزانه':'treasury','ارتش':'army','جمعیت':'population','مالیات':'tax'}; key=aliases.get(key,key)
    if key not in ('treasury','army','population','tax'): return await message.answer('آمار نامعتبر.')
    set_kingdom(tg,**{key:val}); await message.answer('✅ آمار حکومت تنظیم شد.')
