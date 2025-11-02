"""
Database models for LeadOn CRM
Supports both Companies and People with job postings enrichment
"""

from sqlalchemy import Column, Integer, String, Text, DateTime, Float, ForeignKey, Boolean, JSON
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship
from datetime import datetime

Base = declarative_base()


class Company(Base):
    """Company/Organization model"""
    __tablename__ = 'companies'
    
    id = Column(Integer, primary_key=True)
    name = Column(String(255), nullable=False, index=True)
    website = Column(String(500))
    industry = Column(String(255))
    description = Column(Text)
    employee_count = Column(String(50))  # e.g., "11-50", "51-200"
    location = Column(String(255))
    
    # Apollo enrichment data
    apollo_id = Column(String(100), unique=True, index=True)
    linkedin_url = Column(String(500))
    founded_year = Column(Integer)
    funding_stage = Column(String(100))
    total_funding = Column(String(100))
    technologies = Column(JSON)  # List of technologies used

    # CRM fields
    tags = Column(JSON)  # List of tags for categorization
    relationship_stage = Column(String(50))  # e.g., "prospect", "contacted", "qualified", "customer"

    # AI matching score (for product fit analysis)
    match_score = Column(Float)  # 0-100 score from Claude analysis
    match_reasoning = Column(Text)  # Why this company is a good fit

    # AI Enrichment Fields (for personalized outreach)
    industry_analysis = Column(Text)  # AI-generated analysis of company's industry and position
    pain_points = Column(JSON)  # List of identified pain points/challenges
    value_proposition = Column(Text)  # Personalized value prop based on our company profile
    enrichment_notes = Column(Text)  # Additional AI-generated insights
    last_enriched_at = Column(DateTime)  # When the company was last enriched

    # Metadata
    source = Column(String(50))  # 'job_posting', 'apollo', 'manual'
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    contacts = relationship("Contact", back_populates="company", cascade="all, delete-orphan")
    job_postings = relationship("JobPosting", back_populates="company", cascade="all, delete-orphan")
    
    def __repr__(self):
        return f"<Company(id={self.id}, name='{self.name}')>"


class Contact(Base):
    """Contact/Person model"""
    __tablename__ = 'contacts'
    
    id = Column(Integer, primary_key=True)
    name = Column(String(255), nullable=False, index=True)
    email = Column(String(255), index=True)
    title = Column(String(255))
    
    # Company relationship
    company_id = Column(Integer, ForeignKey('companies.id'), nullable=True)
    company = relationship("Company", back_populates="contacts")
    company_name = Column(String(255))  # Denormalized for quick access
    
    # Contact details
    phone = Column(String(50))
    linkedin_url = Column(String(500), index=True)
    city = Column(String(100))
    state = Column(String(100))
    country = Column(String(100))
    
    # Apollo data
    apollo_id = Column(String(100), unique=True, index=True)
    seniority = Column(String(50))
    departments = Column(JSON)  # List of departments

    # Metadata
    source = Column(String(50))  # 'apollo', 'job_posting', 'manual'
    tags = Column(JSON)  # List of tags (e.g., ['fintech', 'founder', 'Series B'])
    source_reason = Column(String(500))  # Why this contact was added (e.g., "Found via search: Find CTOs at AI companies")
    search_query = Column(String(500))  # The search query that found this contact

    # LinkedIn Automation Workflow
    workflow_stage = Column(String(50))  # 'new', 'connect_sent', 'connected', 'liked', 'commented', 'messaged', 'replied', 'qualified', 'disqualified'
    last_action = Column(String(100))  # Last action taken (e.g., "Sent connection request", "Liked 3 posts", "Sent message")
    last_action_date = Column(DateTime)  # When the last action was taken
    next_action = Column(String(100))  # Next planned action (e.g., "Like posts", "Send message", "Follow up")
    next_action_date = Column(DateTime)  # When to take the next action
    automation_notes = Column(Text)  # Notes about the automation sequence

    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    def __repr__(self):
        return f"<Contact(id={self.id}, name='{self.name}', title='{self.title}')>"


class JobPosting(Base):
    """Job posting model - scraped from LinkedIn, Indeed, etc."""
    __tablename__ = 'job_postings'
    
    id = Column(Integer, primary_key=True)
    job_id = Column(String(100), unique=True, index=True)  # External job ID
    
    # Company relationship
    company_id = Column(Integer, ForeignKey('companies.id'), nullable=True)
    company = relationship("Company", back_populates="job_postings")
    company_name = Column(String(255), index=True)  # Denormalized
    
    # Job details
    job_title = Column(String(255), nullable=False, index=True)
    job_description = Column(Text)
    level = Column(String(100))  # Seniority level
    location = Column(String(255))
    
    # Company info from job posting
    company_description = Column(Text)
    
    # Job posting metadata
    url = Column(String(500))
    posted_date = Column(DateTime)
    scraped_at = Column(DateTime, default=datetime.utcnow)
    source = Column(String(50))  # 'linkedin', 'indeed', 'google_jobs'
    
    # AI analysis
    is_relevant = Column(Boolean, default=False)  # Flagged by AI as relevant
    relevance_score = Column(Float)  # 0-100 score
    relevance_reasoning = Column(Text)  # Why this job is relevant
    
    # Search query that found this job
    search_query = Column(String(500))
    search_location = Column(String(255))
    
    def __repr__(self):
        return f"<JobPosting(id={self.id}, title='{self.job_title}', company='{self.company_name}')>"


