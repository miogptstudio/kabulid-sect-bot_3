"""سیستم مقامات ربات — اختیارات محدود از قدرت ادمین/سازنده.

سلسله‌مراتب: سازنده > ادمین > معاون ادمین > مدیر > ویژه > کاربر

فقط سازنده و ادمین مقام می‌دهند.
هر مقام پایین‌تر، بخشی از اختیارات مدیریتی را دارد (نه همه).
"""
from __future__ import annotations
from bot.config import ADMIN_IDS
from services.persist import get_dict, save as _psave

STAFF_CREATOR = "سازنده"
STAFF_ADMIN = "ادمین"
STAFF_DEPUTY = "معاون ادمین"
STAFF_MANAGER = "مدیر"
STAFF_SPECIAL = "ویژه"
STAFF_USER = "کاربر"

STAFF_ORDER = [
    STAFF_CREATOR, STAFF_ADMIN, STAFF_DEPUTY, STAFF_MANAGER, STAFF_SPECIAL, STAFF_USER,
]

STAFF_POWER = {
    STAFF_CREATOR: 100,
    STAFF_ADMIN: 80,
    STAFF_DEPUTY: 60,
    STAFF_MANAGER: 40,
    STAFF_SPECIAL: 20,
    STAFF_USER: 0,
}

# حداقل مقام برای هر دسترسی
PERM_GIVE_STAFF = STAFF_ADMIN       # دادن/گرفتن مقام
PERM_BAN = STAFF_DEPUTY             # بن / آنبن
PERM_RESTRICT = STAFF_MANAGER       # محدود کردن زمان‌دار
PERM_GIVEMONEY = STAFF_MANAGER      # دادن پول (سقف دارد)
PERM_TAKEMONEY = STAFF_DEPUTY       # گرفتن پول
PERM_SETCULT = STAFF_ADMIN          # تنظیم تذهیب کامل
PERM_IMMORTAL = STAFF_ADMIN         # نامیرایی
PERM_PROMOTE_RANK = STAFF_MANAGER   # ارتقا/تنزل رتبه بازی
PERM_DIAG = STAFF_SPECIAL           # تشخیص ربات
PERM_VIEW_USER = STAFF_SPECIAL      # دیدن وضعیت کاربر
PERM_WARN = STAFF_SPECIAL           # اخطار
PERM_UNRESTRICT = STAFF_MANAGER     # برداشتن محدودیت
PERM_GIVEPOWER = STAFF_DEPUTY       # دادن قدرت
PERM_TRANSFER_CULT = STAFF_CREATOR  # فقط سازنده
PERM_PANEL = STAFF_SPECIAL          # دیدن پنل مدیریت محدود

# سقف دادن پول در هر دستور (بر اساس مقام)
MONEY_LIMITS = {
    STAFF_CREATOR: 10**18,
    STAFF_ADMIN: 50_000_000,
    STAFF_DEPUTY: 5_000_000,
    STAFF_MANAGER: 500_000,
    STAFF_SPECIAL: 50_000,
    STAFF_USER: 0,
}


def _data() -> dict:
    return get_dict("bot_staff_ranks")


def is_creator(tg_id: int) -> bool:
    return int(tg_id) in set(int(x) for x in (ADMIN_IDS or []))


def get_staff(tg_id: int) -> str:
    tg_id = int(tg_id)
    if is_creator(tg_id):
        return STAFF_CREATOR
    d = _data()
    rank = d.get(str(tg_id))
    if rank in STAFF_POWER and rank != STAFF_CREATOR:
        return rank
    return STAFF_USER


def get_power(tg_id: int) -> int:
    return STAFF_POWER.get(get_staff(tg_id), 0)


def has_perm(tg_id: int, min_rank: str) -> bool:
    return get_power(tg_id) >= STAFF_POWER.get(min_rank, 999)


def money_limit(tg_id: int) -> int:
    return int(MONEY_LIMITS.get(get_staff(tg_id), 0))


def check_money_amount(tg_id: int, amount: int) -> tuple[bool, str]:
    lim = money_limit(tg_id)
    if lim <= 0:
        return False, "⛔️ برای دادن پول مقام کافی نداری."
    if int(amount) > lim:
        return False, f"⛔️ سقف مجاز برای مقام تو: {lim:,} در هر دستور."
    return True, ""


