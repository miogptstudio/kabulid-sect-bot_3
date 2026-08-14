"""قوانین فرقه، آزمون عضویت، مسابقه ارتقای اعضا"""
from __future__ import annotations
import random
from datetime import datetime, timedelta
from services.persist import get_dict, save as _psave

DEFAULT_RULES = [
    "به رهبر و ارجمندان احترام بگذار.",
    "خیانت به فرقه جرم سنگین است.",
    "مأموریت‌های فرقه را جدی بگیر.",
    "منابع فرقه را هدر نده.",
    "در دفاع از قلمرو شرکت کن.",
]

# سوالات آزمون عمومی (رهبر می‌تواند سوال اختصاصی هم بگذارد)
DEFAULT_QUESTIONS = [
    {"q": "اولویت عضو فرقه چیست؟", "options": ["منافع شخصی", "منافع فرقه", "بی‌تفاوتی"], "answer": 1},
    {"q": "در صورت حمله به قلمرو چه باید کرد؟", "options": ["فرار", "اطلاع و دفاع", "بی‌خیال"], "answer": 1},
    {"q": "خزانه فرقه مال کیست؟", "options": ["فقط رهبر", "همه اعضا به‌صورت جمعی", "غریبه‌ها"], "answer": 1},
    {"q": "خیانت به فرقه چه پیامدی دارد؟", "options": ["پاداش", "مجازات و اخراج", "هیچی"], "answer": 1},
    {"q": "ارتقای مقام چگونه است؟", "options": ["با پول فقط", "با مشارکت و مسابقه داخلی", "شانسی"], "answer": 1},
    {"q": "مأموریت فرقه را چه کسی صادر می‌کند؟", "options": ["هر کسی", "رهبر یا ارجمند", "ربات"], "answer": 1},
    {"q": "برج تهذیب برای چیست؟", "options": ["دکوراسیون", "بونوس تذهیب اعضا", "زندان"], "answer": 1},
    {"q": "کتابخانه فرقه چه می‌دهد؟", "options": ["سکه", "تکنیک فرقه‌ای", "پت"], "answer": 1},
]


def _rules() -> dict:
    return get_dict("sect_rules")


def _exams() -> dict:
    return get_dict("sect_exams")


def _passed() -> dict:
    return get_dict("sect_exam_passed")


def _promo() -> dict:
    return get_dict("sect_promo_comp")


def get_rules(sect_id: int) -> list[str]:
    m = _rules()
    sk = str(int(sect_id))
    if sk not in m:
        m[sk] = list(DEFAULT_RULES)
        _psave("sect_rules")
    return list(m[sk])


def set_rules(sect_id: int, rules: list[str]) -> str:
    rules = [r.strip() for r in rules if r.strip()]
    if not rules:
        return "حداقل یک قانون لازم است."
    if len(rules) > 15:
        return "حداکثر ۱۵ قانون."
    m = _rules()
    m[str(int(sect_id))] = rules
    _psave("sect_rules")
    return f"✅ {len(rules)} قانون ثبت شد."


def rules_text(sect_id: int, sect_name: str = "") -> str:
    rules = get_rules(sect_id)
    lines = [f"📜 <b>قوانین فرقه {sect_name}</b>", ""]
    for i, r in enumerate(rules, 1):
        lines.append(f"{i}. {r}")
    lines += [
        "",
        "عضویت: اول قوانین را بخوان، بعد /sectexam نام‌فرقه",
        "رهبر: /setsectrules قانون1 | قانون2 | ...",
    ]
    return chr(10).join(lines)


def get_questions(sect_id: int) -> list[dict]:
    m = _exams()
    sk = str(int(sect_id))
    custom = m.get(sk)
    if custom and isinstance(custom, list) and len(custom) >= 3:
        return custom
    return list(DEFAULT_QUESTIONS)


