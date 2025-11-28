"""
Banco de dados - 2 schemas simples
"""
import sqlite3
import os

DB_PATH = os.path.join(os.path.dirname(__file__), '..', 'sentiment.db')


def init_db():
    """Inicializa banco com 2 tabelas"""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    # Schema 1: Users
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            email TEXT NOT NULL UNIQUE,
            password_hash TEXT NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')

    # Schema 2: Analyses
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS analyses (
            id TEXT PRIMARY KEY,
            user_id INTEGER NOT NULL,
            text TEXT NOT NULL,
            sentiment TEXT NULL,
            score REAL NULL,
            status TEXT DEFAULT 'pending',
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES users(id)
        )
    ''')

    conn.commit()
    conn.close()
    print("✓ Banco inicializado (2 schemas)")


def get_db():
    """Retorna conexão"""
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


if __name__ == '__main__':
    init_db()