def set_staff(target_tg: int, rank: str, by_tg: int) -> tuple[bool, str]:
    if not has_perm(by_tg, PERM_GIVE_STAFF):
        return False, "⛔️ فقط سازنده و ادمین می‌توانند مقام بدهند."
    target_tg = int(target_tg)
    if is_creator(target_tg):
        return False, "مقام سازنده ثابت است و تغییر نمی‌کند."
    rank = (rank or "").strip()
    aliases = {
        "سازنده": STAFF_CREATOR, "ادمین": STAFF_ADMIN, "admin": STAFF_ADMIN,
        "معاون": STAFF_DEPUTY, "معاون ادمین": STAFF_DEPUTY, "deputy": STAFF_DEPUTY,
        "مدیر": STAFF_MANAGER, "manager": STAFF_MANAGER,
        "ویژه": STAFF_SPECIAL, "special": STAFF_SPECIAL,
        "کاربر": STAFF_USER, "user": STAFF_USER, "حذف": STAFF_USER, "برداشتن": STAFF_USER,
    }
    rank = aliases.get(rank, rank)
    if rank not in STAFF_POWER:
        return False, "مقام نامعتبر.\nمجاز: ادمین | معاون ادمین | مدیر | ویژه | کاربر"
    if rank == STAFF_CREATOR:
        return False, "مقام سازنده فقط از طریق ADMIN_IDS تنظیم می‌شود."
    if get_power(by_tg) < STAFF_POWER[STAFF_CREATOR]:
        if STAFF_POWER[rank] >= get_power(by_tg):
            return False, "نمی‌توانی مقامی برابر یا بالاتر از خودت بدهی."
    d = _data()
    key = str(target_tg)
    if rank == STAFF_USER:
        d.pop(key, None)
        _psave("bot_staff_ranks")
        return True, f"✅ مقام کاربر <code>{target_tg}</code> برداشته شد."
    d[key] = rank
    _psave("bot_staff_ranks")
    return True, f"✅ مقام <code>{target_tg}</code> → <b>{rank}</b>"


def list_staff() -> str:
    d = _data()
    lines = ["👑 <b>مقامات ربات</b>", ""]
    lines.append("🛠 سازنده: " + ", ".join(f"<code>{x}</code>" for x in ADMIN_IDS))
    by_rank = {r: [] for r in (STAFF_ADMIN, STAFF_DEPUTY, STAFF_MANAGER, STAFF_SPECIAL)}
    for tid, rank in d.items():
        if rank in by_rank:
            by_rank[rank].append(tid)
    for rank in (STAFF_ADMIN, STAFF_DEPUTY, STAFF_MANAGER, STAFF_SPECIAL):
        ids = by_rank.get(rank) or []
        lines.append(f"\n<b>{rank}</b>:")
        if ids:
            for i in ids:
                lines.append(f"• <code>{i}</code>")
        else:
            lines.append("• —")
    lines.append(
        "\n/setstaff آیدی مقام\n/mystaff\n/stafflist"
    )
    return "\n".join(lines)


def staff_help_text(tg_id: int) -> str:
    rank = get_staff(tg_id)
    lim = money_limit(tg_id)
    lines = [
        f"مقام تو: <b>{rank}</b>",
        "",
        "سلسله: سازنده > ادمین > معاون ادمین > مدیر > ویژه",
        "",
        "اختیارات تو:",
        f"{'✅' if has_perm(tg_id, PERM_GIVE_STAFF) else '❌'} دادن مقام",
        f"{'✅' if has_perm(tg_id, PERM_BAN) else '❌'} بن / آنبن",
        f"{'✅' if has_perm(tg_id, PERM_RESTRICT) else '❌'} محدود کردن",
        f"{'✅' if has_perm(tg_id, PERM_GIVEMONEY) else '❌'} دادن پول (سقف {lim:,})",
        f"{'✅' if has_perm(tg_id, PERM_TAKEMONEY) else '❌'} گرفتن پول",
        f"{'✅' if has_perm(tg_id, PERM_GIVEPOWER) else '❌'} دادن قدرت",
        f"{'✅' if has_perm(tg_id, PERM_SETCULT) else '❌'} تنظیم تذهیب",
        f"{'✅' if has_perm(tg_id, PERM_IMMORTAL) else '❌'} نامیرایی",
        f"{'✅' if has_perm(tg_id, PERM_PROMOTE_RANK) else '❌'} ارتقای رتبه بازی",
        f"{'✅' if has_perm(tg_id, PERM_DIAG) else '❌'} تشخیص ربات",
        f"{'✅' if has_perm(tg_id, PERM_TRANSFER_CULT) else '❌'} انتقال تذهیب (فقط سازنده)",
        "",
        "دستورات: /setstaff /stafflist /mystaff /admin",
    ]
    return "\n".join(lines)
