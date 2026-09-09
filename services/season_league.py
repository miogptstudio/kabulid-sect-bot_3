"""لیگ فصلی جهان رزمی — امتیاز، رده، پاداش پایان فصل"""
from __future__ import annotations
from datetime import datetime
from services.persist import get_dict, save

TIERS = [
    (0, "برنز", "🥉"),
    (100, "نقره", "🥈"),
    (300, "طلا", "🥇"),
    (600, "پلاتین", "💎"),
    (1000, "الماس", "👑"),
    (2000, "افسانه رزمی", "🐉"),
]


def _season_id() -> str:
    now = datetime.utcnow()
    # فصل = سال-ماه
    return f"{now.year}-{now.month:02d}"


def _data() -> dict:
    d = get_dict("season_league")
    sid = _season_id()
    if d.get("season") != sid:
        d.clear()
        d["season"] = sid
        d["scores"] = {}
        d["history"] = d.get("history") or []
        save("season_league")
    if "scores" not in d:
        d["scores"] = {}
    return d


def add_score(tg: int, points: int, reason: str = "") -> int:
    d = _data()
    k = str(int(tg))
    scores = d.setdefault("scores", {})
    scores[k] = int(scores.get(k) or 0) + int(points)
    d["scores"] = scores
    save("season_league")
    return scores[k]


def score_of(tg: int) -> int:
    d = _data()
    return int((d.get("scores") or {}).get(str(int(tg)) or 0) or 0)


def tier_of(score: int) -> tuple[str, str]:
    name, emoji = TIERS[0][1], TIERS[0][2]
    for need, n, e in TIERS:
        if score >= need:
            name, emoji = n, e
    return name, emoji


def leaderboard(limit: int = 15) -> list[tuple[str, int]]:
    d = _data()
    items = [(k, int(v)) for k, v in (d.get("scores") or {}).items()]
    items.sort(key=lambda x: -x[1])
    return items[:limit]


def status_text(tg: int) -> str:
    d = _data()
    sc = score_of(tg)
    tier, emoji = tier_of(sc)
    lines = [
        f"🏆 <b>لیگ فصلی جهان رزمی</b>",
        f"فصل: <code>{d.get('season')}</code>",
        f"امتیاز تو: <b>{sc:,}</b> — {emoji} {tier}",
        "",
        "نحوه امتیاز:",
        "• برد دوئل: +15",
        "• باخت دوئل: +3",
        "• طبقه سیاه‌چال: +10 × شماره طبقه",
        "• مأموریت روزانه: +8",
        "• فصل کمپین: +25",
        "",
        "🏅 برترین‌ها:",
    ]
    board = leaderboard(10)
    if not board:
        lines.append("هنوز کسی امتیاز ندارد.")
    else:
        for i, (uid, s) in enumerate(board, 1):
            t, e = tier_of(s)
            mark = " 👈" if uid == str(tg) else ""
            lines.append(f"{i}. <code>{uid}</code> — {s:,} {e}{mark}")
    lines.append("\n/league — وضعیت")
    return "\n".join(lines)
