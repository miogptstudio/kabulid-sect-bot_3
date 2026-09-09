"""کمپین داستانی جهان رزمی — فصول پیشرفت‌محور"""
from __future__ import annotations
from datetime import datetime
from services.persist import get_dict, save

CHAPTERS = [
    {
        "id": 1, "title": "بیدار شدن در دشت",
        "story": "چشم‌هایت را باز می‌کنی. باد دشت آغازین صورتت را می‌نوازد. شهری در دوردست می‌درخشد.",
        "objective": "دستور /mycity را بزن و شهر آغازین را ببین",
        "stat": "view_city", "target": 1,
        "reward_coins": 500, "reward_xp": 30, "reward_energy": 200,
    },
    {
        "id": 2, "title": "اولین تیغ",
        "story": "استادی پیر در دهکده تیغ می‌گوید: بدون دوئل، جنگجو نیستی.",
        "objective": "یک دوئل انجام بده (برد یا باخت)",
        "stat": "duels_done", "target": 1,
        "reward_coins": 800, "reward_xp": 50, "reward_energy": 500,
    },
    {
        "id": 3, "title": "راه تذهیب",
        "story": "چی در رگ‌هایت جریان می‌یابد. باید انرژی جذب کنی.",
        "objective": "۳۰۰۰ انرژی تذهیب جذب کن",
        "stat": "energy_gained", "target": 3000,
        "reward_coins": 1200, "reward_xp": 80, "reward_energy": 1000,
    },
    {
        "id": 4, "title": "پژواک آرش",
        "story": "شایعه کمان افسانه‌ای در بازار هزارراه پیچیده است.",
        "objective": "/arash را بخوان",
        "stat": "arash_view", "target": 1,
        "reward_coins": 600, "reward_xp": 40, "reward_energy": 300,
    },
    {
        "id": 5, "title": "گشت در جهان",
        "story": "مرزهای دشت را باید بشناسی. حرکت کن.",
        "objective": "۱۵ حرکت در جهان باز",
        "stat": "moves", "target": 15,
        "reward_coins": 1500, "reward_xp": 100, "reward_energy": 800,
    },
    {
        "id": 6, "title": "آزمون رعد",
        "story": "قله رعد تو را می‌خواند. سه دوئل پیروز لازم است.",
        "objective": "۳ دوئل پیروز",
        "stat": "duels_won", "target": 3,
        "reward_coins": 2500, "reward_xp": 150, "reward_energy": 2000,
    },
    {
        "id": 7, "title": "مهر طلسم",
        "story": "در شهر مهرها باید یک طلسم بخری یا بسازی.",
        "objective": "۲ خرید از فروشگاه",
        "stat": "buys", "target": 2,
        "reward_coins": 1800, "reward_xp": 90, "reward_energy": 600,
    },
    {
        "id": 8, "title": "دروازه پوچی",
        "story": "مرز جهان جایی است که قوانین می‌شکنند. ۵ دوئل دیگر.",
        "objective": "۵ دوئل پیروز (مجموع پیشرفت این فصل)",
        "stat": "duels_won", "target": 5,
        "reward_coins": 4000, "reward_xp": 200, "reward_energy": 3000,
    },
    {
        "id": 9, "title": "خون اژدها",
        "story": "دشت اژدها زیر پایت می‌لرزد. قدرت واقعی را نشان بده.",
        "objective": "۱۰ دوئل پیروز در این فصل",
        "stat": "duels_won", "target": 10,
        "reward_coins": 8000, "reward_xp": 400, "reward_energy": 5000,
    },
    {
        "id": 10, "title": "تاج جهان رزمی",
        "story": "افسانه کامل شد. تو دیگر نوآموز نیستی — جنگجوی جهان رزمی هستی.",
        "objective": "۲۰ دوئل پیروز در این فصل",
        "stat": "duels_won", "target": 20,
        "reward_coins": 20000, "reward_xp": 1000, "reward_energy": 15000,
        "title": "legend",
    },
]


