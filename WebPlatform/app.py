from flask import Flask, render_template, jsonify, request
import threading
import os
import time
import random
import datetime
import database
from dotenv import load_dotenv
from selenium_bot import ARCaptchaBot

app = Flask(__name__)
app.template_folder = 'templates'
app.static_folder = 'static'
load_dotenv()
email_ = os.getenv("ARCA_USERNAME")
password_ = os.getenv("ARCA_PASSWORD")
from fakecaptcha_bot import FakeCaptchaBot
BOT_REGISTRY = {
    "arcaptcha": ARCaptchaBot,
    "fakecaptch": FakeCaptchaBot, # <-- new robot
}

progress_status = {"value": 0, "status": "idle"}
is_running = False

@app.route("/")
def Platform():
    database.init_db()
    history = database.get_all_runs()
    total = len(history)
    successful = sum(1 for h in history if h["status"] == "success")
    failed = sum(1 for h in history if h["status"] in ["failed", "blocked"])

    return render_template(
        "index.html",
        history=history,
        total_history=total,
        successful=successful,
        failed=failed,
        bots=list(BOT_REGISTRY.keys())
    )

@app.route("/api/run", methods=["POST"])
def _run():
    global is_running, progress_status
    if is_running:
        return jsonify({"message": "A bot is already running."})

    data = request.get_json() or {}
    bot_name = data.get("bot_name", "arcaptcha")
    mode = data.get("mode", "Headful")
    headless = (mode == "Headless")
    
    is_running = True
    progress_status = {"value": 0, "status": "running"}

    def run_task():
        global is_running, progress_status
        
        bot_class = BOT_REGISTRY.get(bot_name)
        bot = bot_class()
        start_time = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        
        def update_progress():
            while is_running and progress_status["value"] < 95:
                time.sleep(1)
                if is_running:
                    progress_status["value"] += random.randint(2, 5)
                    if progress_status["value"] > 95:
                        progress_status["value"] = 95

        timer_thread = threading.Thread(target=update_progress)
        timer_thread.start()
        
        result = bot.run(headless=headless, username_sec=email_, password_sec=password_)

        
        end_time = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        
        database.save_run(
            bot_name=bot.get_name(),
            browser_mode=mode,
            start_time=start_time,
            end_time=end_time,
            challenge_id=result.get("challenge_id"),
            username=email_,
            password=password_,
            status=result.get("status"),
            error_details=result.get("error", "")
        )
        
        is_running = False
        progress_status["value"] = 100
        progress_status["status"] = "done"

    threading.Thread(target=run_task).start()

    return jsonify({"message": f"Bot started in {mode} mode."})

@app.route("/api/progress")
def get_progress():
    return jsonify(progress_status)

if __name__ == "__main__":
    database.init_db()
    app.run(debug=False, host='0.0.0.0', port=8000)