def set_questions(sect_id: int, questions: list[dict]) -> str:
    if len(questions) < 3:
        return "حداقل ۳ سوال."
    m = _exams()
    m[str(int(sect_id))] = questions
    _psave("sect_exams")
    return f"✅ {len(questions)} سوال آزمون ثبت شد."


def has_passed(tg_id: int, sect_id: int) -> bool:
    return bool(_passed().get(f"{int(tg_id)}:{int(sect_id)}"))


def mark_passed(tg_id: int, sect_id: int) -> None:
    m = _passed()
    m[f"{int(tg_id)}:{int(sect_id)}"] = datetime.utcnow().isoformat()
    _psave("sect_exam_passed")


# جلسه آزمون فعال: tg -> {sect_id, sect_name, qs, idx, correct, started}
_sessions: dict[int, dict] = {}


def start_exam(tg_id: int, sect_id: int, sect_name: str) -> str:
    if has_passed(tg_id, sect_id):
        return f"قبلاً آزمون «{sect_name}» را پاس کرده‌ای. /joinsect {sect_name}"
    qs = get_questions(sect_id)
    pick = random.sample(qs, k=min(5, len(qs)))
    # shuffle options but track answer index
    prepared = []
    for item in pick:
        opts = list(item["options"])
        ans_text = opts[item["answer"]]
        random.shuffle(opts)
        prepared.append({
            "q": item["q"],
            "options": opts,
            "answer": opts.index(ans_text),
        })
    _sessions[int(tg_id)] = {
        "sect_id": int(sect_id),
        "sect_name": sect_name,
        "qs": prepared,
        "idx": 0,
        "correct": 0,
    }
    return _ask(tg_id)


def _ask(tg_id: int) -> str:
    s = _sessions.get(int(tg_id))
    if not s:
        return "آزمونی فعال نیست. /sectexam نام‌فرقه"
    i = s["idx"]
    if i >= len(s["qs"]):
        return finish_exam(tg_id)
    q = s["qs"][i]
    lines = [
        f"📝 <b>آزمون عضویت — {s['sect_name']}</b>",
        f"سوال {i+1}/{len(s['qs'])}",
        "",
        q["q"],
        "",
    ]
    for n, opt in enumerate(q["options"], 1):
        lines.append(f"{n}) {opt}")
    lines += ["", "پاسخ: /examanswer شماره"]
    return chr(10).join(lines)


def answer_exam(tg_id: int, choice: int) -> str:
    s = _sessions.get(int(tg_id))
    if not s:
        return "آزمونی فعال نیست."
    i = s["idx"]
    if i >= len(s["qs"]):
        return finish_exam(tg_id)
    q = s["qs"][i]
    if choice < 1 or choice > len(q["options"]):
        return f"شماره بین ۱ و {len(q['options'])}."
    if choice - 1 == q["answer"]:
        s["correct"] += 1
        feedback = "✅ درست"
    else:
        feedback = f"❌ غلط — پاسخ: {q['options'][q['answer']]}"
    s["idx"] += 1
    if s["idx"] >= len(s["qs"]):
        return feedback + chr(10) + chr(10) + finish_exam(tg_id)
    return feedback + chr(10) + chr(10) + _ask(tg_id)


