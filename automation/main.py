import json
import time
import os
import glob
import sys
import subprocess
import argparse
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.common.action_chains import ActionChains
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.chrome.service import Service

# ==========================================
#             SHARED UTILITIES
# ==========================================

def launch_chrome_debugger():
    """
    Launches Chrome in remote debugging mode if it's not already running.
    """
    # Verify this path matches your OS (MacOS example below)
    chrome_path = "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome"
    user_data_dir = os.path.expanduser("~/gemini-bot") 
    port = "9222"

    # Check if port is in use
    is_running = os.system(f"lsof -i :{port} > /dev/null 2>&1")
    
    if is_running == 0:
        print(f"[*] Chrome is already running on port {port}. Connecting...")
        return

    print(f"[*] Launching Chrome on port {port}...")
    cmd = [
        chrome_path,
        f"--remote-debugging-port={port}",
        f"--user-data-dir={user_data_dir}"
    ]
    
    try:
        subprocess.Popen(cmd)
        time.sleep(4) 
    except FileNotFoundError:
        print(f"[!] Could not find Chrome at: {chrome_path}")
        sys.exit(1)

def get_next_scenario(folder_path):
    # Sort files to ensure processing order
    files = sorted(glob.glob(os.path.join(folder_path, "*.json")))
    
    for filepath in files:
        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            # Delete empty files
            if not data:
                print(f"[*] File {os.path.basename(filepath)} is empty. Deleting...")
                os.remove(filepath)
                continue
            
            # Return first scenario found
            first_key = next(iter(data))
            return filepath, first_key, data[first_key]
            
        except json.JSONDecodeError:
            print(f"[!] Error reading {filepath}. Skipping.")
            continue
            
    return None, None, None

def remove_scenario_from_file(filepath, key):
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        if key in data:
            del data[key]
        
        if not data:
            print(f"[*] All scenarios done in {os.path.basename(filepath)}. Deleting file.")
            os.remove(filepath)
        else:
            with open(filepath, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=4, ensure_ascii=False)
            print(f"[*] Removed '{key}' from {os.path.basename(filepath)}.")
            
    except Exception as e:
        print(f"[!] Error updating file: {e}")

# ==========================================
#             PLATFORM CLASSES
# ==========================================

class GeminiAutomation:
    def __init__(self, driver, wait, long_wait):
        self.driver = driver
        self.wait = wait
        self.long_wait = long_wait

    def focus_tab(self):
        for handle in self.driver.window_handles:
            self.driver.switch_to.window(handle)
            if "gemini.google.com" in self.driver.current_url:
                print("Found existing Gemini tab.")
                return
        print("Opening new Gemini tab...")
        self.driver.execute_script("window.open('https://gemini.google.com', '_blank');")
        self.driver.switch_to.window(self.driver.window_handles[-1])

    def run_generation(self, scenario):
        print("[*] Clicking 'New chat'...")
        try:
            new_chat_btn = self.wait.until(EC.element_to_be_clickable(
                (By.XPATH, "//*[contains(text(), 'New chat')]")
            ))
            new_chat_btn.click()
            time.sleep(2) 
        except Exception as e:
            print(f"[!] Could not find 'New chat': {e}")

        prompt = (
            f"Subject: {scenario.get('Subject', '')} "
            f"Action: {scenario.get('Action', '')} "
            f"Scene: {scenario.get('Scene', '')} "
            f"Style: {scenario.get('Style', '')} "
            f"Sounds: {scenario.get('Sounds', '')} "
            f"Technical(Negative Prompt): {scenario.get('Technical(Negative Prompt)', '')}"
        )
        
        print(f"[*] Sending prompt: {prompt[:50]}...")

        try:
            # 1. Click Tools
            tools_btn = self.wait.until(EC.element_to_be_clickable(
                (By.XPATH, "//button[.//span[contains(text(), 'Tools')]]")
            ))
            tools_btn.click()
            time.sleep(1)

            # 2. Click Create videos
            video_menu = self.wait.until(EC.element_to_be_clickable(
                (By.XPATH, "//div[contains(text(), 'Create videos')]")
            ))
            video_menu.click()
            time.sleep(1)

            # 3. Type Prompt
            input_box = self.wait.until(EC.presence_of_element_located(
                (By.CSS_SELECTOR, "div[contenteditable='true']")
            ))
            input_box.clear()
            input_box.send_keys(prompt)
            time.sleep(1)
            
            # 4. Submit
            input_box.send_keys(Keys.ENTER)
            print("[*] Prompt submitted! Waiting for result...")
            
            # 5. Wait for Result & Download
            self.download_video()
            time.sleep(5)

        except Exception as e:
            print(f"[!] Gemini Error: {e}")
            raise e

    def download_video(self):
        print("[*] Waiting for video generation...")
        try:
            video_element = self.long_wait.until(EC.presence_of_element_located(
                (By.TAG_NAME, "video")
            ))
            print("[*] Video generated! Finding download button...")
            time.sleep(2)

            actions = ActionChains(self.driver)
            actions.move_to_element(video_element).perform()
            time.sleep(1)

            download_btn = self.wait.until(EC.element_to_be_clickable(
                (By.XPATH, "//button[@aria-label='Download video']")
            ))
            download_btn.click()
            print("[*] Download started successfully!")
            time.sleep(5)
        except Exception as e:
            print(f"[!] Auto-download failed: {e}")


