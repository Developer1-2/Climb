"""
Browser Automation Script for Betpawa Platform

This script builds a browser automated system using Selenium WebDriver in Python.
The automation:
- Opens a browser
- Navigates to the Betpawa platform
- Logs in to the account
- Extracts the current balance
- Displays it in the console

Dependencies: selenium, python-dotenv (for credentials)
"""

from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.service import Service
import time
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()


class BetpawaBrowser:
    """Handles browser automation for Betpawa platform"""
    
    def __init__(self, username=None, password=None, headless=False):
        """
        Initialize the Betpawa browser automation.
        
        Args:
            username (str): Betpawa account username
            password (str): Betpawa account password
            headless (bool): Run browser in headless mode
        """
        self.username = username or os.getenv('BETPAWA_USERNAME')
        self.password = password or os.getenv('BETPAWA_PASSWORD')
        self.headless = headless
        self.driver = None
        self.url = "https://www.betpawa.et"  # Betpawa platform URL
        
    def initialize_driver(self):
        """Initialize and configure the Chrome WebDriver"""
        options = webdriver.ChromeOptions()
        
        if self.headless:
            options.add_argument('--headless')
        
        options.add_argument('--no-sandbox')
        options.add_argument('--disable-dev-shm-usage')
        options.add_argument('--disable-blink-features=AutomationControlled')
        options.add_experimental_option("excludeSwitches", ["enable-automation"])
        options.add_experimental_option('useAutomationExtension', False)
        
        self.driver = webdriver.Chrome(options=options)
        print("✓ Chrome WebDriver initialized successfully")
        
    def navigate_to_platform(self):
        """Navigate to Betpawa platform"""
        try:
            print(f"Navigating to {self.url}...")
            self.driver.get(self.url)
            time.sleep(3)
            print("✓ Navigated to Betpawa platform")
        except Exception as e:
            print(f"✗ Error navigating to platform: {e}")
            raise
    
    def login(self):
        """Login to Betpawa account"""
        try:
            print("Attempting to login...")
            
            # Wait for and fill username field
            username_field = WebDriverWait(self.driver, 10).until(
                EC.presence_of_element_located((By.ID, "username"))
            )
            username_field.clear()
            username_field.send_keys(self.username)
            print("✓ Username entered")
            
            # Fill password field
            password_field = self.driver.find_element(By.ID, "password")
            password_field.clear()
            password_field.send_keys(self.password)
            print("✓ Password entered")
            
            # Click login button
            login_button = self.driver.find_element(By.CSS_SELECTOR, "button[type='submit']")
            login_button.click()
            
            # Wait for login to complete
            WebDriverWait(self.driver, 15).until(
                EC.presence_of_element_located((By.CLASS_NAME, "dashboard"))
            )
            print("✓ Login successful")
            time.sleep(2)
            
        except Exception as e:
            print(f"✗ Login failed: {e}")
            raise
    
    def extract_balance(self):
        """Extract current account balance"""
        try:
            print("Extracting account balance...")
            
            # Wait for balance element to load
            balance_element = WebDriverWait(self.driver, 10).until(
                EC.presence_of_element_located((By.CLASS_NAME, "balance"))
            )
            
            balance = balance_element.text
            print(f"✓ Balance extracted: {balance}")
            return balance
            
        except Exception as e:
            print(f"✗ Error extracting balance: {e}")
            return None
    
    def run(self):
        """Execute the complete automation workflow"""
        try:
            self.initialize_driver()
            self.navigate_to_platform()
            self.login()
            balance = self.extract_balance()
            
            print("\n" + "="*50)
            print("AUTOMATION COMPLETE")
            print("="*50)
            print(f"Current Balance: {balance}")
            print("="*50 + "\n")
            
            return balance
            
        except Exception as e:
            print(f"\n✗ Automation failed: {e}")
            return None
        finally:
            self.cleanup()
    
    def cleanup(self):
        """Close the browser and cleanup resources"""
        if self.driver:
            self.driver.quit()
            print("✓ Browser closed and resources cleaned up")


def main():
    """Main execution function"""
    # Initialize browser automation
    betpawa = BetpawaBrowser()
    
    # Run the automation
    balance = betpawa.run()
    
    return balance


if __name__ == "__main__":
    main()
