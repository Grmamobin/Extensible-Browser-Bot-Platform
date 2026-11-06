import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import database
from base_bot import BaseBot
TEST_DB_NAME = 'test_history.db'
database.DB_NAME = TEST_DB_NAME

class MockSuccessBot(BaseBot):
    def get_name(self): return "Mock Success Bot"
    def run(self, headless=True):
        # Simulates a perfect run where the captcha is solved and ID is extracted
        return {"status": "success", "challenge_id": "123456789", "error": ""}

class MockBlockedBot(BaseBot):
    def get_name(self): return "Mock Blocked Bot"
    def run(self, headless=True):
        # Simulates ARCaptcha blocking the bot before it can solve the puzzle
        return {"status": "blocked", "challenge_id": None, "error": "ARCaptcha blocked the request"}

class MockTimeoutBot(BaseBot):
    def get_name(self): return "Mock Timeout Bot"
    def run(self, headless=True):
        # Simulates the bot taking too long and timing out while waiting for the puzzle
        return {"status": "failed", "challenge_id": None, "error": "Timeout waiting for puzzle"}

class MockMissingIdBot(BaseBot):
    def get_name(self): return "Mock Missing ID Bot"
    def run(self, headless=True):
        # Simulates a scenario where the puzzle is solved but the JS extraction fails
        return {"status": "success", "challenge_id": None, "error": "Could not extract challenge_id via JS"}

class MockFormFailBot(BaseBot):
    def get_name(self): return "Mock Form Fail Bot"
    def run(self, headless=True):
        # Simulates a scenario where the captcha is solved, but the login credentials fail
        return {"status": "failed", "challenge_id": "987654321", "error": "Login form submission failed"}

# ==========================================
# Mock Bots for Advanced Tests
# ==========================================

class MockTimeoutDuringExtractionBot(BaseBot):
    def get_name(self): return "Timeout During Extraction Bot"
    def run(self, headless=True):
        # Simulates a timeout specifically during the JS challenge_id extraction phase
        return {"status": "failed", "challenge_id": None, "error": "Timeout while extracting challenge_id via JS"}

class MockBrowserCrashBot(BaseBot):
    def get_name(self): return "Browser Crash Bot"
    def run(self, headless=True):
        # Simulates the Chrome browser crashing or disconnecting unexpectedly
        return {"status": "failed", "challenge_id": None, "error": "WebDriverException: chrome not reachable"}

class MockRetrySuccessBot(BaseBot):
    def get_name(self): return "Retry Success Bot"
    def run(self, headless=True):
        # Simulates the bot failing on the first attempt but succeeding on the retry
        return {"status": "success", "challenge_id": "RETRY_SUCCESS_999", "error": "First attempt failed, second attempt succeeded"}

class MockDomChangedBot(BaseBot):
    def get_name(self): return "DOM Changed Bot"
    def run(self, headless=True):
        # Simulates ARCaptcha updating their HTML, causing element selectors to fail
        return {"status": "failed", "challenge_id": None, "error": "NoSuchElementException: Unable to locate img.puzzle"}

class MockJsInjectionFailBot(BaseBot):
    def get_name(self): return "JS Injection Fail Bot"
    def run(self, headless=True):
        # Simulates a scenario where the JavaScript context is lost or modified
        return {"status": "success", "challenge_id": None, "error": "JavascriptException: window.arcaptcha is undefined"}

# ==========================================
# Test Execution
# ==========================================