class GrokAutomation:
    def __init__(self, driver, wait, long_wait):
        self.driver = driver
        self.wait = wait
        self.long_wait = long_wait

    def focus_tab(self):
        for handle in self.driver.window_handles:
            self.driver.switch_to.window(handle)
            if "grok.com" in self.driver.current_url:
                print("Found existing Grok tab.")
                return
        print("Opening new Grok tab...")
        self.driver.get("https://grok.com/imagine")

    def run_generation(self, scenario):
        self.driver.get("https://grok.com/imagine")
        time.sleep(3)

        # TODO: move this detection to the end of the video generation process
        if self.is_rate_limited():
            raise Exception("Rate Limit Reached")

        prompt = (
            f"Subject: {scenario.get('Subject', '')} "
            f"Action: {scenario.get('Action', '')} "
            f"Scene: {scenario.get('Scene', '')} "
            f"Style: {scenario.get('Style', '')} "
        )
        print(f"[*] Sending prompt to Grok: {prompt[:50]}...")

        try:
            input_box = self.wait.until(EC.presence_of_element_located(
                (By.CSS_SELECTOR, "div[contenteditable='true']")
            ))
            
            input_box.send_keys(prompt)
            time.sleep(1)
            input_box.send_keys(Keys.ENTER)
            
            print("[*] Prompt submitted. Waiting for generation...")

            # Sleep until video appears
            # For now, just wait fixed time.
            # TODO We can improve this later with better detection by waiting until generating message disappears
            time.sleep(90)

            # Wait for specific download button
            download_btn = self.long_wait.until(EC.element_to_be_clickable(
                (By.XPATH, "//button[@aria-label='Download']")
            ))
            
            print("[*] Video generated. Clicking download...")
            download_btn.click()
            time.sleep(5)

            # Cleanup
            self.cleanup_post()

        except Exception as e:
            if "Rate Limit" in str(e):
                raise e
            print(f"[!] Grok Error: {e}")
            raise e

    def cleanup_post(self):
        print("[*] Starting cleanup (Unsave/Delete)...")
        try:
            # Click 'More' (...)
            more_menu = self.wait.until(EC.element_to_be_clickable(
                (By.XPATH, "//button[contains(@aria-label, 'More') or .//svg[contains(@class, 'lucide-more-horizontal')]]")
            ))
            more_menu.click()
            time.sleep(1)

            # Click Unsave if present
            # Grok menu items don't consist of buttons. They are divs.
            try:
                unsave_xpath = "//div[@role='menuitem']//span[text()='Unsave']/.."
                element = self.wait.until(
                    EC.presence_of_element_located((By.XPATH, unsave_xpath))
                )

                self.driver.execute_script("arguments[0].click();", element)
                print("[*] Clicked 'Unsave'.")
                time.sleep(1)
                more_menu.click() # Re-open menu
                time.sleep(1)
            except:
                pass

            # Click Delete

            delete_xpath = "//div[@role='menuitem']//span[text()='Delete post']/.."
            element = self.wait.until(
                EC.presence_of_element_located((By.XPATH, delete_xpath))
            )

            self.driver.execute_script("arguments[0].click();", element)

            delete_button = self.wait.until(
                EC.element_to_be_clickable((By.XPATH, "//button[normalize-space()='Delete post']"))
            )

            delete_button.click()            

            """
            try:
                confirm_btn = self.driver.find_element(By.XPATH, "//button[contains(text(), 'Delete') and not(contains(text(), 'post'))]")
                confirm_btn.click()
            except:
                pass
            """

            time.sleep(2)

        except Exception as e:
            print(f"[!] Cleanup failed: {e}")

    def is_rate_limited(self):
        try:
            body_text = self.driver.find_element(By.TAG_NAME, "body").text
            if "rate limit reached" in body_text.lower():
                print("[!] Rate limit detected!")
                return True
        except:
            pass
        return False

