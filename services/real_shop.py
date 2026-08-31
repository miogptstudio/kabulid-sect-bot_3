"""فروشگاه ویژه با پرداخت دستی و تأیید ادمین.
پرداخت خارج از ربات انجام می‌شود؛ ربات فقط سفارش، رسید و وضعیت تأیید را نگه می‌دارد.
شماره کارت هرگز داخل کد قرار نمی‌گیرد و از محیط خوانده می‌شود.
"""
from __future__ import annotations
from datetime import datetime
import secrets
import asyncio
from services.persist import get_dict, save

_FULFILL_LOCK = asyncio.Lock()

PRODUCTS = {
    "rank_apprentice": {"name": "ارتقای رتبه — یک مرحله", "price_toman": 49000, "type": "rank", "promote_steps": 1, "description": "یک مرحله ارتقای رتبه پس از تأیید ادمین."},
    "rank_elder": {"name": "ارتقای رتبه — دو مرحله", "price_toman": 99000, "type": "rank", "promote_steps": 2, "description": "دو مرحله ارتقای رتبه پس از تأیید ادمین."},
    "rank_guardian": {"name": "ارتقای رتبه — سه مرحله", "price_toman": 199000, "type": "rank", "promote_steps": 3, "description": "سه مرحله ارتقای رتبه پس از تأیید ادمین."},
    "chest_pack_small": {"name": "بسته صندوق کوچک", "price_toman": 29000, "type": "bundle", "coins": 25000, "description": "۲۵٬۰۰۰ سکه؛ پاداش ثابت پس از تأیید."},
    "chest_pack_large": {"name": "بسته صندوق بزرگ", "price_toman": 79000, "type": "bundle", "coins": 100000, "description": "۱۰۰٬۰۰۰ سکه؛ پاداش ثابت پس از تأیید."},
}

def card_number() -> str:
    """شماره کارت مقصد را از env می‌خواند و فقط قالب ۱۶ رقمی را می‌پذیرد."""
    import os
    raw = os.getenv("PAYMENT_CARD_NUMBER", "").strip()
    digits = "".join(ch for ch in raw if ch.isdigit())
    if len(digits) != 16:
        return ""
    return digits


def payment_ready() -> bool:
    return bool(card_number())

def catalog():
    return [{"id": k, **v} for k, v in PRODUCTS.items()]

def create_order(tg_id: int, product_id: str) -> dict:
    if product_id not in PRODUCTS:
        raise ValueError("محصول پیدا نشد")
    orders = get_dict("real_shop_orders")
    # جلوگیری از چند سفارش همزمان تأییدنشده برای یک محصول/کاربر
    for o in orders.values():
        if int(o.get("tg_id", 0)) == int(tg_id) and o.get("product_id") == product_id and o.get("status") in {"pending", "receipt_submitted"}:
            return o
    oid = secrets.token_hex(8).upper()
    p = PRODUCTS[product_id]
    order = {
        "id": oid, "tg_id": int(tg_id), "product_id": product_id,
        "amount_toman": int(p["price_toman"]), "status": "pending",
        "receipt_file_id": None, "receipt_caption": None, "admin_id": None,
        "created_at": datetime.utcnow().isoformat(), "updated_at": datetime.utcnow().isoformat(),
    }
    orders[oid] = order
    save("real_shop_orders")
    return order

def get_order(order_id: str) -> dict | None:
    return get_dict("real_shop_orders").get(str(order_id).upper())

def list_orders(status: str | None = None, tg_id: int | None = None, product_id: str | None = None) -> list[dict]:
    rows = list(get_dict("real_shop_orders").values())
    if status and status != "all":
        rows = [o for o in rows if o.get("status") == status]
    if tg_id is not None:
        rows = [o for o in rows if int(o.get("tg_id", 0)) == int(tg_id)]
    if product_id:
        rows = [o for o in rows if o.get("product_id") == product_id]
    return sorted(rows, key=lambda o: o.get("created_at", ""), reverse=True)

