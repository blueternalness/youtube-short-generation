import json
import time
import os
import glob
import sys
import subprocess
import argparse
import re
import random
from datetime import datetime
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
    # Verify this path matches your OS
    chrome_path = "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome"
    user_data_dir = os.path.expanduser("~/gemini-bot") 
    port = "9222"

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
            
            if not data:
                print(f"[*] File {os.path.basename(filepath)} is empty. Deleting...")
                os.remove(filepath)
                continue
            
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

def get_generation_prompt(prompt_path):
    """Reads a random text file from the prompts folder."""   
    try:
        with open(prompt_path, 'r', encoding='utf-8') as f:
            return f.read()
    except Exception as e:
        print(f"[!] Error reading prompt file: {e}")
        return None

def extract_json_from_text(text):
    """Extracts JSON object from a string using regex, handling Markdown blocks."""
    # Pattern to find JSON block enclosed in ```json ... ``` or just { ... }
    # 1. Try finding markdown code block first
    match = re.search(r"```json\s*(\{.*?\})\s*```", text, re.DOTALL)
    if not match:
        # 2. Try finding just the outer braces
        match = re.search(r"(\{.*\})", text, re.DOTALL)
    
    if match:
        json_str = match.group(1)
        try:
            return json.loads(json_str)
        except json.JSONDecodeError:
            print("[!] Text found looks like JSON but failed to parse.")
            return None
    return None

# ==========================================
#             PLATFORM CLASSES
# ==========================================

class GeminiScenarioGenerator:
    """Handles generating new scenarios via Gemini chat."""
    def __init__(self, driver, wait):
        self.driver = driver
        self.wait = wait

    def generate_and_save(self, prompt_text, output_folder):
        print("\n--- Starting Scenario Generation ---")
        
        # 1. Focus Tab
        self._focus_tab()

        # 2. Start New Chat
        self._new_chat()

        # 3. Send Prompt
        print("[*] Sending scenario generation prompt...")
        try:
            input_box = self.wait.until(EC.presence_of_element_located(
                (By.CSS_SELECTOR, "div[contenteditable='true']")
            ))
            input_box.clear()
            # Send keys in chunks if too long, or just send
            self.driver.execute_script("arguments[0].innerText = arguments[1];", input_box, prompt_text)
            input_box.send_keys(" ") # Trigger event
            time.sleep(1)
            input_box.send_keys(Keys.ENTER)
        except Exception as e:
            print(f"[!] Error sending prompt: {e}")
            return False

        # 4. Wait for and Extract Response
        print("[*] Waiting for Gemini to generate scenarios...")
        time.sleep(10) # Initial buffer
        
        # Wait for "stopped" state or long enough time. 
        # Strategy: Poll for the latest message content until it contains "}"
        max_retries = 30
        extracted_data = None
        
        for i in range(max_retries):
            try:
                # Get all response containers
                print(f"[*] Checking for Gemini response... (Attempt {i})")
                # METHOD A: Get all markdown text (General purpose)
                # Use CSS Selector '.markdown' to match "markdown markdown-main-panel..."
                responses = self.driver.find_elements(By.CSS_SELECTOR, ".markdown")
                
                if responses:
                    # Get the text of the very last response
                    last_response_text = responses[-1].text
                    extracted_data = extract_json_from_text(last_response_text)
                
                # METHOD B: Fallback - Target the code block directly (Specific to your HTML snippet)
                if not extracted_data:
                    code_blocks = self.driver.find_elements(By.TAG_NAME, "code")
                    if code_blocks:
                        last_code_text = code_blocks[-1].text
                        extracted_data = extract_json_from_text(last_code_text)
                
                if extracted_data:
                    print("[*] Successfully extracted JSON data.")
                    break
            except Exception as e:
                print(e)
                pass
            time.sleep(2)

        if not extracted_data:
            print("[!] Failed to extract valid JSON from Gemini response.")
            return False

        # 5. Save to File
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"{timestamp}.json"
        output_path = os.path.join(output_folder, filename)
        
        try:
            with open(output_path, 'w', encoding='utf-8') as f:
                json.dump(extracted_data, f, indent=4, ensure_ascii=False)
            print(f"[*] Saved new scenarios to: {output_path}")
            return True
        except Exception as e:
            print(f"[!] Error saving file: {e}")
            return False

    def _focus_tab(self):
        for handle in self.driver.window_handles:
            self.driver.switch_to.window(handle)
            if "gemini.google.com" in self.driver.current_url:
                return
        self.driver.execute_script("window.open('https://gemini.google.com', '_blank');")
        self.driver.switch_to.window(self.driver.window_handles[-1])

    def _new_chat(self):
        try:
            new_chat_btn = self.wait.until(EC.element_to_be_clickable(
                (By.XPATH, "//*[contains(text(), 'New chat')]")
            ))
            new_chat_btn.click()
            time.sleep(2)
        except:
            print("[!] Could not click New Chat (might already be new).")

