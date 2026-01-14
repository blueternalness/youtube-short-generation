import json
import time
import os
import glob
import sys
import subprocess
import argparse
import re
import requests
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
import shutil

# ==========================================
#             SHARED UTILITIES
# ==========================================

def launch_chrome_debugger():
    """Launches Chrome in remote debugging mode."""
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


def move_latest_download(download_dir, target_folder, new_filename):
    """
    Waits for a new file to appear in the download_dir and moves it to target_folder.
    """
    # Wait for the file to appear (timeout 20s)
    end_time = time.time() + 20
    while time.time() < end_time:
        # Get list of files in download dir
        files = glob.glob(os.path.join(download_dir, "*"))
        # Filter out hidden files or temporary download files (.crdownload)
        files = [f for f in files if not f.endswith('.crdownload') and not f.endswith('.tmp')]
        
        if not files:
            time.sleep(1)
            continue

        # Find the latest file
        latest_file = max(files, key=os.path.getctime)
        
        # Check if this file was created in the last 10 seconds (to ensure it's the one we just clicked)
        if time.time() - os.path.getctime(latest_file) < 10:
            target_path = os.path.join(target_folder, new_filename)
            shutil.move(latest_file, target_path)
            print(f"[*] Moved downloaded image to: {target_path}")
            return target_path
        
        time.sleep(1)
    
    return None        

def get_next_scenario(folder_path):
    files = sorted(glob.glob(os.path.join(folder_path, "*.json")))
    for filepath in files:
        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            if not data:
                os.remove(filepath)
                continue
            
            first_key = next(iter(data))
            return filepath, first_key, data[first_key]
            
        except json.JSONDecodeError:
            continue
    return None, None, None

def remove_scenario_from_file(filepath, key):
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        if key in data:
            del data[key]
        
        if not data:
            os.remove(filepath)
        else:
            with open(filepath, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=4, ensure_ascii=False)
    except Exception as e:
        print(f"[!] Error updating file: {e}")

def get_generation_prompt(prompt_path):
    try:
        with open(prompt_path, 'r', encoding='utf-8') as f:
            return f.read()
    except Exception as e:
        print(f"[!] Error reading prompt file: {e}")
        return None

def extract_json_from_text(text):
    match = re.search(r"```json\s*(\{.*?\})\s*```", text, re.DOTALL)
    if not match:
        match = re.search(r"(\{.*\})", text, re.DOTALL)
    
    if match:
        json_str = match.group(1)
        try:
            return json.loads(json_str)
        except json.JSONDecodeError:
            return None
    return None

def download_image_from_url(url, save_path):
    try:
        response = requests.get(url, stream=True)
        if response.status_code == 200:
            with open(save_path, 'wb') as f:
                for chunk in response.iter_content(1024):
                    f.write(chunk)
            return True
    except Exception as e:
        print(f"[!] Image download failed: {e}")
    return False

# ==========================================
#             PLATFORM CLASSES
# ==========================================

class GeminiScenarioGenerator:
    """Handles Phase 1: Generating JSON Scenarios."""
    def __init__(self, driver, wait):
        self.driver = driver
        self.wait = wait

    def generate_and_save(self, prompt_text, output_folder):
        print("\n--- Starting Scenario Generation ---")
        self._focus_tab()
        self._new_chat()

        print("[*] Sending scenario generation prompt...")
        self._send_message(prompt_text)

        print("[*] Waiting for Gemini response...")
        time.sleep(10)
        
        extracted_data = self._extract_json_response()
        
        if not extracted_data:
            print("[!] Failed to extract valid JSON.")
            return False

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
            pass

    def _send_message(self, text):
        try:
            input_box = self.wait.until(EC.presence_of_element_located(
                (By.CSS_SELECTOR, "div[contenteditable='true']")
            ))
            input_box.clear()
            self.driver.execute_script("arguments[0].innerText = arguments[1];", input_box, text)
            input_box.send_keys(" ")
            time.sleep(1)
            input_box.send_keys(Keys.ENTER)
        except Exception as e:
            print(f"[!] Error sending prompt: {e}")

    def _extract_json_response(self):
        for i in range(20):
            try:
                responses = self.driver.find_elements(By.CSS_SELECTOR, ".markdown")
                if responses:
                    data = extract_json_from_text(responses[-1].text)
                    if data: return data
                
                code_blocks = self.driver.find_elements(By.TAG_NAME, "code")
                if code_blocks:
                    data = extract_json_from_text(code_blocks[-1].text)
                    if data: return data
            except:
                pass
            time.sleep(2)
        return None


