import os
import json
import time
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, NoSuchElementException


class SessionManager:
    """Manages LinkedIn authentication and session persistence"""
    
    def __init__(self, email: str, password: str, headless: bool = False):
        self.email = email
        self.password = password
        self.headless = headless
        self.driver = None
        self.cookies_file = "linkedin_cookies.json"
    
    def init_driver(self):
        """Initialize Chrome driver with options"""
        options = webdriver.ChromeOptions()
        
        if self.headless:
            options.add_argument('--headless=new')
        
        options.add_argument('--no-sandbox')
        options.add_argument('--disable-dev-shm-usage')
        options.add_argument('--disable-blink-features=AutomationControlled')
        options.add_experimental_option("excludeSwitches", ["enable-automation"])
        options.add_experimental_option('useAutomationExtension', False)
        options.add_argument('user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36')
        
        self.driver = webdriver.Chrome(options=options)
        self.driver.execute_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")
        return self.driver
    
    def save_cookies(self):
        """Save cookies to file"""
        cookies = self.driver.get_cookies()
        with open(self.cookies_file, 'w') as f:
            json.dump(cookies, f)
        print(f"✓ Cookies saved to {self.cookies_file}")
    
    def load_cookies(self):
        """Load cookies from file"""
        if not os.path.exists(self.cookies_file):
            return False
        
        try:
            with open(self.cookies_file, 'r') as f:
                cookies = json.load(f)
            
            self.driver.get("https://www.linkedin.com")
            time.sleep(2)
            
            for cookie in cookies:
                if 'sameSite' in cookie and cookie['sameSite'] not in ['Strict', 'Lax', 'None']:
                    cookie['sameSite'] = 'None'
                self.driver.add_cookie(cookie)
            
            self.driver.refresh()
            time.sleep(3)
            print("✓ Cookies loaded")
            return True
        except Exception as e:
            print(f"✗ Failed to load cookies: {e}")
            return False
    
    def login(self):
        """Login to LinkedIn"""
        print("Attempting to login to LinkedIn...")
        
        self.driver.get("https://www.linkedin.com/login")
        time.sleep(2)
        
        try:
            # Enter email
            email_field = WebDriverWait(self.driver, 10).until(
                EC.presence_of_element_located((By.ID, "username"))
            )
            email_field.send_keys(self.email)
            
            # Enter password
            password_field = self.driver.find_element(By.ID, "password")
            password_field.send_keys(self.password)
            
            # Click login button
            login_button = self.driver.find_element(By.CSS_SELECTOR, "button[type='submit']")
            login_button.click()
            
            # Wait for redirect to feed
            time.sleep(5)
            
            # Check if login was successful
            if "feed" in self.driver.current_url or "mynetwork" in self.driver.current_url:
                print("✓ Login successful!")
                self.save_cookies()
                return True
            else:
                print("✗ Login may have failed - check for 2FA or security challenge")
                return False
                
        except Exception as e:
            print(f"✗ Login failed: {e}")
            return False
    
    def start_session(self):
        """Start a LinkedIn session (try cookies first, then login)"""
        self.init_driver()
        
        # Try loading cookies first
        if self.load_cookies():
            # Verify session is still valid
            self.driver.get("https://www.linkedin.com/feed/")
            time.sleep(3)
            
            if "feed" in self.driver.current_url:
                print("✓ Session restored from cookies")
                return True
            else:
                print("Cookies expired, logging in...")
        
        # If cookies don't work, login
        return self.login()
    
    def close(self):
        """Close the browser"""
        if self.driver:
            self.driver.quit()
            print("✓ Browser closed")
