"""جنگ‌های جهان‌گشای فرقه‌ها — پایدار، قابل‌رقابت و بدون نیاز به سرویس خارجی."""
from datetime import datetime, timedelta
import random

from aiogram import Router
from aiogram.filters import Command
from aiogram.types import Message
from sqlalchemy import select

from database.engine import async_session
from database.crud import get_or_create_user
from bot.config import ADMIN_IDS
from database.models_v2 import Sect, SectMember
from services.persist import get_dict, save

router = Router()

PREP_MINUTES = 5
WAR_HOURS = 3
ATTACK_COOLDOWN_SECONDS = 10
WAR_RESTART_COOLDOWN_SECONDS = 10

HOLY_SECTS = [
    ("معبد سپیده جاودان", "راه نور"),
    ("فرقه شمشیر آسمانی", "راه شمشیر"),
    ("قصر ستاره‌های پاک", "راه ستاره"),
    ("دره اژدهای مقدس", "راه اژدها"),
    ("کاخ رعد نه‌گانه", "راه رعد"),
]

RANKS = {
    "leader": "رهبر",
    "holy_daughter": "دختر مقدس",
    "holy_son": "پسر مقدس",
    "commander": "فرمانده جنگ",
    "elder": "ارشد",
}

def _wars():
    return get_dict("sect_wars")

def _save():
    save("sect_wars")

def _now():
    return datetime.utcnow()

def _dt(v):
    try:
        return datetime.fromisoformat(v) if v else None
    except (TypeError, ValueError):
        return None

def ensure_holy_sects():
    data = get_dict("holy_sects")
    changed = False
    for idx, (name, path) in enumerate(HOLY_SECTS, 1):
        k = str(idx)
        if k not in data:
            data[k] = {
                "name": name, "path": path, "controller_id": None,
                "holy_daughter_id": None, "holy_son_id": None,
                "branch_control": 0, "war_wins": 0,
            }
            changed = True
    if changed:
        save("holy_sects")
    return data

def _war_duration_text(end):
    sec = max(0, int((end - _now()).total_seconds()))
    return f"{sec//3600}ساعت {(sec%3600)//60}دقیقه"

async def _member(session, user):
    q = await session.execute(select(SectMember).where(SectMember.user_id == user.id))
    return q.scalars().first()

async def _sect(session, sect_id):
    return await session.get(Sect, sect_id)

async def _start_war(session, attacker, defender, creator_id, kind="sect"):
    wars = _wars()
    now = _now()
    # یک حمله جدید می‌تواند هر ۱۰ ثانیه ثبت شود؛ هر جنگ خودش ۳ ساعت ادامه دارد.
    for w in wars.values():
        if w.get("status") in ("preparing", "active") and (
            int(w["attacker_id"]) in (attacker.id, defender.id)
            or int(w["defender_id"]) in (attacker.id, defender.id)
        ):
            return None, "این فرقه در حال حاضر درگیر جنگ است."

    wid = str(max([int(x) for x in wars.keys() if str(x).isdigit()] + [0]) + 1)
    prep_end = now + timedelta(minutes=PREP_MINUTES)
    end = prep_end + timedelta(hours=WAR_HOURS)
    wars[wid] = {
        "id": int(wid), "kind": kind,
        "attacker_id": attacker.id, "defender_id": defender.id,
        "creator_id": creator_id, "status": "preparing",
        "created_at": now.isoformat(), "prep_end": prep_end.isoformat(),
        "end": end.isoformat(), "last_attack": None,
        "attacker_score": 0, "defender_score": 0,
        "attacker_rank": None, "defender_rank": None,
        "winner": None, "reward_claimed": False,
    }
    _save()
    return wars[wid], None

def _refresh(w):
    now = _now()
    prep = _dt(w.get("prep_end"))
    end = _dt(w.get("end"))
    if w.get("status") == "preparing" and prep and now >= prep:
        w["status"] = "active"
    if w.get("status") == "active" and end and now >= end:
        w["status"] = "finished"
        a, d = int(w["attacker_score"]), int(w["defender_score"])
        w["winner"] = "attacker" if a > d else ("defender" if d > a else "draw")
    return w

def _role_score(role):
    return {"رهبر": 5, "دختر مقدس": 4, "پسر مقدس": 4, "فرمانده جنگ": 3, "ارشد": 2}.get(role, 1)

