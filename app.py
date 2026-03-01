# LOCAL DO ARQUIVO: app.py
import os
import sqlite3
import functools
import requests
from flask import Flask, request, jsonify, render_template, redirect, url_for, session, flash
from werkzeug.security import generate_password_hash, check_password_hash

app = Flask(__name__)

# --- CONFIGURAÇÕES DE SEGURANÇA ---
# Em produção, use uma chave aleatória real.
app.secret_key = os.environ.get('SECRET_KEY', 'chave_super_secreta_dev_123')
ADMIN_PASSWORD = os.environ.get('ADMIN_PASS', 'admin123')

# Caminhos
DATABASE = os.path.join(app.root_path, 'mmr_tracker.db')
HERO_IMG_DIR = os.path.join(app.root_path, 'static', 'hero_images')

# Cache em Memória para Heróis (evita ler disco toda hora)
HEROES_DATA = {}

# --- FUNÇÕES AUXILIARES ---
def get_db_conn():
    conn = sqlite3.connect(DATABASE)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    return conn

def load_hero_data():
    """Baixa imagens e dados dos heróis ao iniciar o servidor."""
    global HEROES_DATA
    if not os.path.exists(HERO_IMG_DIR):
        os.makedirs(HERO_IMG_DIR)
    
    try:
        print("Inicializando: Carregando dados de heróis da OpenDota...")
        resp = requests.get("https://api.opendota.com/api/heroes", timeout=15)
        resp.raise_for_status()
        
        heroes_list = resp.json()
        for hero in heroes_list:
            h_id = str(hero['id'])
            # Nome do arquivo limpo
            fname = f"{hero['name'].replace('npc_dota_hero_', '')}_sb.png"
            local_path = os.path.join(HERO_IMG_DIR, fname)
            
            # Baixa a imagem se não tivermos
            if not os.path.exists(local_path):
                try:
                    img_url = f"https://cdn.cloudflare.steamstatic.com/apps/dota2/images/heroes/{fname}"
                    img_resp = requests.get(img_url, timeout=5)
                    if img_resp.status_code == 200:
                        with open(local_path, 'wb') as f:
                            f.write(img_resp.content)
                except Exception:
                    pass # Continua mesmo se uma imagem falhar
            
            HEROES_DATA[h_id] = {
                'name': hero['localized_name'],
                'img': f"/static/hero_images/{fname}"
            }
        print(f"Sucesso: {len(HEROES_DATA)} heróis carregados.")
    except Exception as e:
        print(f"AVISO: Falha ao carregar heróis. O site funcionará sem ícones. Erro: {e}")

# Executa o carregamento
load_hero_data()

def sync_matches_and_mmr(user_id, conn):
    """
    Função Mágica:
    1. Busca partidas novas na OpenDota.
    2. Salva no cache.
    3. SE for Ranked, calcula +/- 25 MMR e atualiza o histórico automaticamente.
    """
    try:
        # 1. Busca o que já temos cacheado para saber o que é novo
        cached = conn.execute('SELECT match_id FROM matches_cache WHERE user_id = ?', (user_id,)).fetchall()
        existing_ids = {row['match_id'] for row in cached}

        # 2. Busca na API
        print(f"Sincronizando partidas para {user_id}...")
        r = requests.get(f"https://api.opendota.com/api/players/{user_id}/recentMatches", timeout=4)
        
        if r.status_code == 200:
            new_data = r.json()
            # Ordena do mais antigo para o mais novo para calcular o MMR na ordem certa
            new_data.sort(key=lambda x: x['start_time']) 
            
            updates_count = 0
            
            for m in new_data:
                mid = m['match_id']
                if mid not in existing_ids:
                    # A. Insere no Cache de Partidas
                    conn.execute('''
                        INSERT INTO matches_cache 
                        (match_id, user_id, hero_id, kills, deaths, assists, duration, game_mode, radiant_win, player_slot, start_time)
                        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    ''', (mid, user_id, m['hero_id'], m['kills'], m['deaths'], m['assists'], m['duration'], m['game_mode'], m['radiant_win'], m['player_slot'], m['start_time']))
                    
                    # B. Lógica de AUTO-TRACK MMR
                    # Lobby Type 7 = Ranked. Game Mode 22 = Ranked All Pick.
                    # Vamos ser abrangentes: se lobby_type for 7, conta.
                    lobby_type = m.get('lobby_type', 0)
                    if lobby_type == 7: 
                        # Busca o último MMR conhecido
                        last_mmr_row = conn.execute('SELECT mmr FROM mmr_history WHERE user_id = ? ORDER BY timestamp DESC LIMIT 1', (user_id,)).fetchone()
                        
                        if last_mmr_row:
                            current_mmr = last_mmr_row['mmr']
                            # Determina Vitória/Derrota
                            is_radiant = m.get('player_slot') < 128
                            radiant_win = m.get('radiant_win')
                            victory = (is_radiant and radiant_win) or (not is_radiant and not radiant_win)
                            
                            # Estimativa Padrão: +/- 25
                            change = 25 if victory else -25
                            new_mmr = current_mmr + change
                            result_text = 'vitoria' if victory else 'derrota'
                            
                            # Insere no histórico de MMR
                            conn.execute('''
                                INSERT INTO mmr_history (user_id, mmr, diferenca, resultado) 
                                VALUES (?, ?, ?, ?)
                            ''', (user_id, new_mmr, change, f"Auto: {result_text}"))
                            print(f"AUTO-MMR: Match {mid} -> {new_mmr} ({change})")

                    updates_count += 1
            
            if updates_count > 0:
                conn.commit()
                print(f"Sincronização completa: {updates_count} novas partidas processadas.")
                
    except Exception as e:
        print(f"Erro na sincronização automática: {e}")


