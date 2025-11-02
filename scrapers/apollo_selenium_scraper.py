"""
Apollo.io Selenium scraper for free plan users.
Uses browser automation to scrape contact data when API is not available.
"""

import time
import os
from typing import Optional, List, Dict, Any
from datetime import datetime

from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.options import Options
from selenium.common.exceptions import TimeoutException, NoSuchElementException
from loguru import logger
from dotenv import load_dotenv

from .base_scraper import BaseScraper
from .schemas import Contact, SearchResult

load_dotenv()


class ApolloSeleniumScraper(BaseScraper):
    """
    Selenium-based scraper for Apollo.io when API is not available (free plan).
    """
    
    BASE_URL = "https://app.apollo.io"
    
    def __init__(
        self,
        email: Optional[str] = None,
        password: Optional[str] = None,
        headless: bool = False
    ):
        """
        Initialize Selenium scraper.
        
        Args:
            email: Apollo.io login email
            password: Apollo.io login password
            headless: Run browser in headless mode
        """
        super().__init__()
        
        self.email = email or os.getenv("APOLLO_EMAIL")
        self.password = password or os.getenv("APOLLO_PASSWORD")
        
        if not self.email or not self.password:
            raise ValueError(
                "Apollo.io credentials required. Set APOLLO_EMAIL and APOLLO_PASSWORD "
                "environment variables or pass email/password parameters."
            )
        
        # Setup Chrome options
        chrome_options = Options()
        if headless:
            chrome_options.add_argument("--headless=new")
        chrome_options.add_argument("--no-sandbox")
        chrome_options.add_argument("--disable-dev-shm-usage")
        chrome_options.add_argument("--disable-blink-features=AutomationControlled")
        chrome_options.add_experimental_option("excludeSwitches", ["enable-automation"])
        chrome_options.add_experimental_option("useAutomationExtension", False)
        
        # Initialize driver
        self.driver = webdriver.Chrome(options=chrome_options)
        self.wait = WebDriverWait(self.driver, 10)
        
        logger.info("Selenium scraper initialized")
        
        # Login
        self._login()
    
    def _login(self):
        """Login to Apollo.io."""
        logger.info("Logging in to Apollo.io...")
        
        try:
            self.driver.get(f"{self.BASE_URL}/sign-in")
            time.sleep(2)
            
            # Enter email
            email_input = self.wait.until(
                EC.presence_of_element_located((By.NAME, "email"))
            )
            email_input.send_keys(self.email)
            
            # Enter password
            password_input = self.driver.find_element(By.NAME, "password")
            password_input.send_keys(self.password)
            
            # Click login button
            login_button = self.driver.find_element(By.CSS_SELECTOR, "button[type='submit']")
            login_button.click()
            
            # Wait for redirect to dashboard
            time.sleep(5)
            
            if "sign-in" not in self.driver.current_url:
                logger.info("Successfully logged in to Apollo.io")
            else:
                raise Exception("Login failed - still on sign-in page")
                
        except Exception as e:
            logger.error(f"Login failed: {e}")
            raise
    
    def search(self, query: str, **kwargs) -> Dict[str, Any]:
        """
        Search for people on Apollo.io.
        
        Args:
            query: Search query
            **kwargs: Additional parameters (titles, locations, etc.)
            
        Returns:
            Search results as dict
        """
        result = self.search_people(query=query, **kwargs)
        return result.model_dump()
    
    def search_people(
        self,
        query: Optional[str] = None,
        titles: Optional[List[str]] = None,
        locations: Optional[List[str]] = None,
        limit: int = 25
    ) -> SearchResult:
        """
        Search for people using Selenium.
        
        Args:
            query: General search query
            titles: Job titles to filter
            locations: Locations to filter
            limit: Maximum number of results
            
        Returns:
            SearchResult with contacts
        """
        logger.info(f"Searching people with query: {query}")
        
        try:
            # Navigate to people search
            self.driver.get(f"{self.BASE_URL}/#/people")
            time.sleep(3)
            
            # TODO: Implement search filters
            # This is a placeholder - actual implementation would:
            # 1. Enter search query in search box
            # 2. Apply filters (titles, locations)
            # 3. Scrape results from the page
            # 4. Parse contact data
            
            contacts = []
            
            # For now, return empty result with message
            logger.warning(
                "Selenium scraping requires manual implementation of page selectors. "
                "This is a placeholder. Consider upgrading to a paid Apollo.io plan for API access."
            )
            
            return SearchResult(
                contacts=contacts,
                total_results=0,
                page=1,
                per_page=limit,
                query=query
            )
            
        except Exception as e:
            self._handle_error(e, "search_people")
            return SearchResult(contacts=[], total_results=0, page=1, per_page=limit)
    
    def close(self):
        """Close browser and cleanup."""
        if hasattr(self, 'driver'):
            self.driver.quit()
        super().close()
        logger.info("Selenium scraper closed")
    
    def __del__(self):
        """Cleanup on deletion."""
        self.close()

