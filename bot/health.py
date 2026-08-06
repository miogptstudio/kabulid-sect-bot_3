import logging
from pathlib import Path
from aiohttp import web

logger = logging.getLogger(__name__)

WEBAPP_DIR = Path(__file__).resolve().parent.parent / "webapp"


async def health_handler(request):
    return web.Response(text="Bot is running ✅", status=200)


async def api_profile(request):
    tg_id = request.query.get("tg_id")
    if not tg_id:
        return web.json_response({"error": "tg_id لازم است"}, status=400)
    try:
        tg_id = int(tg_id)
    except ValueError:
        return web.json_response({"error": "tg_id نامعتبر"}, status=400)

    from database.engine import async_session
    from database.crud import get_user_by_telegram_id
    from services.cultivation import get_or_create_cultivation
    from services.sects import get_user_sect
    from database.models_v2 import Sect

    async with async_session() as session:
        user = await get_user_by_telegram_id(session, tg_id)
        if not user:
            return web.json_response({"error": "کاربر پیدا نشد. اول /start بزن."})

        cult = None
        try:
            c = await get_or_create_cultivation(session, user.id)
            cult = {"realm": c.realm, "stage": c.stage, "energy": c.energy, "root": c.spiritual_root}
        except Exception:
            pass

        sect_name = None
        try:
            m = await get_user_sect(session, user.id)
            if m:
                s = await session.get(Sect, m.sect_id)
                if s:
                    sect_name = s.name
        except Exception:
            pass

        return web.json_response({
            "full_name": user.full_name,
            "rank": user.rank,
            "role": user.role,
            "level": user.level,
            "xp": user.xp,
            "gender": user.gender,
            "wins": user.wins,
            "losses": user.losses,
            "cultivation": cult,
            "sect": sect_name,
        })


async def api_ranking(request):
    from database.engine import async_session
    from database.models import User
    from services.ranking import get_rank_index
    from sqlalchemy import select

    async with async_session() as session:
        result = await session.execute(
            select(User).where(User.is_active == True, User.is_banned == False)
        )
        users = list(result.scalars().all())
        users = sorted(users, key=lambda u: (-get_rank_index(u.rank), -u.xp, -u.wins))[:3]
        return web.json_response({
            "top": [
                {"full_name": u.full_name, "rank": u.rank, "level": u.level, "xp": u.xp, "wins": u.wins, "losses": u.losses}
                for u in users
            ]
        })


async def api_sects(request):
    from database.engine import async_session
    from database.models_v2 import Sect
    from sqlalchemy import select

    async with async_session() as session:
        result = await session.execute(select(Sect).where(Sect.is_active == True))
        sects = result.scalars().all()
        return web.json_response({
            "sects": [
                {"name": s.name, "sect_type": s.sect_type, "member_count": s.member_count, "total_points": s.total_points}
                for s in sects
            ]
        })



async def api_daily(request):
    """ورود روزانه وب‌اپ: +۵ سنگ بهشتی یک‌بار در روز"""
    tg_id = request.query.get("tg_id")
    if not tg_id:
        return web.json_response({"error": "tg_id لازم است"}, status=400)
    try:
        tg_id = int(tg_id)
    except ValueError:
        return web.json_response({"error": "نامعتبر"}, status=400)
    from datetime import datetime, date
    from database.engine import async_session
    from database.crud import get_user_by_telegram_id
    from services.economy import get_or_create_wallet

    async with async_session() as session:
        user = await get_user_by_telegram_id(session, tg_id)
        if not user:
            return web.json_response({"error": "اول در ربات /start بزن"})
        w = await get_or_create_wallet(session, user.id)
        today = date.today()
        last = getattr(w, "last_daily_web", None) or getattr(w, "last_daily_coin", None)
        # reuse last_daily_coin if no separate field - check coins daily field OR store in spirit as marker
        # use last_daily_coin date for simplicity separate key via checking a note
        # Store web daily on last_daily_coin only if we add field - use heavenly claim via checking
        from sqlalchemy import text as sqltext
        # Simple: use last_daily_coin for bot dailycoin; for web use a file-less approach with last_daily_coin + 1 day offset
        # Better: add attribute last_web_daily if column exists
        claimed = False
        if hasattr(w, "last_daily_coin") and w.last_daily_coin and w.last_daily_coin.date() == today:
            # allow separate web daily - use spirit_stones modulo trick no
            pass
        # Use coins field as last web daily stored in a JSON - simplest: check heaven claimed today via comparing
        # Add in-memory daily set
        global _web_daily
        try:
            _web_daily
        except NameError:
            _web_daily = set()
        key = (tg_id, today.isoformat())
        if key in _web_daily:
            return web.json_response({"ok": False, "msg": "امروز پاداش ورود را گرفتی."})
        w.heavenly_stones = (w.heavenly_stones or 0) + 5
        _web_daily.add(key)
        await session.commit()
        return web.json_response({
            "ok": True,
            "msg": "+۵ سنگ بهشتی",
            "heavenly_stones": w.heavenly_stones,
        })