async def _sect_power(session, sect):
    q = await session.execute(select(SectMember).where(SectMember.sect_id == sect.id))
    members = q.scalars().all()
    return max(1, int(sect.power_level or 0)) + sum(max(1, int(m.contribution_points or 0)) + _role_score(m.status)*10 for m in members)

@router.message(Command("holysects", "فرقههای_مقدس", "فرقههای_مقدس"))
async def holy_sects(message: Message):
    data = ensure_holy_sects()
    lines = ["🕊️ <b>پنج فرقه مقدس</b>", ""]
    for i, x in enumerate(data.values(), 1):
        c = x.get("controller_id") or "آزاد"
        lines.append(f"{i}. <b>{x['name']}</b> — {x['path']} — کنترل: {c}")
        lines.append(f"   👧 {x.get('holy_daughter_id') or 'آزاد'} | 👦 {x.get('holy_son_id') or 'آزاد'}")
    await message.answer("\n".join(lines))

@router.message(Command("holyrole", "مقاممقدس", "مقام_مقدس"))
async def holy_role(message: Message):
    if message.from_user.id not in ADMIN_IDS:
        await message.answer("⛔️ فقط ادمین می‌تواند این مقام را تعیین کند.")
        return
    parts = (message.text or "").split()
    if len(parts) < 4:
        await message.answer("فرمت: /holyrole شماره_فرقه daughter|son آیدی_تلگرام")
        return
    try: idx, uid = int(parts[1]), int(parts[3])
    except ValueError:
        await message.answer("شماره فرقه و آیدی باید عدد باشند.")
        return
    if idx not in range(1, 6) or parts[2].lower() not in ("daughter", "son"):
        await message.answer("نمونه: /holyrole 1 daughter 123456")
        return
    data = ensure_holy_sects()
    key = "holy_daughter_id" if parts[2].lower() == "daughter" else "holy_son_id"
    data[str(idx)][key] = uid
    save("holy_sects")
    await message.answer(f"✅ مقام {RANKS['holy_daughter' if key=='holy_daughter_id' else 'holy_son']} برای فرقه {idx} ثبت شد.")

@router.message(Command("holycontrol", "کنترل_فرقه_مقدس"))
async def holy_control(message: Message):
    if message.from_user.id not in ADMIN_IDS:
        await message.answer("⛔️ فقط ادمین می‌تواند این مقام را تعیین کند.")
        return
    parts = (message.text or "").split()
    if len(parts) < 3:
        await message.answer("فرمت ادمین: /holycontrol شماره_فرقه آیدی_تلگرام")
        return
    try:
        idx, uid = int(parts[1]), int(parts[2])
    except ValueError:
        await message.answer("شماره فرقه و آیدی باید عدد باشند.")
        return
    if idx not in range(1, 6):
        await message.answer("شماره فرقه باید ۱ تا ۵ باشد.")
        return
    data = ensure_holy_sects()
    data[str(idx)]["controller_id"] = uid
    save("holy_sects")
    await message.answer(f"✅ کنترل «{data[str(idx)]['name']}» به بازیکن {uid} سپرده شد.")

@router.message(Command("sectwar", "جنگ_فرقه", "جنگفرقه"))
async def sect_war(message: Message):
    parts = (message.text or "").split()
    async with async_session() as session:
        user = await get_or_create_user(session, message.from_user.id, message.from_user.full_name, message.from_user.username)
        mem = await _member(session, user)
        if not mem:
            await message.answer("برای جنگ باید عضو یک فرقه باشی.")
            return
        if len(parts) < 2:
            await message.answer("فرمت: /sectwar آیدی_فرقه\nجنگ پس از ۵ دقیقه آماده‌سازی شروع می‌شود و حداقل ۳ ساعت ادامه دارد.")
            return
        try: target_id = int(parts[1])
        except ValueError:
            await message.answer("آیدی فرقه باید عدد باشد.")
            return
        attacker = await _sect(session, mem.sect_id)
        defender = await _sect(session, target_id)
        if not attacker or not defender or attacker.id == defender.id:
            await message.answer("فرقه هدف معتبر نیست.")
            return
        w, err = await _start_war(session, attacker, defender, user.id)
        if err:
            await message.answer("⚔️ " + err)
            return
        await message.answer(
            f"⚔️ <b>اعلام جنگ!</b>\n{attacker.name} → {defender.name}\n"
            f"🛡 آماده‌سازی: ۵ دقیقه\n⏱ مدت نبرد: ۳ ساعت\n"
            f"🔥 بعد از شروع، حمله‌ها با فاصله حداقل ۱۰ ثانیه قابل ثبت‌اند.\n"
            f"🆔 شناسه جنگ: <code>{w['id']}</code>"
        )

