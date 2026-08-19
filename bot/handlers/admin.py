from datetime import datetime, timedelta
from aiogram import Router, F
from aiogram.types import Message
from aiogram.filters import Command
from bot.config import ADMIN_IDS
from database.engine import async_session
from database.crud import get_user_by_telegram_id, get_or_create_user
from database.models import (
    User, ROLE_LEADER, ROLE_DEPUTY, ROLE_ARJOMAND, ROLE_SENIOR, ROLE_MEMBER
)
from services.ranking import promote, demote, RANKS
from services.roles import can_restrict, can_promote_demote, can_set_deputy, can_ban, can_manage
from services.i18n import tr

router = Router()


def is_config_admin(user_id: int) -> bool:
    return user_id in ADMIN_IDS


def _staff_ok(user_id: int, min_rank: str) -> bool:
    from services.staff import has_perm
    return has_perm(user_id, min_rank)


@router.message(Command("admin"))
async def cmd_admin(message: Message):
    async with async_session() as session:
        user = await get_or_create_user(
            session,
            telegram_id=message.from_user.id,
            full_name=message.from_user.full_name,
            username=message.from_user.username
        )

    from services.staff import has_perm, PERM_DIAG, get_staff, staff_help_text
    if not has_perm(message.from_user.id, PERM_DIAG):
        await message.answer("⛔️ پنل مدیریت برای مقام ویژه و بالاتر است.")
        return

    text = (
        "🛠 <b>پنل مدیریت</b>\n\n"
        "<b>دستورات نقشها:</b>\n"
        "/setrole آیدی نقش\n"
        "نقشها: رهبر | معاون رهبر | ارجمند | ارشد | عضو\n\n"
        "<b>محدود کردن:</b>\n"
        "/restrict &lt;telegram_id&gt; &lt;دقیقه&gt; [دلیل]\n"
        "/unrestrict &lt;telegram_id&gt;\n\n"
        "<b>رتبه:</b>\n"
        "/promote &lt;telegram_id&gt;\n"
        "/demote &lt;telegram_id&gt;\n\n"
        "<b>دیگر:</b>\n"
        "/ban &lt;telegram_id&gt;\n"
        "/unban آیدی"
    )
    await message.answer(text)


@router.message(Command("setrole"))
async def cmd_setrole(message: Message):
    async with async_session() as session:
        actor = await get_or_create_user(
            session, message.from_user.id,
            message.from_user.full_name, message.from_user.username
        )

        if not (is_config_admin(message.from_user.id) or actor.role == ROLE_LEADER):
            await message.answer(tr(message.from_user.id, "⛔️ فقط رهبر میتونه نقش تعیین کنه."))
            return

        parts = message.text.split(maxsplit=2)
        if len(parts) < 3:
            await message.answer(tr(message.from_user.id, "فرمت: /setrole آیدی نقش"))
            return

        try:
            tg_id = int(parts[1])
        except ValueError:
            await message.answer(tr(message.from_user.id, "آیدی باید عدد باشد."))
            return

        role_name = parts[2].strip()
        valid_roles = [ROLE_LEADER, ROLE_DEPUTY, ROLE_ARJOMAND, ROLE_SENIOR, ROLE_MEMBER]
        if role_name not in valid_roles:
            await message.answer(f"نقش معتبر نیست.\nنقشهای مجاز:\n" + "\n".join(valid_roles))
            return

        target = await get_user_by_telegram_id(session, tg_id)
        if not target:
            await message.answer(tr(message.from_user.id, "کاربر پیدا نشد."))
            return

        target.role = role_name
        await session.commit()
        await message.answer(f"✅ نقش {target.full_name} به «{role_name}» تغییر کرد.")