class GeminiVideoAutomation:
    """Handles Video Generation logic (Original)."""
    def __init__(self, driver, wait, long_wait):
        self.driver = driver
        self.wait = wait
        self.long_wait = long_wait

    def focus_tab(self):
        for handle in self.driver.window_handles:
            self.driver.switch_to.window(handle)
            if "gemini.google.com" in self.driver.current_url:
                return
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

        parts = []

        if scenario.get("Subject"):
            parts.append(f"Subject: {scenario['Subject']}")
        if scenario.get("Action"):
            parts.append(f"Action: {scenario['Action']}")
        if scenario.get("Scene"):
            parts.append(f"Scene: {scenario['Scene']}")
        if scenario.get("Style"):
            parts.append(f"Style: {scenario['Style']}")
        if scenario.get("Sounds"):
            parts.append(f"Sounds: {scenario['Sounds']}")
        if scenario.get("TechnicalDetails"):
            parts.append(f"TechnicalDetails: {scenario['TechnicalDetails']}")
        if scenario.get("Technical(Negative Prompt)"):
            parts.append(f"Technical(Negative Prompt): {scenario['Technical(Negative Prompt)']}")

        prompt = " ".join(parts)
        
        print(f"[*] Sending Video Prompt...")

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

        """
        prompt = (
            f"Subject: {scenario.get('Subject', '')} "
            f"Action: {scenario.get('Action', '')} "
            f"Scene: {scenario.get('Scene', '')} "
            f"Style: {scenario.get('Style', '')} "
        )
        """
        
        parts = []

        if scenario.get("Subject"):
            parts.append(f"Subject: {scenario['Subject']}")
        if scenario.get("Action"):
            parts.append(f"Action: {scenario['Action']}")
        if scenario.get("Scene"):
            parts.append(f"Scene: {scenario['Scene']}")
        if scenario.get("Style"):
            parts.append(f"Style: {scenario['Style']}")
        if scenario.get("Sounds"):
            parts.append(f"Sounds: {scenario['Sounds']}")
        if scenario.get("TechnicalDetails"):
            parts.append(f"TechnicalDetails: {scenario['TechnicalDetails']}")
        if scenario.get("Technical(Negative Prompt)"):
            parts.append(f"Technical(Negative Prompt): {scenario['Technical(Negative Prompt)']}")

        prompt = " ".join(parts)        

        print(f"[*] Sending prompt to Grok: {prompt[:50]}...")

        try:
            input_box = self.wait.until(EC.presence_of_element_located(
                (By.CSS_SELECTOR, "textarea[aria-label='Ask Grok anything']")
            ))

            input_box.send_keys(prompt)
            time.sleep(1)
            input_box.send_keys(Keys.ENTER)
            
            print("[*] Prompt submitted. Waiting for generation...")

            time.sleep(5)
            if self.is_rate_limited():
                raise Exception("Rate Limit Reached")

            # Sleep until video appears
            # For now, just wait fixed time.
            # TODO We can improve this later with better detection by waiting until generating message disappears
            time.sleep(50 + random.randint(1, 5))

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
        
        self.mode = mode
        self.scenario_bot = GeminiScenarioGenerator(self.driver, self.wait)        
        
        if mode == "gemini":
            self.video_bot = GeminiVideoAutomation(self.driver, self.wait, self.long_wait)
        elif mode == "grok":
            self.video_bot = GrokAutomation(self.driver, self.wait, self.long_wait)
        else:
            raise ValueError("Only gemini and grok mode supports video generation currently.")

    def run_scenario_generation(self, prompt_path, output_folder, count):
        """Phase 1: Generate Scenarios"""
        print(f"\n=== PHASE 1: GENERATING {count} BATCHES OF SCENARIOS ===")
        
        for i in range(count):
            print(f"\n[Batch {i+1}/{count}]")
            
            # 1. Get Prompt text
            prompt_text = get_generation_prompt(prompt_path)
            if not prompt_text:
                print("[!] No prompts found. Skipping generation.")
                break

            # 2. Run Generation
            success = self.scenario_bot.generate_and_save(prompt_text, output_folder)
            
            if success:
                print(f"[*] Batch {i+1} completed successfully.")
            else:
                print(f"[!] Batch {i+1} failed.")
            
            time.sleep(3)

    def run_video_generation(self, folder_path, max_videos=999):
        """Phase 2: Generate Videos from Scenarios"""
        print(f"\n=== PHASE 2: GENERATING VIDEOS FROM {folder_path} ===")
        
        processed_count = 0
        while True: # Run until no files left or max count reached
            if processed_count >= max_videos:
                print("[*] Max video count reached.")
                break

            filepath, key, scenario = get_next_scenario(folder_path)
            
            if not scenario:
                print("[!] No more scenarios found in folder.")
                break
                
            print(f"\n--- Processing Video Scenaro: {key} ---")
            print(f"[*] Source File: {os.path.basename(filepath)}")
            
            self.video_bot.focus_tab()
            time.sleep(1)

            try:
                self.video_bot.run_generation(scenario)
                remove_scenario_from_file(filepath, key)
                processed_count += 1
            except Exception as e:
                print(f"[!] Video generation failed: {e}")
                if "Rate Limit" in str(e):
                    break
                continue
            
            time.sleep(3)