class GeminiImageWorkflow:
    """Handles Steps 3, 4, 5: Image Gen -> Download -> Next Step Text Gen."""
    def __init__(self, driver, wait, long_wait):
        self.driver = driver
        self.wait = wait
        self.long_wait = long_wait
        self.chrome_download_dir = os.path.expanduser("~/Downloads")

    def focus_tab(self):
        for handle in self.driver.window_handles:
            self.driver.switch_to.window(handle)
            if "gemini.google.com" in self.driver.current_url:
                return
        self.driver.execute_script("window.open('https://gemini.google.com', '_blank');")
        self.driver.switch_to.window(self.driver.window_handles[-1])

    def run_image_generation(self, scenario, images_folder, next_step_prompt_template):
        print("[*] Starting Gemini Image Workflow...")
        self.focus_tab()
        
        # 1. Start Fresh Chat for this Scenario
        try:
            new_chat_btn = self.wait.until(EC.element_to_be_clickable((By.XPATH, "//*[contains(text(), 'New chat')]")))
            new_chat_btn.click()
            time.sleep(2)

            # 1. Click Tools
            tools_btn = self.wait.until(EC.element_to_be_clickable(
                (By.XPATH, "//button[.//span[contains(text(), 'Tools')]]")
            ))
            tools_btn.click()
            time.sleep(1)

            # 2. Click Create images
            image_menu = self.wait.until(EC.element_to_be_clickable(
                (By.XPATH, "//div[contains(text(), 'Create images')]")
            ))
            image_menu.click()
            time.sleep(1)
        except Exception as e:
            print(f"[!] Error setting up image generation chat: {e}")
            raise e

        # 2. Construct Image Prompt from Scenario
        # Adjust keys based on your JSON structure
        image_prompt = (
            f"Subject: {scenario.get('Subject', '')}, "
            f"Action: {scenario.get('Action', '')}, "
            f"Scene: {scenario.get('Scene', '')}, "
            f"Style: {scenario.get('Style', '')},"
            f"Technical(Negative Prompt): {scenario.get('Technical(Negative Prompt)', '')}"
        )

        print("[*] Sending Image Generation Prompt...")
        self._send_message(image_prompt)

        # 3. Wait for Image and Download (Step 3 & 4)
        print("[*] Waiting for image generation...")
        time.sleep(10)
        
        local_image_path = self._click_download_button(images_folder)
        if not local_image_path:
            raise Exception("Failed to download image from Gemini.")
        
        # 4. Generate Next Step Description (Step 5)
        # We use the same chat session so Gemini knows the context of the image it just made.
        print("[*] Requesting Next Step Description...")
        self._send_message(next_step_prompt_template)

        local_next_step_text_path = self._get_next_step_response(images_folder)
        if not local_next_step_text_path:
            raise Exception("Failed to get next step description.")

        print(f"[*] Next Step Description: {local_next_step_text_path[:50]}...")
        return local_image_path, local_next_step_text_path

    def _send_message(self, text):
        input_box = self.wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, "div[contenteditable='true']")))
        input_box.clear()
        self.driver.execute_script("arguments[0].innerText = arguments[1];", input_box, text)
        input_box.send_keys(" ")
        time.sleep(1)
        input_box.send_keys(Keys.ENTER)

    def _click_download_button(self, save_folder):
        """
        Locates the generated image container, hovers over it, and clicks the download button.
        """
        max_retries = 30
        for _ in range(max_retries):
            try:
                # 1. Find the generated image container
                # Based on your HTML: <single-image class="generated-image large">
                images = self.driver.find_elements(By.TAG_NAME, "single-image")
                
                if not images:
                    time.sleep(2)
                    continue

                target_image = images[-1] # Get the most recent one

                # 2. Hover to reveal controls (ActionChains)
                actions = ActionChains(self.driver)
                actions.move_to_element(target_image).perform()
                time.sleep(1) 

                # 3. Find the Download Button inside this specific image container
                # Selector based on your HTML: aria-label="Download full size image"
                download_btn = target_image.find_element(By.XPATH, ".//button[@aria-label='Download full size image']")
                
                # 4. Click it
                download_btn.click()
                print("[*] Clicked Gemini download button.")
                
                # 5. Handle file move
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                filename = f"generated_{timestamp}.jpg"
                
                # Use the shared utility to find the new file in ~/Downloads and move it
                saved_path = move_latest_download(self.chrome_download_dir, save_folder, filename)
                
                if saved_path:
                    return saved_path
                
            except Exception as e:
                print(f"Debug: Retrying download click... {e}") # Uncomment for debug
                pass
            
            time.sleep(2)
            
        print("[!] Could not find or click the download button.")
        return None


    def _get_next_step_response(self, images_folder):

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
                    break
            except Exception as e:
                print(e)
            time.sleep(2)

        if not extracted_data:
            print("[!] Failed to extract valid JSON from Gemini response.")
            return False

        # 5. Save to File
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"{timestamp}.json"
        output_path = os.path.join(images_folder, filename)
        
        try:
            with open(output_path, 'w', encoding='utf-8') as f:
                json.dump(extracted_data, f, indent=4, ensure_ascii=False)
            print(f"[*] Saved new scenarios to: {output_path}")
            return output_path
        except Exception as e:
            print(f"[!] Error saving file: {e}")
            return False