def run_tests():
    # if os.path.exists(TEST_DB_NAME):
        # os.remove(TEST_DB_NAME)
    database.init_db()

    print("\n--- Running Combined Tests ---")

    # Test 1: Basic Success
    bot = MockSuccessBot()
    result = bot.run()
    database.save_run(bot.get_name(), "Headless", "2026-01-01 10:00:00", "2026-01-01 10:00:10", result["challenge_id"], "demo", "demo", result["status"], result["error"])
    runs = database.get_all_runs()
    assert len(runs) == 1 and runs[0]["status"] == "success" and runs[0]["challenge_id"] == "123456789"
    print("Test 1 (Success) passed.")

    # Test 2: Captcha Blocking
    bot = MockBlockedBot()
    result = bot.run()
    database.save_run(bot.get_name(), "Headful", "2026-01-01 10:00:00", "2026-01-01 10:00:05", result["challenge_id"], "demo", "demo", result["status"], result["error"])
    runs = database.get_all_runs()
    assert runs[0]["status"] == "blocked" and runs[0]["challenge_id"] is None and "blocked" in runs[0]["error_details"]
    print("Test 2 (Blocked) passed.")

    # Test 3: Timeout Waiting for Puzzle
    bot = MockTimeoutBot()
    result = bot.run()
    database.save_run(bot.get_name(), "Headless", "2026-01-01 10:00:00", "2026-01-01 10:00:30", result["challenge_id"], "demo", "demo", result["status"], result["error"])
    runs = database.get_all_runs()
    assert runs[0]["status"] == "failed" and "Timeout" in runs[0]["error_details"]
    print("Test 3 (Timeout) passed.")

    # Test 4: Missing Challenge ID
    bot = MockMissingIdBot()
    result = bot.run()
    database.save_run(bot.get_name(), "Headless", "2026-01-01 10:00:00", "2026-01-01 10:00:15", result["challenge_id"], "demo", "demo", result["status"], result["error"])
    runs = database.get_all_runs()
    assert runs[0]["challenge_id"] is None and "Could not extract" in runs[0]["error_details"]
    print("Test 4 (Missing ID) passed.")

    # Test 5: Unsuccessful Form Verification
    bot = MockFormFailBot()
    result = bot.run()
    database.save_run(bot.get_name(), "Headful", "2026-01-01 10:00:00", "2026-01-01 10:00:20", result["challenge_id"], "demo", "demo", result["status"], result["error"])
    runs = database.get_all_runs()
    assert runs[0]["status"] == "failed" and runs[0]["challenge_id"] == "987654321" and "Login form" in runs[0]["error_details"]
    print("Test 5 (Form Fail) passed.")

    # Test 6: Timeout During Challenge ID Extraction
    bot = MockTimeoutDuringExtractionBot()
    result = bot.run()
    database.save_run(bot.get_name(), "Headless", "2026-01-01 10:00:00", "2026-01-01 10:01:00", result["challenge_id"], "demo", "demo", result["status"], result["error"])
    runs = database.get_all_runs()
    assert runs[0]["status"] == "failed" and "Timeout while extracting" in runs[0]["error_details"]
    print("Test 6 (Timeout During Extraction) passed.")

    # Test 7: Browser Crash
    bot = MockBrowserCrashBot()
    result = bot.run()
    database.save_run(bot.get_name(), "Headful", "2026-01-01 10:00:00", "2026-01-01 10:00:15", result["challenge_id"], "demo", "demo", result["status"], result["error"])
    runs = database.get_all_runs()
    assert runs[0]["status"] == "failed" and "chrome not reachable" in runs[0]["error_details"]
    print("Test 7 (Browser Crash) passed.")

    # Test 8: Retry Success
    bot = MockRetrySuccessBot()
    result = bot.run()
    database.save_run(bot.get_name(), "Headless", "2026-01-01 10:00:00", "2026-01-01 10:00:25", result["challenge_id"], "demo", "demo", result["status"], result["error"])
    runs = database.get_all_runs()
    assert runs[0]["status"] == "success" and runs[0]["challenge_id"] == "RETRY_SUCCESS_999" and "second attempt succeeded" in runs[0]["error_details"]
    print("Test 8 (Retry Success) passed.")

    # Test 9: DOM Changed
    bot = MockDomChangedBot()
    result = bot.run()
    database.save_run(bot.get_name(), "Headful", "2026-01-01 10:00:00", "2026-01-01 10:00:10", result["challenge_id"], "demo", "demo", result["status"], result["error"])
    runs = database.get_all_runs()
    assert runs[0]["status"] == "failed" and "Unable to locate img.puzzle" in runs[0]["error_details"]
    print("Test 9 (DOM Changed) passed.")

    # Test 10: JS Injection Fail
    bot = MockJsInjectionFailBot()
    result = bot.run()
    database.save_run(bot.get_name(), "Headless", "2026-01-01 10:00:00", "2026-01-01 10:00:20", result["challenge_id"], "demo", "demo", result["status"], result["error"])
    runs = database.get_all_runs()
    assert runs[0]["status"] == "success" and runs[0]["challenge_id"] is None and "window.arcaptcha is undefined" in runs[0]["error_details"]
    print("Test 10 (JS Injection Fail) passed.")

    # os.remove(TEST_DB_NAME)
    print("\nAll 10 Combined Tests Passed Successfully!")

if __name__ == "__main__":
    run_tests()