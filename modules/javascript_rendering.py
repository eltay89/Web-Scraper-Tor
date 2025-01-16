from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from bs4 import BeautifulSoup
import time

class JavaScriptRenderer:
    def __init__(self, settings):
        self.settings = settings
        self.driver = None
        self.init_driver()
        
    def init_driver(self):
        """Initialize the web driver"""
        options = webdriver.ChromeOptions()
        options.add_argument('--headless')
        options.add_argument('--disable-gpu')
        options.add_argument('--no-sandbox')
        options.add_argument('--disable-dev-shm-usage')
        
        if self.settings.get('proxy'):
            options.add_argument(f'--proxy-server={self.settings["proxy"]}')
            
        self.driver = webdriver.Chrome(
            service=Service(self.settings.get('chrome_driver_path')),
            options=options
        )
        
    def render_page(self, url):
        """Render a page with JavaScript"""
        try:
            self.driver.get(url)
            # Wait for page to load completely
            WebDriverWait(self.driver, self.settings.get('timeout', 10)).until(
                EC.presence_of_element_located((By.TAG_NAME, "body"))
            )
            # Additional wait for dynamic content
            time.sleep(self.settings.get('render_wait', 2))
            
            # Get the page source after rendering
            page_source = self.driver.page_source
            return BeautifulSoup(page_source, 'html.parser')
            
        except Exception as e:
            raise Exception(f"JavaScript rendering failed: {str(e)}")
            
    def close(self):
        """Close the web driver"""
        if self.driver:
            self.driver.quit()