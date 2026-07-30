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
                {"full_name": u.full_name, "rank": u.rank, "level": u.level, "xp": u.xp, "wins": u.wins}
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


async def start_health_server(port: int = 8080):
    app = web.Application()
    app.router.add_get("/", health_handler)
    app.router.add_get("/health", health_handler)
    app.router.add_get("/api/profile", api_profile)
    app.router.add_get("/api/ranking", api_ranking)
    app.router.add_get("/api/sects", api_sects)

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
