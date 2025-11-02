"""
Agentic Search Service - Intelligent, iterative contact search with Claude
Uses an agentic workflow to:
1. Generate multiple search queries from user input
2. Execute searches and analyze results
3. Learn from successful matches
4. Iteratively refine searches until quality results are found
"""

import os
import json
from typing import Dict, List, Optional, Any, Tuple
from loguru import logger
from anthropic import Anthropic
import httpx

from scrapers.apollo_scraper import ApolloClient
from database.db_manager import DatabaseManager
from database.models import Contact, Company


class AgenticSearchService:
    """
    Intelligent search service that uses Claude to iteratively improve searches.
    """
    
    def __init__(self, apollo_client: ApolloClient, db_manager: DatabaseManager):
        """
        Initialize the agentic search service.
        
        Args:
            apollo_client: Apollo.io API client
            db_manager: Database manager for storing results
        """
        self.apollo = apollo_client
        self.db = db_manager
        
        # Initialize Claude client
        api_key = os.getenv("ANTHROPIC_API_KEY")
        if not api_key:
            raise ValueError("ANTHROPIC_API_KEY not set")
        
        http_client = httpx.Client(timeout=60.0, follow_redirects=True)
        self.claude = Anthropic(api_key=api_key, http_client=http_client)
        
        self.model = "claude-3-haiku-20240307"
    
    def run_agentic_search(
        self,
        user_query: str,
        product_description: str = "",
        max_iterations: int = 3,
        min_results: int = 10,
        max_results_per_query: int = 25
    ) -> Dict[str, Any]:
        """
        Run an agentic search workflow that iteratively improves searches.
        
        Args:
            user_query: User's natural language query
            product_description: Description of product/service being sold
            max_iterations: Maximum number of search iterations
            min_results: Minimum number of quality results to find
            max_results_per_query: Max results per individual search
        
        Returns:
            Dictionary with contacts, companies, and search metadata
        """
        logger.info(f"🤖 Starting agentic search for: {user_query}")
        
        all_contacts = []
        all_companies = set()
        search_history = []
        iteration = 0
        
        # Step 1: Generate initial search queries
        logger.info("Step 1: Generating initial search queries...")
        search_queries = self._generate_search_queries(user_query, product_description)
        logger.info(f"Generated {len(search_queries)} initial queries")
        
        # Step 2: Execute initial searches
        for query_params in search_queries:
            if len(all_contacts) >= min_results:
                break
            
            iteration += 1
            logger.info(f"\n--- Iteration {iteration}/{max_iterations} ---")
            logger.info(f"Searching with: {query_params}")
            
            # Execute search
            contacts, companies = self._execute_apollo_search(
                query_params,
                max_results=max_results_per_query
            )
            
            search_history.append({
                "iteration": iteration,
                "query_params": query_params,
                "results_count": len(contacts),
                "companies_found": len(companies)
            })
            
            if contacts:
                all_contacts.extend(contacts)
                all_companies.update(companies)
                logger.info(f"✅ Found {len(contacts)} contacts, {len(companies)} companies")
                
                # Step 3: Learn from successful matches
                if len(all_contacts) < min_results and iteration < max_iterations:
                    logger.info("Step 3: Learning from successful matches...")
                    expansion_queries = self._learn_and_expand(
                        user_query,
                        product_description,
                        contacts,
                        search_history
                    )
                    
                    if expansion_queries:
                        logger.info(f"Generated {len(expansion_queries)} expansion queries")
                        search_queries.extend(expansion_queries)
            else:
                logger.warning(f"⚠️  No results for query: {query_params}")
                
                # Step 4: Refine search if no results
                if iteration < max_iterations:
                    logger.info("Step 4: Refining search parameters...")
                    refined_queries = self._refine_failed_search(
                        query_params,
                        search_history,
                        user_query,
                        product_description
                    )
                    
                    if refined_queries:
                        logger.info(f"Generated {len(refined_queries)} refined queries")
                        search_queries.extend(refined_queries)
        
        # Deduplicate contacts
        unique_contacts = self._deduplicate_contacts(all_contacts)
        
        logger.info(f"\n🎉 Agentic search complete!")
        logger.info(f"   Total iterations: {iteration}")
        logger.info(f"   Unique contacts: {len(unique_contacts)}")
        logger.info(f"   Companies: {len(all_companies)}")
        
        return {
            "contacts": unique_contacts,
            "companies": list(all_companies),
            "search_history": search_history,
            "iterations": iteration,
            "stats": {
                "total_contacts": len(unique_contacts),
                "total_companies": len(all_companies),
                "queries_executed": len(search_history),
                "avg_results_per_query": len(all_contacts) / len(search_history) if search_history else 0
            }
        }
    
    def _generate_search_queries(
        self,
        user_query: str,
        product_description: str
    ) -> List[Dict[str, Any]]:
        """
        Use Claude to generate multiple targeted search queries.
        
        Returns:
            List of search parameter dictionaries
        """
        prompt = f"""You are an expert at B2B lead generation and Apollo.io searches.

User Query: {user_query}
Product/Service: {product_description or "Not specified"}

Generate 3-5 diverse, targeted Apollo.io search queries to find the best contacts.

For each query, provide:
1. titles: List of job titles (CEO, CTO, VP Sales, etc.)
2. keywords: List of relevant keywords/industries (AI, SaaS, FinTech, etc.)
3. person_seniorities: List of seniority levels (c_suite, vp, director, manager)
4. organization_num_employees_ranges: List of company size ranges (1-10, 11-50, 51-200, 201-500, 501-1000, 1001-5000, 5001-10000, 10001+)
5. reasoning: Why this query will find good matches

Be specific and diverse. Use different combinations to maximize coverage.

Examples:
- For "Find companies that need sales automation":
  * Query 1: titles=["VP Sales", "Sales Director"], keywords=["B2B", "SaaS"], seniorities=["vp", "director"]
  * Query 2: titles=["Chief Revenue Officer", "Head of Sales"], keywords=["technology", "software"], seniorities=["c_suite"]
  * Query 3: titles=["Sales Operations Manager"], keywords=["startup", "growth"], seniorities=["manager", "director"]

Return ONLY a valid JSON array of query objects. No other text.

Format:
[
  {{
    "titles": ["CEO", "Founder"],
    "keywords": ["AI", "machine learning"],
    "person_seniorities": ["c_suite"],
    "organization_num_employees_ranges": ["11-50", "51-200"],
    "reasoning": "Target AI startup founders and CEOs at small-medium companies"
  }}
]
"""
        
        response = self.claude.messages.create(
            model=self.model,
            max_tokens=2000,
            messages=[{"role": "user", "content": prompt}]
        )
        
        # Extract JSON from response
        text = response.content[0].text
        
        # Parse JSON
        try:
            queries = json.loads(text)
            return queries
        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse Claude response: {e}")
            logger.error(f"Response: {text}")
            # Return fallback query
            return [{
                "titles": ["CEO", "CTO", "VP"],
                "keywords": [],
                "person_seniorities": ["c_suite", "vp"],
                "organization_num_employees_ranges": [],
                "reasoning": "Fallback broad search"
            }]
    
    def _execute_apollo_search(
        self,
        query_params: Dict[str, Any],
        max_results: int = 25
    ) -> Tuple[List[Dict[str, Any]], List[str]]:
        """
        Execute an Apollo search with given parameters.
        
        Returns:
            Tuple of (contacts list, companies set)
        """
        try:
            result = self.apollo.search_people(
                titles=query_params.get("titles"),
                keywords=query_params.get("keywords"),
                person_seniorities=query_params.get("person_seniorities"),
                organization_num_employees_ranges=query_params.get("organization_num_employees_ranges"),
                per_page=max_results
            )
            
            contacts = [c.model_dump() for c in result.contacts]
            companies = list(set([c.get("company") for c in contacts if c.get("company")]))
            
            return contacts, companies
            
        except Exception as e:
            logger.error(f"Apollo search failed: {e}")
            return [], []
    
    def _learn_and_expand(
        self,
        user_query: str,
        product_description: str,
        successful_contacts: List[Dict[str, Any]],
        search_history: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        """
        Learn from successful matches and generate expansion queries.
        
        Args:
            user_query: Original user query
            product_description: Product description
            successful_contacts: Contacts that were found
            search_history: History of searches so far
        
        Returns:
            List of new search parameter dictionaries
        """
        # Extract patterns from successful contacts
        sample_contacts = successful_contacts[:5]  # Use first 5 as examples
        
        contact_summary = "\n".join([
            f"- {c.get('title', 'Unknown')} at {c.get('organization_name', 'Unknown')} "
            f"(Industry: {c.get('organization_industry', 'Unknown')})"
            for c in sample_contacts
        ])
        
        prompt = f"""You found some good matches! Now generate 2-3 MORE search queries to find SIMILAR contacts.

Original Query: {user_query}
Product: {product_description or "Not specified"}

Successful Matches Found:
{contact_summary}

Previous Searches:
{json.dumps(search_history, indent=2)}

Based on these successful matches, generate 2-3 NEW search queries that will find SIMILAR contacts.
Look for patterns in:
- Job titles and functions
- Industries and keywords
- Company sizes
- Seniority levels

Return ONLY a valid JSON array. No other text.

Format:
[
  {{
    "titles": ["Similar Title 1", "Similar Title 2"],
    "keywords": ["pattern keyword 1", "pattern keyword 2"],
    "person_seniorities": ["c_suite"],
    "organization_num_employees_ranges": ["51-200"],
    "reasoning": "Why this will find similar matches"
  }}
]
"""
        
        try:
            response = self.claude.messages.create(
                model=self.model,
                max_tokens=1500,
                messages=[{"role": "user", "content": prompt}]
            )
            
            text = response.content[0].text
            queries = json.loads(text)
            return queries
            
        except Exception as e:
            logger.error(f"Failed to generate expansion queries: {e}")
            return []
    
    def _refine_failed_search(
        self,
        failed_query: Dict[str, Any],
        search_history: List[Dict[str, Any]],
        user_query: str,
        product_description: str
    ) -> List[Dict[str, Any]]:
        """
        Analyze why a search failed and generate refined alternatives.
        
        Returns:
            List of refined search parameter dictionaries
        """
        prompt = f"""A search returned 0 results. Help refine it.

Original User Query: {user_query}
Product: {product_description or "Not specified"}

Failed Search:
{json.dumps(failed_query, indent=2)}

Search History:
{json.dumps(search_history, indent=2)}

Why might this search have failed? Generate 2 alternative searches that are:
1. Broader (fewer filters, more general titles)
2. Different angle (different job functions that might have same needs)

Return ONLY a valid JSON array. No other text.

Format:
[
  {{
    "titles": ["Broader Title"],
    "keywords": ["keyword"],
    "person_seniorities": ["vp", "director"],
    "organization_num_employees_ranges": [],
    "reasoning": "Why this is better"
  }}
]
"""
        
        try:
            response = self.claude.messages.create(
                model=self.model,
                max_tokens=1500,
                messages=[{"role": "user", "content": prompt}]
            )
            
            text = response.content[0].text
            queries = json.loads(text)
            return queries
            
        except Exception as e:
            logger.error(f"Failed to refine search: {e}")
            return []
    
    def _deduplicate_contacts(self, contacts: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Deduplicate contacts by email, LinkedIn URL, or ID.
        Handles Apollo's placeholder emails (email_not_unlocked@domain.com).
        """
        seen_emails = set()
        seen_linkedin = set()
        seen_ids = set()
        unique = []

        # Apollo's placeholder emails that should not be used for deduplication
        placeholder_emails = {
            "email_not_unlocked@domain.com",
            "email_not_available@domain.com",
            "noemail@domain.com"
        }

        for contact in contacts:
            email = contact.get("email")
            linkedin = contact.get("linkedin_url")
            contact_id = contact.get("id")

            # Ignore placeholder emails for deduplication
            if email in placeholder_emails:
                email = None

            # Check if we've seen this contact before
            is_duplicate = False

            if email and email in seen_emails:
                is_duplicate = True
            elif linkedin and linkedin in seen_linkedin:
                is_duplicate = True
            elif contact_id and contact_id in seen_ids:
                is_duplicate = True

            if not is_duplicate:
                # Add to seen sets
                if email:
                    seen_emails.add(email)
                if linkedin:
                    seen_linkedin.add(linkedin)
                if contact_id:
                    seen_ids.add(contact_id)

                unique.append(contact)

        return unique