# ==========================================
#             CONTROLLER
# ==========================================

class AutomationController:
    def __init__(self, mode="gemini"):
        launch_chrome_debugger()        
        print(f"[*] Connecting to Chrome (Mode: {mode})...")
        
        self.options = Options()
        self.options.add_experimental_option("debuggerAddress", "127.0.0.1:9222")
        
        self.driver = webdriver.Chrome(
            service=Service(ChromeDriverManager().install()),
            options=self.options
        )
        self.wait = WebDriverWait(self.driver, 20)
        self.long_wait = WebDriverWait(self.driver, 300)
        
        if mode == "gemini":
            self.bot = GeminiAutomation(self.driver, self.wait, self.long_wait)
        elif mode == "grok":
            self.bot = GrokAutomation(self.driver, self.wait, self.long_wait)
        else:
            raise ValueError("Invalid mode.")

    def run(self, folder_path, count=3):
        for i in range(count):
            filepath, key, scenario = get_next_scenario(folder_path)
            
            if not scenario:
                print("[!] No more scenarios found!")
                break
                
            print(f"\n--- Processing Video {i+1}/{count} ---")
            print(f"[*] File: {os.path.basename(filepath)} | Scenario: {key}")
            
            self.bot.focus_tab()

            try:
                self.bot.run_generation(scenario)
                # Success -> Remove from file
                remove_scenario_from_file(filepath, key)
            except Exception as e:
                print(f"[!] Stopping batch due to error: {e}")
                if "Rate Limit" in str(e):
                    print("[!] Exiting due to Rate Limit.")
                    break
                # On random error, skip to next iteration
                continue
            
            time.sleep(5)

# ==========================================
#             MAIN ENTRY
# ==========================================

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Automate video generation on Gemini or Grok.")
    
    # 1. Mode Argument (Required)
    parser.add_argument(
        "--mode", 
        type=str, 
        choices=["gemini", "grok"], 
        required=True, 
        help="Select the generation platform."
    )
    
    # 2. Folder Argument (Optional)
    parser.add_argument(
        "--folder", 
        type=str, 
        help="Path to the scenarios folder. Defaults to ./<mode>/scenarios"
    )
    
    # 3. Count Argument (Optional)
    parser.add_argument(
        "--count", 
        type=int, 
        default=3, 
        help="Number of videos to generate in this run (Default: 3)."
    )
    
    args = parser.parse_args()

    # Determine default folder if not provided
    if not args.folder:
        # TODO: Update paths as necessary (If we need to add more modes or scenarios in future)
        args.folder = f"./{args.mode}/scenarios/fruit_cutting" if args.mode == "gemini" else f"./{args.mode}/scenarios/animal_chef"

    # Validate folder existence
    if not os.path.exists(args.folder):
        print(f"[!] Folder '{args.folder}' does not exist.")
        print(f"[!] Please create it or specify a different folder using --folder")
        exit(1)

    print(f"[*] Starting Automation | Mode: {args.mode} | Count: {args.count}")
    print(f"[*] Scenario Folder: {args.folder}")

    controller = AutomationController(mode=args.mode)
    controller.run(args.folder, count=args.count)
