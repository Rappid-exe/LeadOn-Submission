"""
Job Enrichment Service
Orchestrates job posting scraping, company extraction, Apollo enrichment, and AI matching
"""

import logging
from typing import List, Dict, Any, Optional
from datetime import datetime

from linkedin_scrape import scrape_first_n_jobs
from scrapers.apollo_scraper import ApolloClient
from ai_agent.intent_parser import IntentParser
from database.db_manager import DatabaseManager
from database.models import Company, Contact, JobPosting

logger = logging.getLogger(__name__)


class JobEnrichmentService:
    """
    Service that enriches lead generation with job postings
    
    Workflow:
    1. User query → Claude analyzes and generates job search queries
    2. Scrape job postings from LinkedIn
    3. Extract companies from job postings
    4. Use Apollo to find directors/executives at those companies
    5. AI matching to score companies based on relevance
    """
    
    def __init__(self, apollo_client: ApolloClient, intent_parser: IntentParser,
                 db_manager: DatabaseManager):
        self.apollo = apollo_client
        self.claude = intent_parser
        self.db = db_manager
    
    def generate_job_search_queries(self, user_query: str, product_description: str = "") -> List[Dict[str, str]]:
        """
        Use Claude to generate job search queries based on user's product/service
        
        Args:
            user_query: User's natural language query
            product_description: Description of the product being sold
            
        Returns:
            List of {query, location} dicts for job searching
        """
        prompt = f"""
You are helping a sales team find companies to sell their product to by analyzing job postings.

User's request: {user_query}
Product/Service: {product_description}

Generate 3-5 job search queries that would help find companies that are good fits for this product.
Think about what roles these companies would be hiring for if they need this product.

For example:
- If selling sales automation → look for "Business Development Representative", "Sales Development Representative"
- If selling marketing tools → look for "Marketing Manager", "Growth Marketing"
- If selling dev tools → look for "Software Engineer", "DevOps Engineer"

Return ONLY a JSON array of objects with "query" and "location" fields.
Example: [{{"query": "Business Development Representative", "location": "United States"}}, ...]

Keep locations broad (country or major city) unless user specified otherwise.
"""
        
        try:
            response = self.claude.client.messages.create(
                model="claude-3-haiku-20240307",
                max_tokens=500,
                messages=[{"role": "user", "content": prompt}]
            )
            
            # Parse JSON response
            import json
            text = response.content[0].text.strip()
            # Extract JSON if wrapped in markdown
            if "```json" in text:
                text = text.split("```json")[1].split("```")[0].strip()
            elif "```" in text:
                text = text.split("```")[1].split("```")[0].strip()
            
            queries = json.loads(text)
            logger.info(f"Generated {len(queries)} job search queries")
            return queries
            
        except Exception as e:
            logger.error(f"Error generating job queries: {e}")
            # Fallback to simple query
            return [{"query": "Business Development", "location": "United States"}]
    
    def scrape_job_postings(self, queries: List[Dict[str, str]], 
                           jobs_per_query: int = 20) -> List[Dict[str, Any]]:
        """
        Scrape job postings from LinkedIn
        
        Args:
            queries: List of {query, location} dicts
            jobs_per_query: Number of jobs to scrape per query
            
        Returns:
            List of job posting dicts
        """
        all_jobs = []
        
        for q in queries:
            try:
                logger.info(f"Scraping jobs: {q['query']} in {q['location']}")
                jobs = scrape_first_n_jobs(
                    query=q['query'],
                    location=q['location'],
                    n=jobs_per_query
                )
                
                # Add search metadata
                for job in jobs:
                    job['search_query'] = q['query']
                    job['search_location'] = q['location']
                
                all_jobs.extend(jobs)
                logger.info(f"Found {len(jobs)} jobs for {q['query']}")
                
            except Exception as e:
                logger.error(f"Error scraping jobs for {q}: {e}")
                continue
        
        logger.info(f"Total jobs scraped: {len(all_jobs)}")
        return all_jobs
    
    def save_job_postings_to_db(self, session, jobs: List[Dict[str, Any]]) -> List[JobPosting]:
        """
        Save job postings to database and create/link companies
        
        Returns:
            List of JobPosting objects
        """
        saved_jobs = []
        
        for job_data in jobs:
            try:
                # Get or create company
                company_name = job_data.get('company')
                if not company_name:
                    continue
                
                company, created = self.db.get_or_create_company(
                    session,
                    name=company_name,
                    description=job_data.get('company_description'),
                    source='job_posting'
                )
                
                # Create job posting
                job, created = self.db.get_or_create_job_posting(
                    session,
                    job_id=job_data.get('job_id'),
                    company_id=company.id,
                    company_name=company_name,
                    job_title=job_data.get('job_title'),
                    job_description=job_data.get('job_description'),
                    level=job_data.get('level'),
                    company_description=job_data.get('company_description'),
                    source='linkedin',
                    search_query=job_data.get('search_query'),
                    search_location=job_data.get('search_location')
                )
                
                saved_jobs.append(job)
                
            except Exception as e:
                logger.error(f"Error saving job posting: {e}")
                continue
        
        logger.info(f"Saved {len(saved_jobs)} job postings to database")
        return saved_jobs
    
    def _sanitize_text(self, text: str) -> str:
        """
        Sanitize text by removing control characters that break JSON parsing.
        """
        if not text:
            return ""

        # Replace control characters with spaces
        import re
        # Remove all control characters except newline and tab
        text = re.sub(r'[\x00-\x08\x0b-\x0c\x0e-\x1f\x7f-\x9f]', ' ', text)
        # Replace multiple spaces with single space
        text = re.sub(r'\s+', ' ', text)
        return text.strip()

    def analyze_company_fit(self, session, company: Company, user_query: str,
                           product_description: str = "") -> Dict[str, Any]:
        """
        Use Claude to analyze if a company is a good fit based on job postings

        Returns:
            {score: float, reasoning: str}
        """
        # Get company's job postings
        jobs = self.db.get_job_postings_by_company(session, company.id)

        if not jobs:
            return {"score": 0, "reasoning": "No job postings available"}

        # Build context from job postings (sanitize text to avoid control characters)
        job_context = "\n\n".join([
            f"Job: {self._sanitize_text(job.job_title)}\nDescription: {self._sanitize_text(job.job_description[:500])}..."
            for job in jobs[:3]  # Use top 3 jobs
        ])

        # Sanitize company info
        company_name = self._sanitize_text(company.name)
        company_desc = self._sanitize_text(company.description or "N/A")
        user_query_clean = self._sanitize_text(user_query)
        product_desc_clean = self._sanitize_text(product_description)

        prompt = f"""
Analyze if this company is a good fit for our product.

User's goal: {user_query_clean}
Product/Service: {product_desc_clean}

Company: {company_name}
Company Description: {company_desc}

Recent Job Postings:
{job_context}

Based on the job postings and company info, rate this company's fit on a scale of 0-100.
Consider:
- Are they hiring roles that would use our product?
- Does their company description suggest they need our solution?
- What's their growth stage and hiring velocity?

Return ONLY a JSON object: {{"score": <0-100>, "reasoning": "<brief explanation>"}}
"""

        try:
            response = self.claude.client.messages.create(
                model="claude-3-haiku-20240307",
                max_tokens=300,
                messages=[{"role": "user", "content": prompt}]
            )

            import json
            text = response.content[0].text.strip()
            if "```json" in text:
                text = text.split("```json")[1].split("```")[0].strip()
            elif "```" in text:
                text = text.split("```")[1].split("```")[0].strip()

            result = json.loads(text)
            return result

        except Exception as e:
            logger.error(f"Error analyzing company fit: {e}")
            return {"score": 50, "reasoning": "Error during analysis"}
    
    def enrich_companies_with_apollo(self, session, companies: List[Company],
                                    target_titles: List[str] = None,
                                    max_contacts_per_company: int = 1) -> List[Contact]:
        """
        Use Apollo to find contacts at companies

        Args:
            companies: List of Company objects
            target_titles: List of job titles to search for (e.g., ["CEO", "Director"])
            max_contacts_per_company: Maximum contacts to find per company (default: 1 to save credits)

        Returns:
            List of Contact objects
        """
        if target_titles is None:
            # Focus on top decision makers only - CEO or Director level
            target_titles = ["CEO", "Chief Executive Officer", "Director", "Managing Director"]

        all_contacts = []

        for company in companies:
            try:
                logger.info(f"Enriching {company.name} with Apollo (max {max_contacts_per_company} contact)...")

                # Get job postings for this company to add context
                job_postings = session.query(JobPosting).filter(
                    JobPosting.company_id == company.id
                ).all()

                # Build job context for tags
                job_titles = [jp.job_title for jp in job_postings if jp.job_title]
                job_context = f"recruiting for {', '.join(job_titles[:3])}" if job_titles else "has job openings"

                # Search Apollo for contacts at this company
                # Use per_page=25 to get options, but we'll only save the top ones
                result = self.apollo.search_people(
                    company_names=[company.name],
                    titles=target_titles,
                    per_page=25  # Get options to choose from
                )

                # Prioritize contacts: CEO > Director > others
                # Only take the first max_contacts_per_company
                contacts_to_save = []
                for contact_obj in result.contacts[:max_contacts_per_company]:
                    contacts_to_save.append(contact_obj)

                if not contacts_to_save:
                    logger.warning(f"No contacts found for {company.name}")
                    continue

                # Save contacts to database with job posting context
                for contact_obj in contacts_to_save:
                    # Extract tags from contact
                    if isinstance(contact_obj, dict):
                        existing_tags = contact_obj.get('tags', [])
                    else:
                        existing_tags = getattr(contact_obj, 'tags', [])

                    # Add job posting context tag
                    enhanced_tags = existing_tags.copy() if existing_tags else []
                    enhanced_tags.append(f"job_posting:{job_titles[0][:30] if job_titles else 'unknown'}")

                    # Build source reason with job context
                    source_reason = f"Found via job enrichment: {company.name} is {job_context}"

                    # contact_obj is already a Contact object from Apollo scraper
                    # We need to check if it's a dict or object
                    if isinstance(contact_obj, dict):
                        # It's a dictionary
                        contact, created = self.db.get_or_create_contact(
                            session,
                            email=contact_obj.get('email'),
                            linkedin_url=contact_obj.get('linkedin_url'),
                            name=contact_obj.get('name'),
                            title=contact_obj.get('title'),
                            company_id=company.id,
                            company_name=company.name,
                            phone=contact_obj.get('phone'),
                            city=contact_obj.get('city'),
                            state=contact_obj.get('state'),
                            country=contact_obj.get('country'),
                            seniority=contact_obj.get('seniority'),
                            tags=enhanced_tags,
                            source_reason=source_reason,
                            source='apollo'
                        )
                    else:
                        # It's a Contact object - access attributes safely with getattr
                        contact, created = self.db.get_or_create_contact(
                            session,
                            email=getattr(contact_obj, 'email', None),
                            linkedin_url=getattr(contact_obj, 'linkedin_url', None),
                            name=getattr(contact_obj, 'name', ''),
                            title=getattr(contact_obj, 'title', None),
                            company_id=company.id,
                            company_name=company.name,
                            phone=getattr(contact_obj, 'phone', None),
                            city=getattr(contact_obj, 'city', None),
                            state=getattr(contact_obj, 'state', None),
                            country=getattr(contact_obj, 'country', None),
                            seniority=getattr(contact_obj, 'seniority', None),
                            tags=enhanced_tags,
                            source_reason=source_reason,
                            source='apollo'
                        )

                    all_contacts.append(contact)

                    if created:
                        logger.info(f"✅ Added {contact.name} ({contact.title}) from {company.name}")
                    else:
                        logger.info(f"♻️  Updated {contact.name} from {company.name}")

                logger.info(f"Saved {len(contacts_to_save)} contact(s) at {company.name} (found {len(result.contacts)} total)")

            except Exception as e:
                logger.error(f"Error enriching {company.name}: {e}")
                continue

        logger.info(f"Total contacts enriched: {len(all_contacts)}")
        return all_contacts
    
    def run_full_enrichment(self, user_query: str, product_description: str = "",
                           jobs_per_query: int = 20, min_match_score: float = 60,
                           max_contacts_per_company: int = 1) -> Dict[str, Any]:
        """
        Run the complete job enrichment workflow

        Args:
            user_query: User's search query
            product_description: Description of product/service
            jobs_per_query: Number of job postings to scrape per query
            min_match_score: Minimum company match score (0-100)
            max_contacts_per_company: Max contacts to find per company (default: 1 to save credits)

        Returns:
            {
                'companies': List[Company],
                'contacts': List[Contact],
                'job_postings': List[JobPosting],
                'stats': {...}
            }
        """
        session = self.db.get_session()

        try:
            # Step 1: Generate job search queries
            logger.info("Step 1: Generating job search queries...")
            queries = self.generate_job_search_queries(user_query, product_description)

            # Step 2: Scrape job postings
            logger.info("Step 2: Scraping job postings...")
            jobs = self.scrape_job_postings(queries, jobs_per_query)

            # Step 3: Save to database
            logger.info("Step 3: Saving job postings to database...")
            job_postings = self.save_job_postings_to_db(session, jobs)

            # Step 4: Get unique companies
            company_ids = list(set([job.company_id for job in job_postings if job.company_id]))
            companies = [session.query(Company).get(cid) for cid in company_ids]

            # Step 5: Analyze company fit with AI
            logger.info("Step 5: Analyzing company fit...")
            for company in companies:
                analysis = self.analyze_company_fit(session, company, user_query, product_description)
                self.db.update_company_match_score(session, company.id,
                                                   analysis['score'], analysis['reasoning'])

            # Step 6: Filter companies by match score
            matched_companies = [c for c in companies if c.match_score and c.match_score >= min_match_score]
            logger.info(f"Found {len(matched_companies)} companies with score >= {min_match_score}")

            # Step 7: Enrich with Apollo contacts (only 1 per company to save credits)
            logger.info(f"Step 7: Enriching with Apollo contacts ({max_contacts_per_company} per company)...")
            contacts = self.enrich_companies_with_apollo(
                session,
                matched_companies,
                max_contacts_per_company=max_contacts_per_company
            )

            # IMPORTANT: Commit all changes to database!
            session.commit()
            logger.info(f"✅ Committed {len(contacts)} contacts to database")

            return {
                'companies': matched_companies,
                'contacts': contacts,
                'job_postings': job_postings,
                'stats': {
                    'total_jobs_scraped': len(job_postings),
                    'total_companies': len(companies),
                    'matched_companies': len(matched_companies),
                    'total_contacts': len(contacts)
                }
            }

        except Exception as e:
            session.rollback()
            logger.error(f"Error in full enrichment workflow: {e}")
            raise
        finally:
            session.close()

