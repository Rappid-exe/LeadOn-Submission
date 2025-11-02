"""
Apollo.io API scraper for contact and company data.
Implements the Apollo.io REST API for searching and enriching contacts.
"""

import os
import requests
from typing import Optional, List, Dict, Any
from datetime import datetime
from time import time, sleep

from dotenv import load_dotenv
from loguru import logger

from .base_scraper import BaseScraper
from .schemas import (
    Contact,
    Organization,
    SearchResult,
    ApolloPersonSearchRequest,
    ApolloOrganizationSearchRequest,
    ApolloEnrichmentRequest
)

# Load environment variables
load_dotenv()


class ApolloClient(BaseScraper):
    """
    Apollo.io API client for searching and enriching contact data.
    """
    
    BASE_URL = "https://api.apollo.io/api/v1"
    
    def __init__(
        self,
        api_key: Optional[str] = None,
        rate_limit_requests: int = 60,
        rate_limit_window: int = 60
    ):
        """
        Initialize Apollo.io client.

        Args:
            api_key: Apollo.io API key (defaults to APOLLO_API_KEY env var)
            rate_limit_requests: Max requests per time window
            rate_limit_window: Time window in seconds
        """
        # Call parent class constructor
        super().__init__()

        # Get API key from parameter or environment
        api_key = api_key or os.getenv("APOLLO_API_KEY")
        if not api_key:
            raise ValueError("Apollo API key is required. Set APOLLO_API_KEY environment variable or pass api_key parameter.")

        # Set instance attributes
        self.api_key = api_key
        self.rate_limit_requests = rate_limit_requests
        self.rate_limit_window = rate_limit_window

        # Create HTTP session
        self.session = requests.Session()
        self.session.headers.update({
            "Content-Type": "application/json",
            "Cache-Control": "no-cache",
            "X-Api-Key": self.api_key
        })

        # Rate limiting tracking
        self.request_times = []

        logger.info("Apollo.io client initialized")

    def _make_request(
        self,
        method: str,
        url: str,
        json_data: Optional[Dict[str, Any]] = None,
        params: Optional[Dict[str, Any]] = None
    ) -> requests.Response:
        """
        Make an HTTP request with rate limiting.

        Args:
            method: HTTP method (GET, POST, etc.)
            url: Full URL to request
            json_data: JSON data for POST requests
            params: Query parameters for GET requests

        Returns:
            Response object
        """
        # Rate limiting: ensure we don't exceed rate_limit_requests per rate_limit_window
        current_time = time()

        # Remove requests older than the time window
        self.request_times = [t for t in self.request_times if current_time - t < self.rate_limit_window]

        # If we've hit the rate limit, wait
        if len(self.request_times) >= self.rate_limit_requests:
            sleep_time = self.rate_limit_window - (current_time - self.request_times[0])
            if sleep_time > 0:
                logger.info(f"⏳ Rate limit reached, sleeping for {sleep_time:.1f}s")
                sleep(sleep_time)
                current_time = time()
                self.request_times = [t for t in self.request_times if current_time - t < self.rate_limit_window]

        # Make the request
        self.request_times.append(current_time)

        if method.upper() == "POST":
            response = self.session.post(url, json=json_data)
        elif method.upper() == "GET":
            response = self.session.get(url, params=params)
        else:
            raise ValueError(f"Unsupported HTTP method: {method}")

        # Check for errors
        response.raise_for_status()

        return response

    def search_people(
        self,
        query: Optional[str] = None,
        titles: Optional[List[str]] = None,
        locations: Optional[List[str]] = None,
        seniorities: Optional[List[str]] = None,
        company_names: Optional[List[str]] = None,
        industries: Optional[List[str]] = None,
        employee_ranges: Optional[List[str]] = None,
        page: int = 1,
        per_page: int = 25,
        **kwargs
    ) -> SearchResult:
        """
        Search for people using Apollo.io People Search API.
        
        Args:
            query: General keyword search
            titles: List of job titles (e.g., ["CEO", "CTO"])
            locations: List of locations (e.g., ["San Francisco, CA, USA"])
            seniorities: List of seniority levels (e.g., ["executive", "director"])
            company_names: List of company names
            industries: List of industries
            employee_ranges: List of employee count ranges (e.g., ["11-50", "51-200"])
            page: Page number (default 1)
            per_page: Results per page (default 25, max 100)
            **kwargs: Additional API parameters
            
        Returns:
            SearchResult object with contacts
        """
        url = f"{self.BASE_URL}/mixed_people/search"
        
        # Build request payload
        payload = {
            "page": page,
            "per_page": min(per_page, 100)  # API max is 100
        }
        
        if query:
            payload["q_keywords"] = query
        if titles:
            payload["person_titles"] = titles
        if locations:
            payload["person_locations"] = locations
        if seniorities:
            payload["person_seniorities"] = seniorities
        if company_names:
            payload["q_organization_name"] = company_names[0] if len(company_names) == 1 else None
        if industries:
            # Use industry keywords instead of tag IDs for broader search
            payload["organization_industry_keywords"] = industries
        if employee_ranges:
            payload["organization_num_employees_ranges"] = employee_ranges
        
        # Add any additional parameters
        payload.update(kwargs)
        
        logger.info(f"Searching people with query: {query}, page: {page}")
        
        try:
            response = self._make_request("POST", url, json_data=payload)
            data = response.json()

            # Debug: Log first person's raw data to see what Apollo returns
            people = data.get("people", [])
            if people and len(people) > 0:
                logger.info(f"🔍 Sample raw data from Apollo (first contact):")
                first_person = people[0]
                logger.info(f"   Name: {first_person.get('name')}")
                logger.info(f"   Title: {first_person.get('title')}")
                logger.info(f"   Organization: {first_person.get('organization')}")

            # Parse response
            contacts = self._parse_people_response(data)
            
            # Build result
            result = SearchResult(
                contacts=contacts,
                total_results=data.get("pagination", {}).get("total_entries", 0),
                page=data.get("pagination", {}).get("page", page),
                per_page=data.get("pagination", {}).get("per_page", per_page),
                total_pages=data.get("pagination", {}).get("total_pages", 0),
                query=query,
                filters=payload
            )
            
            logger.info(f"Found {len(contacts)} contacts (total: {result.total_results})")
            return result
            
        except Exception as e:
            self._handle_error(e, "search_people")
            return SearchResult(contacts=[], total_results=0, page=page, per_page=per_page)
    
    def search(self, query: str, **kwargs) -> Dict[str, Any]:
        """
        Generic search method (implements abstract method from BaseScraper).
        
        Args:
            query: Search query
            **kwargs: Additional parameters
            
        Returns:
            Search results as dict
        """
        result = self.search_people(query=query, **kwargs)
        return result.model_dump()
    
    def enrich_person(
        self,
        email: Optional[str] = None,
        first_name: Optional[str] = None,
        last_name: Optional[str] = None,
        domain: Optional[str] = None,
        linkedin_url: Optional[str] = None,
        reveal_personal_emails: bool = True,
        reveal_phone_number: bool = True
    ) -> Optional[Contact]:
        """
        Enrich a person's data using Apollo.io People Enrichment API.
        
        Args:
            email: Person's email address
            first_name: Person's first name
            last_name: Person's last name
            domain: Company domain
            linkedin_url: LinkedIn profile URL
            reveal_personal_emails: Whether to reveal personal emails (uses credits)
            reveal_phone_number: Whether to reveal phone numbers (uses credits)
            
        Returns:
            Contact object with enriched data, or None if not found
        """
        url = f"{self.BASE_URL}/people/match"
        
        payload = {
            "reveal_personal_emails": reveal_personal_emails,
            "reveal_phone_number": reveal_phone_number
        }
        
        if email:
            payload["email"] = email
        if first_name:
            payload["first_name"] = first_name
        if last_name:
            payload["last_name"] = last_name
        if domain:
            payload["domain"] = domain
        if linkedin_url:
            payload["linkedin_url"] = linkedin_url
        
        logger.info(f"Enriching person: {email or linkedin_url or f'{first_name} {last_name}'}")
        
        try:
            response = self._make_request("POST", url, json_data=payload)
            data = response.json()
            
            if data.get("person"):
                contact = self._parse_person(data["person"])
                logger.info(f"Successfully enriched: {contact.name}")
                return contact
            else:
                logger.warning("No person found for enrichment")
                return None
                
        except Exception as e:
            self._handle_error(e, "enrich_person")
            return None
    
    def search_organizations(
        self,
        query: Optional[str] = None,
        locations: Optional[List[str]] = None,
        employee_ranges: Optional[List[str]] = None,
        industries: Optional[List[str]] = None,
        funding_stages: Optional[List[str]] = None,
        technologies: Optional[List[str]] = None,
        page: int = 1,
        per_page: int = 25,
        **kwargs
    ) -> SearchResult:
        """
        Search for organizations using Apollo.io Organization Search API.
        
        Args:
            query: Company name or keyword search
            locations: List of locations
            employee_ranges: List of employee count ranges
            industries: List of industries
            funding_stages: List of funding stages
            technologies: List of technologies used
            page: Page number
            per_page: Results per page
            **kwargs: Additional API parameters
            
        Returns:
            SearchResult object with organizations
        """
        url = f"{self.BASE_URL}/mixed_companies/search"
        
        payload = {
            "page": page,
            "per_page": min(per_page, 100)
        }
        
        if query:
            payload["q_organization_name"] = query
        if locations:
            payload["organization_locations"] = locations
        if employee_ranges:
            payload["organization_num_employees_ranges"] = employee_ranges
        if industries:
            payload["organization_industry_tag_ids"] = industries
        if funding_stages:
            payload["organization_latest_funding_stage_cd"] = funding_stages
        if technologies:
            payload["organization_technology_slugs"] = technologies
        
        payload.update(kwargs)
        
        logger.info(f"Searching organizations with query: {query}, page: {page}")
        
        try:
            response = self._make_request("POST", url, json_data=payload)
            data = response.json()
            
            organizations = self._parse_organizations_response(data)
            
            result = SearchResult(
                organizations=organizations,
                total_results=data.get("pagination", {}).get("total_entries", 0),
                page=data.get("pagination", {}).get("page", page),
                per_page=data.get("pagination", {}).get("per_page", per_page),
                total_pages=data.get("pagination", {}).get("total_pages", 0),
                query=query,
                filters=payload
            )
            
            logger.info(f"Found {len(organizations)} organizations (total: {result.total_results})")
            return result
            
        except Exception as e:
            self._handle_error(e, "search_organizations")
            return SearchResult(organizations=[], total_results=0, page=page, per_page=per_page)

    def _parse_people_response(self, data: Dict[str, Any]) -> List[Contact]:
        """
        Parse Apollo.io people search response into Contact objects.

        Args:
            data: Raw API response data

        Returns:
            List of Contact objects
        """
        contacts = []
        people = data.get("people", [])

        for person_data in people:
            try:
                contact = self._parse_person(person_data)
                contacts.append(contact)
            except Exception as e:
                logger.warning(f"Failed to parse person: {e}")
                continue

        return contacts

    def _parse_person(self, person_data: Dict[str, Any]) -> Contact:
        """
        Parse a single person object into a Contact.

        Args:
            person_data: Raw person data from API

        Returns:
            Contact object
        """
        # Extract organization info
        org = person_data.get("organization", {}) or {}
        company_name = org.get("name")

        # Extract industry from SIC/NAICS codes
        sic_codes = org.get("sic_codes", [])
        naics_codes = org.get("naics_codes", [])

        # Generate tags based on title, seniority, and industry
        tags = []
        title = person_data.get("title", "").lower()
        seniority = person_data.get("seniority", "").lower()

        # Add role-based tags with more descriptive names
        if any(word in title for word in ["ceo", "chief executive", "founder", "co-founder"]):
            tags.append("role:ceo_founder")
        if any(word in title for word in ["cto", "chief technology"]):
            tags.append("role:cto")
        if any(word in title for word in ["cfo", "chief financial"]):
            tags.append("role:cfo")
        if any(word in title for word in ["coo", "chief operating"]):
            tags.append("role:coo")
        if any(word in title for word in ["vp", "vice president"]):
            tags.append("role:vp")
        if "director" in title and "managing" not in title:
            tags.append("role:director")
        if "head of" in title or "head " in title:
            tags.append("role:head")
        if "engineer" in title:
            tags.append("dept:engineering")
        if any(word in title for word in ["sales", "revenue", "business development"]):
            tags.append("dept:sales")
        if "product" in title:
            tags.append("dept:product")
        if any(word in title for word in ["marketing", "growth"]):
            tags.append("dept:marketing")

        # Add seniority tag with better formatting
        if seniority:
            # Map Apollo seniority to readable tags
            seniority_map = {
                "c_suite": "C-Suite Executive",
                "vp": "VP Level",
                "director": "Director Level",
                "manager": "Manager Level",
                "senior": "Senior Level",
                "entry": "Entry Level"
            }
            readable_seniority = seniority_map.get(seniority, seniority.title())
            tags.append(f"seniority:{readable_seniority}")

        # Add industry tags from codes (simplified mapping)
        if "7372" in sic_codes or "541511" in naics_codes:
            tags.append("industry:software")
        if "7375" in sic_codes or "518" in naics_codes or "519" in naics_codes:
            tags.append("industry:saas")
        if "6282" in sic_codes or "523" in naics_codes:
            tags.append("industry:fintech")
        if "5045" in sic_codes or "334" in naics_codes:
            tags.append("industry:hardware")
        if "7371" in sic_codes or "541512" in naics_codes:
            tags.append("industry:consulting")

        # Debug: Log raw data for first contact to see what Apollo returns
        person_name = person_data.get("name", "Unknown")
        logger.debug(f"📋 Parsing contact: {person_name}")
        logger.debug(f"   Title: {person_data.get('title')}")
        logger.debug(f"   Tags generated: {tags}")
        logger.debug(f"   Company name extracted: {company_name}")

        # Warn if company name is missing
        if not company_name:
            logger.warning(f"⚠️  No company name for {person_name}")

        # Build contact with only attributes that exist in the Contact schema
        contact = Contact(
            apollo_id=person_data.get("id"),
            name=person_data.get("name", ""),
            title=person_data.get("title"),
            company=company_name,  # Contact schema uses 'company', not 'company_name'
            email=person_data.get("email"),
            linkedin_url=person_data.get("linkedin_url"),
            phone=person_data.get("phone_numbers", [{}])[0].get("raw_number") if person_data.get("phone_numbers") else None,
            city=person_data.get("city"),
            state=person_data.get("state"),
            country=person_data.get("country"),
            tags=tags,  # Add generated tags
            source="apollo"  # Use "apollo" not "apollo.io"
        )

        return contact

    def _parse_organizations_response(self, data: Dict[str, Any]) -> List[Organization]:
        """
        Parse Apollo.io organization search response into Organization objects.

        Args:
            data: Raw API response data

        Returns:
            List of Organization objects
        """
        organizations = []
        orgs = data.get("organizations", [])

        for org_data in orgs:
            try:
                organization = self._parse_organization(org_data)
                organizations.append(organization)
            except Exception as e:
                logger.warning(f"Failed to parse organization: {e}")
                continue

        return organizations

    def _parse_organization(self, org_data: Dict[str, Any]) -> Organization:
        """
        Parse a single organization object into an Organization.

        Args:
            org_data: Raw organization data from API

        Returns:
            Organization object
        """
        organization = Organization(
            apollo_id=org_data.get("id"),
            name=org_data.get("name", ""),
            domain=org_data.get("primary_domain"),
            website=org_data.get("website_url"),
            linkedin_url=org_data.get("linkedin_url"),
            industry=org_data.get("industry"),
            description=org_data.get("short_description"),
            employee_count=org_data.get("estimated_num_employees"),
            founded_year=org_data.get("founded_year"),
            city=org_data.get("city"),
            state=org_data.get("state"),
            country=org_data.get("country"),
            funding_stage=org_data.get("latest_funding_stage"),
            total_funding=org_data.get("total_funding"),
            technologies=org_data.get("technologies", []),
            source="apollo.io",
            created_at=datetime.now(),
            last_updated=datetime.now()
        )

        return organization

    def get_contact_details(self, contact_id: str) -> Dict[str, Any]:
        """
        Get detailed information about a contact by ID.

        Args:
            contact_id: Apollo contact ID

        Returns:
            Dictionary with contact details
        """
        # This method is required by BaseScraper but not currently used
        # Can be implemented later if needed for enrichment
        logger.warning(f"get_contact_details not implemented yet for contact_id: {contact_id}")
        return {}