def finish_exam(tg_id: int) -> str:
    s = _sessions.pop(int(tg_id), None)
    if not s:
        return "جلسه‌ای نبود."
    total = len(s["qs"])
    ok = s["correct"]
    need = max(3, (total + 1) // 2)  # حداقل نصف (گرد بالا) و حداقل ۳ اگر ۵ سوال
    if total <= 3:
        need = total  # همه درست
    if ok >= need:
        mark_passed(tg_id, s["sect_id"])
        return (
            f"🎉 قبول شدی! ({ok}/{total})" + chr(10)
            + f"حالا: /joinsect {s['sect_name']}"
        )
    return (
        f"مردود ({ok}/{total}) — نیاز حداقل {need} پاسخ درست." + chr(10)
        + f"دوباره: /sectexam {s['sect_name']}"
    )


# ---------- مسابقه ارتقا ----------
# وضعیت‌های فرقه از پایین به بالا (باید با SECT_STATUS هم‌خوان باشد)
PROMO_ORDER = [
    "عضو دسته‌های پایین‌تر",
    "عضو بیرونی",
    "عضو داخلی",
    "ارشد",
    "ارجمند",
]


def start_promo_comp(sect_id: int, target_status: str, hours: int = 24) -> str:
    if target_status not in PROMO_ORDER:
        return "مقصد: " + " | ".join(PROMO_ORDER[1:])
    m = _promo()
    sk = str(int(sect_id))
    m[sk] = {
        "target": target_status,
        "scores": {},  # tg_id -> points
        "ends": (datetime.utcnow() + timedelta(hours=hours)).isoformat(),
        "active": True,
    }
    _psave("sect_promo_comp")
    return (
        f"🏆 مسابقه ارتقا به <b>{target_status}</b> شروع شد." + chr(10)
        + f"مدت: {hours} ساعت" + chr(10)
        + "اعضا با /promocompete امتیاز می‌گیرند (مأموریت/مشارکت)." + chr(10)
        + "پایان: /endpromocomp (رهبر) یا خودکار"
    )


def add_promo_score(sect_id: int, tg_id: int, points: int = 1) -> None:
    m = _promo()
    sk = str(int(sect_id))
    data = m.get(sk)
    if not data or not data.get("active"):
        return
    try:
        if datetime.utcnow() > datetime.fromisoformat(data["ends"]):
            data["active"] = False
            m[sk] = data
            _psave("sect_promo_comp")
            return
    except Exception:
        pass
    scores = data.setdefault("scores", {})
    scores[str(int(tg_id))] = int(scores.get(str(int(tg_id)), 0) or 0) + int(points)
    data["scores"] = scores
    m[sk] = data
    _psave("sect_promo_comp")


def promo_status(sect_id: int) -> str:
    m = _promo()
    data = m.get(str(int(sect_id)))
    if not data:
        return "مسابقه ارتقایی فعال نیست. رهبر: /startpromocomp مقصد"
    scores = data.get("scores") or {}
    ranked = sorted(scores.items(), key=lambda x: -int(x[1]))
    lines = [
        f"🏆 مسابقه ارتقا → <b>{data.get('target')}</b>",
        f"{'🟢 فعال' if data.get('active') else '🔴 تمام‌شده'}",
        f"پایان: {data.get('ends', '')[:16]}",
        "",
    ]
    if not ranked:
        lines.append("هنوز امتیازی ثبت نشده. /promocompete")
    else:
        for i, (tg, sc) in enumerate(ranked[:10], 1):
            lines.append(f"{i}. `{tg}` — {sc} امتیاز")
    lines += ["", "/promocompete — ثبت امتیاز رقابت", "/endpromocomp — اعلام برنده (رهبر)"]
    return chr(10).join(lines)


def end_promo_comp(sect_id: int) -> tuple[str | None, str]:
    """برمی‌گرداند (برنده_tg یا None, پیام)"""
    m = _promo()
    sk = str(int(sect_id))
    data = m.get(sk)
    if not data:
        return None, "مسابقه‌ای نیست."
    scores = data.get("scores") or {}
    data["active"] = False
    m[sk] = data
    _psave("sect_promo_comp")
    if not scores:
        return None, "کسی شرکت نکرد."
    winner_tg, sc = max(scores.items(), key=lambda x: int(x[1]))
    return str(winner_tg), (
        f"🏁 مسابقه تمام شد." + chr(10)
        + f"برنده: `{winner_tg}` با {sc} امتیاز" + chr(10)
        + f"مقصد ارتقا: <b>{data.get('target')}</b>" + chr(10)
        + "رهبر می‌تواند با /promotewinner وضعیت برنده را اعمال کند."
    )
