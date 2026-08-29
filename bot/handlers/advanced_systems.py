from aiogram import Router, F
from aiogram.types import Message, CallbackQuery
from aiogram.filters import Command
from bot.config import ADMIN_IDS
from database.engine import async_session
from database.crud import get_or_create_user, get_user_by_telegram_id
from services.power import calc_power
from services.advanced_systems import *

router = Router()

@router.message(Command("powerstats", "قدرترزمی", "قدرت_رزمی"))
async def power_stats(message: Message):
    async with async_session() as s:
        u=await get_or_create_user(s,message.from_user.id,message.from_user.full_name,message.from_user.username)
        p=await calc_power(s,u)
    st=get_stats(u.telegram_id); bl=get_bloodline(u.telegram_id)
    await message.answer(f"⚔️ <b>قدرت رزمی کامل</b>\n\nقدرت نهایی: <b>{p['total']:,}</b>\nقدرت پایه: {p.get('base',0):,}\nقدرت تذهیب: {p.get('realm',0):,}\nسلاح/زره: {p.get('weapon',0):,}\nبدن: {p.get('body',0):,}\nروح: {p.get('spirit',0):,}\nتبار: {bl}\nقدرت مستقیم ادمین: {p.get('admin',0):,}\n\n📌 قدرت نهایی از تذهیب، تجهیزات، بدن، روح، تکنیکها، تبار و پاداشهای مستقیم تشکیل میشود.")

@router.message(Command("bloodlines", "تبارها", "تبار"))
async def bloodlines(message: Message):
    from aiogram.utils.keyboard import InlineKeyboardBuilder
    from html import escape
    uid = message.from_user.id
    current = get_bloodline(uid)
    text = (
        "🧬 <b>تبارها</b>\n\n"
        "برای فعال کردن تبار، روی دکمه «فعال کردن» همان تبار بزن. "
        "تبار انتخابشده فوراً به عنوان تبار فعال ثبت میشود.\n\n"
        + "\n".join(
            f"• <b>{escape(k)}</b> — ضریب ×{v[0]} — {escape(v[1])}"
            + (" ← فعال" if k == current else "")
            for k, v in BLOODLINES.items()
        )
    )
    kb = InlineKeyboardBuilder()
    for name in BLOODLINES:
        kb.button(text=f"🧬 فعال کردن {name}", callback_data=f"activateblood:{uid}:{name}")
    kb.button(text="🔄 تبار فعلی", callback_data=f"myblood:{uid}")
    kb.adjust(2)
    await message.answer(text, reply_markup=kb.as_markup())

@router.callback_query(F.data.startswith("activateblood:"))
async def cb_activate_bloodline(callback: CallbackQuery):
    parts = callback.data.split(":", 2)
    if len(parts) != 3:
        return await callback.answer("درخواست نامعتبر است.", show_alert=True)
    try:
        owner = int(parts[1])
    except ValueError:
        return await callback.answer("درخواست نامعتبر است.", show_alert=True)
    if callback.from_user.id != owner:
        return await callback.answer("⛔ این پنل برای صاحبش است.", show_alert=True)
    name = activate_bloodline(owner, parts[2])
    if not name:
        return await callback.answer("❌ این تبار وجود ندارد.", show_alert=True)
    await callback.answer(f"✅ تبار «{name}» فعال شد.", show_alert=True)
    try:
        await callback.message.edit_text(
            f"🧬 <b>تبار فعال شد</b>\n\n"
            f"تبار فعلی: <b>{name}</b>\n"
            f"ضریب تبار: ×{BLOODLINES[name][0]}\n\n"
            "برای تغییر تبار دوباره /bloodlines را بزن.",
            reply_markup=None,
        )
    except Exception:
        pass

@router.callback_query(F.data.startswith("myblood:"))
async def cb_my_bloodline(callback: CallbackQuery):
    parts = callback.data.split(":", 1)
    try:
        owner = int(parts[1])
    except Exception:
        return await callback.answer("درخواست نامعتبر است.", show_alert=True)
    if callback.from_user.id != owner:
        return await callback.answer("⛔ این پنل برای صاحبش است.", show_alert=True)
    name = get_bloodline(owner)
    await callback.answer(f"تبار فعلی: {name} ×{BLOODLINES[name][0]}", show_alert=True)

