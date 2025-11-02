"""
Database manager for LeadOn CRM
Handles database connections, CRUD operations, and migrations
"""

import os
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session
from sqlalchemy.pool import StaticPool
from typing import List, Optional, Dict, Any
from datetime import datetime
import logging

from database.models import Base, Company, Contact, JobPosting, Campaign, SearchHistory

logger = logging.getLogger(__name__)


class DatabaseManager:
    """Manages database operations for LeadOn CRM"""
    
    def __init__(self, database_url: Optional[str] = None):
        """
        Initialize database manager
        
        Args:
            database_url: Database connection string (defaults to SQLite)
        """
        if database_url is None:
            # Default to SQLite in the database folder
            db_path = os.path.join(os.path.dirname(__file__), "leadon.db")
            database_url = f"sqlite:///{db_path}"
        
        self.database_url = database_url
        
        # Create engine
        if database_url.startswith("sqlite"):
            # SQLite-specific settings
            self.engine = create_engine(
                database_url,
                connect_args={"check_same_thread": False},
                poolclass=StaticPool
            )
        else:
            self.engine = create_engine(database_url)
        
        # Create session factory
        self.SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=self.engine)
        
        # Create tables
        self.create_tables()
        
        logger.info(f"Database initialized: {database_url}")
    
    def create_tables(self):
        """Create all tables if they don't exist"""
        Base.metadata.create_all(bind=self.engine)
        logger.info("Database tables created/verified")
    
    def get_session(self) -> Session:
        """Get a new database session"""
        return self.SessionLocal()
    
    # ==================== Company Operations ====================
    
    def create_company(self, session: Session, **kwargs) -> Company:
        """Create a new company"""
        company = Company(**kwargs)
        session.add(company)
        session.commit()
        session.refresh(company)
        logger.info(f"Created company: {company.name}")
        return company
    
    def get_company_by_name(self, session: Session, name: str) -> Optional[Company]:
        """Get company by name"""
        return session.query(Company).filter(Company.name == name).first()
    
    def get_company_by_apollo_id(self, session: Session, apollo_id: str) -> Optional[Company]:
        """Get company by Apollo ID"""
        return session.query(Company).filter(Company.apollo_id == apollo_id).first()
    
    def get_or_create_company(self, session: Session, name: str, **kwargs) -> tuple[Company, bool]:
        """
        Get existing company or create new one
        
        Returns:
            (company, created) tuple where created is True if new company was created
        """
        company = self.get_company_by_name(session, name)
        if company:
            return company, False
        
        company = self.create_company(session, name=name, **kwargs)
        return company, True
    
    def update_company_match_score(self, session: Session, company_id: int, 
                                   score: float, reasoning: str):
        """Update company's AI match score"""
        company = session.query(Company).filter(Company.id == company_id).first()
        if company:
            company.match_score = score
            company.match_reasoning = reasoning
            company.updated_at = datetime.utcnow()
            session.commit()
            logger.info(f"Updated match score for {company.name}: {score}")
    
    def get_top_matched_companies(self, session: Session, limit: int = 50) -> List[Company]:
        """Get companies with highest match scores"""
        return session.query(Company)\
            .filter(Company.match_score.isnot(None))\
            .order_by(Company.match_score.desc())\
            .limit(limit)\
            .all()
    
    # ==================== Contact Operations ====================
    
    def create_contact(self, session: Session, **kwargs) -> Contact:
        """Create a new contact (does not commit - caller should commit)"""
        contact = Contact(**kwargs)
        session.add(contact)
        session.flush()  # Flush to get the ID, but don't commit yet
        logger.info(f"Created contact: {contact.name}")
        return contact
    
    def get_contact_by_email(self, session: Session, email: str) -> Optional[Contact]:
        """Get contact by email"""
        return session.query(Contact).filter(Contact.email == email).first()
    
    def get_contact_by_linkedin(self, session: Session, linkedin_url: str) -> Optional[Contact]:
        """Get contact by LinkedIn URL"""
        return session.query(Contact).filter(Contact.linkedin_url == linkedin_url).first()
    
    def get_or_create_contact(self, session: Session, email: Optional[str] = None,
                             linkedin_url: Optional[str] = None, **kwargs) -> tuple[Contact, bool]:
        """
        Get existing contact or create new one.
        If contact exists, updates tags and source_reason if provided.

        Returns:
            (contact, created) tuple
        """
        contact = None
        if email:
            contact = self.get_contact_by_email(session, email)
        if not contact and linkedin_url:
            contact = self.get_contact_by_linkedin(session, linkedin_url)

        if contact:
            # Update existing contact with new tags and source_reason if provided
            if 'tags' in kwargs and kwargs['tags']:
                # Merge new tags with existing tags (avoid duplicates)
                existing_tags = contact.tags or []
                new_tags = kwargs['tags']
                merged_tags = list(set(existing_tags + new_tags))
                contact.tags = merged_tags

            if 'source_reason' in kwargs and kwargs['source_reason']:
                # Update source reason if new one is more specific
                contact.source_reason = kwargs['source_reason']

            session.flush()
            return contact, False

        contact = self.create_contact(session, email=email, linkedin_url=linkedin_url, **kwargs)
        return contact, True
    
    def get_contacts_by_company(self, session: Session, company_id: int) -> List[Contact]:
        """Get all contacts for a company"""
        return session.query(Contact).filter(Contact.company_id == company_id).all()
    
    # ==================== Job Posting Operations ====================
    
    def create_job_posting(self, session: Session, **kwargs) -> JobPosting:
        """Create a new job posting"""
        job = JobPosting(**kwargs)
        session.add(job)
        session.commit()
        session.refresh(job)
        logger.info(f"Created job posting: {job.job_title} at {job.company_name}")
        return job
    
    def get_job_posting_by_id(self, session: Session, job_id: str) -> Optional[JobPosting]:
        """Get job posting by external job ID"""
        return session.query(JobPosting).filter(JobPosting.job_id == job_id).first()
    
    def get_or_create_job_posting(self, session: Session, job_id: str, **kwargs) -> tuple[JobPosting, bool]:
        """Get existing job posting or create new one"""
        job = self.get_job_posting_by_id(session, job_id)
        if job:
            return job, False
        
        job = self.create_job_posting(session, job_id=job_id, **kwargs)
        return job, True
    
    def get_job_postings_by_company(self, session: Session, company_id: int) -> List[JobPosting]:
        """Get all job postings for a company"""
        return session.query(JobPosting).filter(JobPosting.company_id == company_id).all()
    
    def get_relevant_job_postings(self, session: Session, limit: int = 100) -> List[JobPosting]:
        """Get job postings flagged as relevant by AI"""
        return session.query(JobPosting)\
            .filter(JobPosting.is_relevant == True)\
            .order_by(JobPosting.relevance_score.desc())\
            .limit(limit)\
            .all()
    
    def update_job_relevance(self, session: Session, job_id: int, 
                            is_relevant: bool, score: float, reasoning: str):
        """Update job posting's relevance score"""
        job = session.query(JobPosting).filter(JobPosting.id == job_id).first()
        if job:
            job.is_relevant = is_relevant
            job.relevance_score = score
            job.relevance_reasoning = reasoning
            session.commit()
            logger.info(f"Updated relevance for job {job.job_title}: {score}")
    
    # ==================== Campaign Operations ====================
    
    def create_campaign(self, session: Session, **kwargs) -> Campaign:
        """Create a new campaign"""
        campaign = Campaign(**kwargs)
        session.add(campaign)
        session.commit()
        session.refresh(campaign)
        logger.info(f"Created campaign: {campaign.name}")
        return campaign
    
    def get_campaign(self, session: Session, campaign_id: int) -> Optional[Campaign]:
        """Get campaign by ID"""
        return session.query(Campaign).filter(Campaign.id == campaign_id).first()
    
    def update_campaign_stats(self, session: Session, campaign_id: int,
                             companies: int = 0, contacts: int = 0, jobs: int = 0):
        """Update campaign statistics"""
        campaign = self.get_campaign(session, campaign_id)
        if campaign:
            campaign.total_companies += companies
            campaign.total_contacts += contacts
            campaign.total_job_postings += jobs
            campaign.updated_at = datetime.utcnow()
            session.commit()
    
    # ==================== Search History ====================
    
    def create_search_history(self, session: Session, **kwargs) -> SearchHistory:
        """Create search history entry"""
        history = SearchHistory(**kwargs)
        session.add(history)
        session.commit()
        session.refresh(history)
        return history


# Global database manager instance
db_manager = None

def get_db_manager() -> DatabaseManager:
    """Get or create global database manager"""
    global db_manager
    if db_manager is None:
        db_manager = DatabaseManager()
    return db_manager