class GrokImageToVideo:
    """Handles Steps 6, 7, 8: Upload Image -> Input Prompt -> Download Video."""
    def __init__(self, driver, wait, long_wait):
        self.driver = driver
        self.wait = wait
        self.long_wait = long_wait

    def focus_tab(self):
        for handle in self.driver.window_handles:
            self.driver.switch_to.window(handle)
            if "grok.com" in self.driver.current_url:
                return
        self.driver.get("https://grok.com/imagine")

    def get_next_step_description(file_path):
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
            if not data:
                raise Exception(f"[*] File {os.path.basename(file_path)} is empty. Deleting...")
            os.remove(file_path)

            return data

        except json.JSONDecodeError:
            print(f"[!] Error reading {file_path}. Skipping.")

        return None

    def generate_video(self, image_path, next_step_text_path):
        # TODO: Read prompt from next_step_text_path
        print("\n--- Starting Grok Video Generation ---")
        self.focus_tab()
        self.driver.get("https://grok.com/imagine") # Refresh to ensure clean state
        time.sleep(3)

        try:
            # 1. Upload Image (Step 6)
            print(f"[*] Uploading image: {os.path.basename(image_path)}")
            
            # Find generic file input. Grok often hides it, so we target input[type='file']
            file_input = self.wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, "input[type='file']")))
            file_input.send_keys(os.path.abspath(image_path))
            
            # Wait for upload processing (usually a preview image appears)
            time.sleep(5) 

            # 2. Enter Prompt (Step 7)
            print("[*] Entering next step prompt...")
            text_area = self.wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, "textarea, div[contenteditable='true']")))
            
            # Sometimes Grok has a specific "Edit" or "Describe" box for the image-to-video.
            # Assuming standard prompt box for now.
            text_area.click()
            next_steps = self.get_next_step_description(next_step_text_path)

            # TODO: add Middle scene prompt if video quality is bad.
            final_scene_prompt = f"{next_steps.get('FinalScene', '')} "

            text_area.send_keys(final_scene_prompt)
            time.sleep(1)
            text_area.send_keys(Keys.ENTER)

            # 3. Wait for Generation & Download (Step 8)
            print("[*] Waiting for video generation...")
            
            # Check for Rate Limit
            if self.is_rate_limited():
                raise Exception("Rate Limit Reached")

            # Wait loop for download button
            # This can take 60s+
            time.sleep(30) 
            
            download_btn = self.long_wait.until(EC.element_to_be_clickable(
                (By.XPATH, "//button[@aria-label='Download']")
            ))
            
            print("[*] Video generated. Clicking download...")
            download_btn.click()
            time.sleep(5)

            # Cleanup
            self.cleanup_post()

        except Exception as e:
            print(f"[!] Grok Error: {e}")
            if "Rate Limit" in str(e): raise e
            
    def cleanup_post(self):
        # Reuse existing cleanup logic
        try:
            more_menu = self.wait.until(EC.element_to_be_clickable(
                (By.XPATH, "//button[contains(@aria-label, 'More') or .//svg[contains(@class, 'lucide-more-horizontal')]]")
            ))
            more_menu.click()
            time.sleep(1)
            
            # Try to delete
            delete_xpath = "//div[@role='menuitem']//span[text()='Delete post']/.."
            element = self.wait.until(EC.presence_of_element_located((By.XPATH, delete_xpath)))
            self.driver.execute_script("arguments[0].click();", element)
            
            cfm_btn = self.wait.until(EC.element_to_be_clickable((By.XPATH, "//button[normalize-space()='Delete post']")))
            cfm_btn.click()
            time.sleep(2)
        except:
            pass

    def is_rate_limited(self):
        try:
            if "rate limit" in self.driver.find_element(By.TAG_NAME, "body").text.lower():
                return True
        except: pass
        return False


