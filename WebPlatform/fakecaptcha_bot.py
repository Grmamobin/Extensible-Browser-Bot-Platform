from base_bot import BaseBot
import time

class FakeCaptchaBot(BaseBot):
    def get_name(self):
        return "Fake Bot"

    def run(self, headless=True, username_sec="", password_sec=""):
        print("Running...")
        time.sleep(2)
        
        return {
            "status": "success",
            "challenge_id": "FAKE12345",
            "error": ""
        }