# --- DECORATORS DE SEGURANÇA ---
def login_required(f):
    @functools.wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            # Se for AJAX/API, retorna JSON. Se for navegador, redireciona.
            if request.path.startswith('/api/'):
                return jsonify({"success": False, "message": "Sessão expirada. Faça login novamente."}), 401
            return redirect(url_for('home'))
        return f(*args, **kwargs)
    return decorated_function

def admin_required(f):
    @functools.wraps(f)
    def decorated_function(*args, **kwargs):
        if not session.get('admin_logged_in'):
            return jsonify({"success": False, "message": "Acesso negado."}), 403
        return f(*args, **kwargs)
    return decorated_function

# --- ROTAS DE PÁGINAS (FRONTEND) ---
@app.route('/')
def home():
    if 'user_id' in session:
        return redirect(url_for('dashboard'))
    return render_template('registro.html')

@app.route('/dashboard')
@login_required
def dashboard():
    conn = get_db_conn()
    user = conn.execute('SELECT * FROM users WHERE id = ?', (session['user_id'],)).fetchone()
    conn.close()
    return render_template('dashboard.html', user=user)

@app.route('/historico')
@login_required
def historico():
    conn = get_db_conn()
    user = conn.execute('SELECT * FROM users WHERE id = ?', (session['user_id'],)).fetchone()
    conn.close()
    return render_template('historico.html', user=user)

@app.route('/estatisticas')
@login_required
def estatisticas():
    conn = get_db_conn()
    user = conn.execute('SELECT * FROM users WHERE id = ?', (session['user_id'],)).fetchone()
    conn.close()
    return render_template('estatisticas.html', user=user)

@app.route('/recordes')
@login_required
def recordes():
    conn = get_db_conn()
    user = conn.execute('SELECT * FROM users WHERE id = ?', (session['user_id'],)).fetchone()
    conn.close()
    return render_template('recordes.html', user=user)

# --- ROTAS DO ADMIN (PÁGINAS) ---
@app.route('/admin', methods=['GET', 'POST'])
def admin_login():
    if request.method == 'POST':
        if request.form.get('password') == ADMIN_PASSWORD:
            session['admin_logged_in'] = True
            return redirect(url_for('admin_login'))
        flash('Senha incorreta!', 'error')
    
    if session.get('admin_logged_in'):
        return render_template('admin.html')
    return render_template('admin_login.html')

@app.route('/admin/logout')
def admin_logout():
    session.pop('admin_logged_in', None)
    return redirect(url_for('admin_login'))

# --- ROTAS DA API: AUTH ---
@app.route('/api/login', methods=['POST'])
def api_login():
    data = request.json
    conn = get_db_conn()
    user = conn.execute('SELECT * FROM users WHERE nickname = ?', (data.get('nickname'),)).fetchone()
    conn.close()
    
    if user and check_password_hash(user['password'], data.get('password')):
        session['user_id'] = user['id'] # Salva na sessão segura
        return jsonify({"success": True, "redirect": "/dashboard"})
    return jsonify({"success": False, "message": "Credenciais inválidas"}), 401

