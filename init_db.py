# LOCAL DO ARQUIVO: init_db.py
import sqlite3
import os

# Define caminhos absolutos para evitar erros de pasta
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DATABASE = os.path.join(BASE_DIR, 'mmr_tracker.db')

# Schema com tabela de cache e segurança reforçada
schema = """
CREATE TABLE IF NOT EXISTS users (
    id INTEGER PRIMARY KEY, -- Steam ID 32-bit
    nickname TEXT NOT NULL UNIQUE,
    password TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS mmr_history (
    entry_id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER NOT NULL,
    mmr INTEGER NOT NULL,
    diferenca INTEGER NOT NULL,
    resultado TEXT NOT NULL, -- 'vitoria', 'derrota', 'empate', 'inicial'
    timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users (id) ON DELETE CASCADE
);

-- NOVA TABELA: Cache de partidas para evitar requisições lentas na API
CREATE TABLE IF NOT EXISTS matches_cache (
    match_id INTEGER PRIMARY KEY,
    user_id INTEGER NOT NULL,
    hero_id INTEGER,
    kills INTEGER,
    deaths INTEGER,
    assists INTEGER,
    duration INTEGER,
    game_mode INTEGER,
    radiant_win BOOLEAN,
    player_slot INTEGER,
    start_time INTEGER,
    FOREIGN KEY (user_id) REFERENCES users (id) ON DELETE CASCADE
);
"""

def init_db():
    try:
        print(f"Conectando ao banco em: {DATABASE}")
        conn = sqlite3.connect(DATABASE)
        cursor = conn.cursor()
        
        # Habilita chaves estrangeiras para o DELETE CASCADE funcionar
        cursor.execute("PRAGMA foreign_keys = ON")
        
        cursor.executescript(schema)
        conn.commit()
        print("Banco de dados inicializado/atualizado com sucesso!")
        print("Tabelas verificadas: users, mmr_history, matches_cache.")
    except sqlite3.Error as e:
        print(f"Erro crítico no banco de dados: {e}")
    finally:
        if conn: conn.close()

if __name__ == '__main__':
    init_db()