@router.message(Command("restrict"))
async def cmd_restrict(message: Message):
    async with async_session() as session:
        actor = await get_or_create_user(
            session, message.from_user.id,
            message.from_user.full_name, message.from_user.username
        )

        from services.staff import has_perm, PERM_RESTRICT
        if not can_restrict(actor) and not has_perm(message.from_user.id, PERM_RESTRICT):
            await message.answer(tr(message.from_user.id, "⛔️ دسترسی نداری."))
            return

        parts = message.text.split()
        if len(parts) < 3:
            await message.answer(tr(message.from_user.id, "فرمت: /restrict &lt;telegram_id&gt; &lt;دقیقه&gt; [دلیل]"))
            return

        try:
            tg_id = int(parts[1])
            minutes = int(parts[2])
        except ValueError:
            await message.answer(tr(message.from_user.id, "آیدی و دقیقه باید عدد باشند."))
            return

        reason = " ".join(parts[3:]) if len(parts) > 3 else "بدون دلیل"

        target = await get_user_by_telegram_id(session, tg_id)
        if not target:
            await message.answer(tr(message.from_user.id, "کاربر پیدا نشد."))
            return

        if not can_manage(actor, target) and not is_config_admin(message.from_user.id):
            await message.answer(tr(message.from_user.id, "⛔️ نمیتونی این کاربر رو محدود کنی."))
            return

        target.restricted_until = datetime.utcnow() + timedelta(minutes=minutes)
        target.restriction_reason = reason
        await session.commit()

        await message.answer(
            f"🔇 {target.full_name} به مدت {minutes} دقیقه محدود شد.\n"
            f"دلیل: {reason}"
        )


@router.message(Command("unrestrict"))
async def cmd_unrestrict(message: Message):
    async with async_session() as session:
        actor = await get_or_create_user(
            session, message.from_user.id,
            message.from_user.full_name, message.from_user.username
        )

        from services.staff import has_perm, PERM_RESTRICT
        if not can_restrict(actor) and not has_perm(message.from_user.id, PERM_RESTRICT):
            await message.answer(tr(message.from_user.id, "⛔️ دسترسی نداری."))
            return

        parts = message.text.split()
        if len(parts) < 2:
            await message.answer(tr(message.from_user.id, "فرمت: /unrestrict &lt;telegram_id&gt;"))
            return

        try:
            tg_id = int(parts[1])
        except ValueError:
            await message.answer(tr(message.from_user.id, "آیدی باید عدد باشد."))
            return

        target = await get_user_by_telegram_id(session, tg_id)
        if not target:
            await message.answer(tr(message.from_user.id, "کاربر پیدا نشد."))
            return

        target.restricted_until = None
        target.restriction_reason = None
        await session.commit()
        await message.answer(f"✅ محدودیت {target.full_name} برداشته شد.")


@router.message(Command("promote"))
async def cmd_promote(message: Message):
    async with async_session() as session:
        actor = await get_or_create_user(
            session, message.from_user.id,
            message.from_user.full_name, message.from_user.username
        )

        from services.staff import has_perm, PERM_PROMOTE_RANK
        if not can_promote_demote(actor) and not has_perm(message.from_user.id, PERM_PROMOTE_RANK):
            await message.answer(tr(message.from_user.id, "⛔️ دسترسی نداری."))
            return

        parts = message.text.split()
        if len(parts) < 2:
            await message.answer(tr(message.from_user.id, "فرمت: /promote &lt;telegram_id&gt;"))
            return

        try:
            tg_id = int(parts[1])
        except ValueError:
            await message.answer(tr(message.from_user.id, "آیدی باید عدد باشد."))
            return

        user = await get_user_by_telegram_id(session, tg_id)
        if not user:
            await message.answer(tr(message.from_user.id, "کاربر پیدا نشد."))
            return

        new_rank = promote(user)
        await session.commit()
        if new_rank:
            await message.answer(f"✅ {user.full_name} به «{new_rank}» ارتقا یافت.")
        else:
            await message.answer(tr(message.from_user.id, "کاربر در بالاترین رتبه است."))


@router.message(Command("demote"))
async def cmd_demote(message: Message):
    async with async_session() as session:
        actor = await get_or_create_user(
            session, message.from_user.id,
            message.from_user.full_name, message.from_user.username
        )

        from services.staff import has_perm, PERM_PROMOTE_RANK
        if not can_promote_demote(actor) and not has_perm(message.from_user.id, PERM_PROMOTE_RANK):
            await message.answer(tr(message.from_user.id, "⛔️ دسترسی نداری."))
            return

        parts = message.text.split()
        if len(parts) < 2:
            await message.answer(tr(message.from_user.id, "فرمت: /demote &lt;telegram_id&gt;"))
            return

        try:
            tg_id = int(parts[1])
        except ValueError:
            await message.answer(tr(message.from_user.id, "آیدی باید عدد باشد."))
            return

        user = await get_user_by_telegram_id(session, tg_id)
        if not user:
            await message.answer(tr(message.from_user.id, "کاربر پیدا نشد."))
            return

        new_rank = demote(user)
        await session.commit()
        if new_rank:
            await message.answer(f"✅ {user.full_name} به «{new_rank}» تنزل یافت.")
        else:
            await message.answer(tr(message.from_user.id, "کاربر در پایینترین رتبه است."))


