"""
Company Profile Service
Analyzes user's website to create a company profile for AI-powered enrichment
"""

import anthropic
import requests
from bs4 import BeautifulSoup
from loguru import logger
from typing import Dict, List, Optional
import json
import os


class CompanyProfileService:
    """Service for creating and managing company profiles"""
    
    def __init__(self, anthropic_api_key: str):
        self.client = anthropic.Anthropic(api_key=anthropic_api_key)
        
    def scrape_website(self, url: str) -> str:
        """Scrape content from a website"""
        try:
            logger.info(f"🌐 Scraping website: {url}")
            
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
            }
            
            response = requests.get(url, headers=headers, timeout=10)
            response.raise_for_status()
            
            soup = BeautifulSoup(response.content, 'html.parser')
            
            # Remove script and style elements
            for script in soup(["script", "style", "nav", "footer"]):
                script.decompose()
            
            # Get text content
            text = soup.get_text()
            
            # Clean up whitespace
            lines = (line.strip() for line in text.splitlines())
            chunks = (phrase.strip() for line in lines for phrase in line.split("  "))
            text = ' '.join(chunk for chunk in chunks if chunk)
            
            # Limit to first 10000 characters to avoid token limits
            text = text[:10000]
            
            logger.info(f"✅ Scraped {len(text)} characters from {url}")
            return text
            
        except Exception as e:
            logger.error(f"Error scraping website {url}: {e}")
            return ""
    
    def analyze_website_with_ai(self, website_content: str, url: str) -> Dict:
        """Use Claude to analyze website and extract company profile"""
        try:
            logger.info("🤖 Analyzing website with Claude AI...")
            
            prompt = f"""Analyze this website content and extract a comprehensive company profile.

Website URL: {url}

Website Content:
{website_content}

Please provide a detailed analysis in JSON format with the following structure:
{{
    "company_name": "The company name",
    "tagline": "Company tagline or slogan",
    "description": "What the company does (2-3 sentences)",
    "products_services": ["Product 1", "Product 2", "Service 1"],
    "target_customers": "Who they serve (industries, company sizes, roles)",
    "value_propositions": ["Value prop 1", "Value prop 2", "Value prop 3"],
    "differentiators": "What makes them unique",
    "use_cases": ["Use case 1", "Use case 2", "Use case 3"],
    "ai_summary": "A comprehensive 2-paragraph summary of the company"
}}

Focus on:
1. What problems they solve
2. Who their ideal customers are
3. Key benefits and value propositions
4. Unique selling points
5. Common use cases

Return ONLY valid JSON, no additional text."""

            message = self.client.messages.create(
                model="claude-3-haiku-20240307",
                max_tokens=2000,
                messages=[{
                    "role": "user",
                    "content": prompt
                }]
            )
            
            response_text = message.content[0].text.strip()
            
            # Try to extract JSON if wrapped in markdown
            if "```json" in response_text:
                response_text = response_text.split("```json")[1].split("```")[0].strip()
            elif "```" in response_text:
                response_text = response_text.split("```")[1].split("```")[0].strip()
            
            profile_data = json.loads(response_text)
            
            logger.info(f"✅ AI analysis complete for {profile_data.get('company_name', 'Unknown')}")
            return profile_data
            
        except Exception as e:
            logger.error(f"Error analyzing website with AI: {e}")
            return {}
    
    def create_profile_from_website(self, url: str) -> Dict:
        """
        Create a complete company profile from a website URL
        
        Returns:
            Dict with profile data
        """
        try:
            # Scrape website
            content = self.scrape_website(url)
            
            if not content:
                return {"error": "Failed to scrape website"}
            
            # Analyze with AI
            profile_data = self.analyze_website_with_ai(content, url)
            
            if not profile_data:
                return {"error": "Failed to analyze website"}
            
            # Add website URL
            profile_data['website_url'] = url
            
            return profile_data
            
        except Exception as e:
            logger.error(f"Error creating profile from website: {e}")
            return {"error": str(e)}
    
    def save_profile_to_db(self, session, profile_data: Dict) -> bool:
        """Save company profile to database"""
        try:
            from database.models import CompanyProfile
            
            # Check if profile already exists
            existing = session.query(CompanyProfile).first()
            
            if existing:
                # Update existing profile
                existing.website_url = profile_data.get('website_url')
                existing.company_name = profile_data.get('company_name')
                existing.tagline = profile_data.get('tagline')
                existing.description = profile_data.get('description')
                existing.products_services = json.dumps(profile_data.get('products_services', []))
                existing.target_customers = profile_data.get('target_customers')
                existing.value_propositions = json.dumps(profile_data.get('value_propositions', []))
                existing.differentiators = profile_data.get('differentiators')
                existing.use_cases = json.dumps(profile_data.get('use_cases', []))
                existing.ai_summary = profile_data.get('ai_summary')
                
                logger.info("✅ Updated existing company profile")
            else:
                # Create new profile
                profile = CompanyProfile(
                    website_url=profile_data.get('website_url'),
                    company_name=profile_data.get('company_name'),
                    tagline=profile_data.get('tagline'),
                    description=profile_data.get('description'),
                    products_services=json.dumps(profile_data.get('products_services', [])),
                    target_customers=profile_data.get('target_customers'),
                    value_propositions=json.dumps(profile_data.get('value_propositions', [])),
                    differentiators=profile_data.get('differentiators'),
                    use_cases=json.dumps(profile_data.get('use_cases', [])),
                    ai_summary=profile_data.get('ai_summary')
                )
                session.add(profile)
                logger.info("✅ Created new company profile")
            
            session.commit()
            return True
            
        except Exception as e:
            logger.error(f"Error saving profile to database: {e}")
            session.rollback()
            return False
    
    def get_profile_from_db(self, session) -> Optional[Dict]:
        """Get company profile from database"""
        try:
            from database.models import CompanyProfile
            
            profile = session.query(CompanyProfile).first()
            
            if not profile:
                return None
            
            return {
                'id': profile.id,
                'website_url': profile.website_url,
                'company_name': profile.company_name,
                'tagline': profile.tagline,
                'description': profile.description,
                'products_services': json.loads(profile.products_services) if profile.products_services else [],
                'target_customers': profile.target_customers,
                'value_propositions': json.loads(profile.value_propositions) if profile.value_propositions else [],
                'differentiators': profile.differentiators,
                'use_cases': json.loads(profile.use_cases) if profile.use_cases else [],
                'ai_summary': profile.ai_summary,
                'created_at': profile.created_at.isoformat() if profile.created_at else None,
                'updated_at': profile.updated_at.isoformat() if profile.updated_at else None
            }
            
        except Exception as e:
            logger.error(f"Error getting profile from database: {e}")
            return None