# ==========================================
#             MAIN ENTRY
# ==========================================

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Automate Scenario & Video generation.")
    
    parser.add_argument("--mode", type=str, default="gemini", choices=["gemini", "grok"])
    parser.add_argument("--count", type=int, default=1, help="Number of scenario batches to generate.")
    parser.add_argument("--concept", type=str, default="cute_baby", choices=["baby_with_animal","obese_human","cute_baby","fruit_cutting", "animal_mukbang", "animal_chef", "tiny_worker_building_food"], required=True, help="Video generation concept (e.g., cute_baby).")    

    args = parser.parse_args()

    default_path = "/Users/vhehf/Desktop/Personal materials/StartUp/YoutubeShortsGeneration/youtube-short-generation"
    scenario_generation_prompt_path = os.path.join(default_path, "prompts", args.concept, "video_scenario_generation", f"{args.concept}_scenario_generation_prompt_{args.mode}.txt")
    automation_folder = os.path.join(default_path, "automation", "video_scenarios", args.mode, args.concept)

    # Validate folders
    if not os.path.exists(scenario_generation_prompt_path):
        print(f"[!] Prompt folder '{scenario_generation_prompt_path}' does not exist.")
        exit(1)
    if not os.path.exists(automation_folder):
        print(f"[!] Automation folder '{automation_folder}' does not exist.")
        exit(1)

    controller = AutomationController(mode=args.mode)

    # Step 1: Generate Scenarios
    controller.run_scenario_generation(
        prompt_path=scenario_generation_prompt_path,
        output_folder=automation_folder,
        count=args.count
    )

    # Step 2: Generate Videos
    # We pass a large number for video count to ensure we process all generated scenarios
    controller.run_video_generation(
        folder_path=automation_folder,
        max_videos=args.count * 5
    )