@router.message(Command("setcult", "تنظیمتذهیب"))
async def cmd_set_cult(message: Message):
    """سازنده: تنظیم تذهیب در هر قلمرو، از ابتدایی تا بالاترین قلمروهای تعریفشده.
    فرمت: /setcult ID قلمرو مرحله [انرژی] یا ریپلای + /setcult قلمرو مرحله [انرژی]
    قلمرو میتواند نام کامل یا شماره آن در فهرست قلمروها باشد؛ مرحله تا ۱۵ است.
    """
    from services.staff import has_perm, PERM_SETCULT
    if not has_perm(message.from_user.id, PERM_SETCULT):
        await message.answer("⛔️ نیاز به مقام ادمین یا بالاتر.")
        return
    from database.models_v2 import CULTIVATION_REALMS
    from services.cultivation import get_or_create_cultivation
    parts = (message.text or "").split()
    async with async_session() as session:
        target = None
        if message.reply_to_message:
            t = message.reply_to_message.from_user
            target = await get_or_create_user(session, t.id, t.full_name, t.username)
            args = parts[1:]
        elif len(parts) >= 4:
            try:
                tg = int(parts[1])
            except ValueError:
                await message.answer(tr(message.from_user.id, "فرمت: ریپلای+/setcult قلمرو مرحله [انرژی]\nیا /setcult telegram_id قلمرو مرحله [انرژی]"))
                return
            target = await get_user_by_telegram_id(session, tg)
            if not target:
                target = await get_or_create_user(session, tg, str(tg), None)
            args = parts[2:]
        else:
            await message.answer(
                "فرمت:\nریپلای + /setcult قلمرو مرحله [انرژی]\n"
                "یا /setcult telegram_id قلمرو مرحله [انرژی]\n"
                f"قلمروها: 1 تا {len(CULTIVATION_REALMS)} (نام کامل یا شماره)"
            )
            return
        if len(args) < 2:
            await message.answer(tr(message.from_user.id, "قلمرو و مرحله لازم است."))
            return

        # برای قلمروهای خیلی بالا، نام میتواند چندکلمهای باشد.
        # قالب را از انتها میخوانیم: آخرین عدد = مرحله و عدد بعدی = انرژی.
        try:
            stage = int(args[-1])
            energy = 0
            realm_parts = args[:-1]
            if realm_parts and realm_parts[-1].lstrip("+-").isdigit():
                energy = int(realm_parts[-1])
                realm_parts = realm_parts[:-1]
            realm_raw = " ".join(realm_parts).strip()
        except ValueError:
            await message.answer(tr(message.from_user.id, "مرحله باید عدد باشد. مثال: /setcult آسمانیاعظم 15 1000000000000"))
            return

        # شماره قلمرو نیز پشتیبانی میشود؛ برای دادن سریع قلمروهای بسیار بالا.
        realm = None
        if realm_raw.lstrip("+-").isdigit():
            idx = int(realm_raw) - 1
            if 0 <= idx < len(CULTIVATION_REALMS):
                realm = CULTIVATION_REALMS[idx]
        else:
            realm = next((r for r in CULTIVATION_REALMS if r == realm_raw), None)
            if realm is None:
                # تطبیق منعطف برای فاصله/نیمفاصله
                norm = realm_raw.replace(" ", "").replace("‌", "")
                realm = next((r for r in CULTIVATION_REALMS if r.replace(" ", "").replace("‌", "") == norm), None)

        if realm is None:
            await message.answer(
                "❌ قلمرو نامعتبر.\n"
                f"شماره قلمرو را هم میتوانی بدهی: 1 تا {len(CULTIVATION_REALMS)}\n"
                "مثال: /setcult 60 15 1000000000000"
            )
            return
        if not 1 <= stage <= 15:
            await message.answer("❌ مرحله باید بین 1 تا 15 باشد.")
            return
        if energy < 0:
            await message.answer("❌ انرژی نمیتواند منفی باشد.")
            return

        cult = await get_or_create_cultivation(session, target.id)
        cult.realm = realm
        cult.stage = stage
        cult.energy = energy
        await session.commit()
    await message.answer(
        f"✅ تذهیب {target.full_name}:\nقلمرو {realm} | مرحله {stage} | انرژی {energy}"
    )


