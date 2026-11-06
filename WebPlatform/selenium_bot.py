from base_bot import BaseBot
from seleniumbase import Driver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.wait import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.action_chains import ActionChains
import time
import requests
import cv2
import random
import os


class PuzzleCaptchaSolver:
    def __init__(self, gap_image_path, bg_image_path, output_image_path):
        self.gap_image_path = gap_image_path
        self.bg_image_path = bg_image_path
        self.output_image_path = output_image_path

    def discern(self):
        gap_img = cv2.imread(self.gap_image_path, cv2.IMREAD_UNCHANGED)
        bg_img = cv2.imread(self.bg_image_path, cv2.IMREAD_COLOR)

        if gap_img is None or bg_img is None:
            print("Error: Could not read images.")
            return 0

        # Extract the shape mask from the slider ---->>>>
        if len(gap_img.shape) == 3 and gap_img.shape[2] == 4:
            _, mask = cv2.threshold(gap_img[:, :, 3], 1, 255, cv2.THRESH_BINARY)
        else:
            gap_gray = cv2.cvtColor(gap_img, cv2.COLOR_BGR2GRAY)
            _, mask = cv2.threshold(gap_gray, 240, 255, cv2.THRESH_BINARY_INV)

        x, y, w, h = cv2.boundingRect(mask)
        mask_cropped = mask[y:y+h, x:x+w]

        # Background for matching is setting ---->>>>
        bg_gray = cv2.cvtColor(bg_img, cv2.COLOR_BGR2GRAY)
        bg_edges = cv2.Canny(bg_gray, 100, 200)

        mask_edges = cv2.Canny(mask_cropped, 100, 200)

        # Template Matching (shape edges) ---->>>>
        result = cv2.matchTemplate(bg_edges, mask_edges, cv2.TM_CCORR_NORMED)
        
        # (highest match)
        _, max_val, _, max_loc = cv2.minMaxLoc(result)
        
        # Draw the result ---->>>>
        tl = max_loc
        br = (tl[0] + w, tl[1] + h)
        cv2.rectangle(bg_img, tl, br, (0, 0, 255), 2)
        cv2.imwrite(self.output_image_path, bg_img)

        return tl[0]