@router.message(Command("warattack", "حمله_جنگ", "حملهجنگ"))
async def war_attack(message: Message):
    parts = (message.text or "").split()
    if len(parts) < 2:
        await message.answer("فرمت: /warattack شناسه_جنگ")
        return
    try: wid = str(int(parts[1]))
    except ValueError:
        await message.answer("شناسه جنگ باید عدد باشد.")
        return
    wars = _wars()
    w = wars.get(wid)
    if not w:
        await message.answer("جنگ پیدا نشد.")
        return
    _refresh(w)
    if w["status"] != "active":
        _save()
        await message.answer("جنگ هنوز شروع نشده یا تمام شده است.")
        return
    member_side = None
    async with async_session() as session:
        user = await get_or_create_user(session, message.from_user.id, message.from_user.full_name, message.from_user.username)
        mem = await _member(session, user)
        if not mem:
            await message.answer("عضو هیچ‌یک از دو فرقه نیستی.")
            return
        if mem.sect_id == int(w["attacker_id"]): member_side = "attacker"
        elif mem.sect_id == int(w["defender_id"]): member_side = "defender"
        else:
            await message.answer("فقط اعضای دو فرقه درگیر می‌توانند بجنگند.")
            return
        last = _dt(w.get("last_attack"))
        if last and (_now()-last).total_seconds() < ATTACK_COOLDOWN_SECONDS:
            await message.answer("⏳ هنوز فرصت حمله بعدی نرسیده؛ حداقل فاصله ۱۰ ثانیه است.")
            return
        sect = await _sect(session, mem.sect_id)
        base = await _sect_power(session, sect)
        roll = max(1, int(base * random.uniform(0.85, 1.15)))
    w["last_attack"] = _now().isoformat()
    w[f"{member_side}_score"] = int(w.get(f"{member_side}_score", 0)) + roll
    _save()
    await message.answer(f"⚔️ حمله ثبت شد! قدرت این ضربه: {roll:,}\nامتیاز شما: {w[member_side+'_score']:,}")

@router.message(Command("warclaim", "جایزهجنگ", "جایزه_جنگ"))
async def war_claim(message: Message):
    parts = (message.text or "").split()
    if len(parts) < 2:
        await message.answer("فرمت: /warclaim شناسه_جنگ")
        return
    try: wid = str(int(parts[1]))
    except ValueError:
        await message.answer("شناسه جنگ باید عدد باشد.")
        return
    wars = _wars(); w = wars.get(wid)
    if not w:
        await message.answer("جنگ پیدا نشد.")
        return
    _refresh(w)
    if w.get("status") != "finished":
        await message.answer("🏁 این جنگ هنوز تمام نشده.")
        return
    if w.get("reward_claimed"):
        await message.answer("🎁 جایزه این جنگ قبلاً دریافت شده.")
        return
    winner_side = w.get("winner")
    if winner_side == "draw":
        await message.answer("⚖️ جنگ مساوی شد؛ جایزه اصلی تقسیم نشده باقی می‌ماند.")
        return
    winner_id = int(w["attacker_id"] if winner_side == "attacker" else w["defender_id"])
    # برای جنگ فرقه‌ای، اعضای پیروز پاداش صندوق و پیشرفت شاخه می‌گیرند.
    async with async_session() as session:
        user = await get_or_create_user(session, message.from_user.id, message.from_user.full_name, message.from_user.username)
        if w.get("kind") == "player":
            if user.id != winner_id:
                await message.answer("فقط برنده جنگ می‌تواند جایزه را دریافت کند.")
                return
            from services.economy import add_coins
            coins = 5000
            await add_coins(session, user.id, coins)
            w["reward_claimed"] = True
            _save()
            await message.answer(f"🏆 جایزه جنگ بازیکنی: +{coins:,} سکه")
            return
        mem = await _member(session, user)
        if not mem or mem.sect_id != winner_id:
            await message.answer("فقط اعضای فرقه پیروز می‌توانند جایزه بگیرند.")
            return
        from services.economy import add_coins
        await add_coins(session, user.id, 1500)
        holy = ensure_holy_sects()
        # اگر برنده یکی از پنج فرقه مقدس باشد، کنترل شاخه/رتبه مقدس تقویت می‌شود.
        for x in holy.values():
            if x.get("controller_id") == user.telegram_id:
                x["branch_control"] = int(x.get("branch_control", 0)) + 1
        save("holy_sects")
        w["reward_claimed"] = True
        _save()
        await message.answer("🏆 جایزه جنگ: +۱٬۵۰۰ سکه + یک امتیاز کنترل شاخه فرقه.\n🌱 پاداش پیشرفت جنگی ثبت شد.")

