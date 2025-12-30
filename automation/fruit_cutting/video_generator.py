import json
import time
import os
import glob
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.common.action_chains import ActionChains
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.chrome.service import Service
import sys
import subprocess

def launch_chrome_debugger():
    """
    Launches Chrome in remote debugging mode if it's not already running.
    """
    chrome_path = "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome"
    user_data_dir = os.path.expanduser("~/gemini-bot") # Expands $HOME safely
    port = "9222"

    # 1. Check if port 9222 is already in use (Chrome already open?)
    # Simple check using os.system (returns 0 if successful/found)
    is_running = os.system(f"lsof -i :{port} > /dev/null 2>&1")
    
    if is_running == 0:
        print(f"[*] Chrome is already running on port {port}. Connecting...")
        return

    print(f"[*] Launching Chrome on port {port}...")
    
    # 2. Launch Chrome as a subprocess
    # We use Popen so it runs in the background and doesn't block this script
    cmd = [
        chrome_path,
        f"--remote-debugging-port={port}",
        f"--user-data-dir={user_data_dir}"
    ]
    
    try:
        subprocess.Popen(cmd)
        time.sleep(4) # Give Chrome time to open
    except FileNotFoundError:
        print(f"[!] Could not find Chrome at: {chrome_path}")
        sys.exit(1)

class GeminiAutomation:
    def __init__(self):
        launch_chrome_debugger()        
        print("[*] Connecting to existing Chrome on port 9222...")
        
        self.options = Options()
        # This tells Selenium: "Don't launch Chrome. Just talk to this address."
        self.options.add_experimental_option("debuggerAddress", "127.0.0.1:9222")
        
        # We assume ChromeDriver is in your PATH or installed via webdriver-manager
        # If you have webdriver_manager:
        from webdriver_manager.chrome import ChromeDriverManager
        from selenium.webdriver.chrome.service import Service
        
        self.driver = webdriver.Chrome(
            service=Service(ChromeDriverManager().install()),
            options=self.options
        )
        self.wait = WebDriverWait(self.driver, 20)

    def focus_gemini_tab(self):
        """
        Finds an existing Gemini tab or opens a new one.
        """
        # Check current tabs
        for handle in self.driver.window_handles:
            self.driver.switch_to.window(handle)
            if "gemini.google.com" in self.driver.current_url:
                print("Found existing Gemini tab.")
                return

        # If not found, open a new tab
        print("Opening new Gemini tab...")
        self.driver.execute_script("window.open('https://gemini.google.com', '_blank');")
        self.driver.switch_to.window(self.driver.window_handles[-1])

    def start_new_chat(self):
        print("[*] Clicking 'New chat'...")
        try:
            new_chat_btn = self.wait.until(EC.element_to_be_clickable(
                (By.XPATH, "//*[contains(text(), 'New chat')]")
            ))
            new_chat_btn.click()
            time.sleep(2) 
        except Exception as e:
            print(f"[!] Could not find 'New chat' button: {e}")

    def download_generated_video(self):
        print("[*] Waiting for video generation to complete...")
        try:
            # 1. Wait for the video tag to appear (confirmation that generation finished)
            video_element = self.long_wait.until(EC.presence_of_element_located(
                (By.TAG_NAME, "video")
            ))
            print("[*] Video generated! Finding download button...")
            time.sleep(2) # Brief pause to let UI settle

            # 2. Hover over the video player area to ensure buttons appear
            # (Sometimes buttons are hidden until mouseover)
            actions = ActionChains(self.driver)
            actions.move_to_element(video_element).perform()
            time.sleep(1)

            # 3. Click the specific button from your HTML
            download_btn = self.wait.until(EC.element_to_be_clickable(
                (By.XPATH, "//button[@aria-label='Download video']") # Download video
            ))
            
            # Click it
            download_btn.click()
            print("[*] Download started successfully!")
            
            # Wait a few seconds to ensure the download request is sent
            time.sleep(5)

        except Exception as e:
            print(f"[!] Auto-download failed: {e}")

    def generate_video(self, scenario):
        prompt = (
            f"Subject: {scenario['Subject']} "
            f"Action: {scenario['Action']} "
            f"Scene: {scenario['Scene']} "
            f"Style: {scenario['Style']} "
            f"Sounds: {scenario['Sounds']} "
            f"Technical(Negative Prompt): {scenario['Technical(Negative Prompt)']}"
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
                (By.XPATH, "//div[contains(text(), 'Create images')]")
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
            time.sleep(200)
            
            # 5. Wait for Result & Download
            self.download_generated_video()
            time.sleep(10)

        except Exception as e:
            print(f"[!] Error during automation: {e}")

    def get_next_scenario(self, folder_path):
        # Sort files numerically/alphabetically
        files = sorted(glob.glob(os.path.join(folder_path, "*.json")))
        
        for filepath in files:
            try:
                with open(filepath, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                
                # Check empty file
                if not data:
                    print(f"[*] File {os.path.basename(filepath)} is empty. Deleting...")
                    os.remove(filepath)
                    continue
                
                # Return first item
                first_key = next(iter(data))
                return filepath, first_key, data[first_key]
                
            except json.JSONDecodeError:
                print(f"[!] Error reading {filepath}. Skipping.")
                continue
                
        return None, None, None

    def remove_scenario_from_file(self, filepath, key):
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

    def run(self, folder_path, count=3):
        for i in range(count):
            # 1. Get Scenario
            filepath, key, scenario = self.get_next_scenario(folder_path)
            
            if not scenario:
                print("[!] No more scenarios found!")
                break
                
            print(f"\n--- Processing Video {i+1}/{count} ---")
            print(f"[*] File: {os.path.basename(filepath)} | Scenario: {key}")
            self.focus_gemini_tab()


            # 2. Reset Chat & Generate
            self.start_new_chat()
            self.generate_video(scenario)
            
            # 3. Clean up JSON
            self.remove_scenario_from_file(filepath, key)
            
            # 4. Wait (Bot Pause)
            time.sleep(10)

if __name__ == "__main__":
    SCENARIO_FOLDER = "scenarios"
    
    if not os.path.exists(SCENARIO_FOLDER):
        print(f"Folder '{SCENARIO_FOLDER}' not found!")
        exit()

    bot = GeminiAutomation()
    bot.run(SCENARIO_FOLDER, count=3)
