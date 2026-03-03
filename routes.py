import sqlite3
import json
import time
import urllib.parse
import httpx
from pathlib import Path
import hashlib
import csv
import io

from litestar import get, post, Request, Response
from litestar.response import Template, Redirect

from config import DB_DIR, MAIN_DB
from services import (
    steamid64_to_accountid, register_user, get_user_config,
    set_user_config, sync_user_matches, fetch_heroes, fetch_items,
    get_hero_image_url, heroes_cache, items_cache, init_main_db, fetch_match_details,
    fetch_player_profile, get_user_profile, fetch_player_peers
)

IMG_CACHE = Path("img_cache")
(IMG_CACHE / "heroes").mkdir(parents=True, exist_ok=True)
(IMG_CACHE / "items").mkdir(parents=True, exist_ok=True)

TRANSPARENT_1X1 = b'\x89PNG\r\n\x1a\n\x00\x00\x00\rIHDR\x00\x00\x00\x01\x00\x00\x00\x01\x08\x06\x00\x00\x00\x1f\x15\xc4\x89\x00\x00\x00\nIDATx\x9cc\x00\x01\x00\x00\x05\x00\x01\r\n-\xb4\x00\x00\x00\x00IEND\xaeB`\x82'

def get_current_user(request: Request) -> str | None:
    return request.cookies.get("account_id")

def check_admin_auth(request: Request) -> bool:
    return request.cookies.get("admin_auth") == "1"

def get_admin_setting(key: str):
    with sqlite3.connect(MAIN_DB) as conn:
        cursor = conn.execute("SELECT value FROM admin_settings WHERE key = ?", (key,))
        row = cursor.fetchone()
        return row[0] if row else None

def set_admin_setting(key: str, value: str):
    with sqlite3.connect(MAIN_DB) as conn:
        conn.execute("INSERT OR REPLACE INTO admin_settings (key, value) VALUES (?, ?)", (key, value))
        conn.commit()

def get_item_info(item_id: int):
    if not item_id or item_id == 0:
        return {"url": None, "name": "Vazio"}
    item = items_cache.get(str(item_id))
    name = item.get("dname", f"Item {item_id}") if item else f"Item {item_id}"
    return {"url": f"/img/item/{item_id}", "name": name}

@get("/img/hero/{hero_id:str}")
async def img_hero(hero_id: str) -> Response:
    cache_path = IMG_CACHE / "heroes" / f"{hero_id}.png"
    if cache_path.exists():
        return Response(content=cache_path.read_bytes(), media_type="image/png")

    hero_data = heroes_cache.get(hero_id)
    if hero_data and "name" in hero_data:
        short_name = hero_data["name"].replace("npc_dota_hero_", "")
        img_url = f"https://cdn.cloudflare.steamstatic.com/apps/dota2/images/heroes/{short_name}_lg.png"
        try:
            async with httpx.AsyncClient() as client:
                resp = await client.get(img_url)
                if resp.status_code == 200:
                    cache_path.write_bytes(resp.content)
                    return Response(content=resp.content, media_type="image/png")
        except Exception:
            pass
    return Response(content=TRANSPARENT_1X1, media_type="image/png")

@get("/img/item/{item_id:str}")
async def img_item(item_id: str) -> Response:
    cache_path = IMG_CACHE / "items" / f"{item_id}.png"
    if cache_path.exists():
        return Response(content=cache_path.read_bytes(), media_type="image/png")

    item_data = items_cache.get(item_id)
    if not item_data:
        return Response(content=TRANSPARENT_1X1, media_type="image/png")

    urls_to_try = []
    dname = item_data.get("dname")
    
    if dname:
        raw_name = dname.replace(" ", "_")
        filename = f"{raw_name}_itemicon_dota2_gameasset.png"
        md5_hash = hashlib.md5(filename.encode('utf-8')).hexdigest()
        url_filename = filename.replace("'", "%27")
        urls_to_try.append(f"https://liquipedia.net/commons/images/thumb/{md5_hash[0]}/{md5_hash[:2]}/{url_filename}/60px-{url_filename}")
        
        filename_alt = f"{raw_name}_itemicon.png"
        md5_hash_alt = hashlib.md5(filename_alt.encode('utf-8')).hexdigest()
        url_filename_alt = filename_alt.replace("'", "%27")
        urls_to_try.append(f"https://liquipedia.net/commons/images/thumb/{md5_hash_alt[0]}/{md5_hash_alt[:2]}/{url_filename_alt}/60px-{url_filename_alt}")

    if "name" in item_data:
        short_name = item_data["name"].replace("item_", "")
        urls_to_try.append(f"https://cdn.cloudflare.steamstatic.com/apps/dota2/images/dota_react/items/{short_name}.png")

    headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"}
    
    async with httpx.AsyncClient() as client:
        for img_url in urls_to_try:
            try:
                resp = await client.get(img_url, headers=headers)
                if resp.status_code == 200:
                    cache_path.write_bytes(resp.content)
                    return Response(content=resp.content, media_type="image/png")
            except Exception:
                continue
                
    return Response(content=TRANSPARENT_1X1, media_type="image/png")