@router.message(Command("activatebloodline", "فعالکردنتبار", "فعالتبار"))
async def activate_bloodline_cmd(message: Message):
    parts = (message.text or "").split(maxsplit=1)
    if len(parts) < 2:
        return await message.answer("فرمت: /activatebloodline نام تبار\nمثال: /activatebloodline الهی")
    name = activate_bloodline(message.from_user.id, parts[1])
    if not name:
        return await message.answer("❌ تبار پیدا نشد. /bloodlines را بزن.")
    await message.answer(f"✅ تبار «{name}» فعال شد.\nضریب تبار: ×{BLOODLINES[name][0]}")

@router.message(Command("mybloodline", "تباری", "تبارمن"))
async def my_bloodline(message: Message):
    name=get_bloodline(message.from_user.id); await message.answer(f"🧬 تبار فعلی: <b>{name}</b>\nضریب تبار: ×{BLOODLINES[name][0]}\n\nبرای تغییر: /bloodlines یا /activatebloodline نام")

@router.message(Command("setbloodline", "تنظیمتبار"))
async def set_bl(message: Message):
    if message.from_user.id not in ADMIN_IDS: return await message.answer("⛔ فقط سازنده.")
    parts=(message.text or '').split(maxsplit=2)
    target=message.reply_to_message.from_user.id if message.reply_to_message else (int(parts[1]) if len(parts)>2 else None)
    name=(parts[-1] if parts else '').strip()
    if target is None: return await message.answer("فرمت: /setbloodline TELEGRAM_ID تبار یا ریپلای + /setbloodline تبار")
    got=set_bloodline(target,name)
    await message.answer(f"✅ تبار {target} → {got}" if got else "❌ تبار پیدا نشد. /bloodlines")

@router.message(Command("familytree", "شجره", "شجرهنامه"))
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
    await message.answer("🌳 <b>شجرهنامه/خانواده</b>\n\n"+('\n'.join(lines) if lines else 'هنوز رابطه خانوادگی ثبتشدهای نداری.')+"\n\nبرای فرزندان، از /mychildren استفاده کن.")

@router.message(Command("kingdom", "mykingdom", "قلمرومن", "حکومت"))
async def kingdom(message: Message):
    from aiogram.types import FSInputFile
    from services.portraits import panel_url
    await message.answer_photo(FSInputFile(panel_url("kingdom")), caption="👑 <b>حکومت و قلمرو</b>")
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

# ==================== امکانات توسعهیافته V32 ====================
from aiogram import F

@router.message(Command("crime", "جرم", "تحت_تعقیب"))
async def crime_cmd(message: Message):
    from services.advanced_systems import crime_status, commit_crime
    p=(message.text or "").split()
    if len(p)>1 and p[1] in ("انجام", "ارتکاب"):
        r=commit_crime(message.from_user.id, severity=5, bounty=500)
        return await message.answer(f"🚨 جرم ثبت شد!\n⚠️ تحت تعقیب: {r['wanted']}\n💰 جایزه دستگیری: {r['bounty']:,}")
    r=crime_status(message.from_user.id)
    await message.answer(f"⚖️ <b>وضعیت قانونی</b>\n⚠️ تحت تعقیب: {r['wanted']}\n💰 جایزه: {r['bounty']:,}\n🔒 زندان: {'بله' if is_jailed(message.from_user.id) else 'خیر'}")

@router.message(Command("worldmap", "نقشه", "نقشه_جهان"))
async def worldmap_cmd(message: Message):
    from services.advanced_systems import world_state, discover_region
    d=world_state(); name,reg=discover_region(message.from_user.id)
    await message.answer(f"🗺️ <b>نقشه جهان</b>\n🌤 وضعیت: {d['seasons']}\n☠️ خطر جهانی: {d['danger']}\n\n📍 منطقه کشفشده: <b>{name}</b>\n⚠️ خطر: {reg['danger']}\n⛏ منابع: {reg['resources']:,}")