@app.route('/api/register', methods=['POST'])
def api_register():
    data = request.json
    try:
        user_id = int(data['id'])
        mmr = int(data['mmr_inicial'])
        hashed = generate_password_hash(data['password'])
        
        conn = get_db_conn()
        conn.execute('INSERT INTO users (id, nickname, password) VALUES (?, ?, ?)', (user_id, data['nickname'], hashed))
        conn.execute('INSERT INTO mmr_history (user_id, mmr, diferenca, resultado) VALUES (?, ?, 0, "inicial")', (user_id, mmr))
        conn.commit()
        conn.close()
        
        session['user_id'] = user_id # Loga automaticamente
        return jsonify({"success": True, "redirect": "/dashboard"})
    except sqlite3.IntegrityError:
        return jsonify({"success": False, "message": "ID Steam ou Nickname já cadastrados."}), 409
    except Exception as e:
        return jsonify({"success": False, "message": str(e)}), 500

@app.route('/logout')
def logout():
    session.pop('user_id', None)
    return redirect(url_for('home'))

# --- ROTAS DA API: USUÁRIO (Secure) ---
@app.route('/api/mmr_data', methods=['GET'])
@login_required
def api_mmr_data():
    uid = session['user_id']
    conn = get_db_conn()
    
    # [NOVO] Sincroniza OpenDota ao carregar o dashboard para atualizar MMR auto
    sync_matches_and_mmr(uid, conn)
    
    history = conn.execute('SELECT * FROM mmr_history WHERE user_id = ? ORDER BY timestamp ASC', (uid,)).fetchall()
    conn.close()
    return jsonify({"historico_mmr": [dict(row) for row in history]})

@app.route('/api/update_mmr', methods=['POST'])
@login_required
def api_update_mmr():
    uid = session['user_id']
    try:
        novo_mmr = int(request.json['mmr_atualizado'])
    except:
        return jsonify({"success": False, "message": "Valor inválido"}), 400
    
    conn = get_db_conn()
    last = conn.execute('SELECT mmr FROM mmr_history WHERE user_id = ? ORDER BY timestamp DESC LIMIT 1', (uid,)).fetchone()
    
    if not last: return jsonify({"success": False, "message": "Erro de consistência"}), 400
    
    diff = novo_mmr - last['mmr']
    res = 'vitoria' if diff > 0 else 'derrota' if diff < 0 else 'empate'
    
    conn.execute('INSERT INTO mmr_history (user_id, mmr, diferenca, resultado) VALUES (?, ?, ?, ?)',
                 (uid, novo_mmr, diff, res))
    conn.commit()
    conn.close()
    return jsonify({"success": True})

@app.route('/api/local_stats')
@login_required
def api_local_stats():
    uid = session['user_id']
    conn = get_db_conn()
    v = conn.execute("SELECT COUNT(*) FROM mmr_history WHERE user_id=? AND resultado LIKE '%vitoria%'", (uid,)).fetchone()[0]
    d = conn.execute("SELECT COUNT(*) FROM mmr_history WHERE user_id=? AND resultado LIKE '%derrota%'", (uid,)).fetchone()[0]
    conn.close()
    
    total = v + d
    wr = (v/total*100) if total > 0 else 0
    return jsonify({"success": True, "vitorias": v, "derrotas": d, "total_partidas": total, "winrate": round(wr, 1)})

# --- ROTAS DA API: CACHE & OPENDOTA ---
@app.route('/api/recent_matches', methods=['GET'])
@login_required
def api_recent_matches():
    uid = session['user_id']
    conn = get_db_conn()
    
    # [NOVO] Garante que também sincroniza aqui caso o user vá direto para o histórico
    sync_matches_and_mmr(uid, conn)
    
    # Carrega do banco (agora sempre atualizado)
    cached = conn.execute('SELECT * FROM matches_cache WHERE user_id = ? ORDER BY start_time DESC', (uid,)).fetchall()
    matches_list = [dict(m) for m in cached]
    
    conn.close()
    
    # Adiciona nomes e imagens dos heróis
    for m in matches_list:
        hid = str(m.get('hero_id'))
        m['hero_name'] = HEROES_DATA.get(hid, {}).get('name', 'Unknown')
        m['hero_image'] = HEROES_DATA.get(hid, {}).get('img', '')

    return jsonify(matches_list)