@get("/")
async def login_page(request: Request) -> Template | Redirect:
    if get_current_user(request):
        return Redirect(path="/dashboard")
    error = request.query_params.get("error")
    return Template(template_name="login.html", context={"error": error})

@get("/login/steam")
async def login_steam(request: Request) -> Redirect:
    base_url = f"{request.url.scheme}://{request.url.netloc}"
    params = {
        'openid.ns': 'http://specs.openid.net/auth/2.0',
        'openid.mode': 'checkid_setup',
        'openid.return_to': f'{base_url}/login/steam/callback',
        'openid.realm': base_url,
        'openid.identity': 'http://specs.openid.net/auth/2.0/identifier_select',
        'openid.claimed_id': 'http://specs.openid.net/auth/2.0/identifier_select',
    }
    url = f"https://steamcommunity.com/openid/login?{urllib.parse.urlencode(params)}"
    return Redirect(path=url)

@get("/login/steam/callback")
async def login_steam_callback(request: Request) -> Redirect:
    params = dict(request.query_params)
    params['openid.mode'] = 'check_authentication'
    
    async with httpx.AsyncClient() as client:
        resp = await client.post('https://steamcommunity.com/openid/login', data=params)
        
    if 'is_valid:true' in resp.text:
        claimed_id = params.get('openid.claimed_id', '')
        steamid64 = claimed_id.split('/')[-1]
        account_id = steamid64_to_accountid(steamid64)
        register_user(account_id)
        
        response = Redirect(path="/dashboard")
        response.set_cookie("account_id", account_id, max_age=86400 * 30)
        return response
        
    return Redirect(path="/?error=auth_failed")

@get("/logout")
async def logout(request: Request) -> Response:
    response = Redirect(path="/")
    response.delete_cookie("account_id")
    return response

@get("/setup-mmr")
async def setup_mmr_page(request: Request) -> Template | Redirect:
    account_id = get_current_user(request)
    if not account_id: return Redirect(path="/")
    
    if get_user_config(account_id, "start_mmr") or get_user_config(account_id, "is_calibrating") == "1":
        return Redirect(path="/dashboard")
        
    return Template(template_name="setup.html")

@post("/setup-mmr")
async def process_setup_mmr(request: Request) -> Redirect:
    account_id = get_current_user(request)
    if not account_id: return Redirect(path="/")
    
    register_user(account_id)
    data = await request.form()
    start_mmr = data.get("mmr")
    is_calibrating = data.get("is_calibrating")
    
    if is_calibrating:
        set_user_config(account_id, "is_calibrating", "1")
        set_user_config(account_id, "start_time", str(int(time.time())))
    elif start_mmr:
        set_user_config(account_id, "start_mmr", start_mmr)
        set_user_config(account_id, "is_calibrating", "0")
        set_user_config(account_id, "start_time", str(int(time.time())))
        
    return Redirect(path="/dashboard")

@post("/calibrate-mmr")
async def process_calibrate(request: Request) -> Redirect:
    account_id = get_current_user(request)
    if not account_id: return Redirect(path="/")
    
    data = await request.form()
    calibrated_mmr = data.get("mmr")
    
    if calibrated_mmr:
        set_user_config(account_id, "start_mmr", calibrated_mmr)
        set_user_config(account_id, "is_calibrating", "0")
        set_user_config(account_id, "start_time", str(int(time.time())))
        
    return Redirect(path="/dashboard")

