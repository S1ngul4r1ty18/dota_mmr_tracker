import sqlite3
import time
import httpx
import asyncio
import hashlib  # <--- ADICIONE ESTE IMPORT PARA GERAR OS HASHES DA LIQUIPEDIA
from typing import List, Dict, Any

from config import DB_DIR, MAIN_DB, OPENDOTA_API_URL

heroes_cache = {}
items_cache = {}

async def fetch_heroes():
    if not heroes_cache:
        try:
            async with httpx.AsyncClient() as client:
                response = await client.get(f"{OPENDOTA_API_URL}/constants/heroes")
                if response.status_code == 200:
                    heroes_cache.update(response.json())
        except Exception as e:
            pass

async def fetch_items():
    if not items_cache:
        try:
            async with httpx.AsyncClient() as client:
                response = await client.get(f"{OPENDOTA_API_URL}/constants/items")
                if response.status_code == 200:
                    data = response.json()
                    for key, item in data.items():
                        if "id" in item:
                            items_cache[str(item["id"])] = item
        except Exception as e:
            pass

def get_hero_image_url(hero_id: int) -> str:
    return f"/img/hero/{hero_id}"

def get_item_image_url(item_id: int) -> str | None:
    if not item_id or item_id == 0: return None
    return f"/img/item/{item_id}"

def steamid64_to_accountid(steamid64: str) -> str:
    try:
        if len(steamid64) == 17 and steamid64.startswith("7656"):
            return str(int(steamid64) - 76561197960265728)
        return steamid64
    except ValueError:
        return steamid64

async def fetch_matches(account_id: str, limit: int = None) -> List[Dict[str, Any]]:
    async with httpx.AsyncClient() as client:
        projects = ["start_time", "hero_id", "lobby_type", "game_mode", "radiant_win", "player_slot", 
                    "duration", "kills", "deaths", "assists", "last_hits", "denies", 
                    "hero_damage", "tower_damage", "hero_healing", "gold_per_min", "xp_per_min"]
        proj_str = "&".join(f"project={p}" for p in projects)
        url = f"{OPENDOTA_API_URL}/players/{account_id}/matches?{proj_str}&significant=0"
        
        if limit:
            url += f"&limit={limit}"
            
        try:
            response = await client.get(url, timeout=45.0)
            if response.status_code == 200:
                return response.json()
        except Exception as e:
            print(f"Erro ao buscar partidas na API OpenDota: {e}")
        return []

async def fetch_match_details(match_id: int) -> Dict[str, Any] | None:
    async with httpx.AsyncClient() as client:
        try:
            response = await client.get(f"{OPENDOTA_API_URL}/matches/{match_id}", timeout=20.0)
            if response.status_code == 200:
                return response.json()
        except Exception:
            pass
        return None

def get_rank_name(tier: int) -> str:
    if not tier: return "Não Calibrado"
    if tier >= 80: return "Immortal"
    ranks = {1: "Herald", 2: "Guardian", 3: "Crusader", 4: "Archon", 5: "Legend", 6: "Ancient", 7: "Divine"}
    badge = tier // 10
    star = tier % 10
    name = ranks.get(badge, "Desconhecido")
    return f"{name} {star}" if badge < 8 else name

# --- NOVA FUNÇÃO PARA GERAR A IMAGEM DA MEDALHA ---
def get_rank_url(tier: int) -> str:
    if not tier:
        filename = "SeasonalRank0-0.png"
    elif tier >= 80:
        filename = "SeasonalRankTop0.png"
    else:
        badge = tier // 10
        star = tier % 10
        filename = f"SeasonalRank{badge}-{star}.png"
        
    md5_hash = hashlib.md5(filename.encode('utf-8')).hexdigest()
    return f"https://liquipedia.net/commons/images/thumb/{md5_hash[0]}/{md5_hash[:2]}/{filename}/160px-{filename}"

async def fetch_player_profile(account_id: str):
    async with httpx.AsyncClient() as client:
        try:
            response = await client.get(f"{OPENDOTA_API_URL}/players/{account_id}", timeout=15.0)
            if response.status_code == 200:
                data = response.json()
                profile = data.get("profile")
                rank_tier = data.get("rank_tier")
                mmr_estimate = data.get("mmr_estimate", {}).get("estimate") if data.get("mmr_estimate") else None
                computed_mmr = data.get("computed_mmr")
                computed_mmr_turbo = data.get("computed_mmr_turbo")
                
                if profile:
                    name = profile.get("personaname", "")
                    avatar = profile.get("avatarfull", "")
                    with sqlite3.connect(MAIN_DB) as conn:
                        conn.execute("""
                            UPDATE users 
                            SET personaname = ?, avatarfull = ?, rank_tier = ?, mmr_estimate = ?, computed_mmr = ?, computed_mmr_turbo = ?
                            WHERE account_id = ?
                        """, (name, avatar, rank_tier, mmr_estimate, computed_mmr, computed_mmr_turbo, account_id))
                        conn.commit()
        except Exception as e:
            pass