@router.message(Command("kingdomup", "ارتقای_حکومت"))
async def kingdom_up_cmd(message: Message):
    from services.advanced_systems import kingdom_upgrade, get_kingdom
    p=(message.text or "").split(); stat=p[1] if len(p)>1 else "army"; amount=int(p[2]) if len(p)>2 and p[2].isdigit() else 1
    k=kingdom_upgrade(message.from_user.id,stat,amount)
    await message.answer(f"👑 ارتقای حکومت انجام شد.\n📊 {stat}: {k.get(stat,0):,}")

@router.message(Command("sectwar", "جنگ_فرقه"))
async def sectwar_cmd(message: Message):
    from services.advanced_systems import sect_war
    p=(message.text or "").split()
    if len(p)<2 or not p[1].lstrip('-').isdigit(): return await message.answer("فرمت: /sectwar TELEGRAM_ID")
    r=sect_war(message.from_user.id,int(p[1])); await message.answer(f"⚔️ جنگ فرقهای\nامتیاز تو: {r['score_a']}\nامتیاز حریف: {r['score_b']}\n🏆 برنده: {'تو' if r['winner']==message.from_user.id else 'حریف'}")

@router.message(Command("worldboss", "باس_جهانی", "اژدهای_جهانی"))
async def worldboss_cmd(message: Message):
    from services.advanced_systems import world_boss, hit_world_boss
    p=(message.text or "").split(); d=world_boss()
    if len(p)>1 and p[1].isdigit(): d,dmg=hit_world_boss(message.from_user.id,int(p[1])); await message.answer(f"🐉 {d['name']}\n💥 آسیب: {dmg:,}\n❤️ جان باقیمانده: {d['hp']:,}/{d['max_hp']:,}")
    else: await message.answer(f"🐉 <b>{d['name']}</b>\n❤️ {d['hp']:,}/{d['max_hp']:,}\n💰 پاداش پایه: {d['reward']:,}\nبرای حمله: /worldboss مقدار_آسیب")

@router.message(Command("chest", "صندوق", "گنج", "صندوقروزانه"))
async def chest_cmd(message: Message):
    from services.advanced_systems import open_chest
    result=open_chest(message.from_user.id, None)
    amount, remaining, grade=result
    if amount is None:
        hours=remaining//3600; minutes=(remaining%3600)//60
        return await message.answer(f"⏳ صندوق روزانه آماده نیست.\nزمان باقی‌مانده: <b>{hours} ساعت و {minutes} دقیقه</b>")
    async with async_session() as session:
        from services.economy import get_or_create_wallet
        u=await get_or_create_user(session,message.from_user.id,message.from_user.full_name,message.from_user.username)
        w=await get_or_create_wallet(session,u.id); w.coins=int(w.coins or 0)+int(amount)
        await session.commit()
    await message.answer(f"🎁 <b>صندوق روزانه باز شد!</b>\n🎲 رتبه شانسی: <b>{grade}</b>\n💰 +{amount:,} سکه\n\nفردا دوباره شانس داری.")

@router.message(Command("chests", "فروشگاهصندوق", "خریدصندوق"))
async def chest_shop_cmd(message: Message):
    from services.advanced_systems import chest_shop
    lines=["🎁 <b>فروشگاه صندوق‌ها</b>","","صندوق روزانه رایگان است و رتبه‌اش شانسی است:","/chest"]
    for rank,price,rr in chest_shop():
        lines.append(f"• <b>{rank}</b> — {price:,} سکه — پاداش {rr[0]:,} تا {rr[1]:,}")
    lines.append("\nخرید: /buychest نام‌رتبه")
    await message.answer("\n".join(lines))