def _rec(tg: int) -> dict:
    d = get_dict("campaign")
    k = str(int(tg))
    if k not in d:
        d[k] = {"chapter": 1, "progress": 0, "claimed": [], "started_at": datetime.utcnow().isoformat()}
        save("campaign")
    return d[k]


def current_chapter(tg: int) -> dict | None:
    rec = _rec(tg)
    ch = int(rec.get("chapter") or 1)
    for c in CHAPTERS:
        if c["id"] == ch:
            return c
    return None


def status_text(tg: int) -> str:
    rec = _rec(tg)
    ch = current_chapter(tg)
    if not ch:
        return "🏆 <b>کمپین جهان رزمی کامل شد!</b>\nهمه فصول را پشت سر گذاشتی.\n/titles"
    prog = int(rec.get("progress") or 0)
    target = int(ch["target"])
    pct = min(100, int(100 * prog / max(1, target)))
    bar = "█" * (pct // 10) + "░" * (10 - pct // 10)
    lines = [
        "📖 <b>کمپین داستانی جهان رزمی</b>",
        f"فصل {ch['id']}/10: <b>{ch['title']}</b>",
        "",
        ch["story"],
        "",
        f"🎯 هدف: {ch['objective']}",
        f"پیشرفت: {prog}/{target} [{bar}] {pct}%",
        f"🎁 پاداش: {ch['reward_coins']:,} سکه | {ch['reward_xp']} XP | {ch['reward_energy']:,} انرژی",
        "",
        "پیشرفت با بازی خودکار است. وقتی کامل شد: /claimcampaign",
    ]
    return "\n".join(lines)


def progress(tg: int, stat: str, amount: int = 1) -> str | None:
    """پیشرفت فصل فعلی؛ اگر کامل شد پیام برمی‌گرداند"""
    rec = _rec(tg)
    ch = current_chapter(tg)
    if not ch or ch.get("stat") != stat:
        return None
    rec["progress"] = int(rec.get("progress") or 0) + int(amount)
    d = get_dict("campaign")
    d[str(int(tg))] = rec
    save("campaign")
    if rec["progress"] >= int(ch["target"]):
        return f"📖 فصل «{ch['title']}» کامل شد! /claimcampaign"
    return None


def claim(tg: int) -> tuple[str, dict]:
    rec = _rec(tg)
    ch = current_chapter(tg)
    if not ch:
        return "کمپین کامل است.", {}
    if int(rec.get("progress") or 0) < int(ch["target"]):
        return f"هنوز فصل کامل نشده ({rec.get('progress', 0)}/{ch['target']}).", {}
    rewards = {
        "coins": int(ch["reward_coins"]),
        "xp": int(ch["reward_xp"]),
        "energy": int(ch["reward_energy"]),
        "title": ch.get("title"),
    }
    claimed = list(rec.get("claimed") or [])
    claimed.append(ch["id"])
    rec["claimed"] = claimed
    rec["chapter"] = int(ch["id"]) + 1
    rec["progress"] = 0
    d = get_dict("campaign")
    d[str(int(tg))] = rec
    save("campaign")
    if rewards.get("title"):
        try:
            from services.titles import grant
            grant(tg, rewards["title"])
        except Exception:
            pass
    msg = (
        f"✅ فصل {ch['id']} — <b>{ch['title']}</b> دریافت شد!\n"
        f"💰 +{rewards['coins']:,} سکه\n"
        f"✨ +{rewards['xp']} XP\n"
        f"⚡ +{rewards['energy']:,} انرژی"
    )
    if rewards.get("title"):
        msg += f"\n🏅 لقب جدید باز شد"
    nxt = current_chapter(tg)
    if nxt:
        msg += f"\n\n📖 فصل بعد: <b>{nxt['title']}</b>\n/campaign"
    else:
        msg += "\n\n🏆 کمپین کامل شد!"
    return msg, rewards