# ==========================================
#             CONTROLLER
# ==========================================

class AutomationController:
    def __init__(self):
        launch_chrome_debugger()        
        print("[*] Connecting to Chrome...")
        
        self.options = Options()
        self.options.add_experimental_option("debuggerAddress", "127.0.0.1:9222")
        
        self.driver = webdriver.Chrome(
            service=Service(ChromeDriverManager().install()),
            options=self.options
        )
        self.wait = WebDriverWait(self.driver, 20)
        self.long_wait = WebDriverWait(self.driver, 300)
        
        self.scenario_bot = GeminiScenarioGenerator(self.driver, self.wait)
        self.gemini_workflow = GeminiImageWorkflow(self.driver, self.wait, self.long_wait)
        self.grok_bot = GrokImageToVideo(self.driver, self.wait, self.long_wait)

    def run_scenario_generation(self, prompt_path, output_folder, count):
        """Step 1 & 2: Generate Scenarios"""
        print(f"\n=== PHASE 1: GENERATING SCENARIOS ===")
        
        prompt_text = get_generation_prompt(prompt_path)
        if not prompt_text:
            print("[!] Prompt file missing.")
            return

        for i in range(count):
            print(f"\n[Batch {i+1}/{count}]")
            if not self.scenario_bot.generate_and_save(prompt_text, output_folder):
                print("[!] Batch failed.")
            time.sleep(3)

    def run_image_to_video_loop(self, scenario_folder, images_folder, next_step_prompt_path, count):
        """Steps 3 to 9"""
        print(f"\n=== PHASE 2: IMAGE TO VIDEO LOOP ({count} iterations) ===")
        
        next_step_template = get_generation_prompt(next_step_prompt_path)
        if not next_step_template:
            print("[!] Next step prompt template missing.")
            return

        processed_count = 0
        
        while processed_count < count:
            # 1. Get a Scenario
            filepath, key, scenario = get_next_scenario(scenario_folder)
            if not scenario:
                print("[!] No more scenarios available.")
                break

            print(f"\n--- Processing Item {processed_count + 1}/{count}: {key} ---")
            
            try:
                # Steps 3, 4, 5: Gemini (Image Gen -> Download -> Text Gen)
                image_path, next_step_text_path = self.gemini_workflow.run_image_generation(
                    scenario, 
                    images_folder, 
                    next_step_template
                )

                print(f"[*] Generated Image: {image_path}")
                print(f"[*] Next Step Text: {next_step_text_path}")


                # Steps 6, 7, 8: Grok (Upload -> Video Gen -> Download)
                self.grok_bot.generate_video(image_path, next_step_text_path)
                
                # Cleanup Scenario
                remove_scenario_from_file(filepath, key)
                processed_count += 1
                
            except Exception as e:
                print(f"[!] Critical Loop Error: {e}")
                if "Rate Limit" in str(e):
                    print("[!] Rate limit hit. Stopping.")
                    break
            
            time.sleep(5)

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--count", type=int, default=1, help="Total items to process.")
    parser.add_argument("--concept", type=str, required=True, help="Concept folder name.")
    args = parser.parse_args()

    # Paths
    base_path = "/Users/vhehf/Desktop/Personal materials/StartUp/YoutubeShortsGeneration/youtube-short-generation"
    
    # Input Prompts
    scenario_prompt_path = os.path.join(base_path, "prompts", args.concept, "image_scenario_generation", f"{args.concept}_scenario_generation_prompt_grok.txt")
    next_step_prompt_path = os.path.join(base_path, "prompts", args.concept, "next_scene_description_generation", f"{args.concept}_next_scene_description_generation_prompt_grok.txt")
    
    # Automation Folders
    scenario_output_folder = os.path.join(base_path, "automation", "image_scenarios", args.concept)
    images_output_folder = os.path.join(base_path, "automation", "images")

    # Ensure directories exist
    os.makedirs(scenario_output_folder, exist_ok=True)
    os.makedirs(images_output_folder, exist_ok=True)

    controller = AutomationController()

    # Phase 1: Create Scenarios
    controller.run_scenario_generation(scenario_prompt_path, scenario_output_folder, args.count)

    # Phase 2: Process Scenarios (Image -> Video)
    controller.run_image_to_video_loop(scenario_output_folder, images_output_folder, next_step_prompt_path, args.count)