class ARCaptchaBot(BaseBot):
    def get_name(self):
        return "ARCaptcha Selenium Bot"

    def run(self, headless=True , username_sec="", password_sec=""):
        status = "failed"
        challenge_id = None
        error_msg = ""

        driver = Driver(uc=True, browser="chrome", headless=headless)
        try:
            driver.uc_open_with_reconnect("https://demo.arcaptcha.co/", reconnect_time=3)
            driver.implicitly_wait(0.5)
            # print("Simulating ARCaptcha block for testing...")
            # raise Exception("ARCaptcha detected Selenium automation. Request blocked.")
             
            # Based on `https://www.selenium.dev/documentation/webdriver/drivers/remote_webdriver/` ---->>>>
            email = driver.find_element(by=By.CSS_SELECTOR, value="input[type='email']")
            password = driver.find_element(by=By.CSS_SELECTOR, value="input[type='password']")

            email.send_keys(username_sec)
            password.send_keys(password_sec)

            wait = WebDriverWait(driver, timeout=15)

            checkbox_captcha = wait.until(EC.element_to_be_clickable((By.ID, "input-checkbox")))
            checkbox_captcha.click()

            driver.switch_to.default_content()
            
            time.sleep(3)

            # Allow to attempt for 2 times ---->>>>
            max_attempts = 2
            attempt = 1
            puzzle_solved = False

            while attempt <= max_attempts and not puzzle_solved:
                print(f"[*] Attempt {attempt} of {max_attempts} to solve the puzzle...")
                
                try:
                    # Load image ---->>>>
                    wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, "img.puzzle")))
                    time.sleep(1)

                    # Extract Slider ---->>>>
                    slider_element = driver.find_element(By.CSS_SELECTOR, "img.puzzle")
                    slider_url = slider_element.get_attribute("src")
                    if slider_url and slider_url.startswith("http"):
                        response = requests.get(slider_url)
                        if response.status_code == 200:
                            with open("slider.png", "wb") as f:
                                f.write(response.content)

                    # Extract Background ---->>>>
                    bg_element = driver.find_elements(By.CSS_SELECTOR, "img.tw-object-contain")[0]
                    bg_url = bg_element.get_attribute("src")
                    if bg_url and bg_url.startswith("http"):
                        response = requests.get(bg_url)
                        if response.status_code == 200:
                            with open("bg.png", "wb") as f:
                                f.write(response.content)

                    solver = PuzzleCaptchaSolver(
                        gap_image_path="slider.png",
                        bg_image_path="bg.png",
                        output_image_path="result.png"
                    )
                    position = solver.discern()
                    
                    # Scale Drag Distance ----->>>>
                    bg_width_rendered = bg_element.size['width']
                    bg_img = cv2.imread("bg.png")
                    if bg_img is not None:
                        bg_width_native = bg_img.shape[1]
                        scale_ratio = bg_width_rendered / bg_width_native
                        drag_distance = int(position * scale_ratio)
                    else:
                        drag_distance = position
                        
                    print(f"[DEBUG] Native pos: {position}, Calculated drag: {drag_distance}")

                    # Drag ----->>>>
                    slider_handle = driver.find_element(By.CSS_SELECTOR, "div.draggable")
                    action = ActionChains(driver)
                    action.click_and_hold(slider_handle).perform()
                    
                    current = 0
                    while current < drag_distance:
                        step = random.randint(5, 15)
                        if current + step > drag_distance:
                            step = drag_distance - current
                        action.move_by_offset(step, 0).perform()
                        current += step
                        time.sleep(random.uniform(0.02, 0.08))
                        
                    time.sleep(0.5)
                    action.release().perform()
                    time.sleep(2)

                    # Check if solved? ----->>>>
                    overlay = driver.find_elements(By.ID, "arcaptcha_full_body_container")
                    if not overlay:
                        print("[*] Puzzle solved successfully!")
                        puzzle_solved = True
                        status = "success"
                        
                        # Extract Challenge ID via js code --->>
                        try:
                            script_tag = driver.find_element(By.CSS_SELECTOR, "script[id^='challenge-script-']")
                            widget_id = script_tag.get_attribute("id").replace("challenge-script-", "")
                            challenge_id = driver.execute_script(f"return window.arcaptcha.getWidget('{widget_id}').getChallengeID();")
                            print(f"Extracted Challenge ID: {challenge_id}")
                        except Exception as js_err:
                            print(f"Could not extract challenge ID: {js_err}")
                            error_msg = str(js_err)
                        
                    else:
                        print("Puzzle failed. Retrying...")
                        refresh_btn = driver.find_elements(By.CSS_SELECTOR, "svg")
                        if len(refresh_btn) >= 3:
                            driver.execute_script("arguments[0].click();", refresh_btn[2])
                        else:
                            driver.execute_script("arguments[0].click();", refresh_btn[-1])
                        time.sleep(3) # <<<<---- Wait for new images to load

                except Exception as e:
                    print(f"[!] Error during attempt {attempt}: {e}")
                    error_msg = str(e)
                    time.sleep(2)

                attempt += 1

            driver.switch_to.default_content()
            
            login_btn = driver.find_element(By.XPATH, "//button[contains(text(), 'Login')]")
            try:
                login_btn.click()
            except:
                print("Login button intercepted by overlay. Forcing click...")
                driver.execute_script("arguments[0].click();", login_btn)

            time.sleep(3)

            try:
                success_element = driver.find_element(By.XPATH, "//*[contains(text(), 'success') or contains(text(), 'Success') or contains(text(), 'welcome') or contains(text(), 'Welcome')]")
                status = "success"
            except:
                if "Blocked!" in driver.page_source:
                    status = "blocked"
                elif "login" not in driver.current_url.lower() and "demo.arcaptcha.co" not in driver.current_url:
                    status = "success"
                elif "error" in driver.page_source.lower() or "invalid" in driver.page_source.lower():
                    status = "failed"

        except Exception as e:
            print(f"Error encountered: {e}")
            error_msg = str(e)

        finally:
            driver.quit()
            
        return {"status": status, "challenge_id": challenge_id, "error": error_msg}