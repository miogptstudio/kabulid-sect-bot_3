"""سیستم شغل — پایدار"""
from __future__ import annotations
from datetime import datetime, timedelta
from services.persist import get_dict, save as _psave

JOBS = {
    "کشاورز": {"desc": "برداشت و گیاه؛ بونوس باغ", "mult": 1.15},
    "آهنگر": {"desc": "ساخت سلاح؛ بونوس آهنگری", "mult": 1.2},
    "کیمیاگر": {"desc": "معجون و قرص؛ بونوس ساخت", "mult": 1.25},
    "تاجر": {"desc": "خرید/فروش بهتر؛ کارمزد کمتر", "mult": 1.1},
    "شکارچی": {"desc": "شکار و پت قوی‌تر", "mult": 1.2},
    "سرباز": {"desc": "قدرت دوئل بیشتر", "mult": 1.3},
    "روحانی": {"desc": "تذهیب سریع‌تر", "mult": 1.2},
    "ماجراجو": {"desc": "غنیمت غار و شهر", "mult": 1.15},
    "معدن‌چی": {"desc": "برداشت معدن بیشتر", "mult": 1.25},
    "استاد": {"desc": "دانش و شاگردی", "mult": 1.15},
}


def _jobs() -> dict:
    return get_dict("user_jobs")


def _changes() -> dict:
    return get_dict("job_changes")


def get_job(tg_id: int) -> str | None:
    return _jobs().get(str(int(tg_id)))


def set_job(tg_id: int, job: str) -> str:
    job = (job or "").strip()
    if job not in JOBS:
        # fuzzy
        for k in JOBS:
            if job in k or k in job:
                job = k
                break
    if job not in JOBS:
        return "شغل نامعتبر. /jobs"
    cur = get_job(tg_id)
    if cur == job:
        return f"همین حالا شغل «{job}» را داری."
    if cur:
        return change_job(tg_id, job)
    m = _jobs()
    m[str(int(tg_id))] = job
    _psave("user_jobs")
    info = JOBS[job]
    return f"✅ شغل «{job}» انتخاب شد.\n{info['desc']} (×{info['mult']})\n/myjob | /work"


def change_job(tg_id: int, job: str) -> str:
    job = (job or "").strip()
    if job not in JOBS:
        for k in JOBS:
            if job in k or k in job:
                job = k
                break
    if job not in JOBS:
        return "شغل نامعتبر. /jobs"
    now = datetime.utcnow()
    ch = _changes()
    last = ch.get(str(int(tg_id)))
    if last:
        try:
            last_dt = datetime.fromisoformat(str(last))
            if now - last_dt < timedelta(hours=24):
                left = int((timedelta(hours=24) - (now - last_dt)).total_seconds() // 3600) + 1
                return f"⏳ هر ۲۴ ساعت یک‌بار می‌توانی شغل عوض کنی. مانده ≈{left} ساعت"
        except Exception:
            pass
    m = _jobs()
    m[str(int(tg_id))] = job
    ch[str(int(tg_id))] = now.isoformat()
    _psave("user_jobs")
    _psave("job_changes")
    return f"✅ شغل به «{job}» تغییر کرد.\n/myjob | /work"


def list_jobs() -> str:
    lines = ["💼 <b>شغل‌ها</b>", ""]
    for n, i in JOBS.items():
        lines.append(f"• <b>{n}</b> — {i['desc']} (×{i['mult']})")
    lines += ["", "/job — انتخاب با دکمه", "/job نام", "/myjob", "/changejob نام", "/work — کار روزانه شغل"]
    return "\n".join(lines)


def job_mult(tg_id: int) -> float:
    j = get_job(tg_id)
    if not j:
        return 1.0
    return float(JOBS.get(j, {}).get("mult") or 1.0)


def work(tg_id: int) -> str | dict:
    """پاداش روزانه شغل"""
    j = get_job(tg_id)
    if not j:
        return "شغلی نداری. /jobs"
    cd = get_dict("job_work_cd")
    now = datetime.utcnow()
    last = cd.get(str(int(tg_id)))
    if last:
        try:
            last_dt = datetime.fromisoformat(str(last))
            if now - last_dt < timedelta(hours=6):
                left = int((timedelta(hours=6) - (now - last_dt)).total_seconds() // 60)
                return f"⏳ کار بعدی تا {left} دقیقه دیگر. (هر ۶ ساعت)"
        except Exception:
            pass
    cd[str(int(tg_id))] = now.isoformat()
    _psave("job_work_cd")
    mult = job_mult(tg_id)
    coins = int(50 * mult)
    stones = 1 if mult >= 1.2 else 0
    return {
        "job": j,
        "coins": coins,
        "spirit_stones": stones,
        "msg": f"💼 کار به‌عنوان <b>{j}</b> تمام شد!\n🪙 +{coins} سکه" + (f"\n💎 +{stones} سنگ روحی" if stones else ""),
    }