@get("/profile")
async def profile_page(request: Request) -> Template | Redirect:
    account_id = get_current_user(request)
    if not account_id: return Redirect(path="/")
    
    await fetch_player_profile(account_id)
    profile = get_user_profile(account_id)
    peers = await fetch_player_peers(account_id)
    
    allies = sorted([p for p in peers if p.get('with_games', 0) > 0], key=lambda x: x.get('with_games', 0), reverse=True)[:10]
    enemies = sorted([p for p in peers if p.get('against_games', 0) > 0], key=lambda x: x.get('against_games', 0), reverse=True)[:10]
    
    return Template("profile.html", context={
        "account_id": account_id,
        "profile": profile,
        "allies": allies,
        "enemies": enemies
    })

@get("/dashboard")
async def dashboard(request: Request) -> Template | Redirect:
    account_id = get_current_user(request)
    if not account_id: return Redirect(path="/")
    
    start_mmr = get_user_config(account_id, "start_mmr")
    is_calibrating = get_user_config(account_id, "is_calibrating") == "1"
    
    if not start_mmr and not is_calibrating:
        return Redirect(path="/setup-mmr")
        
    start_time = int(get_user_config(account_id, "start_time") or 0)
    
    await fetch_player_profile(account_id)
    profile = get_user_profile(account_id)
    
    await sync_user_matches(account_id)
    await fetch_heroes()
    
    db_path = DB_DIR / f"{account_id}.sqlite"
    matches_data = []
    
    if is_calibrating:
        current_mmr = "Calibrando"
        chart_labels = []
        chart_data = []
        
        with sqlite3.connect(db_path) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.execute("SELECT * FROM matches ORDER BY played_at DESC LIMIT 20")
            for m in cursor.fetchall():
                matches_data.append({
                    "match_id": m["match_id"],
                    "hero_img": get_hero_image_url(m["hero_id"]),
                    "is_win": bool(m["is_win"]),
                    "mmr_change": m["mmr_change"],
                    "total_mmr": "-",
                    "prev_mmr": 0,
                    "lobby_type": m["lobby_type"],
                    "game_mode": m["game_mode"],
                    "played_at": time.strftime('%d/%m/%Y %H:%M', time.localtime(m["played_at"]))
                })
        recent_matches = matches_data
    else:
        current_mmr = int(start_mmr)
        chart_labels = ["Início"]
        chart_data = [current_mmr]
        
        with sqlite3.connect(db_path) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.execute("SELECT * FROM matches WHERE played_at > ? ORDER BY played_at ASC", (start_time,))
            all_matches = cursor.fetchall()
            
            for m in all_matches:
                prev_mmr = current_mmr
                current_mmr += m["mmr_change"]
                chart_labels.append(f"#{m['match_id']}")
                chart_data.append(current_mmr)
                
                matches_data.insert(0, {
                    "match_id": m["match_id"],
                    "hero_img": get_hero_image_url(m["hero_id"]),
                    "is_win": bool(m["is_win"]),
                    "mmr_change": m["mmr_change"],
                    "total_mmr": current_mmr,
                    "prev_mmr": prev_mmr,
                    "lobby_type": m["lobby_type"],
                    "game_mode": m["game_mode"],
                    "played_at": time.strftime('%d/%m/%Y %H:%M', time.localtime(m["played_at"]))
                })
                
        recent_matches = matches_data[:20]

    return Template(
        template_name="dashboard.html",
        context={
            "account_id": account_id,
            "profile": profile,
            "current_mmr": current_mmr,
            "is_calibrating": is_calibrating,
            "recent_matches": recent_matches,
            "chart_labels": json.dumps(chart_labels),
            "chart_data": json.dumps(chart_data)
        }
    )

@post("/update-match")
async def update_match(request: Request) -> Redirect:
    account_id = get_current_user(request)
    if not account_id: return Redirect(path="/")
    
    data = await request.form()
    match_id = data.get("match_id")
    new_total_mmr = data.get("total_mmr")
    prev_mmr = data.get("prev_mmr")
    
    if match_id and new_total_mmr and prev_mmr:
        new_change = int(new_total_mmr) - int(prev_mmr)
        with sqlite3.connect(DB_DIR / f"{account_id}.sqlite") as conn:
            conn.execute("UPDATE matches SET mmr_change = ? WHERE match_id = ?", (new_change, int(match_id)))
            conn.commit()
            
    return Redirect(path="/dashboard")