async def fetch_player_peers(account_id: str) -> List[Dict[str, Any]]:
    async with httpx.AsyncClient() as client:
        try:
            response = await client.get(f"{OPENDOTA_API_URL}/players/{account_id}/peers", timeout=15.0)
            if response.status_code == 200:
                return response.json()
        except Exception:
            pass
    return []

def init_main_db():
    with sqlite3.connect(MAIN_DB) as conn:
        conn.execute("""
            CREATE TABLE IF NOT EXISTS users (
                account_id TEXT PRIMARY KEY,
                registered_at INTEGER
            )
        """)
        try:
            conn.execute("ALTER TABLE users ADD COLUMN personaname TEXT")
        except sqlite3.OperationalError:
            pass
        try:
            conn.execute("ALTER TABLE users ADD COLUMN avatarfull TEXT")
        except sqlite3.OperationalError:
            pass
        try:
            conn.execute("ALTER TABLE users ADD COLUMN rank_tier INTEGER")
        except sqlite3.OperationalError:
            pass
        try:
            conn.execute("ALTER TABLE users ADD COLUMN mmr_estimate INTEGER")
        except sqlite3.OperationalError:
            pass
        try:
            conn.execute("ALTER TABLE users ADD COLUMN computed_mmr REAL")
        except sqlite3.OperationalError:
            pass
        try:
            conn.execute("ALTER TABLE users ADD COLUMN computed_mmr_turbo REAL")
        except sqlite3.OperationalError:
            pass
            
        conn.execute("""
            CREATE TABLE IF NOT EXISTS admin_settings (
                key TEXT PRIMARY KEY,
                value TEXT
            )
        """)
        cursor = conn.execute("SELECT value FROM admin_settings WHERE key = 'password'")
        if not cursor.fetchone():
            conn.execute("INSERT INTO admin_settings (key, value) VALUES ('password', 'superadmin123')")
            conn.execute("INSERT INTO admin_settings (key, value) VALUES ('needs_change', '1')")
        conn.commit()

def init_user_db(account_id: str):
    db_path = DB_DIR / f"{account_id}.sqlite"
    with sqlite3.connect(db_path) as conn:
        conn.execute("CREATE TABLE IF NOT EXISTS config (key TEXT PRIMARY KEY, value TEXT)")
        conn.execute("""
            CREATE TABLE IF NOT EXISTS matches (
                match_id INTEGER PRIMARY KEY,
                hero_id INTEGER,
                is_win BOOLEAN,
                mmr_change INTEGER,
                played_at INTEGER
            )
        """)
        cols = ["lobby_type", "game_mode", "duration", "kills", "deaths", "assists", 
                "last_hits", "denies", "hero_damage", "tower_damage", "hero_healing", 
                "gold_per_min", "xp_per_min"]
        for col in cols:
            try:
                conn.execute(f"ALTER TABLE matches ADD COLUMN {col} INTEGER DEFAULT 0")
            except sqlite3.OperationalError:
                pass
        conn.commit()

def register_user(account_id: str):
    init_main_db()
    with sqlite3.connect(MAIN_DB) as conn:
        conn.execute(
            "INSERT OR IGNORE INTO users (account_id, registered_at) VALUES (?, ?)", 
            (account_id, int(time.time()))
        )
        conn.commit()
    init_user_db(account_id)