@router.message(Command("givemoney", "بدهپول"))
async def cmd_give_money(message: Message):
    from services.staff import has_perm, PERM_GIVEMONEY, check_money_amount, money_limit
    if not has_perm(message.from_user.id, PERM_GIVEMONEY):
        await message.answer(
            "⛔️ نیاز به مقام مدیر یا بالاتر.\n"
            f"سقف پول‌دهی مقام تو: {money_limit(message.from_user.id):,}"
        )
        return
    from services.economy import get_or_create_wallet
    parts = (message.text or "").split()
    # /givemoney coins 100  یا ریپلای
    async with async_session() as session:
        if message.reply_to_message:
            t = message.reply_to_message.from_user
            target = await get_or_create_user(session, t.id, t.full_name, t.username)
            args = parts[1:]
        elif len(parts) >= 4:
            target = await get_user_by_telegram_id(session, int(parts[1]))
            if not target:
                await message.answer(tr(message.from_user.id, "کاربر پیدا نشد."))
                return
            args = parts[2:]
        else:
            await message.answer(
                "فرمت: ریپلای + /givemoney نوع مقدار\n"
                "نوع: coins | spirit | heavenly | celestial | god\n"
                "یا /givemoney telegram_id نوع مقدار"
            )
            return
        if len(args) < 2:
            await message.answer(tr(message.from_user.id, "نوع و مقدار لازم است."))
            return
        kind, amount = args[0], int(args[1])
        ok_lim, lim_msg = check_money_amount(message.from_user.id, amount)
        if not ok_lim:
            await message.answer(lim_msg)
            return
        w = await get_or_create_wallet(session, target.id)
        money_fields = {
            "coins": "coins", "سکه": "coins",
            "spirit": "spirit_stones", "روحی": "spirit_stones",
            "heavenly": "heavenly_stones", "بهشتی": "heavenly_stones",
            "celestial": "celestial_stones", "آسمانی": "celestial_stones",
            "god": "god_stones", "خدا": "god_stones",
            "chaos": "chaos_stones", "هرجومرج": "chaos_stones",
            "void": "void_stones", "پوچی": "void_stones",
            "origin": "origin_stones", "ازلی": "origin_stones",
            "destiny": "destiny_stones", "تقدیر": "destiny_stones",
            "immortal": "immortal_stones", "جاودان": "immortal_stones",
            "creation": "creation_stones", "خلقت": "creation_stones",
            "absolute": "absolute_stones", "مطلق": "absolute_stones",
            "faith": "faith_stones", "ایمان": "faith_stones",
            "dragon": "dragon_coins", "اژدها": "dragon_coins",
            "karma": "karma_points", "کارما": "karma_points",
        }
        field = money_fields.get(kind)
        if not field:
            await message.answer(tr(message.from_user.id, "نوع نامعتبر"))
            return
        setattr(w, field, int(getattr(w, field, 0) or 0) + amount)
        if field == "coins":
            pass
        else:
            pass
        await session.commit()
    await message.answer(f"✅ به {target.full_name}: +{amount} {kind}")


@router.message(Command("takemoney", "بگیرپول"))
async def cmd_take_money(message: Message):
    from services.staff import has_perm, PERM_GIVEMONEY, check_money_amount, money_limit
    if not has_perm(message.from_user.id, PERM_GIVEMONEY):
        await message.answer(
            "⛔️ نیاز به مقام مدیر یا بالاتر.\n"
            f"سقف پول‌دهی مقام تو: {money_limit(message.from_user.id):,}"
        )
        return
    from services.economy import get_or_create_wallet
    parts = (message.text or "").split()
    async with async_session() as session:
        if message.reply_to_message:
            t = message.reply_to_message.from_user
            target = await get_or_create_user(session, t.id, t.full_name, t.username)
            args = parts[1:]
        elif len(parts) >= 4:
            target = await get_user_by_telegram_id(session, int(parts[1]))
            args = parts[2:]
        else:
            await message.answer(tr(message.from_user.id, "مثل /givemoney ولی کم میکند."))
            return
        if not target or len(args) < 2:
            await message.answer(tr(message.from_user.id, "ناقص"))
            return
        kind, amount = args[0], int(args[1])
        w = await get_or_create_wallet(session, target.id)
        if kind in ("coins", "سکه"):
            w.coins = max(0, w.coins - amount)
        elif kind in ("spirit", "روحی"):
            w.spirit_stones = max(0, w.spirit_stones - amount)
        elif kind in ("heavenly", "بهشتی"):
            w.heavenly_stones = max(0, (w.heavenly_stones or 0) - amount)
        elif kind in ("celestial", "آسمانی"):
            w.celestial_stones = max(0, (w.celestial_stones or 0) - amount)
        elif kind in ("god", "خدا"):
            w.god_stones = max(0, (w.god_stones or 0) - amount)
        await session.commit()
    await message.answer(f"✅ از {target.full_name}: −{amount} {kind}")



