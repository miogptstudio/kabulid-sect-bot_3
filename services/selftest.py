"""خودآزمایی ربات — ایمپورت ماژول‌ها + تست سرویس‌های امن."""
from __future__ import annotations
import importlib
import traceback
from typing import Callable, Any

HANDLER_MODULES = [
    "bot.handlers.start",
    "bot.handlers.profile",
    "bot.handlers.cultivation",
    "bot.handlers.sects",
    "bot.handlers.shop",
    "bot.handlers.social",
    "bot.handlers.marriage",
    "bot.handlers.dual",
    "bot.handlers.combat",
    "bot.handlers.help_menu",
    "bot.handlers.admin",
    "bot.handlers.arena",
    "bot.handlers.ranking",
    "bot.handlers.missions",
    "bot.handlers.crafting",
    "bot.handlers.jobs_events",
    "bot.handlers.characters",
    "bot.handlers.codex_items",
    "bot.handlers.pets",
    "bot.handlers.guardian",
    "bot.handlers.duel",
    "bot.handlers.text_navigation",
    "bot.handlers.advanced_systems",
    "bot.handlers.retention",
    "bot.handlers.engagement",
    "bot.handlers.prison_market",
    "bot.handlers.death",
    "bot.handlers.world",
    "bot.handlers.race",
    "bot.handlers.spirit",
    "bot.handlers.lang",
    "bot.handlers.garden",
    "bot.handlers.games",
    "bot.handlers.creatures",
    "bot.handlers.combat_extra",
    "bot.handlers.society_extra",
    "bot.handlers.master",
    "bot.handlers.accounts",
    "bot.handlers.fallback",
]

SERVICE_MODULES = [
    "services.staff",
    "services.servants",
    "services.economy",
    "services.sect_systems",
    "services.sects",
    "services.immortal",
    "services.cultivation",
    "services.power",
    "services.dual",
    "services.roles",
    "bot.servant_images",
    "bot.panel_images",
    "bot.utils.servant_panel",
]


def _run(label: str, fn: Callable[[], Any]) -> tuple[str, bool, str]:
    try:
        fn()
        return label, True, "OK"
    except Exception as e:
        tb = traceback.format_exc()
        return label, False, f"{type(e).__name__}: {e}\n{tb[-500:]}"