@router.message(Command("warstatus", "وضعیتجنگ", "وضعیت_جنگ"))
async def war_status(message: Message):
    wars = _wars()
    if not wars:
        await message.answer("🌍 هیچ جنگی ثبت نشده.")
        return
    lines = ["⚔️ <b>جنگ‌های فعال</b>"]
    for w in list(wars.values())[-10:]:
        _refresh(w)
        end = _dt(w.get("end")) or _now()
        lines.append(
            f"#{w['id']} | {w['attacker_id']} ⚔️ {w['defender_id']} | {w['status']}\n"
            f"   امتیاز: {w['attacker_score']:,} - {w['defender_score']:,} | باقی: {_war_duration_text(end)}"
        )
    _save()
    await message.answer("\n".join(lines))

@router.message(Command("playerwar", "جنگ_بازیکنان", "جنگبازیکنان"))
async def player_war(message: Message):
    if not message.reply_to_message or not message.reply_to_message.from_user:
        await message.answer("برای جنگ بازیکنان، روی پیام بازیکن هدف ریپلای کن و /playerwar بزن.")
        return
    target_id = message.reply_to_message.from_user.id
    if target_id == message.from_user.id:
        await message.answer("نمی‌توانی با خودت وارد جنگ شوی.")
        return
    # جنگ بازیکنان مستقل از فرقه است و همان ۵ دقیقه آماده‌سازی/۳ ساعت نبرد را دارد.
    a = type("PlayerSide", (), {"id": message.from_user.id})()
    d = type("PlayerSide", (), {"id": target_id})()
    wars = _wars()
    now = _now()
    for w in wars.values():
        if w.get("kind") == "player" and w.get("status") in ("preparing", "active") and (
            message.from_user.id in (int(w["attacker_id"]), int(w["defender_id"]))
            or target_id in (int(w["attacker_id"]), int(w["defender_id"]))
        ):
            await message.answer("یکی از بازیکنان همین حالا در یک جنگ بازیکنی است.")
            return
    wid = str(max([int(x) for x in wars.keys() if str(x).isdigit()] + [0]) + 1)
    prep = now + timedelta(minutes=5); end = prep + timedelta(hours=3)
    wars[wid] = {
        "id": int(wid), "kind": "player", "attacker_id": a.id, "defender_id": d.id,
        "creator_id": a.id, "status": "preparing", "created_at": now.isoformat(),
        "prep_end": prep.isoformat(), "end": end.isoformat(), "last_attack": None,
        "attacker_score": 0, "defender_score": 0, "winner": None, "reward_claimed": False,
    }
    _save()
    await message.answer(f"⚔️ جنگ بازیکنی #{wid} ایجاد شد.\nآماده‌سازی: ۵ دقیقه | مدت: ۳ ساعت\nهر دو نفر با /warattack {wid} می‌توانند وارد نبرد شوند.")

@router.message(Command("warhelp", "راهنمایجنگ"))
async def war_help(message: Message):
    await message.answer(
        "⚔️ <b>سیستم جنگ جدید</b>\n\n"
        "/holysects — پنج فرقه مقدس و مسیرهایشان\n"
        "/sectwar آیدی — اعلام جنگ فرقه‌ای\n"
        "/warattack شناسه — ثبت حمله\n"
        "/warstatus — وضعیت جنگ‌ها\n"
        "ریپلای به بازیکن + /playerwar — جنگ آزاد بازیکنان\n\n"
        "🕔 هر جنگ ۵ دقیقه آماده‌سازی دارد.\n"
        "⏱ مدت پایه هر جنگ ۳ ساعت است.\n"
        "🏆 نتیجه بر اساس امتیاز حمله تعیین می‌شود.\n"
        "👑 مقام‌های فرقه: رهبر، دختر مقدس، پسر مقدس، فرمانده جنگ، ارشد."
    )
