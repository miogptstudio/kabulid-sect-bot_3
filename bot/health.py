import logging
import os
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
    """ورود روزانه وباپ: +۵ سنگ بهشتی یکبار در روز"""
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



# --- اتاقهای بازی وباپ ---
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



# ==================== WebApp V43: API یکپارچه ۹ آسمان ====================
import hashlib as _hashlib
import hmac as _hmac
import json as _json
from urllib.parse import parse_qsl as _parse_qsl


def _telegram_webapp_user_id(request):
    """احراز هویت WebApp با initData تلگرام؛ tg_id فقط fallback توسعه است."""
    init_data = request.headers.get("X-Telegram-Init-Data", "")
    token = os.getenv("BOT_TOKEN", "")
    if init_data and token:
        try:
            pairs = dict(_parse_qsl(init_data, keep_blank_values=True))
            received = pairs.pop("hash", "")
            auth_date = int(pairs.get("auth_date", "0"))
            # initData نباید برای مدت طولانی قابل replay باشد.
            if received and auth_date and abs(int(__import__('time').time()) - auth_date) <= 86400:
                data_check = "\n".join(f"{k}={v}" for k, v in sorted(pairs.items()))
                secret = _hmac.new(b"WebAppData", token.encode(), _hashlib.sha256).digest()
                calc = _hmac.new(secret, data_check.encode(), _hashlib.sha256).hexdigest()
                if _hmac.compare_digest(calc, received):
                    user_obj = _json.loads(pairs.get("user", "{}"))
                    if user_obj.get("id"):
                        return int(user_obj["id"])
        except Exception:
            pass
    raw = request.query.get("tg_id")
    try:
        return int(raw) if raw else None
    except Exception:
        return None


async def _web_user(request, session):
    from database.crud import get_user_by_telegram_id
    tid = _telegram_webapp_user_id(request)
    if not tid:
        return None
    user = await get_user_by_telegram_id(session, tid)
    return user


def _wallet_json(w):
    keys = ("coins", "spirit_stones", "heavenly_stones", "celestial_stones", "god_stones", "chaos_stones", "void_stones", "origin_stones", "karma_points", "destiny_stones", "immortal_stones", "creation_stones", "absolute_stones", "faith_stones", "dragon_coins", "eternal_ink")
    return {k: int(getattr(w, k, 0) or 0) for k in keys}


async def api_dashboard(request):
    from database.engine import async_session
    from services.cultivation import get_or_create_cultivation
    from services.economy import get_or_create_wallet
    from services.power import calc_power
    from services.open_world import sky_info, WORLD_NAME
    async with async_session() as session:
        user = await _web_user(request, session)
        if not user:
            return web.json_response({"error": "کاربر پیدا نشد؛ اول /start را بزن."}, status=404)
        c = await get_or_create_cultivation(session, user.id)
        w = await get_or_create_wallet(session, user.id)
        pw = await calc_power(session, user)
        si = sky_info(user)
        sect_name = None
        try:
            from services.sects import get_user_sect
            from database.models_v2 import Sect
            membership = await get_user_sect(session, user.id)
            if membership:
                ss = await session.get(Sect, membership.sect_id)
                sect_name = ss.name if ss else None
        except Exception:
            pass
        return web.json_response({"full_name": user.full_name, "rank": user.rank, "role": user.role, "level": user.level, "xp": user.xp, "power": int(pw.get("total", 0)), "cultivation": {"realm": c.realm, "stage": c.stage, "energy": c.energy, "root": c.spiritual_root}, "wallet": _wallet_json(w), "sect": sect_name, "world": WORLD_NAME, "sky": si["number"], "sky_name": si["name"], "world_x": int(user.world_x or 0), "world_y": int(user.world_y or 0), "city": user.city, "hunger": int(user.hunger or 0), "thirst": int(user.thirst or 0)})