@router.message(Command("buychest", "خریدصندوقرتبه"))
async def buy_chest_cmd(message: Message):
    from services.advanced_systems import CHEST_RANKS
    parts=(message.text or "").split(maxsplit=1)
    if len(parts)<2 or parts[1].strip() not in CHEST_RANKS or CHEST_RANKS[parts[1].strip()]["price"]<=0:
        await message.answer("فرمت: /buychest نادر\nرتبه‌ها: نادر | افسانه‌ای | الهی | مطلق")
        return
    rank=parts[1].strip(); price=CHEST_RANKS[rank]["price"]; lo,hi=CHEST_RANKS[rank]["range"]
    amount=random.randint(lo,hi)
    async with async_session() as session:
        u=await get_or_create_user(session,message.from_user.id,message.from_user.full_name,message.from_user.username)
        from services.economy import get_or_create_wallet
        w=await get_or_create_wallet(session,u.id)
        if int(w.coins or 0)<price:
            await message.answer(f"❌ سکه کافی نیست. نیاز: {price:,} | موجودی: {int(w.coins or 0):,}"); return
        w.coins-=price; w.coins+=amount; await session.commit()
    await message.answer(f"🎁 صندوق <b>{rank}</b> خریداری و باز شد!\n💰 جایزه: +{amount:,} سکه\n🪙 هزینه: {price:,} سکه")

@router.message(Command("chainmission", "ماموریت_زنجیره"))
async def chainmission_cmd(message: Message):
    from services.advanced_systems import chain_mission, advance_chain_mission
    p=(message.text or "").split(); row,step=chain_mission(message.from_user.id)
    if len(p)>1 and p[1] in ("انجام","پیشرفت"): row=advance_chain_mission(message.from_user.id); row,step=chain_mission(message.from_user.id)
    await message.answer(f"📜 <b>مأموریت زنجیرهای</b>\nمرحله: {row['step']}\n🎯 هدف فعلی: {step[0]}\nبرای ثبت پیشرفت: /chainmission انجام")

@router.message(Command("worldevent", "رویداد_جهان"))
async def event_cmd(message: Message):
    from services.advanced_systems import random_event
    e=random_event(); await message.answer(f"🌍 <b>رویداد جهانی</b>\n✨ {e['name']}")

@router.message(Command("alliance", "اتحاد"))
async def alliance_cmd(message: Message):
    from services.advanced_systems import alliance_create, alliance_join, alliance_list
    p=(message.text or "").split(maxsplit=2); tg=message.from_user.id
    if len(p)>=2 and p[1]=="ساخت":
        if len(p)<3: return await message.answer("فرمت: /alliance ساخت نام")
        a=alliance_create(tg,p[2]); return await message.answer(f"🤝 اتحاد «{a['name']}» ساخته شد.")
    if len(p)>=2 and p[1]=="عضویت" and len(p)>2 and p[2].isdigit():
        a=alliance_join(int(p[2]),tg); return await message.answer("✅ عضو شدی." if a else "❌ اتحاد پیدا نشد.")
    ls=alliance_list(); await message.answer("🤝 <b>اتحادها</b>\n\n"+"\n".join(f"• {a['name']} — {len(a['members'])} عضو" for a in ls[:20]) if ls else "🤝 هنوز اتحادی ساخته نشده.")

@router.message(Command("bank", "بانک", "سرمایه"))
async def bank_cmd(message: Message):
    from services.advanced_systems import bank_balance, bank_deposit, bank_invest
    p=(message.text or "").split(); tg=message.from_user.id
    if len(p)>2 and p[1] in ("سپرده","deposit") and p[2].isdigit(): bank_deposit(tg,int(p[2]))
    elif len(p)>2 and p[1] in ("سرمایهگذاری","سرمایهگذاری","invest") and p[2].isdigit(): bank_invest(tg,int(p[2]))
    b=bank_balance(tg); await message.answer(f"🏦 <b>بانک</b>\n💰 سپرده: {b['deposit']:,}\n📈 سرمایهگذاری: {b['invest']:,}\n\nسپرده: /bank سپرده مبلغ\nسرمایهگذاری: /bank سرمایهگذاری مبلغ")

@router.message(Command("powerformula", "فرمول_قدرت"))
async def power_formula_cmd(message: Message):
    await message.answer("⚔️ <b>فرمول قدرت مؤثر</b>\nقدرت پایه + تذهیب + سلاح/زره + بدن + روح + تبار + تکنیک + خدمتکار + قلمرو + ساختمانها + دستاوردها.\n\n⚡ سرعت روی نوبت/جاخالی اثر میگذارد.\n🛡 دفاع روی کاهش آسیب اثر میگذارد.\n❤️ عمر روی دوام و ظرفیت زندهماندن اثر میگذارد.")