@router.message(Command("ban"))
async def cmd_ban(message: Message):
    from services.staff import has_perm, PERM_BAN
    if not has_perm(message.from_user.id, PERM_BAN):
        await message.answer("⛔️ نیاز به مقام معاون ادمین یا بالاتر.")
        return
    parts = (message.text or "").split()
    async with async_session() as session:
        if message.reply_to_message:
            t = message.reply_to_message.from_user
            target = await get_or_create_user(session, t.id, t.full_name, t.username)
        elif len(parts) >= 2:
            try:
                target = await get_user_by_telegram_id(session, int(parts[1]))
            except ValueError:
                await message.answer(tr(message.from_user.id, "آیدی عدد باشد."))
                return
        else:
            await message.answer(tr(message.from_user.id, "فرمت: /ban آیدی  یا ریپلای + /ban"))
            return
        if not target:
            await message.answer(tr(message.from_user.id, "کاربر پیدا نشد."))
            return
        target.is_banned = True
        target.is_active = False
        await session.commit()
    await message.answer(f"🚫 بن شد: {target.full_name}")


@router.message(Command("unban"))
async def cmd_unban(message: Message):
    from services.staff import has_perm, PERM_BAN
    if not has_perm(message.from_user.id, PERM_BAN):
        await message.answer("⛔️ نیاز به مقام معاون ادمین یا بالاتر.")
        return
    parts = (message.text or "").split()
    async with async_session() as session:
        if message.reply_to_message:
            t = message.reply_to_message.from_user
            target = await get_or_create_user(session, t.id, t.full_name, t.username)
        elif len(parts) >= 2:
            try:
                target = await get_user_by_telegram_id(session, int(parts[1]))
            except ValueError:
                await message.answer(tr(message.from_user.id, "آیدی عدد باشد."))
                return
        else:
            await message.answer(tr(message.from_user.id, "فرمت: /unban آیدی  یا ریپلای + /unban"))
            return
        if not target:
            await message.answer(tr(message.from_user.id, "کاربر پیدا نشد."))
            return
        target.is_banned = False
        target.is_active = True
        await session.commit()
    await message.answer(f"✅ آنبن شد: {target.full_name}")


@router.message(Command("unlockconsume", "بازقفلمصرف"))
async def cmd_unlock_consume(message: Message):
    """ادمین: برداشتن قفل مصرف برای خود یا آیدی"""
    from bot.config import ADMIN_IDS
    if message.from_user.id not in ADMIN_IDS:
        await message.answer("فقط ادمین.")
        return
    parts = (message.text or "").split()
    tg = message.from_user.id
    if len(parts) >= 2:
        try:
            tg = int(parts[1])
        except ValueError:
            await message.answer("آیدی نامعتبر")
            return
    from services.forbidden_lock import unlock_consume
    unlock_consume(tg)
    # حذف تکنیک ممنوعه از DB اگر خواست
    try:
        async with async_session() as session:
            from database.crud import get_user_by_telegram_id
            from services.cultivation import FORBIDDEN_TECH_NAME
            from database.models_v3 import UserTechnique, CultivationTechnique
            from sqlalchemy import select, delete
            u = await get_user_by_telegram_id(session, tg)
            if u:
                r = await session.execute(
                    select(CultivationTechnique.id).where(CultivationTechnique.name == FORBIDDEN_TECH_NAME)
                )
                tid = r.scalar_one_or_none()
                if tid:
                    await session.execute(
                        delete(UserTechnique).where(
                            UserTechnique.user_id == u.id,
                            UserTechnique.technique_id == tid,
                        )
                    )
                from database.models_v2 import Cultivation
                cr = await session.execute(select(Cultivation).where(Cultivation.user_id == u.id))
                cult = cr.scalar_one_or_none()
                if cult and cult.talent in ("forbidden_ready", "forbidden_used"):
                    cult.talent = None
                await session.commit()
    except Exception as e:
        await message.answer(f"قفل حافظه برداشته شد؛ DB: {type(e).__name__}")
        return
    await message.answer(f"✅ قفل مصرف برای {tg} برداشته شد (حافظه + تکنیک ممنوعه DB).")