@get("/matches")
async def matches_page(request: Request) -> Template | Redirect:
    account_id = get_current_user(request)
    if not account_id: return Redirect(path="/")
    
    profile = get_user_profile(account_id)
    search = request.query_params.get("search", "")
    mode = request.query_params.get("mode", "all")
    page = int(request.query_params.get("page", 1))
    per_page = 20
    offset = (page - 1) * per_page
    
    matches_data = []
    total_matches = 0
    await fetch_heroes()
    
    where_clauses = []
    params = []
    
    if search:
        where_clauses.append("match_id LIKE ?")
        params.append(f"%{search}%")
        
    if mode == "ranked":
        where_clauses.append("lobby_type = 7")
    elif mode == "turbo":
        where_clauses.append("game_mode = 23")
    elif mode == "other":
        where_clauses.append("(lobby_type != 7 AND game_mode != 23)")
        
    where_sql = ""
    if where_clauses:
        where_sql = "WHERE " + " AND ".join(where_clauses)
    
    with sqlite3.connect(DB_DIR / f"{account_id}.sqlite") as conn:
        conn.row_factory = sqlite3.Row
        total_matches = conn.execute(f"SELECT COUNT(*) FROM matches {where_sql}", params).fetchone()[0]
        cursor = conn.execute(f"SELECT * FROM matches {where_sql} ORDER BY played_at DESC LIMIT ? OFFSET ?", params + [per_page, offset])
        for m in cursor.fetchall():
            matches_data.append({
                "match_id": m["match_id"],
                "hero_img": get_hero_image_url(m["hero_id"]),
                "is_win": bool(m["is_win"]),
                "mmr_change": m["mmr_change"],
                "lobby_type": m["lobby_type"],
                "game_mode": m["game_mode"],
                "played_at": time.strftime('%d/%m/%Y %H:%M', time.localtime(m["played_at"]))
            })
            
    total_pages = max(1, (total_matches + per_page - 1) // per_page)
            
    return Template("matches.html", context={"profile": profile, "matches": matches_data, "search": search, "mode": mode, "page": page, "total_pages": total_pages})

@get("/matches/{match_id:int}")
async def match_detail_page(request: Request, match_id: int) -> Template | Redirect:
    account_id = get_current_user(request)
    if not account_id: return Redirect(path="/")

    profile = get_user_profile(account_id)
    details = await fetch_match_details(match_id)
    if not details: return Redirect(path="/matches")

    await fetch_heroes()
    await fetch_items()

    radiant_win = details.get("radiant_win", False)
    duration = details.get("duration", 0)
    minutes = duration // 60
    seconds = duration % 60

    players = []
    for p in details.get("players", []):
        hero_id = p.get("hero_id", 0)
        hero_data = heroes_cache.get(str(hero_id), {})
        players.append({
            "account_id": p.get("account_id"),
            "personaname": p.get("personaname", "Anónimo"),
            "hero_name": hero_data.get("localized_name", f"Hero #{hero_id}"),
            "hero_img": get_hero_image_url(hero_id),
            "is_radiant": p.get("isRadiant", False),
            "kills": p.get("kills", 0),
            "deaths": p.get("deaths", 0),
            "assists": p.get("assists", 0),
            "gpm": p.get("gold_per_min", 0),
            "xpm": p.get("xp_per_min", 0),
            "is_current_user": str(p.get("account_id")) == account_id,
            "lh": p.get("last_hits", 0),
            "dn": p.get("denies", 0),
            "hero_dmg": p.get("hero_damage", 0),
            "tower_dmg": p.get("tower_damage", 0),
            "hero_heal": p.get("hero_healing", 0),
            "inventory": [get_item_info(p.get(f"item_{i}")) for i in range(6)],
            "neutral_item": get_item_info(p.get("item_neutral")),
            "scepter": p.get("aghanims_scepter") == 1,
            "shard": p.get("aghanims_shard") == 1,
            "moonshard": p.get("moonshard") == 1,
        })

    return Template("match_detail.html", context={"profile": profile, "match_id": match_id, "radiant_win": radiant_win, "duration": f"{minutes:02d}:{seconds:02d}", "players": players})

@get("/records")
async def records_page(request: Request) -> Template | Redirect:
    account_id = get_current_user(request)
    if not account_id: return Redirect(path="/")

    profile = get_user_profile(account_id)
    max_win_streak, max_lose_streak, c_win, c_lose = 0, 0, 0, 0

    with sqlite3.connect(DB_DIR / f"{account_id}.sqlite") as conn:
        conn.row_factory = sqlite3.Row
        # APENAS partidas Casuais (0) ou Ranked (7), excluindo Turbo (23)
        for m in conn.execute("SELECT is_win FROM matches WHERE lobby_type IN (0, 7) AND game_mode != 23 ORDER BY played_at ASC").fetchall():
            if m["is_win"]:
                c_win += 1; c_lose = 0
                if c_win > max_win_streak: max_win_streak = c_win
            else:
                c_lose += 1; c_win = 0
                if c_lose > max_lose_streak: max_lose_streak = c_lose

    await fetch_heroes()
    
    # RESTAURADOS TODOS OS RECORDES + ENVOLVIMENTO EM KILLS!
    queries = {
        "duration": ("Partida Mais Longa", "duration"),
        "kills": ("Mais Kills", "kills"),
        "assists": ("Mais Assistências", "assists"),
        "kill_contrib": ("Maior Envolvimento (K+A)", "kills + assists"),
        "last_hits": ("Mais Last Hits", "last_hits"),
        "denies": ("Mais Denies", "denies"),
        "total_gold": ("Mais Património (Total)", "gold_per_min * (duration / 60.0)"),
        "total_xp": ("Mais Experiência (Total)", "xp_per_min * (duration / 60.0)"),
        "hero_damage": ("Mais Dano a Heróis", "hero_damage"),
        "hero_healing": ("Mais Cura a Heróis", "hero_healing"),
        "tower_damage": ("Mais Dano a Torres", "tower_damage"),
        "kda": ("Melhor KDA Ratio", "(kills + assists) * 1.0 / CASE WHEN deaths = 0 THEN 1 ELSE deaths END")
    }

    formatted_records = []
    with sqlite3.connect(DB_DIR / f"{account_id}.sqlite") as conn:
        conn.row_factory = sqlite3.Row
        for key, (title, order_by) in queries.items():
            # A mesma regra de rigor aplica-se aos recordes
            row = conn.execute(f"SELECT match_id, hero_id, played_at, is_win, lobby_type, game_mode, duration, {order_by} as val FROM matches WHERE duration > 300 AND lobby_type IN (0, 7) AND game_mode != 23 ORDER BY {order_by} DESC LIMIT 1").fetchone()
            if row and row["val"] and row["val"] > 0:
                val = row["val"]
                if key == "duration":
                    val_str = f"{int(val)//3600}:{(int(val)%3600)//60:02d}:{int(val)%60:02d}" if val >= 3600 else f"{int(val)//60}:{int(val)%60:02d}"
                elif key == "kda": val_str = f"{val:.2f}"
                else: val_str = f"{int(val):,}".replace(",", ".")
                
                hero_id = row["hero_id"]
                hero_name = heroes_cache.get(str(hero_id), {}).get("localized_name", f"Hero #{hero_id}")
                dur = row["duration"]
                dur_sub = f"{dur//3600}:{(dur%3600)//60:02d}:{dur%60:02d}" if dur >= 3600 else f"{dur//60}:{dur%60:02d}"
                lobby_name = "Ranked" if row["lobby_type"] == 7 else "Normal"
                
                formatted_records.append({
                    "title": title, "value": val_str, "subtitle": f"{hero_name} ({dur_sub})",
                    "date_str": time.strftime('%d/%m/%Y', time.localtime(row["played_at"])),
                    "lobby_name": lobby_name, "match_id": row["match_id"], "hero_img": get_hero_image_url(hero_id), "is_win": bool(row["is_win"])
                })

    return Template("records.html", context={"profile": profile, "win_streak": max_win_streak, "lose_streak": max_lose_streak, "records": formatted_records})

@get("/heroes")
async def heroes_page(request: Request) -> Template | Redirect:
    account_id = get_current_user(request)
    if not account_id: return Redirect(path="/")
    
    profile = get_user_profile(account_id)
    heroes_stats = []
    await fetch_heroes()
    
    with sqlite3.connect(DB_DIR / f"{account_id}.sqlite") as conn:
        conn.row_factory = sqlite3.Row
        cursor = conn.execute("""
            SELECT hero_id, COUNT(*) as total_games, SUM(CASE WHEN is_win THEN 1 ELSE 0 END) as wins
            FROM matches GROUP BY hero_id ORDER BY total_games DESC, wins DESC
        """)
        for row in cursor.fetchall():
            hero_id = row["hero_id"]
            hero_name = heroes_cache.get(str(hero_id), {}).get("localized_name", f"Hero #{hero_id}")
            wins, total = row["wins"], row["total_games"]
            heroes_stats.append({
                "hero_name": hero_name, "hero_img": get_hero_image_url(hero_id),
                "total_games": total, "wins": wins, "losses": total - wins, "winrate": round((wins/total)*100, 1) if total > 0 else 0
            })
            
    return Template("heroes.html", context={"profile": profile, "heroes": heroes_stats})

# --- ROTAS DE AUTENTICAÇÃO DO ADMIN ---
@get("/admin/login")
async def admin_login_page(request: Request) -> Template:
    return Template("admin_login.html", context={"error": request.query_params.get("error")})

@post("/admin/login")
async def admin_login_post(request: Request) -> Redirect:
    data = await request.form()
    if data.get("password") == get_admin_setting("password"):
        response = Redirect("/painel-admin-secreto-99")
        response.set_cookie("admin_auth", "1", max_age=86400)
        return response
    return Redirect("/admin/login?error=1")

@get("/admin/change-password")
async def admin_change_pwd_page(request: Request) -> Template | Redirect:
    if not check_admin_auth(request): return Redirect("/admin/login")
    return Template("admin_change_password.html")

@post("/admin/change-password")
async def admin_change_pwd_post(request: Request) -> Redirect:
    if not check_admin_auth(request): return Redirect("/admin/login")
    new_pwd = (await request.form()).get("new_password")
    if new_pwd and len(new_pwd) >= 6:
        set_admin_setting("password", new_pwd)
        set_admin_setting("needs_change", "0")
        return Redirect("/painel-admin-secreto-99")
    return Redirect("/admin/change-password")

@get("/painel-admin-secreto-99")
async def superadmin_dashboard(request: Request) -> Template | Redirect:
    if not check_admin_auth(request): return Redirect("/admin/login")
    if get_admin_setting("needs_change") == "1": return Redirect("/admin/change-password")
    
    init_main_db()
    users = []
    with sqlite3.connect(MAIN_DB) as conn:
        conn.row_factory = sqlite3.Row
        for row in conn.execute("SELECT * FROM users ORDER BY registered_at DESC").fetchall():
            total_matches = 0
            try:
                with sqlite3.connect(DB_DIR / f"{row['account_id']}.sqlite") as user_conn:
                    total_matches = user_conn.execute("SELECT COUNT(*) FROM matches").fetchone()[0]
            except: pass
            
            row_dict = dict(row)
            users.append({
                "account_id": row_dict["account_id"],
                "personaname": row_dict.get("personaname") or "Sem Nome",
                "registered_at": time.strftime('%d/%m/%Y %H:%M', time.localtime(row_dict["registered_at"])),
                "total_matches": total_matches
            })
    return Template("admin.html", context={"users": users})

@get("/painel-admin-secreto-99/user/{account_id:str}")
async def admin_audit_user(request: Request, account_id: str) -> Template | Redirect:
    if not check_admin_auth(request): return Redirect("/admin/login")
    
    matches = []
    db_path = DB_DIR / f"{account_id}.sqlite"
    if db_path.exists():
        with sqlite3.connect(db_path) as conn:
            conn.row_factory = sqlite3.Row
            for row in conn.execute("SELECT * FROM matches ORDER BY played_at DESC LIMIT 1000").fetchall():
                match_dict = dict(row)
                match_dict["played_at_str"] = time.strftime('%d/%m/%Y %H:%M', time.localtime(match_dict["played_at"]))
                matches.append(match_dict)
    return Template("admin_user.html", context={"account_id": account_id, "matches": matches})

@get("/painel-admin-secreto-99/user/{account_id:str}/export")
async def admin_export_user(request: Request, account_id: str) -> Response | Redirect:
    if not check_admin_auth(request): return Redirect("/admin/login")
    
    output = io.StringIO()
    db_path = DB_DIR / f"{account_id}.sqlite"
    if db_path.exists():
        with sqlite3.connect(db_path) as conn:
            conn.row_factory = sqlite3.Row
            rows = conn.execute("SELECT * FROM matches ORDER BY played_at DESC").fetchall()
            if rows:
                writer = csv.DictWriter(output, fieldnames=rows[0].keys())
                writer.writeheader()
                for row in rows: writer.writerow(dict(row))
            else:
                output.write("Nenhuma partida encontrada.")
    return Response(content=output.getvalue().encode("utf-8"), media_type="text/csv", headers={"Content-Disposition": f"attachment; filename=matches_{account_id}.csv"})