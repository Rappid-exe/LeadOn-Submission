"""Service for enriching companies using Apollo API"""
import logging
import json
from typing import Dict, List, Optional
from database.models import Company
from scrapers.apollo_scraper import ApolloClient

logger = logging.getLogger(__name__)


class ApolloCompanyEnrichment:
    """Service for enriching company data using Apollo API"""
    
    def __init__(self, apollo_client: ApolloClient):
        self.apollo = apollo_client
    
    def enrich_company(self, session, company: Company) -> bool:
        """
        Enrich a single company using Apollo API
        
        Args:
            session: Database session
            company: Company object to enrich
            
        Returns:
            bool: Success status
        """
        try:
            logger.info(f"🔍 Enriching company with Apollo: {company.name}")
            
            # Search for the company in Apollo
            result = self.apollo.search_organizations(
                query=company.name,
                per_page=1
            )
            
            if not result.organizations:
                logger.warning(f"Company not found in Apollo: {company.name}")
                return False
            
            # Get the first (best match) organization
            org = result.organizations[0]
            
            # Update company with Apollo data
            if org.apollo_id:
                company.apollo_id = org.apollo_id
            
            if org.website and not company.website:
                company.website = org.website
            
            if org.linkedin_url and not company.linkedin_url:
                company.linkedin_url = org.linkedin_url
            
            if org.industry and not company.industry:
                company.industry = org.industry
            
            if org.description and not company.description:
                company.description = org.description
            
            # Update employee count
            if org.employee_count:
                company.employee_count = self._format_employee_count(org.employee_count)
            elif org.employee_count_range:
                company.employee_count = org.employee_count_range
            
            # Update location
            if org.city or org.state or org.country:
                location_parts = []
                if org.city:
                    location_parts.append(org.city)
                if org.state:
                    location_parts.append(org.state)
                if org.country:
                    location_parts.append(org.country)
                company.location = ", ".join(location_parts)
            
            # Add Apollo-specific fields
            if org.founded_year:
                company.founded_year = org.founded_year
            
            if org.funding_stage:
                company.funding_stage = org.funding_stage
            
            if org.total_funding:
                company.total_funding = org.total_funding
            
            if org.technologies:
                company.technologies = json.dumps(org.technologies)
            
            # Generate tags based on Apollo data
            tags = self._generate_tags(org)
            if tags:
                existing_tags = json.loads(company.tags) if company.tags else []
                # Merge tags, avoiding duplicates
                all_tags = list(set(existing_tags + tags))
                company.tags = json.dumps(all_tags)
            
            # Set default relationship stage if not set
            if not company.relationship_stage:
                company.relationship_stage = "prospect"
            
            session.commit()
            
            logger.info(f"✅ Enriched company: {company.name}")
            return True
            
        except Exception as e:
            logger.error(f"Error enriching company {company.name}: {e}")
            session.rollback()
            return False
    
    def enrich_multiple_companies(self, session, companies: List[Company], limit: Optional[int] = None) -> Dict:
        """
        Enrich multiple companies
        
        Args:
            session: Database session
            companies: List of Company objects
            limit: Maximum number of companies to enrich
            
        Returns:
            Dict with success/failure counts
        """
        if limit:
            companies = companies[:limit]
        
        success_count = 0
        failure_count = 0
        
        for company in companies:
            if self.enrich_company(session, company):
                success_count += 1
            else:
                failure_count += 1
        
        return {
            'total': len(companies),
            'success': success_count,
            'failure': failure_count
        }
    
    def _format_employee_count(self, count: int) -> str:
        """
        Format employee count into a range string
        
        Args:
            count: Employee count number
            
        Returns:
            String like "11-50", "51-200", etc.
        """
        if count <= 10:
            return "1-10"
        elif count <= 50:
            return "11-50"
        elif count <= 200:
            return "51-200"
        elif count <= 500:
            return "201-500"
        elif count <= 1000:
            return "501-1000"
        elif count <= 5000:
            return "1001-5000"
        elif count <= 10000:
            return "5001-10000"
        else:
            return "10000+"
    
    def _generate_tags(self, org) -> List[str]:
        """
        Generate tags based on organization data
        
        Args:
            org: Organization object from Apollo
            
        Returns:
            List of tag strings
        """
        tags = []
        
        # Add industry tag
        if org.industry:
            tags.append(f"industry:{org.industry.lower().replace(' ', '_')}")
        
        # Add funding stage tag
        if org.funding_stage:
            tags.append(f"funding:{org.funding_stage.lower().replace(' ', '_')}")
        
        # Add size tag
        if org.employee_count:
            if org.employee_count <= 50:
                tags.append("size:small")
            elif org.employee_count <= 500:
                tags.append("size:medium")
            else:
                tags.append("size:large")
        
        # Add technology tags (limit to top 5)
        if org.technologies:
            for tech in org.technologies[:5]:
                tags.append(f"tech:{tech.lower().replace(' ', '_')}")
        
        # Add location tag
        if org.country:
            tags.append(f"location:{org.country.lower().replace(' ', '_')}")
        
        return tags