@router.message(Command("givepower", "قدرتبده", "setpower"))
async def cmd_give_power(message: Message):
    """ادمین: /givepower telegram_id مقدار [total|power|speed|defense|body]"""
    from services.staff import has_perm, PERM_GIVEMONEY
    if not has_perm(message.from_user.id, PERM_GIVEMONEY):
        await message.answer("⛔️ نیاز به مقام ادمین یا بالاتر.")
        return
    parts = (message.text or "").split()
    if len(parts) < 3:
        await message.answer(
            "فرمت: /givepower TELEGRAM_ID مقدار [total|power|speed|defense|body]\n"
            "مثال: /givepower 6227792513 1000 power\n"
            "یا ریپلای + /givepower 500 body"
        )
        return
    kind = "total"
    try:
        if message.reply_to_message and message.reply_to_message.from_user:
            tid = message.reply_to_message.from_user.id
            amount = int(parts[1])
            if len(parts) >= 3:
                kind = parts[2]
        else:
            tid = int(parts[1])
            amount = int(parts[2])
            if len(parts) >= 4:
                kind = parts[3]
    except ValueError:
        await message.answer("آیدی و مقدار باید عدد باشند.")
        return
    kind = kind.lower()
    if kind in ("body", "بدن"):
        try:
            from services.body_cult import add_body_power
            msg = add_body_power(tid, amount)
        except Exception:
            from services.persist import get_dict, save
            d = get_dict("body_cult")
            sk = str(tid)
            row = d.get(sk) or {"techs": {}, "total_power": 0}
            row["total_power"] = int(row.get("total_power") or 0) + amount
            d[sk] = row
            save("body_cult")
            msg = f"✅ قدرت بدن +{amount} برای `{tid}` (کل: {row['total_power']})"
    else:
        if kind in ("total", "کل", "profile", "قدرت_پروفایل"):
            from services.knowledge import add_admin_power_bonus
            new_total = add_admin_power_bonus(tid, amount)
            msg = f"✅ قدرت مستقیم پروفایل {tid}: +{amount}\nقدرت اعطایی فعلی: {new_total}"
        else:
            from services.knowledge import add_combat_stat
            mapk = {"power": "power", "قدرت": "power", "speed": "speed", "defense": "defense", "دفاع": "defense", "سرعت": "speed"}
            k = mapk.get(kind, "power")
            msg = add_combat_stat(tid, k, amount) + f"\nهدف: `{tid}`"
    await message.answer(msg)


@router.message(Command("transfercult", "انتقالتذهیب", "کپیتذهیب"))
async def cmd_transfer_cult(message: Message):
    """سازنده: انتقال کامل تذهیب یک کاربر به کاربر دیگر؛ مناسب قلمروهای بسیار بالا."""
    from services.staff import has_perm, PERM_SETCULT, is_creator
    if not is_creator(message.from_user.id):
        await message.answer("⛔️ فقط سازنده ربات.")
        return
    parts = (message.text or "").split()
    try:
        if message.reply_to_message:
            # /transfercult SOURCE_ID روی پیام مقصد ریپلای
            if len(parts) < 2:
                await message.answer("فرمت: روی مقصد ریپلای کن و /transfercult SOURCE_TELEGRAM_ID بزن.")
                return
            source_tg = int(parts[1])
            target_tg = message.reply_to_message.from_user.id
        elif len(parts) >= 3:
            source_tg = int(parts[1]); target_tg = int(parts[2])
        else:
            await message.answer("فرمت: /transfercult SOURCE_TELEGRAM_ID TARGET_TELEGRAM_ID\nیا روی مقصد ریپلای + /transfercult SOURCE_TELEGRAM_ID")
            return
    except ValueError:
        await message.answer("هر دو آیدی باید عدد باشند.")
        return
    if source_tg == target_tg:
        await message.answer("مبدأ و مقصد نمیتوانند یکی باشند.")
        return
    from database.models_v2 import Cultivation
    from services.cultivation import get_or_create_cultivation
    async with async_session() as session:
        source = await get_user_by_telegram_id(session, source_tg)
        target = await get_user_by_telegram_id(session, target_tg)
        if not source or not target:
            await message.answer("مبدأ یا مقصد پیدا نشد.")
            return
        sc = await get_or_create_cultivation(session, source.id)
        tc = await get_or_create_cultivation(session, target.id)
        tc.realm = sc.realm
        tc.stage = sc.stage
        tc.energy = sc.energy
        tc.talent = sc.talent
        tc.spiritual_root = sc.spiritual_root
        tc.body_type = sc.body_type
        await session.commit()
    await message.answer(
        f"✅ تذهیب منتقل شد.\n\n"
        f"مبدأ: {source.full_name}\n"
        f"مقصد: {target.full_name}\n"
        f"🧘 {tc.realm} — مرحله {tc.stage}\n"
        f"⚡ انرژی: {tc.energy}\n"
        f"🌱 ریشه: {tc.spiritual_root or 'بدون ریشه'}"
    )