def get_user_profile(account_id: str) -> dict:
    profile = {
        "personaname": "Jogador", 
        "avatarfull": "https://avatars.steamstatic.com/fef49e7fa7e1997310d705b2a6158ff8dc1cdfeb_full.jpg",
        "rank_tier": 0,
        "mmr_estimate": 0,
        "rank_name": "Não Calibrado",
        "rank_url": get_rank_url(0), # <--- Adicionado
        "computed_mmr": 0,
        "computed_mmr_turbo": 0
    }
    with sqlite3.connect(MAIN_DB) as conn:
        conn.row_factory = sqlite3.Row
        cursor = conn.execute("SELECT personaname, avatarfull, rank_tier, mmr_estimate, computed_mmr, computed_mmr_turbo FROM users WHERE account_id = ?", (account_id,))
        row = cursor.fetchone()
        if row and row["personaname"]:
            row_dict = dict(row)
            profile.update(row_dict)
            profile["rank_name"] = get_rank_name(profile["rank_tier"])
            profile["rank_url"] = get_rank_url(profile.get("rank_tier") or 0) # <--- Adicionado
            
            # Formatar para exibição limpa se existirem
            if profile["computed_mmr"]:
                profile["computed_mmr"] = round(profile["computed_mmr"])
            if profile["computed_mmr_turbo"]:
                profile["computed_mmr_turbo"] = round(profile["computed_mmr_turbo"])
                
    return profile

def get_user_config(account_id: str, key: str) -> str:
    db_path = DB_DIR / f"{account_id}.sqlite"
    if not db_path.exists(): return None
    with sqlite3.connect(db_path) as conn:
        cursor = conn.execute("SELECT value FROM config WHERE key = ?", (key,))
        row = cursor.fetchone()
        return row[0] if row else None

def set_user_config(account_id: str, key: str, value: str):
    db_path = DB_DIR / f"{account_id}.sqlite"
    with sqlite3.connect(db_path) as conn:
        conn.execute("INSERT OR REPLACE INTO config (key, value) VALUES (?, ?)", (key, str(value)))
        conn.commit()

async def sync_user_matches(account_id: str):
    init_user_db(account_id)
    
    start_time_str = get_user_config(account_id, "start_time")
    if not start_time_str: return
    start_time = int(start_time_str)

    db_path = DB_DIR / f"{account_id}.sqlite"

    is_initial = not get_user_config(account_id, "initial_sync_done")
    needs_v5_turbo_fetch = not get_user_config(account_id, "v5_turbo_real_fix")
    
    limit = 2000 if (is_initial or needs_v5_turbo_fetch) else 50
        
    matches = await fetch_matches(account_id, limit=limit)
    
    if matches:
        with sqlite3.connect(db_path) as conn:
            to_insert = []
            to_update = []
            
            for match in matches:
                player_slot = match.get("player_slot")
                if player_slot is None: continue
                
                radiant_win = match.get("radiant_win")
                is_radiant = player_slot < 128
                is_win = (is_radiant and radiant_win) or (not is_radiant and not radiant_win)
                
                lobby_type = match.get("lobby_type", 0)
                game_mode = match.get("game_mode", 0)
                played_at = match.get("start_time", 0)
                
                mmr_change = 0
                if played_at > start_time and lobby_type == 7:
                    mmr_change = 25 if is_win else -25
                    
                to_insert.append((
                    match["match_id"], match.get("hero_id", 0), is_win, mmr_change, played_at, lobby_type, game_mode,
                    match.get("duration", 0), match.get("kills", 0), match.get("deaths", 0), match.get("assists", 0),
                    match.get("last_hits", 0), match.get("denies", 0), match.get("hero_damage", 0), 
                    match.get("tower_damage", 0), match.get("hero_healing", 0), match.get("gold_per_min", 0), match.get("xp_per_min", 0)
                ))
                
                to_update.append((
                    lobby_type, game_mode, match.get("duration", 0), match.get("kills", 0), 
                    match.get("deaths", 0), match.get("assists", 0), match.get("last_hits", 0), 
                    match.get("denies", 0), match.get("hero_damage", 0), match.get("tower_damage", 0), 
                    match.get("hero_healing", 0), match.get("gold_per_min", 0), match.get("xp_per_min", 0),
                    match["match_id"]
                ))
                
            conn.executemany("""
                INSERT OR IGNORE INTO matches 
                (match_id, hero_id, is_win, mmr_change, played_at, lobby_type, game_mode,
                 duration, kills, deaths, assists, last_hits, denies, hero_damage, tower_damage, hero_healing, gold_per_min, xp_per_min)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, to_insert)
            
            conn.executemany("""
                UPDATE matches SET 
                    lobby_type=?, game_mode=?, duration=?, kills=?, deaths=?, assists=?, last_hits=?, 
                    denies=?, hero_damage=?, tower_damage=?, hero_healing=?, gold_per_min=?, xp_per_min=?
                WHERE match_id=?
            """, to_update)
            conn.commit()

        if is_initial: set_user_config(account_id, "initial_sync_done", "1")
        if needs_v5_turbo_fetch: set_user_config(account_id, "v5_turbo_real_fix", "1")