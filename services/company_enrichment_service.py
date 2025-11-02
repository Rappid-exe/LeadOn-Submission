"""
Company Enrichment Service
Uses AI to enrich company data with personalized insights and value propositions
"""

import anthropic
from loguru import logger
from typing import Dict, List, Optional
import json
from datetime import datetime


class CompanyEnrichmentService:
    """Service for enriching company data with AI-powered insights"""
    
    def __init__(self, anthropic_api_key: str):
        self.client = anthropic.Anthropic(api_key=anthropic_api_key)
    
    def enrich_company(self, company_data: Dict, our_profile: Dict) -> Dict:
        """
        Enrich a single company with AI-generated insights
        
        Args:
            company_data: Dict with company info (name, website, industry, description, etc.)
            our_profile: Dict with our company profile
            
        Returns:
            Dict with enrichment data (industry_analysis, pain_points, value_proposition, etc.)
        """
        try:
            logger.info(f"🔍 Enriching company: {company_data.get('name')}")
            
            prompt = f"""You are a B2B sales intelligence AI. Analyze this target company and create a personalized outreach strategy.

OUR COMPANY PROFILE:
Company: {our_profile.get('company_name')}
What We Do: {our_profile.get('description')}
Products/Services: {json.dumps(our_profile.get('products_services', []))}
Target Customers: {our_profile.get('target_customers')}
Value Propositions: {json.dumps(our_profile.get('value_propositions', []))}
Differentiators: {our_profile.get('differentiators')}
Use Cases: {json.dumps(our_profile.get('use_cases', []))}

TARGET COMPANY:
Name: {company_data.get('name')}
Website: {company_data.get('website', 'N/A')}
Industry: {company_data.get('industry', 'N/A')}
Description: {company_data.get('description', 'N/A')}
Employee Count: {company_data.get('employee_count', 'N/A')}
Location: {company_data.get('location', 'N/A')}

Please provide a comprehensive enrichment analysis in JSON format:
{{
    "industry_analysis": "2-3 sentences analyzing their industry position, challenges, and opportunities",
    "pain_points": [
        "Specific pain point 1 they likely face",
        "Specific pain point 2 they likely face",
        "Specific pain point 3 they likely face"
    ],
    "value_proposition": "A personalized 2-3 sentence value proposition explaining how OUR product/service solves THEIR specific problems. Be specific and compelling.",
    "enrichment_notes": "Additional insights about why they're a good fit, potential objections, and recommended approach",
    "outreach_angle": "The best angle to use when reaching out (e.g., 'cost savings', 'efficiency', 'growth', 'compliance')",
    "talking_points": [
        "Specific talking point 1 for sales conversation",
        "Specific talking point 2 for sales conversation",
        "Specific talking point 3 for sales conversation"
    ]
}}

Focus on:
1. Their specific industry challenges
2. How our solution addresses their pain points
3. Concrete benefits they would get
4. Why now is a good time to reach out

Return ONLY valid JSON, no additional text."""

            message = self.client.messages.create(
                model="claude-3-haiku-20240307",
                max_tokens=1500,
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
            
            enrichment_data = json.loads(response_text)
            
            logger.info(f"✅ Enriched company: {company_data.get('name')}")
            return enrichment_data
            
        except Exception as e:
            logger.error(f"Error enriching company {company_data.get('name')}: {e}")
            return {}
    
    def enrich_and_save(self, session, company_id: int, our_profile: Dict) -> bool:
        """
        Enrich a company and save to database
        
        Args:
            session: Database session
            company_id: ID of company to enrich
            our_profile: Our company profile
            
        Returns:
            bool: Success status
        """
        try:
            from database.models import Company
            
            # Get company from database
            company = session.query(Company).filter(Company.id == company_id).first()
            
            if not company:
                logger.error(f"Company {company_id} not found")
                return False
            
            # Prepare company data
            company_data = {
                'name': company.name,
                'website': company.website,
                'industry': company.industry,
                'description': company.description,
                'employee_count': company.employee_count,
                'location': company.location
            }
            
            # Enrich with AI
            enrichment = self.enrich_company(company_data, our_profile)
            
            if not enrichment:
                return False
            
            # Save enrichment to database
            company.industry_analysis = enrichment.get('industry_analysis')
            company.pain_points = json.dumps(enrichment.get('pain_points', []))
            company.value_proposition = enrichment.get('value_proposition')
            company.enrichment_notes = enrichment.get('enrichment_notes')
            company.last_enriched_at = datetime.utcnow()
            
            # Also save additional fields if they exist
            if 'outreach_angle' in enrichment:
                notes = company.enrichment_notes or ""
                notes += f"\n\nOutreach Angle: {enrichment['outreach_angle']}"
                if 'talking_points' in enrichment:
                    notes += f"\n\nTalking Points:\n" + "\n".join(f"- {tp}" for tp in enrichment['talking_points'])
                company.enrichment_notes = notes
            
            session.commit()
            
            logger.info(f"✅ Saved enrichment for {company.name}")
            return True
            
        except Exception as e:
            logger.error(f"Error enriching and saving company: {e}")
            session.rollback()
            return False
    
    def enrich_multiple_companies(self, session, company_ids: List[int], our_profile: Dict) -> Dict:
        """
        Enrich multiple companies
        
        Args:
            session: Database session
            company_ids: List of company IDs to enrich
            our_profile: Our company profile
            
        Returns:
            Dict with success/failure counts
        """
        success_count = 0
        failure_count = 0
        
        for company_id in company_ids:
            try:
                if self.enrich_and_save(session, company_id, our_profile):
                    success_count += 1
                else:
                    failure_count += 1
            except Exception as e:
                logger.error(f"Error enriching company {company_id}: {e}")
                failure_count += 1
        
        return {
            'total': len(company_ids),
            'success': success_count,
            'failure': failure_count
        }
    
    def enrich_all_companies(self, session, our_profile: Dict, limit: Optional[int] = None) -> Dict:
        """
        Enrich all companies in the database
        
        Args:
            session: Database session
            our_profile: Our company profile
            limit: Optional limit on number of companies to enrich
            
        Returns:
            Dict with success/failure counts
        """
        try:
            from database.models import Company
            
            # Get all companies (or unenriched companies)
            query = session.query(Company)
            
            # Optionally filter to only unenriched companies
            # query = query.filter(Company.last_enriched_at == None)
            
            if limit:
                query = query.limit(limit)
            
            companies = query.all()
            company_ids = [c.id for c in companies]
            
            logger.info(f"🔄 Enriching {len(company_ids)} companies...")
            
            return self.enrich_multiple_companies(session, company_ids, our_profile)
            
        except Exception as e:
            logger.error(f"Error enriching all companies: {e}")
            return {'total': 0, 'success': 0, 'failure': 0}