def run_selftest(tg_id: int | None = None) -> str:
    lines: list[str] = ["🧪 <b>نتیجه /testall</b>", ""]
    ok_n = 0
    fail_n = 0
    fails: list[str] = []

    lines.append("<b>۱) ایمپورت هندلرها</b>")
    for mod in HANDLER_MODULES:
        def _imp(m=mod):
            importlib.import_module(m)
        label, ok, msg = _run(mod, _imp)
        if ok:
            ok_n += 1
            lines.append(f"✅ {mod}")
        else:
            fail_n += 1
            lines.append(f"❌ {mod}")
            fails.append(f"❌ {mod}\n{msg}")

    lines.append("\n<b>۲) ایمپورت سرویس‌ها</b>")
    for mod in SERVICE_MODULES:
        def _imp(m=mod):
            importlib.import_module(m)
        label, ok, msg = _run(mod, _imp)
        if ok:
            ok_n += 1
            lines.append(f"✅ {mod}")
        else:
            fail_n += 1
            lines.append(f"❌ {mod}")
            fails.append(f"❌ {mod}\n{msg}")

    lines.append("\n<b>۳) نمادهای حیاتی</b>")
    symbol_checks = [
        ("codex cmd_item_codex", "bot.handlers.codex_items", "cmd_item_codex"),
        ("codex cmd_codex alias", "bot.handlers.codex_items", "cmd_codex"),
        ("servants_v2", "bot.handlers.social", "cmd_servants_v2"),
        ("profile", "bot.handlers.profile", "cmd_profile"),
        ("cultivation", "bot.handlers.cultivation", "cmd_cultivation"),
        ("help", "bot.handlers.help_menu", "cmd_help"),
        ("servants.buy", "services.servants", "buy"),
        ("servants.train", "services.servants", "train"),
        ("staff.get_staff", "services.staff", "get_staff"),
        ("sect_systems.deposit", "services.sect_systems", "deposit"),
    ]
    for label, mod, attr in symbol_checks:
        def _chk(m=mod, a=attr):
            modu = importlib.import_module(m)
            if not hasattr(modu, a):
                raise AttributeError(f"{m}.{a} missing")
        lb, ok, msg = _run(label, _chk)
        if ok:
            ok_n += 1
            lines.append(f"✅ {label}")
        else:
            fail_n += 1
            lines.append(f"❌ {label}")
            fails.append(f"❌ {label}\n{msg}")

    lines.append("\n<b>۴) فراخوانی امن سرویس‌ها</b>")

    def _servants_market():
        from services import servants as s
        assert len(s.MARKET) > 0
        s.market_list()
        if tg_id:
            s.list_owned(int(tg_id))
            s.owned_text(int(tg_id))

    def _staff():
        from services.staff import get_staff, list_staff, staff_help_text
        if tg_id:
            get_staff(int(tg_id))
            staff_help_text(int(tg_id))
        list_staff()

    def _images():
        from bot.servant_images import get_servant_image_by_id
        from pathlib import Path
        missing = []
        for i in range(1, 37):
            p = get_servant_image_by_id(i)
            if not p or not Path(p).exists():
                missing.append(i)
        if missing:
            raise FileNotFoundError(f"missing servant images: {missing[:10]}")

    def _panels():
        from bot.panel_images import get_panel_image
        for k in ("help", "shop", "sect", "profile"):
            p = get_panel_image(k, "female" if k == "profile" else None)
            if p is None:
                raise FileNotFoundError(f"panel missing: {k}")

    def _train_cd():
        from services.servants import _train_cooldown_seconds
        assert _train_cooldown_seconds(1, 18) == 30
        assert _train_cooldown_seconds(1, 1) >= 300

    def _text_nav_imports():
        import re
        import bot.handlers.text_navigation as tn
        text = open(tn.__file__, encoding="utf-8").read()
        blocks = re.findall(
            r"from bot\.handlers\.(\w+) import (\w+)\s*\n\s*await (\w+)\(",
            text,
        )
        bad = []
        for mod, imported, awaited in blocks:
            if imported != awaited:
                bad.append(f"{mod}: import {imported} await {awaited}")
            modu = importlib.import_module(f"bot.handlers.{mod}")
            if not hasattr(modu, imported):
                bad.append(f"missing {mod}.{imported}")
        if bad:
            raise RuntimeError("; ".join(bad[:15]))

    for label, fn in [
        ("servants market/list", _servants_market),
        ("staff ranks", _staff),
        ("servant images 1-36", _images),
        ("panel images", _panels),
        ("train cooldown unique", _train_cd),
        ("text_nav imports match", _text_nav_imports),
    ]:
        lb, ok, msg = _run(label, fn)
        if ok:
            ok_n += 1
            lines.append(f"✅ {label}")
        else:
            fail_n += 1
            lines.append(f"❌ {label}")
            fails.append(f"❌ {label}\n{msg}")

    lines.append("")
    lines.append(f"📊 جمع: ✅ {ok_n} | ❌ {fail_n}")
    if fails:
        lines.append("\n<b>جزئیات خطاها (کپی کن بفرست):</b>")
        detail = "\n\n".join(fails)
        if len(detail) > 3000:
            detail = detail[:3000] + "\n…"
        lines.append(f"<code>{detail}</code>")
    else:
        lines.append("\n🎉 خطای ایمپورت/سرویس پیدا نشد.")
        lines.append("این تست دستورات نیازمند ریپلای/اکشن خطرناک را اجرا نمی‌کند.")
    return "\n".join(lines)