@router.message(Command("diag", "تشخیص", "debugbot"))
async def cmd_diag(message: Message):
    """تشخیص سریع سیستمها برای ادمین"""
    from services.staff import has_perm, PERM_DIAG
    if not has_perm(message.from_user.id, PERM_DIAG):
        await message.answer("⛔️ نیاز به مقام ویژه یا بالاتر.")
        return
    lines = ["🔧 <b>تشخیص ربات</b>", ""]
    checks = []
    try:
        from services.servants import list_owned, market_list
        bag = list_owned(message.from_user.id)
        checks.append(f"خدمتکار: OK (مالکیت تو: {len(bag)})")
    except Exception as e:
        checks.append(f"خدمتکار: ❌ {type(e).__name__}: {e}")
    try:
        from services.shop import ensure_default_buildings_and_items, get_buildings
        from database.engine import async_session
        async with async_session() as session:
            await ensure_default_buildings_and_items(session)
            b = await get_buildings(session)
            checks.append(f"مغازه: OK ({len(b)} ساختمان)")
    except Exception as e:
        checks.append(f"مغازه: ❌ {type(e).__name__}: {e}")
    try:
        from services.jobs import get_job, list_jobs
        checks.append(f"شغل: OK (فعلی: {get_job(message.from_user.id) or '—'})")
    except Exception as e:
        checks.append(f"شغل: ❌ {type(e).__name__}: {e}")
    try:
        from services.crafting import ensure_default_recipes
        from database.engine import async_session
        from database.models_v3 import Recipe
        from sqlalchemy import select
        async with async_session() as session:
            await ensure_default_recipes(session)
            r = await session.execute(select(Recipe))
            checks.append(f"کیمیاگری: OK ({len(list(r.scalars().all()))} دستور)")
    except Exception as e:
        checks.append(f"کیمیاگری: ❌ {type(e).__name__}: {e}")
    try:
        from services.economy import get_or_create_wallet
        from database.engine import async_session
        from database.crud import get_or_create_user
        async with async_session() as session:
            u = await get_or_create_user(session, message.from_user.id, message.from_user.full_name, message.from_user.username)
            w = await get_or_create_wallet(session, u.id)
            checks.append(f"کیف: OK سکه={w.coins}")
    except Exception as e:
        checks.append(f"کیف: ❌ {type(e).__name__}: {e}")
    try:
        from services.achievements import list_user
        checks.append("دستاورد: OK")
    except Exception as e:
        checks.append(f"دستاورد: ❌ {type(e).__name__}: {e}")
    lines.extend(checks)
    lines.append("\n/version /help /buildings /servants /jobs /craft")
    await message.answer(chr(10).join(lines))


@router.message(Command("immortal", "نامیرا", "setimmortal"))
async def cmd_set_immortal(message: Message):
    """ادمین: /immortal TELEGRAM_ID  یا ریپلای + /immortal"""
    from services.staff import has_perm, PERM_IMMORTAL
    if not has_perm(message.from_user.id, PERM_IMMORTAL):
        await message.answer("⛔️ نیاز به مقام ادمین یا بالاتر.")
        return
    from services.immortal import set_immortal, list_immortals
    parts = (message.text or "").split()
    tid = None
    if message.reply_to_message and message.reply_to_message.from_user:
        tid = message.reply_to_message.from_user.id
    elif len(parts) >= 2 and parts[1].isdigit():
        tid = int(parts[1])
    if tid is None:
        await message.answer(
            "فرمت:\n"
            "/immortal TELEGRAM_ID\n"
            "یا ریپلای روی پیام فرد + /immortal\n\n"
            + list_immortals()
        )
        return
    await message.answer(set_immortal(tid, True, by=message.from_user.id))


