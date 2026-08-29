"""اجرای دستورات ربات بدون اسلش.
این middleware نام همه Commandهای ثبت‌شده را از فایل‌های handler استخراج می‌کند
تا هر دستور مثل «پروفایل»، «خدمتکارها»، «خریدخدمتکار 1» و ... بدون / هم کار کند.
"""
import ast
from pathlib import Path
from typing import Any, Awaitable, Callable

from aiogram import BaseMiddleware
from aiogram.types import Message


_ZERO_WIDTH = "\u200c\u200d\u200e\u200f\ufeff"

def normalize(value: str) -> str:
    value = (value or "").strip().lower()
    for ch in _ZERO_WIDTH:
        value = value.replace(ch, "")
    return "".join(value.split())


def load_command_aliases() -> dict[str, str]:
    """Return normalized alias -> canonical command name."""
    handlers_dir = Path(__file__).resolve().parents[1] / "handlers"
    aliases: dict[str, str] = {
        normalize("شروع"): "start",
        normalize("شروع بازی"): "start",
        normalize("کمک"): "help",
    }
    for path in handlers_dir.glob("*.py"):
        try:
            tree = ast.parse(path.read_text(encoding="utf-8"))
        except Exception:
            continue
        for node in ast.walk(tree):
            if not isinstance(node, ast.Call):
                continue
            if not isinstance(node.func, ast.Name) or node.func.id != "Command":
                continue
            values = [a.value for a in node.args if isinstance(a, ast.Constant) and isinstance(a.value, str)]
            if not values:
                continue
            canonical = values[0]
            for value in values:
                key = normalize(value)
                if key:
                    aliases.setdefault(key, canonical)
    return aliases


class TextCommandMiddleware(BaseMiddleware):
    """قبل از routerها، متن را اگر نام یک Command باشد به /command تبدیل می‌کند."""
    def __init__(self) -> None:
        super().__init__()
        self.aliases = load_command_aliases()
        # بعضی نام‌ها عمداً بین دو سیستم مشترک‌اند؛ این نگاشت‌ها باید
        # با معنای منوی اصلی ثابت بمانند و به ترتیب اسکن فایل‌ها وابسته نباشند.
        self.aliases.update({
            normalize("مقاممن"): "iamadmin",
            normalize("شهرها"): "worldcities",
            normalize("قلمروها"): "territories",
        })
        self._sorted = sorted(self.aliases, key=len, reverse=True)

    def _rewrite(self, text: str) -> str | None:
        raw = (text or "").strip()
        if not raw or raw.startswith("/"):
            return None
        words = raw.split()
        # حداکثر 5 کلمه برای aliasهای طبیعی فارسی.
        for count in range(min(5, len(words)), 0, -1):
            head = " ".join(words[:count])
            key = normalize(head)
            canonical = self.aliases.get(key)
            if canonical:
                args = " ".join(words[count:])
                return "/" + canonical + ((" " + args) if args else "")
        return None

    async def __call__(
        self,
        handler: Callable[[Any, dict], Awaitable[Any]],
        event: Any,
        data: dict,
    ) -> Any:
        if isinstance(event, Message) and event.text and not event.text.lstrip().startswith("/"):
            rewritten = self._rewrite(event.text)
            if rewritten:
                event = event.model_copy(update={"text": rewritten})
        return await handler(event, data)
