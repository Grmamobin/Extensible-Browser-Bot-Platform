from flask import Flask, render_template, jsonify, request
import sqlite3
import threading
import time
import random
# from selenium_bot import run_selenium_bot

app = Flask(__name__)
app.template_folder = '.'
app.static_folder = '.'

progress_status = {"value": 0, "status": "idle"}
is_running = False

def get_db_connection():
    conn = sqlite3.connect('history_db.db')
    conn.row_factory = sqlite3.Row
    return conn

@app.route("/")
def Platform():
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS History (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            mode TEXT,
            challenge_id TEXT,
            username TEXT,
            password TEXT,
            status TEXT
        )
    ''')
    conn.commit()
    
    cursor.execute("SELECT * FROM History ORDER BY id DESC")
    history = cursor.fetchall()
    conn.close()

    return render_template(
        "index.html",
        history=history,
        total_history=len(history),
        successful=sum(1 for h in history if h["status"] == "success"),
        failed=sum(1 for h in history if h["status"] == "failed")
    )

@app.route("/api/run", methods=["POST"])
def _run():
    global is_running, progress_status
    if is_running:
        return jsonify({"message": "A bot is already running."})

    data = request.get_json() or {}
    mode = data.get("mode")
    headless = (mode == "Headless")
    
    is_running = True
    progress_status = {"value": 0, "status": "running"}

    def run_task():
        global is_running, progress_status
        
        def update_progress():
            while is_running and progress_status["value"] < 95:
                time.sleep(1)
                if is_running:
                    progress_status["value"] += random.randint(2, 5)
                    if progress_status["value"] > 95:
                        progress_status["value"] = 95

        timer_thread = threading.Thread(target=update_progress)
        timer_thread.start()
        
        # result = run_selenium_bot(headless=headless)
        
        is_running = False
        progress_status["value"] = 100
        progress_status["status"] = "done"

    threading.Thread(target=run_task).start()

    return jsonify({"message": f"Bot started in {mode} mode."})

@app.route("/api/progress")
def get_progress():
    return jsonify(progress_status)

if __name__ == "__main__":
    app.run(debug=False, port=5000)