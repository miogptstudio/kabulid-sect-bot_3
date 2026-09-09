"""سیاه‌چال جهان رزمی — طبقات، دشمن، غنیمت"""
from __future__ import annotations
from datetime import datetime, timedelta
import random
from services.persist import get_dict, save

FLOORS = [
    {"n": 1, "name": "دهلیز نوآموزان", "hp": 80, "atk": 12, "reward_coins": 200, "reward_xp": 15, "min_power": 0},
    {"n": 2, "name": "سالن تیغ‌ها", "hp": 150, "atk": 22, "reward_coins": 400, "reward_xp": 30, "min_power": 50},
    {"n": 3, "name": "اتاق رعد", "hp": 280, "atk": 35, "reward_coins": 700, "reward_xp": 50, "min_power": 120},
    {"n": 4, "name": "دخمه مهرها", "hp": 450, "atk": 50, "reward_coins": 1200, "reward_xp": 80, "min_power": 250},
    {"n": 5, "name": "راهرو پوچی", "hp": 700, "atk": 75, "reward_coins": 2000, "reward_xp": 120, "min_power": 400},
    {"n": 6, "name": "لانه اژدهای خردسال", "hp": 1100, "atk": 110, "reward_coins": 3500, "reward_xp": 180, "min_power": 700},
    {"n": 7, "name": "تالار خون", "hp": 1800, "atk": 160, "reward_coins": 6000, "reward_xp": 280, "min_power": 1200},
    {"n": 8, "name": "پلکان شکسته آسمان", "hp": 2800, "atk": 220, "reward_coins": 10000, "reward_xp": 400, "min_power": 2000},
    {"n": 9, "name": "قلب مرز پوچی", "hp": 4500, "atk": 320, "reward_coins": 18000, "reward_xp": 600, "min_power": 3500},
    {"n": 10, "name": "تاج نگهبان جهان رزمی", "hp": 8000, "atk": 480, "reward_coins": 35000, "reward_xp": 1000, "min_power": 6000},
]

CD_SECONDS = 90  # بین هر تلاش
ENEMIES = [
    "سایه جنگجو", "گolem سنگی", "مار چی", "شبح رعد", "نگهبان مهر",
    "دیو خاکستر", "اژدهای خردسال", "شمشیر سرگردان", "هیولای پوچی", "نگهبان تاج",
]


def _rec(tg: int) -> dict:
    d = get_dict("dungeon")
    k = str(int(tg))
    if k not in d:
        d[k] = {"best_floor": 0, "last_at": None, "runs": 0, "clears": 0}
        save("dungeon")
    return d[k]


def status_text(tg: int, power: int = 0) -> str:
    rec = _rec(tg)
    lines = [
        "🏰 <b>سیاه‌چال جهان رزمی</b>",
        f"بهترین طبقه: {rec.get('best_floor', 0)}/10",
        f"دفعات ورود: {rec.get('runs', 0)} | پاکسازی کامل: {rec.get('clears', 0)}",
        f"قدرت فعلی تو: {power:,}",
        "",
        "طبقات:",
    ]
    for f in FLOORS:
        lock = "🔒" if power < f["min_power"] else "⚔️"
        mark = "✅" if rec.get("best_floor", 0) >= f["n"] else lock
        lines.append(f"{mark} {f['n']}. {f['name']} — نیاز قدرت {f['min_power']:,}")
    lines.append("\n/dungeonrun — شروع از طبقه بعدی")
    lines.append("کول‌داون بین تلاش: ۹۰ ثانیه")
    return "\n".join(lines)


def _cd_left(rec: dict) -> int:
    last = rec.get("last_at")
    if not last:
        return 0
    try:
        elapsed = (datetime.utcnow() - datetime.fromisoformat(str(last))).total_seconds()
    except Exception:
        return 0
    left = CD_SECONDS - elapsed
    return int(left) if left > 0 else 0


def run(tg: int, power: int) -> dict:
    """یک طبقه را می‌جنگد. returns result dict"""
    rec = _rec(tg)
    left = _cd_left(rec)
    if left > 0:
        return {"ok": False, "msg": f"⏳ سیاه‌چال — {left} ثانیه صبر کن."}

    best = int(rec.get("best_floor") or 0)
    next_floor = min(best + 1, 10)
    floor = FLOORS[next_floor - 1]

    if power < floor["min_power"]:
        return {
            "ok": False,
            "msg": f"🔒 طبقه {floor['n']} — «{floor['name']}»\nقدرت لازم: {floor['min_power']:,}\nقدرت تو: {power:,}",
        }

    enemy = ENEMIES[min(next_floor - 1, len(ENEMIES) - 1)]
    # نبرد ساده: قدرت بازیکن vs hp/atk دشمن
    player_hp = max(50, power // 2)
    enemy_hp = floor["hp"]
    log = [f"⚔️ طبقه {floor['n']}: <b>{floor['name']}</b>", f"دشمن: {enemy} (HP {enemy_hp})"]

    rounds = 0
    won = False
    while rounds < 20 and player_hp > 0 and enemy_hp > 0:
        rounds += 1
        dmg = max(5, int(power * random.uniform(0.08, 0.18)))
        enemy_hp -= dmg
        log.append(f"回合{rounds}: ضربه تو −{dmg} (دشمن {max(0, enemy_hp)} HP)")
        if enemy_hp <= 0:
            won = True
            break
        edmg = max(3, int(floor["atk"] * random.uniform(0.7, 1.3)))
        # قدرت بالا آسیب را کم می‌کند
        reduce = min(0.6, power / (power + floor["min_power"] * 2 + 1))
        edmg = max(1, int(edmg * (1 - reduce)))
        player_hp -= edmg
        log.append(f"  دشمن −{edmg} (تو {max(0, player_hp)} HP)")

    rec["last_at"] = datetime.utcnow().isoformat()
    rec["runs"] = int(rec.get("runs") or 0) + 1

    if won:
        rec["best_floor"] = max(best, floor["n"])
        if floor["n"] >= 10:
            rec["clears"] = int(rec.get("clears") or 0) + 1
        d = get_dict("dungeon")
        d[str(int(tg))] = rec
        save("dungeon")
        # غنیمت تصادفی اضافه
        bonus = random.choice([
            ("سکه اضافی", "coins", int(floor["reward_coins"] * 0.3)),
            ("تکه جوهر", "xp", int(floor["reward_xp"] * 0.5)),
            ("هیچ", None, 0),
        ])
        log.append(f"\n✅ پیروزی!")
        log.append(f"💰 +{floor['reward_coins']:,} سکه | ✨ +{floor['reward_xp']} XP")
        if bonus[1]:
            log.append(f"🎁 غنیمت: {bonus[0]} (+{bonus[2]})")
        return {
            "ok": True, "won": True, "msg": "\n".join(log),
            "coins": floor["reward_coins"] + (bonus[2] if bonus[1] == "coins" else 0),
            "xp": floor["reward_xp"] + (bonus[2] if bonus[1] == "xp" else 0),
            "floor": floor["n"],
        }
    else:
        d = get_dict("dungeon")
        d[str(int(tg))] = rec
        save("dungeon")
        # شکست — پاداش جزئی
        consol_c = floor["reward_coins"] // 5
        consol_x = floor["reward_xp"] // 5
        log.append(f"\n❌ شکست در طبقه {floor['n']}")
        log.append(f"پاداش تسلی: +{consol_c} سکه | +{consol_x} XP")
        return {
            "ok": True, "won": False, "msg": "\n".join(log),
            "coins": consol_c, "xp": consol_x, "floor": floor["n"],
        }