@router.message(Command("unimmortal", "حذفنامیرا"))
async def cmd_unset_immortal(message: Message):
    from services.staff import has_perm, PERM_IMMORTAL
    if not has_perm(message.from_user.id, PERM_IMMORTAL):
        await message.answer("⛔️ نیاز به مقام ادمین یا بالاتر.")
        return
    from services.immortal import set_immortal
    parts = (message.text or "").split()
    tid = None
    if message.reply_to_message and message.reply_to_message.from_user:
        tid = message.reply_to_message.from_user.id
    elif len(parts) >= 2 and parts[1].isdigit():
        tid = int(parts[1])
    if tid is None:
        await message.answer("فرمت: /unimmortal TELEGRAM_ID")
        return
    await message.answer(set_immortal(tid, False, by=message.from_user.id))


# ===== مقامات ربات (سازنده / ادمین / معاون / مدیر / ویژه) =====

@router.message(Command("setstaff", "مقام", "setrank"))
async def cmd_setstaff(message: Message):
    """فقط سازنده و ادمین: /setstaff TELEGRAM_ID مقام"""
    from services.staff import set_staff, list_staff, STAFF_ADMIN, has_perm, PERM_GIVE_STAFF
    if not has_perm(message.from_user.id, PERM_GIVE_STAFF):
        await message.answer("⛔️ فقط سازنده و ادمین می‌توانند مقام بدهند.")
        return
    parts = (message.text or "").split(maxsplit=2)
    tid = None
    rank = None
    if message.reply_to_message and message.reply_to_message.from_user and len(parts) >= 2:
        tid = message.reply_to_message.from_user.id
        rank = parts[1]
    elif len(parts) >= 3:
        if parts[1].isdigit():
            tid = int(parts[1])
            rank = parts[2]
    if tid is None or not rank:
        await message.answer(
            "فرمت:\n"
            "/setstaff TELEGRAM_ID ادمین|معاون ادمین|مدیر|ویژه|کاربر\n"
            "یا ریپلای + /setstaff مقام\n\n"
            + list_staff()
        )
        return
    ok, msg = set_staff(tid, rank, message.from_user.id)
    await message.answer(msg)


@router.message(Command("stafflist", "لیستمقام", "مقامات"))
async def cmd_stafflist(message: Message):
    from services.staff import list_staff, has_perm, PERM_DIAG, PERM_GIVE_STAFF
    if not (has_perm(message.from_user.id, PERM_DIAG) or has_perm(message.from_user.id, PERM_GIVE_STAFF)):
        await message.answer("⛔️ دسترسی نداری.")
        return
    await message.answer(list_staff())


@router.message(Command("mystaff", "مقاممن"))
async def cmd_mystaff(message: Message):
    from services.staff import staff_help_text
    await message.answer(staff_help_text(message.from_user.id))


@router.message(Command("testall", "تست‌همه", "selftest", "آزمایش"))
async def cmd_testall(message: Message):
    """اجرای خودآزمایی: ایمپورت همه هندلرها + سرویس‌های حیاتی و گزارش خطاها."""
    from services.staff import has_perm, PERM_DIAG, is_creator
    if not (has_perm(message.from_user.id, PERM_DIAG) or is_creator(message.from_user.id)):
        await message.answer("⛔️ فقط ویژه / ادمین / سازنده.")
        return
    await message.answer("🧪 در حال اجرای تست‌ها… چند ثانیه صبر کن.")
    try:
        from services.selftest import run_selftest
        report = run_selftest(message.from_user.id)
    except Exception as e:
        import traceback
        report = f"⚠️ خودِ تست ترکید: {type(e).__name__}: {e}\n<code>{traceback.format_exc()[-1500:]}</code>"
    # split if too long
    if len(report) <= 4000:
        await message.answer(report)
    else:
        chunk = ""
        for line in report.splitlines():
            if len(chunk) + len(line) + 1 > 3900:
                await message.answer(chunk)
                chunk = line
            else:
                chunk = chunk + "\n" + line if chunk else line
        if chunk:
            await message.answer(chunk)