class CompanyProfile(Base):
    """User's company profile for AI enrichment"""
    __tablename__ = 'company_profile'

    id = Column(Integer, primary_key=True)
    website_url = Column(String(500), nullable=False)
    company_name = Column(String(255))
    tagline = Column(String(500))
    description = Column(Text)  # What we do
    products_services = Column(JSON)  # List of products/services
    target_customers = Column(Text)  # Who we serve
    value_propositions = Column(JSON)  # Key value props
    differentiators = Column(Text)  # What makes us unique
    use_cases = Column(JSON)  # Common use cases

    # AI-generated from website
    ai_summary = Column(Text)  # AI-generated summary of the company

    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    def __repr__(self):
        return f"<CompanyProfile(id={self.id}, company='{self.company_name}')>"


class Integration(Base):
    """Integration model - stores connected accounts (LinkedIn, Telegram, etc.)"""
    __tablename__ = 'integrations'

    id = Column(Integer, primary_key=True)
    platform = Column(String(50), nullable=False)  # 'linkedin', 'telegram', 'email'
    status = Column(String(20), default='disconnected')  # 'connected', 'disconnected', 'error'

    # Account details
    account_name = Column(String(255))  # Display name
    account_id = Column(String(255))  # Platform-specific ID
    account_email = Column(String(255))  # Email if applicable
    phone_number = Column(String(50))  # Phone number for Telegram user API

    # Authentication
    access_token = Column(Text)  # Encrypted access token (or API hash for Telegram)
    refresh_token = Column(Text)  # Encrypted refresh token (or API ID for Telegram)
    token_expires_at = Column(DateTime)  # Token expiration

    # Configuration
    config = Column(JSON)  # Platform-specific settings

    # Usage stats
    messages_sent = Column(Integer, default=0)
    connections_made = Column(Integer, default=0)
    last_used_at = Column(DateTime)

    # Metadata
    connected_at = Column(DateTime)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    def __repr__(self):
        return f"<Integration(id={self.id}, platform='{self.platform}', status='{self.status}')>"


class TelegramMessage(Base):
    """Telegram message tracking for campaigns"""
    __tablename__ = 'telegram_messages'

    id = Column(Integer, primary_key=True)
    campaign_id = Column(Integer, ForeignKey('campaigns.id'), nullable=True)
    contact_id = Column(Integer, ForeignKey('contacts.id'), nullable=False)
    integration_id = Column(Integer, ForeignKey('integrations.id'), nullable=False)

    # Message details
    phone_number = Column(String(50), nullable=False)
    telegram_user_id = Column(String(100))  # Telegram user ID if found
    telegram_username = Column(String(100))  # @username if available
    message_text = Column(Text, nullable=False)
    message_id = Column(String(100))  # Telegram message ID

    # Status
    status = Column(String(20), default='pending')  # 'pending', 'sent', 'failed', 'no_telegram'
    error_message = Column(Text)

    # Timestamps
    sent_at = Column(DateTime)
    created_at = Column(DateTime, default=datetime.utcnow)

    def __repr__(self):
        return f"<TelegramMessage(id={self.id}, contact_id={self.contact_id}, status='{self.status}')>"


class Campaign(Base):
    """Campaign model - tracks outreach campaigns"""
    __tablename__ = 'campaigns'

    id = Column(Integer, primary_key=True)
    name = Column(String(255), nullable=False)
    objective = Column(Text)  # Campaign goal/objective

    # Integration
    integration_id = Column(Integer, ForeignKey('integrations.id'))  # Which integration to use
    integration = relationship("Integration")

    # Search parameters
    search_query = Column(Text)
    target_titles = Column(JSON)  # List of job titles
    target_locations = Column(JSON)  # List of locations
    target_industries = Column(JSON)  # List of industries

    # Enrichment settings
    use_job_postings = Column(Boolean, default=False)
    job_search_queries = Column(JSON)  # Queries for job posting scraping

    # Stats
    total_companies = Column(Integer, default=0)
    total_contacts = Column(Integer, default=0)
    total_job_postings = Column(Integer, default=0)

    # Metadata
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    def __repr__(self):
        return f"<Campaign(id={self.id}, name='{self.name}')>"


class SearchHistory(Base):
    """Track search history for analytics"""
    __tablename__ = 'search_history'
    
    id = Column(Integer, primary_key=True)
    user_query = Column(Text, nullable=False)
    parsed_intent = Column(JSON)  # Structured intent from Claude
    
    # Results
    companies_found = Column(Integer, default=0)
    contacts_found = Column(Integer, default=0)
    job_postings_found = Column(Integer, default=0)
    
    # Settings
    used_job_enrichment = Column(Boolean, default=False)
    
    # Metadata
    created_at = Column(DateTime, default=datetime.utcnow)
    
    def __repr__(self):
        return f"<SearchHistory(id={self.id}, query='{self.user_query[:50]}...')>"

