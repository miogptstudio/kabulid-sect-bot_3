"""سیستم شغل"""
from datetime import datetime, timedelta

JOBS = {
    "شمشیرزن": {"bonus": "duel", "mult": 1.12, "desc": "قدرت دوئل بیشتر"},
    "کیمیاگر": {"bonus": "craft", "mult": 1.15, "desc": "ساخت معجون موفق‌تر"},
    "بازرگان": {"bonus": "coin", "mult": 1.2, "desc": "سکه روزانه و تجارت"},
    "شکارچی": {"bonus": "hunt", "mult": 1.18, "desc": "شکار و پت بهتر"},
    "تذهیب‌گر": {"bonus": "cult", "mult": 1.15, "desc": "چی و تذهیب بیشتر"},
    "جادوگر": {"bonus": "spell", "mult": 1.14, "desc": "طلسم قوی‌تر"},
    "آهنگر": {"bonus": "weapon", "mult": 1.15, "desc": "سلاح و زره"},
    "درمانگر": {"bonus": "heal", "mult": 1.2, "desc": "درمان زخم و سم"},
    "جاسوس": {"bonus": "stealth", "mult": 1.1, "desc": "غار و اکتشاف"},
    "کشاورز": {"bonus": "garden", "mult": 1.25, "desc": "باغ و گیاه"},
}
_user_job: dict[int, str] = {}
_last_change: dict[int, datetime] = {}


def get_job(tg_id: int) -> str | None:
    return _user_job.get(tg_id)


def set_job(tg_id: int, job: str) -> str:
    if job not in JOBS:
        return "شغل نامعتبر. /jobs"
    if tg_id in _user_job:
        return f"شغل فعلی: {_user_job[tg_id]} — /changejob برای تعویض"
    _user_job[tg_id] = job
    info = JOBS[job]
    return f"✅ شغل «{job}» انتخاب شد." + chr(10) + f"{info['desc']} (×{info['mult']})"


def change_job(tg_id: int, job: str) -> str:
    if job not in JOBS:
        return "شغل نامعتبر. /jobs"
    now = datetime.utcnow()
    last = _last_change.get(tg_id)
    if last and now - last < timedelta(hours=24):
        return "هر ۲۴ ساعت یک‌بار می‌توانی شغل عوض کنی."
    _user_job[tg_id] = job
    _last_change[tg_id] = now
    return f"✅ شغل به «{job}» تغییر کرد."


def list_jobs() -> str:
    lines = ["💼 <b>شغل‌ها</b>", ""]
    for n, i in JOBS.items():
        lines.append(f"• <b>{n}</b> — {i['desc']} (×{i['mult']})")
    lines += ["", "/job نام — انتخاب", "/myjob", "/changejob نام"]
    return chr(10).join(lines)