def order_stats() -> dict:
    rows = list_orders()
    stats = {"total": len(rows), "pending": 0, "receipt_submitted": 0, "approved": 0, "rejected": 0, "revenue_toman": 0}
    for o in rows:
        st = o.get("status")
        if st in stats: stats[st] += 1
        if st == "approved": stats["revenue_toman"] += int(o.get("amount_toman", 0) or 0)
    return stats

def audit_log(order_id: str, action: str, admin_id: int, note: str = "") -> dict:
    logs = get_dict("real_shop_audit")
    lid = secrets.token_hex(8).upper()
    row = {"id": lid, "order_id": str(order_id).upper(), "action": action, "admin_id": int(admin_id), "note": note or "", "created_at": datetime.utcnow().isoformat()}
    logs[lid] = row
    save("real_shop_audit")
    return row

def get_audit(order_id: str) -> list[dict]:
    oid = str(order_id).upper()
    rows = [x for x in get_dict("real_shop_audit").values() if x.get("order_id") == oid]
    return sorted(rows, key=lambda x: x.get("created_at", ""), reverse=True)

def attach_receipt(order_id: str, file_id: str, caption: str | None = None) -> dict:
    orders = get_dict("real_shop_orders")
    oid = str(order_id).upper()
    if oid not in orders:
        raise ValueError("سفارش پیدا نشد")
    o = orders[oid]
    if o.get("status") not in {"pending", "receipt_submitted", "rejected"}:
        raise ValueError("این سفارش دیگر قابل ارسال رسید نیست")
    o.update(receipt_file_id=file_id, receipt_caption=caption or "", status="receipt_submitted", updated_at=datetime.utcnow().isoformat())
    save("real_shop_orders")
    return o

def set_status(order_id: str, status: str, admin_id: int | None = None, note: str = "") -> dict:
    orders = get_dict("real_shop_orders")
    oid = str(order_id).upper()
    if oid not in orders:
        raise ValueError("سفارش پیدا نشد")
    if status not in {"pending", "receipt_submitted", "approved", "rejected"}:
        raise ValueError("وضعیت نامعتبر است")
    o = orders[oid]
    o["status"] = status
    o["admin_id"] = int(admin_id) if admin_id else o.get("admin_id")
    o["updated_at"] = datetime.utcnow().isoformat()
    if status == "pending":
        o["receipt_file_id"] = None
        o["receipt_caption"] = None
    if note:
        o["admin_note"] = note
    save("real_shop_orders")
    if admin_id:
        audit_log(oid, status, int(admin_id), note)
    return o


async def fulfill_order(order_id: str, admin_id: int) -> dict:
    """تأیید سفارش با قفل فرآیندی؛ از دوبار اعمال شدن جایزه در تأیید همزمان جلوگیری می‌کند."""
    async with _FULFILL_LOCK:
        order = get_order(order_id)
        if not order:
            raise ValueError("سفارش پیدا نشد")
        if order.get("status") == "approved" or order.get("fulfilled_at"):
            return order
        if order.get("status") != "receipt_submitted":
            raise ValueError("این سفارش هنوز رسید قابل بررسی ندارد")
        product = PRODUCTS.get(order.get("product_id"))
        if not product:
            raise ValueError("محصول نامعتبر است")

        from database.engine import async_session
        from database.crud import get_user_by_telegram_id
        async with async_session() as session:
            user = await get_user_by_telegram_id(session, int(order["tg_id"]))
            if not user:
                raise ValueError("کاربر پیدا نشد")
            if product.get("type") == "bundle":
                # پاداش‌های فروشگاه در namespace پایدار ثبت می‌شوند.
                from services.advanced_systems import add_stat
                add_stat(user.telegram_id, "coins", int(product.get("coins", 0)))
                await session.commit()
            elif product.get("type") == "rank":
                from services.ranking import promote, can_promote
                for _ in range(int(product.get("promote_steps", 1))):
                    if can_promote(user):
                        promote(user)
                await session.commit()
            else:
                raise ValueError("نوع محصول نامعتبر است")

        order["fulfilled_at"] = datetime.utcnow().isoformat()
        return set_status(order_id, "approved", admin_id, "جایزه با تأیید ادمین اعمال شد.")