async def api_arena_top(request):
    from database.engine import async_session
    from services.arena import arena_leaderboard
    # return structured
    from database.models_v2 import ArenaProfile
    from database.models import User
    from sqlalchemy import select, desc
    async with async_session() as session:
        result = await session.execute(
            select(ArenaProfile, User)
            .join(User, ArenaProfile.user_id == User.id)
            .order_by(desc(ArenaProfile.points))
            .limit(15)
        )
        rows = result.all()
        return web.json_response({
            "top": [
                {"full_name": u.full_name, "tier": p.tier, "points": p.points, "wins": p.wins, "losses": p.losses}
                for p, u in rows
            ]
        })



# --- اتاق‌های بازی وب‌اپ ---
_game_rooms: dict[str, dict] = {}

def _new_code() -> str:
    import random, string
    return "".join(random.choices(string.ascii_uppercase + string.digits, k=5))

async def api_game_room(request):
    """ساخت/ورود/وضعیت اتاق بازی: chess|rps|hukum|nard"""
    import json
    from aiohttp import web
    action = request.query.get("action", "status")
    code = (request.query.get("code") or "").upper()
    game = request.query.get("game", "chess")
    tg_id = request.query.get("tg_id")
    name = request.query.get("name") or "بازیکن"
    try:
        tg_id = int(tg_id) if tg_id else None
    except ValueError:
        return web.json_response({"error": "tg_id"}, status=400)

    if action == "create":
        max_p = {"chess": 2, "rps": 2, "nard": 2, "hukum": 8}.get(game, 2)
        code = _new_code()
        _game_rooms[code] = {
            "game": game,
            "players": [{"id": tg_id, "name": name}],
            "max": max_p,
            "state": {},
            "turn": 0,
        }
        return web.json_response({"code": code, "players": _game_rooms[code]["players"], "max": max_p})

    if action == "join":
        room = _game_rooms.get(code)
        if not room:
            return web.json_response({"error": "اتاق پیدا نشد"})
        if any(p["id"] == tg_id for p in room["players"]):
            return web.json_response({"code": code, "players": room["players"], "max": room["max"]})
        if len(room["players"]) >= room["max"]:
            return web.json_response({"error": "اتاق پر است"})
        room["players"].append({"id": tg_id, "name": name})
        return web.json_response({"code": code, "players": room["players"], "max": room["max"]})

    if action == "status":
        room = _game_rooms.get(code)
        if not room:
            return web.json_response({"error": "اتاق نیست"})
        return web.json_response(room)

    if action == "move":
        room = _game_rooms.get(code)
        if not room:
            return web.json_response({"error": "اتاق نیست"})
        try:
            body = await request.json()
        except Exception:
            body = {}
        # فقط بازیکن داخل اتاق
        if tg_id and not any(p.get("id") == tg_id for p in room.get("players", [])):
            return web.json_response({"error": "عضو این اتاق نیستی"})
        if "state" in body and body["state"] is not None:
            room["state"] = body["state"]
        if "turn" in body and body["turn"] is not None:
            room["turn"] = body["turn"]
        return web.json_response({"ok": True, "state": room["state"], "turn": room["turn"], "players": room["players"]})

    return web.json_response({"error": "action نامعتبر"})


async def start_health_server(port: int = 8080):
    app = web.Application()
    app.router.add_get("/", health_handler)
    app.router.add_get("/health", health_handler)
    app.router.add_get("/api/profile", api_profile)
    app.router.add_get("/api/ranking", api_ranking)
    app.router.add_get("/api/sects", api_sects)
    app.router.add_get("/api/daily", api_daily)
    app.router.add_get("/api/arena", api_arena_top)
    app.router.add_get("/api/game", api_game_room)
    app.router.add_post("/api/game", api_game_room)

    # مینی‌اپ استاتیک
    if WEBAPP_DIR.is_dir():
        app.router.add_get("/app", lambda r: web.FileResponse(WEBAPP_DIR / "index.html"))
        app.router.add_get("/app/", lambda r: web.FileResponse(WEBAPP_DIR / "index.html"))
        app.router.add_static("/app/static", WEBAPP_DIR, show_index=False)
        # مسیرهای مستقیم فایل‌های وب
        async def serve_webapp_file(request):
            name = request.match_info.get("filename", "index.html")
            path = WEBAPP_DIR / name
            if not path.is_file() or not str(path.resolve()).startswith(str(WEBAPP_DIR.resolve())):
                raise web.HTTPNotFound()
            return web.FileResponse(path)

        app.router.add_get("/webapp", lambda r: web.FileResponse(WEBAPP_DIR / "index.html"))
        app.router.add_get("/webapp/", lambda r: web.FileResponse(WEBAPP_DIR / "index.html"))
        app.router.add_get("/webapp/{filename}", serve_webapp_file)
        logger.info(f"WebApp mounted from {WEBAPP_DIR}")
    else:
        logger.warning("webapp directory not found")

    runner = web.AppRunner(app)
    await runner.setup()
    site = web.TCPSite(runner, "0.0.0.0", port)
    await site.start()
    logger.info(f"Health + WebApp server on port {port}")
