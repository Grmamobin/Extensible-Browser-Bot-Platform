import sqlite3

DB_NAME = 'history_db.db'

def init_db():
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS History (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            bot_name TEXT,
            browser_mode TEXT,
            start_time TEXT,
            end_time TEXT,
            challenge_id TEXT,
            username TEXT,
            password TEXT,
            status TEXT,
            error_details TEXT
        )
    ''')
    conn.commit()
    conn.close()

def save_run(bot_name, browser_mode, start_time, end_time, challenge_id, username, password, status, error_details=""):
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute('''
        INSERT INTO History (bot_name, browser_mode, start_time, end_time, challenge_id, username, password, status, error_details)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
    ''', (bot_name, browser_mode, start_time, end_time, challenge_id, username, password, status, error_details))
    conn.commit()
    conn.close()

def get_all_runs():
    conn = sqlite3.connect(DB_NAME)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM History ORDER BY id DESC")
    rows = cursor.fetchall()
    conn.close()
    return rows