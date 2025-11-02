"""
Pydantic schemas for data validation.
Matches the Contact and Organization schemas from context.md.
"""

from datetime import datetime
from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field, HttpUrl, EmailStr


class Contact(BaseModel):
    """
    Contact schema matching context.md specification.
    Represents a person in the CRM system.
    """
    id: Optional[str] = None
    name: str
    title: Optional[str] = None
    company: Optional[str] = None
    email: Optional[EmailStr] = None
    linkedin_url: Optional[str] = None
    phone: Optional[str] = None
    tags: List[str] = Field(default_factory=list)
    source: str = "apollo.io"
    relationship_stage: str = "new_lead"
    created_at: Optional[datetime] = None
    last_updated: Optional[datetime] = None
    
    # Additional Apollo.io specific fields
    apollo_id: Optional[str] = None
    city: Optional[str] = None
    state: Optional[str] = None
    country: Optional[str] = None
    headline: Optional[str] = None
    photo_url: Optional[str] = None
    twitter_url: Optional[str] = None
    facebook_url: Optional[str] = None

    # LinkedIn Automation Workflow
    workflow_stage: Optional[str] = None
    last_action: Optional[str] = None
    last_action_date: Optional[datetime] = None
    next_action: Optional[str] = None
    next_action_date: Optional[datetime] = None
    automation_notes: Optional[str] = None
    
    class Config:
        json_schema_extra = {
            "example": {
                "name": "John Doe",
                "title": "Partner at XYZ Ventures",
                "company": "XYZ Ventures",
                "email": "john@xyz.com",
                "linkedin_url": "https://linkedin.com/in/johndoe",
                "phone": "+1234567890",
                "tags": ["vc", "ai_investor", "fundraising_target"],
                "source": "apollo.io",
                "relationship_stage": "new_lead"
            }
        }


class Organization(BaseModel):
    """
    Organization/Company schema.
    Represents a company in the CRM system.
    """
    id: Optional[str] = None
    name: str
    domain: Optional[str] = None
    website: Optional[str] = None
    linkedin_url: Optional[str] = None
    industry: Optional[str] = None
    description: Optional[str] = None
    
    # Company details
    employee_count: Optional[int] = None
    employee_count_range: Optional[str] = None
    founded_year: Optional[int] = None
    revenue: Optional[str] = None
    revenue_range: Optional[str] = None
    
    # Location
    city: Optional[str] = None
    state: Optional[str] = None
    country: Optional[str] = None
    address: Optional[str] = None
    
    # Funding
    funding_stage: Optional[str] = None
    total_funding: Optional[str] = None
    latest_funding_round: Optional[str] = None
    
    # Technology
    technologies: List[str] = Field(default_factory=list)
    
    # Metadata
    apollo_id: Optional[str] = None
    source: str = "apollo.io"
    created_at: Optional[datetime] = None
    last_updated: Optional[datetime] = None
    
    class Config:
        json_schema_extra = {
            "example": {
                "name": "Anthropic",
                "domain": "anthropic.com",
                "industry": "Artificial Intelligence",
                "employee_count": 150,
                "funding_stage": "Series B",
                "city": "San Francisco",
                "state": "California",
                "country": "United States"
            }
        }


class ApolloPersonSearchRequest(BaseModel):
    """
    Request schema for Apollo.io People Search API.
    """
    q_keywords: Optional[str] = None
    person_titles: Optional[List[str]] = None
    person_locations: Optional[List[str]] = None
    person_seniorities: Optional[List[str]] = None
    organization_ids: Optional[List[str]] = None
    organization_locations: Optional[List[str]] = None
    organization_num_employees_ranges: Optional[List[str]] = None
    industries: Optional[List[str]] = None
    page: int = 1
    per_page: int = 25
    
    class Config:
        json_schema_extra = {
            "example": {
                "q_keywords": "artificial intelligence",
                "person_titles": ["CEO", "CTO", "Founder"],
                "person_locations": ["San Francisco, CA, USA"],
                "organization_num_employees_ranges": ["11-50", "51-200"],
                "page": 1,
                "per_page": 25
            }
        }


class ApolloOrganizationSearchRequest(BaseModel):
    """
    Request schema for Apollo.io Organization Search API.
    """
    q_organization_name: Optional[str] = None
    organization_locations: Optional[List[str]] = None
    organization_num_employees_ranges: Optional[List[str]] = None
    industries: Optional[List[str]] = None
    funding_stage: Optional[List[str]] = None
    technologies: Optional[List[str]] = None
    page: int = 1
    per_page: int = 25
    
    class Config:
        json_schema_extra = {
            "example": {
                "q_organization_name": "AI startup",
                "organization_locations": ["San Francisco, CA, USA"],
                "organization_num_employees_ranges": ["11-50", "51-200"],
                "industries": ["Computer Software"],
                "page": 1,
                "per_page": 25
            }
        }


class ApolloEnrichmentRequest(BaseModel):
    """
    Request schema for Apollo.io People Enrichment API.
    """
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    name: Optional[str] = None
    email: Optional[str] = None
    domain: Optional[str] = None
    organization_name: Optional[str] = None
    linkedin_url: Optional[str] = None
    reveal_personal_emails: bool = False
    reveal_phone_number: bool = False


class SearchResult(BaseModel):
    """
    Generic search result wrapper.
    """
    contacts: List[Contact] = Field(default_factory=list)
    organizations: List[Organization] = Field(default_factory=list)
    total_results: int = 0
    page: int = 1
    per_page: int = 25
    total_pages: int = 0
    query: Optional[str] = None
    filters: Optional[Dict[str, Any]] = None