async def api_world(request):
    from database.engine import async_session
    from services.open_world import world_state, sky_info, current_sky, _location_landmark
    async with async_session() as session:
        user = await _web_user(request, session)
        if not user:
            return web.json_response({"error": "کاربر پیدا نشد"}, status=404)
        d = world_state(); info = sky_info(user); x,y=int(user.world_x or 0),int(user.world_y or 0)
        event=d.get("event"); boss=d.get("boss")
        boss_out=None
        if boss and boss.get("hp",0)>0:
            boss_out={"name":boss.get("name"),"subtitle":boss.get("subtitle"),"hp":boss.get("hp"),"max_hp":boss.get("max_hp"),"x":boss.get("x"),"y":boss.get("y")}
            from services.open_world import boss_phase
            boss_out["phase"]=boss_phase(boss)
        return web.json_response({"world":d.get("world_name"),"sky":current_sky(user),"sky_name":info["name"],"lore":info["lore"],"x":x,"y":y,"city":user.city,"hunger":user.hunger,"thirst":user.thirst,"danger":min(100,8+(abs(x)+abs(y))//5),"landmark":_location_landmark(x,y,current_sky(user)),"landmarks":info["landmarks"],"event":event,"boss":boss_out,"skies":[{"number":n,"name":v["name"]} for n,v in __import__('services.open_world',fromlist=['SKIES']).SKIES.items()]})


async def api_sect_full(request):
    from database.engine import async_session
    from database.models_v2 import Sect, SectMember
    from sqlalchemy import select, desc
    async with async_session() as session:
        user=await _web_user(request,session)
        if not user:return web.json_response({"error":"کاربر پیدا نشد"},status=404)
        m=(await session.execute(select(SectMember).where(SectMember.user_id==user.id))).scalar_one_or_none()
        mine=None
        if m:
            s=await session.get(Sect,m.sect_id)
            if s: mine={"name":s.name,"sect_type":s.sect_type,"member_count":s.member_count,"power_level":int(s.power_level or 0),"leader_power":int(s.leader_power or 0),"parent":None}
            if s and s.parent_sect_id:
                ps=await session.get(Sect,s.parent_sect_id); mine["parent"]=ps.name if ps else None
        rows=(await session.execute(select(Sect).where(Sect.is_active==True).order_by(desc(Sect.power_level)).limit(50))).scalars().all()
        return web.json_response({"mine":mine,"all":[{"name":s.name,"sect_type":s.sect_type,"member_count":s.member_count,"power_level":int(s.power_level or 0),"leader_power":int(s.leader_power or 0)} for s in rows]})


async def api_characters_full(request):
    from services import characters as chars
    tid=_telegram_webapp_user_id(request)
    if not tid:return web.json_response({"error":"Telegram user لازم است"},status=400)
    bag=list(chars._owned.get(tid) or [])
    return web.json_response({"total_power":chars.total_power_bonus(tid),"characters":sorted([{"name":c.get("name"),"rarity":c.get("rarity"),"power":int(c.get("power",0)),"base_power":int(c.get("base_power",0)),"stars":int(c.get("stars",1)),"emoji":c.get("emoji"),"description":c.get("description"),"portrait":c.get("portrait")} for c in bag],key=lambda x:x["power"],reverse=True)})


async def api_shop_full(request):
    from database.engine import async_session
    from services.shop import get_buildings, get_items_of_building
    async with async_session() as session:
        user=await _web_user(request,session)
        if not user:return web.json_response({"error":"کاربر پیدا نشد"},status=404)
        buildings=await get_buildings(session)
        bid=request.query.get("building_id")
        items=[]
        selected=buildings
        if bid:
            try:selected=[b for b in buildings if int(b.id)==int(bid)]
            except: selected=[]
        for b in selected:
            for it in await get_items_of_building(session,b.id):
                eff=it.effect if isinstance(it.effect,dict) else {}
                cur=eff.get("currency","coins")
                names={"coins":"سکه","spirit_stones":"سنگ روحی","heavenly_stones":"سنگ بهشتی","celestial_stones":"سنگ آسمانی","god_stones":"سنگ خدا","eternal_ink":"جوهر ازلی"}
                items.append({"id":it.id,"building_id":b.id,"name":it.name,"item_type":it.item_type,"description":it.description,"price":int(it.price or 0),"currency":cur,"currency_name":names.get(cur,cur),"stock":it.stock})
        return web.json_response({"buildings":[{"id":b.id,"name":b.name,"type":b.building_type} for b in buildings],"items":items})


async def api_chests_full(request):
    from services.advanced_systems import CHEST_RANKS
    from services.persist import get_dict
    tid=_telegram_webapp_user_id(request)
    if not tid:return web.json_response({"error":"Telegram user لازم است"},status=400)
    row=get_dict("chests").get(str(tid),{})
    cooldown=0
    last=row.get("last_open_at")
    if last:
        from datetime import datetime, timedelta
        try: cooldown=max(0,int((timedelta(hours=24)-(datetime.utcnow()-datetime.fromisoformat(str(last)))).total_seconds()))
        except: pass
    return web.json_response({"opened":int(row.get("opened",0)),"last_grade":row.get("last_grade"),"cooldown":cooldown,"shop":[{"rank":r,"price":v["price"],"low":v["range"][0],"high":v["range"][1]} for r,v in CHEST_RANKS.items() if v["price"]>0]})


async def api_action(request):
    from database.engine import async_session
    from services.open_world import move, feed, drink, create_city, create_country, challenge_heaven_stair, world_state, hit_boss, boss_attack_text
    from services import characters as chars
    from services.advanced_systems import open_chest, CHEST_RANKS
    from services.shop import buy_item, get_items_of_building
    from database.models_v3 import ShopItem
    from services.economy import get_or_create_wallet, pay_specific_currency
    from sqlalchemy import select
    try: body=await request.json()
    except: body={}
    action=str(body.get("action") or "")
    async with async_session() as session:
        user=await _web_user(request,session)
        if not user:return web.json_response({"error":"احراز هویت نامعتبر است"},status=401)
        try:
            if action=="move":
                direction=str(body.get("direction")); result=move(user,direction)
                await session.commit(); return web.json_response({"ok":True,"message":f"حرکت به {result.get('direction','')} انجام شد؛ مختصات ({result.get('x')},{result.get('y')})","result":result})
            if action=="feed": feed(user); await session.commit(); return web.json_response({"ok":True,"message":f"گرسنگی: {user.hunger}%"})
            if action=="drink": drink(user); await session.commit(); return web.json_response({"ok":True,"message":f"تشنگی: {user.thirst}%"})
            if action=="create_city": ok,msg=create_city(user,str(body.get("name") or "")); await session.commit(); return web.json_response({"ok":ok,"message":msg},status=200 if ok else 400)
            if action=="create_country": ok,msg=create_country(user,str(body.get("name") or "")); await session.commit(); return web.json_response({"ok":ok,"message":msg},status=200 if ok else 400)
            if action=="heaven_stair":
                from services.power import calc_power
                pw=int((await calc_power(session,user)).get("total",1)); r=challenge_heaven_stair(user,pw); await session.commit(); return web.json_response({"ok":r["ok"],"message":r["message"]},status=200 if r["ok"] else 400)
            if action=="boss_attack":
                b=world_state().get("boss")
                if not b or b.get("hp",0)<=0:return web.json_response({"error":"باس فعالی وجود ندارد"},status=400)
                if (int(user.world_x),int(user.world_y))!=(int(b.get("x")),int(b.get("y"))):return web.json_response({"error":f"باس در ({b.get('x')},{b.get('y')}) است"},status=400)
                from services.power import calc_power
                pw=int((await calc_power(session,user)).get("total",100)); bb,dmg=hit_boss(user.telegram_id,max(100,pw//3)); await session.commit()
                return web.json_response({"ok":True,"message":f"⚔️ {dmg:,} آسیب وارد شد. باس: {bb.get('hp',0):,}/{bb.get('max_hp',0):,}\n{boss_attack_text(bb)}"})
            if action=="pull_character":
                w=await get_or_create_wallet(session,user.id); cost=chars.PULL_COST_COINS
                if int(w.coins or 0)<cost:return web.json_response({"error":f"سکه کافی نیست؛ نیاز {cost:,}"},status=400)
                ok,msg,card=chars.pull(user.telegram_id)
                if not ok:return web.json_response({"error":msg},status=400)
                w.coins-=cost; await session.commit(); return web.json_response({"ok":True,"message":msg,"card":card})
            if action=="merge_characters": return web.json_response({"ok":True,"message":chars.merge_duplicates(user.telegram_id)})
            if action=="buy_item":
                item=await session.get(ShopItem,int(body.get("item_id") or 0))
                if not item:return web.json_response({"error":"آیتم پیدا نشد"},status=404)
                msg=await buy_item(session,user,item,int(body.get("qty") or 1)); return web.json_response({"ok":msg.startswith("✅"),"message":msg},status=200 if msg.startswith("✅") else 400)
            if action=="open_chest":
                amount,left,grade=open_chest(user.telegram_id)
                if left:return web.json_response({"error":f"صندوق روزانه آماده نیست؛ {left//3600} ساعت و {(left%3600)//60} دقیقه باقی مانده"},status=400)
                w=await get_or_create_wallet(session,user.id); w.coins=int(w.coins or 0)+int(amount or 0); await session.commit()
                return web.json_response({"ok":True,"message":f"🎁 صندوق {grade} باز شد؛ +{amount:,} سکه"})
            if action=="buy_chest":
                grade=str(body.get("grade") or ""); cfg=CHEST_RANKS.get(grade)
                if not cfg or cfg["price"]<=0:return web.json_response({"error":"رتبه صندوق نامعتبر است"},status=400)
                w=await get_or_create_wallet(session,user.id); price=int(cfg["price"])
                if int(w.coins or 0)<price:return web.json_response({"error":f"سکه کافی نیست؛ نیاز {price:,}"},status=400)
                import random
                amount=random.randint(*cfg["range"]); w.coins-=price; w.coins+=amount; await session.commit()
                return web.json_response({"ok":True,"message":f"🧰 صندوق {grade} خریدی و +{amount:,} سکه گرفتی."})
            return web.json_response({"error":"عملیات ناشناخته"},status=400)
        except Exception as exc:
            await session.rollback(); logger.exception("web action failed")
            return web.json_response({"error":type(exc).__name__+": "+str(exc)[:220]},status=400)


async def api_admin_summary(request):
    from database.engine import async_session
    from database.models import User
    from database.models_v2 import Sect
    from sqlalchemy import select, func
    async with async_session() as session:
        user=await _web_user(request,session)
        if not user or not user.is_staff:return web.json_response({"error":"دسترسی مدیریت نداری"},status=403)
        players=int((await session.execute(select(func.count()).select_from(User))).scalar() or 0)
        active=int((await session.execute(select(func.count()).select_from(User).where(User.is_active==True,User.is_banned==False))).scalar() or 0)
        sects=int((await session.execute(select(func.count()).select_from(Sect).where(Sect.is_active==True))).scalar() or 0)
        return web.json_response({"role":user.role,"players":players,"active":active,"sects":sects})


async def api_admin_sync(request):
    from database.engine import async_session
    async with async_session() as session:
        user=await _web_user(request,session)
        if not user or not user.is_staff:return web.json_response({"error":"دسترسی مدیریت نداری"},status=403)
        try:
            from services.persist import sync_to_db
            await sync_to_db(); return web.json_response({"ok":True,"message":"همگام‌سازی داده‌ها انجام شد."})
        except Exception as e:return web.json_response({"error":str(e)},status=400)

async def start_health_server(port: int = 8080):
    app = web.Application()
    app.router.add_get("/", health_handler)
    app.router.add_get("/health", health_handler)
    app.router.add_get("/api/profile", api_profile)
    app.router.add_get("/api/dashboard", api_dashboard)
    app.router.add_get("/api/world", api_world)
    app.router.add_get("/api/ranking", api_ranking)
    app.router.add_get("/api/sects", api_sects)
    app.router.add_get("/api/sect", api_sect_full)
    app.router.add_get("/api/characters", api_characters_full)
    app.router.add_get("/api/shop", api_shop_full)
    app.router.add_get("/api/chests", api_chests_full)
    app.router.add_get("/api/daily", api_daily)
    app.router.add_get("/api/arena", api_arena_top)
    app.router.add_get("/api/game", api_game_room)
    app.router.add_post("/api/game", api_game_room)
    app.router.add_post("/api/action", api_action)
    app.router.add_get("/api/admin", api_admin_summary)
    app.router.add_post("/api/admin/sync", api_admin_sync)

    # مینیاپ استاتیک
    if WEBAPP_DIR.is_dir():
        app.router.add_get("/app", lambda r: web.FileResponse(WEBAPP_DIR / "index.html"))
        app.router.add_get("/app/", lambda r: web.FileResponse(WEBAPP_DIR / "index.html"))
        app.router.add_static("/app/static", WEBAPP_DIR, show_index=False)
        assets_dir = WEBAPP_DIR.parent / "assets"
        if assets_dir.is_dir():
            app.router.add_static("/assets", assets_dir, show_index=False)
        # مسیرهای مستقیم فایلهای وب
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
