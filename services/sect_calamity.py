"""مصیبت فرقهها هر ۱۰ ساعت"""
from __future__ import annotations
from datetime import datetime, timedelta

CALAMITY_INTERVAL_H = 10
_protected: set[int] = set()  # sect ids protected by admin
_last_tick: datetime | None = None
_destroyed: set[int] = set()


def protect_sect(sect_id: int) -> str:
    _protected.add(int(sect_id))
    return f"🛡️ فرقه #{sect_id} تا مصیبت بعدی محافظت شد."


def unprotect_sect(sect_id: int) -> str:
    _protected.discard(int(sect_id))
    return f"محافظت فرقه #{sect_id} برداشته شد."


async def tick_calamity(session) -> list[str]:
    """اگر ۱۰ ساعت گذشته، فرقههای بدون محافظت را نابود کن"""
    global _last_tick
    now = datetime.utcnow()
    if _last_tick and (now - _last_tick) < timedelta(hours=CALAMITY_INTERVAL_H):
        return []
    # فقط وقتی واقعاً از آخرین تیک ۱۰س گذشته — در اولین فراخوانی فقط زمان را ست کن
    if _last_tick is None:
        _last_tick = now
        return ["⏳ زمانسنج مصیبت فرقهها شروع شد (هر ۱۰ ساعت)."]
    _last_tick = now
    msgs = []
    try:
        from sqlalchemy import select
        from database.models_v2 import Sect, SectMember
        result = await session.execute(select(Sect))
        sects = list(result.scalars().all())
        for s in sects:
            sid = int(s.id)
            if sid in _protected:
                msgs.append(f"🛡️ فرقه «{s.name}» با محافظت ادمین از مصیبت جان سالم به در برد.")
                continue
            # نابودی: اعضا را جدا کن و فرقه را حذف/علامت
            mems = await session.execute(select(SectMember).where(SectMember.sect_id == sid))
            for m in mems.scalars().all():
                await session.delete(m)
            name = s.name
            await session.delete(s)
            _destroyed.add(sid)
            msgs.append(f"💀 مصیبت: فرقه «{name}» نابود شد.")
        await session.commit()
    except Exception as e:
        msgs.append(f"مصیبت با خطا: {type(e).__name__}")
    if not msgs:
        msgs.append("🌌 مصیبت گذشت؛ فرقهای نبود.")
    return msgs


def status_text() -> str:
    if _last_tick is None:
        left = "هنوز شروع نشده"
    else:
        end = _last_tick + timedelta(hours=CALAMITY_INTERVAL_H)
        sec = (end - datetime.utcnow()).total_seconds()
        if sec < 0:
            left = "آماده تیک بعدی"
        else:
            left = f"{int(sec//3600)}س {int((sec%3600)//60)}د"
    return (
        f"🌪 <b>مصیبت فرقهها</b>" + chr(10)
        + f"فاصله: هر {CALAMITY_INTERVAL_H} ساعت" + chr(10)
        + f"تا مصیبت بعد: {left}" + chr(10)
        + f"محافظتشدهها: {len(_protected)}" + chr(10)
        + "ادمین: /protectsect آیدی | /calamitystatus"
    )
