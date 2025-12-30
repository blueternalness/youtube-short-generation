from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.keys import Keys
import time

class GeminiLiveController:
    def __init__(self):
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

    def generate_video(self, prompt):
        # 1. Ensure we are on the right tab
        self.focus_gemini_tab()
        
        # 2. Click Tools (Pill button)
        # Note: Selectors must be very robust.
        print(f"Typing prompt: {prompt}")
        
        try:
            # (Same logic as before)
            tools_btn = self.wait.until(EC.element_to_be_clickable(
                (By.XPATH, "//button[.//span[contains(text(), 'Tools')]]")
            ))
            tools_btn.click()
            time.sleep(0.5)

            # Click "Create videos"
            video_menu = self.wait.until(EC.element_to_be_clickable(
                (By.XPATH, "//div[contains(text(), 'Create videos')]")
            ))
            video_menu.click()
            time.sleep(0.5)

            # Type Prompt
            input_box = self.wait.until(EC.presence_of_element_located(
                (By.CSS_SELECTOR, "div[contenteditable='true']")
            ))
            input_box.clear()
            input_box.send_keys(prompt)
            time.sleep(0.5)
            input_box.send_keys(Keys.ENTER)
            
        except Exception as e:
            print(f"Error: {e}")

if __name__ == "__main__":
    bot = GeminiLiveController()
    bot.generate_video("A futuristic city with flying cars, 4k, cinematic lighting")