@app.route('/api/records')
@login_required
def api_records():
    # Calcula recordes baseados APENAS no cache local para velocidade
    uid = session['user_id']
    conn = get_db_conn()
    matches = conn.execute('SELECT * FROM matches_cache WHERE user_id = ?', (uid,)).fetchall()
    conn.close()
    
    if not matches: return jsonify({"success": True, "data": []})
    
    records = []
    # Lista de métricas para procurar o máximo
    metrics = [
        ('kills', 'Mais Kills'), 
        ('deaths', 'Mais Mortes'), 
        ('assists', 'Mais Assistências'),
        ('duration', 'Partida mais Longa')
    ]
    
    for key, label in metrics:
        # Pega a partida com o maior valor nessa chave
        best_match = max(matches, key=lambda x: x[key] if x[key] else 0)
        
        hid = str(best_match['hero_id'])
        records.append({
            "key": key,
            "label": label,
            "value": best_match[key],
            "match_id": best_match['match_id'],
            "hero_name": HEROES_DATA.get(hid, {}).get('name', 'Unknown'),
            "hero_image": HEROES_DATA.get(hid, {}).get('img', '')
        })
        
    return jsonify({"success": True, "data": records})

@app.route('/api/match_details/<match_id>')
@login_required
def api_match_details(match_id):
    # Proxy para evitar CORS e usar nossos dados de heróis
    try:
        r = requests.get(f"https://api.opendota.com/api/matches/{match_id}", timeout=6)
        data = r.json()
        
        radiant = []
        dire = []
        
        for p in data.get('players', []):
            hid = str(p.get('hero_id'))
            p_info = {
                "personaname": p.get('personaname', 'Anônimo'),
                "hero_name": HEROES_DATA.get(hid, {}).get('name', 'Unknown'),
                "hero_image": HEROES_DATA.get(hid, {}).get('img', ''),
                "kills": p.get('kills'), "deaths": p.get('deaths'), "assists": p.get('assists')
            }
            if p.get('player_slot') < 128: radiant.append(p_info)
            else: dire.append(p_info)
            
        return jsonify({"success": True, "radiant": radiant, "dire": dire})
    except Exception as e:
        return jsonify({"success": False, "error": str(e)})

# --- ROTAS DA API: ADMIN ---
@app.route('/api/admin/users')
@admin_required
def api_admin_users():
    conn = get_db_conn()
    users = conn.execute('SELECT id, nickname FROM users').fetchall()
    conn.close()
    return jsonify({"success": True, "users": [dict(u) for u in users]})

@app.route('/api/admin/delete_user', methods=['POST'])
@admin_required
def api_admin_delete():
    uid = request.json.get('user_id')
    conn = get_db_conn()
    conn.execute('DELETE FROM users WHERE id = ?', (uid,))
    conn.commit()
    conn.close()
    return jsonify({"success": True})

@app.route('/api/admin/update_password', methods=['POST'])
@admin_required
def api_admin_update_pass():
    uid = request.json.get('user_id')
    pw = request.json.get('new_password')
    hashed = generate_password_hash(pw)
    conn = get_db_conn()
    conn.execute('UPDATE users SET password = ? WHERE id = ?', (hashed, uid))
    conn.commit()
    conn.close()
    return jsonify({"success": True})

@app.route('/api/admin/update_nickname', methods=['POST'])
@admin_required
def api_admin_update_nick():
    uid = request.json.get('user_id')
    nick = request.json.get('new_nickname')
    try:
        conn = get_db_conn()
        conn.execute('UPDATE users SET nickname = ? WHERE id = ?', (nick, uid))
        conn.commit()
        conn.close()
        return jsonify({"success": True})
    except:
        return jsonify({"success": False, "message": "Nickname já existe"}), 409

if __name__ == '__main__':
    if not os.path.exists(DATABASE):
        print("AVISO: Banco de dados não encontrado. Execute 'python init_db.py'.")
    # CONFIGURADO PARA RODAR NA PORTA 61000
    app.run(host='0.0.0.0', port=61000, debug=True)