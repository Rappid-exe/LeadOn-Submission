"""
LinkedIn Profile Scraper

Scrapes public LinkedIn profiles to extract company information.
Uses requests + BeautifulSoup for simple HTML parsing.
"""

import requests
from bs4 import BeautifulSoup
from typing import Optional, Dict
from loguru import logger
import time
import random


class LinkedInScraper:
    """
    Simple LinkedIn profile scraper for extracting company names.
    
    Note: This scrapes public profile pages without authentication.
    LinkedIn may rate-limit or block requests, so use sparingly.
    """
    
    def __init__(self):
        self.session = requests.Session()
        # Use a realistic user agent to avoid being blocked
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.5',
            'Accept-Encoding': 'gzip, deflate, br',
            'DNT': '1',
            'Connection': 'keep-alive',
            'Upgrade-Insecure-Requests': '1'
        })
        
    def extract_company_from_profile(self, linkedin_url: str) -> Optional[Dict[str, str]]:
        """
        Extract company name and title from a LinkedIn profile URL.
        
        Args:
            linkedin_url: Full LinkedIn profile URL
            
        Returns:
            Dict with 'company' and 'title' keys, or None if extraction fails
        """
        try:
            # Add random delay to avoid rate limiting
            time.sleep(random.uniform(1, 3))
            
            logger.debug(f"Scraping LinkedIn profile: {linkedin_url}")
            
            response = self.session.get(linkedin_url, timeout=10)
            
            if response.status_code != 200:
                logger.warning(f"Failed to fetch LinkedIn profile: {response.status_code}")
                return None
            
            soup = BeautifulSoup(response.text, 'html.parser')
            
            # Try to extract company name from various possible locations
            company_name = self._extract_company_name(soup)
            title = self._extract_title(soup)
            
            if company_name or title:
                logger.info(f"✅ Extracted from LinkedIn: Company={company_name}, Title={title}")
                return {
                    'company': company_name,
                    'title': title
                }
            else:
                logger.warning(f"⚠️  Could not extract company/title from LinkedIn profile")
                return None
                
        except requests.exceptions.Timeout:
            logger.error(f"Timeout while scraping LinkedIn profile: {linkedin_url}")
            return None
        except Exception as e:
            logger.error(f"Error scraping LinkedIn profile: {e}")
            return None
    
    def _extract_company_name(self, soup: BeautifulSoup) -> Optional[str]:
        """
        Extract company name from LinkedIn profile HTML.
        
        LinkedIn's HTML structure changes frequently, so we try multiple methods.
        """
        # Method 1: Look for experience section
        try:
            # Try to find the current position (usually first in experience section)
            experience_section = soup.find('section', {'id': 'experience-section'})
            if experience_section:
                company_elem = experience_section.find('p', class_='pv-entity__secondary-title')
                if company_elem:
                    company_name = company_elem.get_text(strip=True)
                    # Clean up "Company Name" or "at Company Name"
                    if company_name.startswith('at '):
                        company_name = company_name[3:]
                    return company_name
        except Exception as e:
            logger.debug(f"Method 1 failed: {e}")
        
        # Method 2: Look for meta tags (public profiles often have these)
        try:
            og_description = soup.find('meta', property='og:description')
            if og_description:
                content = og_description.get('content', '')
                # Format is usually: "Name - Title at Company | LinkedIn"
                if ' at ' in content:
                    parts = content.split(' at ')
                    if len(parts) > 1:
                        company_part = parts[1].split('|')[0].strip()
                        return company_part
        except Exception as e:
            logger.debug(f"Method 2 failed: {e}")
        
        # Method 3: Look for structured data
        try:
            # LinkedIn sometimes includes JSON-LD structured data
            json_ld = soup.find('script', type='application/ld+json')
            if json_ld:
                import json
                data = json.loads(json_ld.string)
                if isinstance(data, dict):
                    # Look for worksFor or jobTitle
                    works_for = data.get('worksFor', {})
                    if isinstance(works_for, dict):
                        company_name = works_for.get('name')
                        if company_name:
                            return company_name
        except Exception as e:
            logger.debug(f"Method 3 failed: {e}")
        
        # Method 4: Look in page title
        try:
            title_tag = soup.find('title')
            if title_tag:
                title_text = title_tag.get_text()
                # Format: "Name - Title - Company | LinkedIn"
                if ' - ' in title_text:
                    parts = title_text.split(' - ')
                    if len(parts) >= 3:
                        company_part = parts[2].split('|')[0].strip()
                        return company_part
        except Exception as e:
            logger.debug(f"Method 4 failed: {e}")
        
        return None
    
    def _extract_title(self, soup: BeautifulSoup) -> Optional[str]:
        """
        Extract job title from LinkedIn profile HTML.
        """
        # Method 1: Look for headline
        try:
            headline = soup.find('h2', class_='mt1 t-18 t-black t-normal break-words')
            if headline:
                return headline.get_text(strip=True)
        except Exception as e:
            logger.debug(f"Title method 1 failed: {e}")
        
        # Method 2: Look in meta tags
        try:
            og_description = soup.find('meta', property='og:description')
            if og_description:
                content = og_description.get('content', '')
                # Format: "Name - Title at Company | LinkedIn"
                if ' - ' in content and ' at ' in content:
                    title_part = content.split(' - ')[1].split(' at ')[0].strip()
                    return title_part
        except Exception as e:
            logger.debug(f"Title method 2 failed: {e}")
        
        # Method 3: Look in page title
        try:
            title_tag = soup.find('title')
            if title_tag:
                title_text = title_tag.get_text()
                # Format: "Name - Title - Company | LinkedIn"
                if ' - ' in title_text:
                    parts = title_text.split(' - ')
                    if len(parts) >= 2:
                        return parts[1].strip()
        except Exception as e:
            logger.debug(f"Title method 3 failed: {e}")
        
        return None
    
    def enrich_contacts_with_linkedin(self, contacts: list) -> list:
        """
        Enrich a list of contacts with company names from LinkedIn.
        
        Args:
            contacts: List of contact dicts with 'linkedin_url' field
            
        Returns:
            List of enriched contacts
        """
        enriched = []
        
        for contact in contacts:
            linkedin_url = contact.get('linkedin_url')
            
            # Skip if no LinkedIn URL or already has company
            if not linkedin_url or contact.get('company'):
                enriched.append(contact)
                continue
            
            # Try to extract company from LinkedIn
            linkedin_data = self.extract_company_from_profile(linkedin_url)
            
            if linkedin_data:
                # Update contact with LinkedIn data
                if linkedin_data.get('company'):
                    contact['company'] = linkedin_data['company']
                if linkedin_data.get('title') and not contact.get('title'):
                    contact['title'] = linkedin_data['title']
            
            enriched.append(contact)
            
            # Rate limiting: don't scrape too fast
            time.sleep(random.uniform(2, 4))
        
        return enriched


# Singleton instance
_linkedin_scraper = None

def get_linkedin_scraper() -> LinkedInScraper:
    """Get or create LinkedIn scraper singleton"""
    global _linkedin_scraper
    if _linkedin_scraper is None:
        _linkedin_scraper = LinkedInScraper()
    return _linkedin_scraper

