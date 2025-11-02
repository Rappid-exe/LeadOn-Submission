"""
AI Agent for parsing user intent and orchestrating scrapers
"""

import os
import json
from typing import Dict, List, Optional, Any
from datetime import datetime
from anthropic import Anthropic
import httpx
from pydantic import BaseModel, Field


class SearchIntent(BaseModel):
    """Parsed search intent from user input"""
    query: str = Field(description="General search query")
    titles: List[str] = Field(default_factory=list, description="Job titles to search for")
    companies: List[str] = Field(default_factory=list, description="Company names")
    locations: List[str] = Field(default_factory=list, description="Geographic locations")
    industries: List[str] = Field(default_factory=list, description="Industries")
    tags: List[str] = Field(default_factory=list, description="Tags for categorization")
    campaign_objective: str = Field(description="Campaign objective/goal")
    website_url: Optional[str] = Field(default=None, description="Website URL if provided")
    scraper_type: str = Field(default="apollo", description="Which scraper to use")
    max_results: int = Field(default=50, description="Maximum number of results")


class IntentParser:
    """
    Parses natural language user input into structured search parameters.
    Uses Claude (Anthropic) to understand intent and extract search criteria.
    """

    def __init__(self, api_key: Optional[str] = None):
        """
        Initialize the intent parser.

        Args:
            api_key: Anthropic API key (defaults to env var)
        """
        self.api_key = api_key or os.getenv("ANTHROPIC_API_KEY")
        if not self.api_key:
            raise ValueError("Anthropic API key is required. Set ANTHROPIC_API_KEY environment variable.")

        # Create httpx client to avoid proxy compatibility issues
        http_client = httpx.Client(
            timeout=60.0,
            follow_redirects=True
        )

        self.client = Anthropic(
            api_key=self.api_key,
            http_client=http_client
        )
    
    def parse_intent(self, user_input: str, website_url: Optional[str] = None) -> SearchIntent:
        """
        Parse user input into structured search intent.

        Args:
            user_input: Natural language description of what user wants
            website_url: Optional website URL provided by user

        Returns:
            SearchIntent object with extracted parameters
        """
        # Build prompt for Claude
        prompt = self._build_prompt(user_input, website_url)

        # Call Claude API with tool use
        response = self.client.messages.create(
            model="claude-3-haiku-20240307",
            max_tokens=1024,
            tools=[{
                "name": "extract_search_intent",
                "description": "Extract structured search parameters from user input for B2B lead generation",
                "input_schema": {
                    "type": "object",
                    "properties": {
                        "query": {
                            "type": "string",
                            "description": "General search query summarizing the intent"
                        },
                        "titles": {
                            "type": "array",
                            "items": {"type": "string"},
                            "description": "Job titles to search for (e.g., CEO, CTO, VP Sales)"
                        },
                        "companies": {
                            "type": "array",
                            "items": {"type": "string"},
                            "description": "Specific company names if mentioned"
                        },
                        "locations": {
                            "type": "array",
                            "items": {"type": "string"},
                            "description": "Geographic locations (cities, states, countries)"
                        },
                        "industries": {
                            "type": "array",
                            "items": {"type": "string"},
                            "description": "Industries or sectors (e.g., AI, SaaS, FinTech)"
                        },
                        "tags": {
                            "type": "array",
                            "items": {"type": "string"},
                            "description": "Tags for categorization (e.g., investor, fundraising, partnership)"
                        },
                        "campaign_objective": {
                            "type": "string",
                            "description": "The goal of the campaign (e.g., partnership, sales, fundraising)"
                        },
                        "scraper_type": {
                            "type": "string",
                            "enum": ["apollo", "website", "linkedin", "jobboard"],
                            "description": "Which scraper to use based on the request"
                        },
                        "max_results": {
                            "type": "integer",
                            "description": "Maximum number of results to return (default 50)"
                        }
                    },
                    "required": ["query", "campaign_objective"]
                }
            }],
            messages=[
                {
                    "role": "user",
                    "content": f"You are an expert at parsing user intent for B2B lead generation. Extract search parameters from natural language.\n\n{prompt}"
                }
            ]
        )

        # Parse tool use response
        tool_use = None
        for block in response.content:
            if block.type == "tool_use":
                tool_use = block
                break

        if not tool_use:
            raise ValueError("Claude did not return a tool use response")

        arguments = tool_use.input

        # Add website URL if provided
        if website_url:
            arguments["website_url"] = website_url

        # Create SearchIntent object
        intent = SearchIntent(**arguments)

        return intent
    
    def _build_prompt(self, user_input: str, website_url: Optional[str] = None) -> str:
        """Build prompt for GPT"""
        prompt = f"User request: {user_input}\n\n"
        
        if website_url:
            prompt += f"Website URL: {website_url}\n\n"
        
        prompt += """
Extract the following information:
1. Job titles they're looking for (CEO, CTO, VP, etc.)
2. Companies (if specific companies mentioned)
3. Locations (cities, states, countries)
4. Industries (AI, SaaS, FinTech, etc.)
5. Tags for categorization (investor, fundraising, partnership, etc.)
6. Campaign objective (what they want to achieve)
7. Which scraper to use (apollo for general search, website if they provided a URL)
8. Maximum number of results (default 50)

Examples:
- "Find CTOs at AI companies in San Francisco" → titles: [CTO], industries: [AI], locations: ["San Francisco, CA, USA"]
- "Get investors in the FinTech space" → tags: [investor], industries: [FinTech]
- "Partnership outreach to SaaS CEOs in New York" → titles: [CEO], industries: [SaaS], locations: ["New York, NY, USA"], campaign_objective: partnership

IMPORTANT for locations:
- Always use full format: "City, State, Country" (e.g., "San Francisco, CA, USA")
- For US cities: "City, State Abbreviation, USA"
- For other countries: "City, Country"
"""
        
        return prompt
    
    def generate_response(self, intent: SearchIntent, results_count: int) -> str:
        """
        Generate a natural language response about the search results.

        Args:
            intent: The parsed search intent
            results_count: Number of contacts found

        Returns:
            Natural language response
        """
        response = self.client.messages.create(
            model="claude-3-haiku-20240307",
            max_tokens=256,
            messages=[
                {
                    "role": "user",
                    "content": f"""You are a helpful assistant for a CRM system. Generate friendly, concise responses.

Generate a response for the user about their search results.

Search intent: {intent.campaign_objective}
Titles: {', '.join(intent.titles) if intent.titles else 'any'}
Companies: {', '.join(intent.companies) if intent.companies else 'any'}
Locations: {', '.join(intent.locations) if intent.locations else 'any'}
Industries: {', '.join(intent.industries) if intent.industries else 'any'}

Results found: {results_count} contacts

Generate a friendly 1-2 sentence response confirming what was found and that it's been added to the CRM.
"""
                }
            ]
        )

        # Extract text from response
        text_content = ""
        for block in response.content:
            if block.type == "text":
                text_content += block.text

        return text_content


class ScraperOrchestrator:
    """
    Orchestrates multiple scrapers based on parsed intent.
    """
    
    def __init__(self):
        """Initialize the orchestrator"""
        self.intent_parser = IntentParser()
    
    async def process_user_request(
        self,
        user_input: str,
        website_url: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Process user request end-to-end.
        
        Args:
            user_input: Natural language description
            website_url: Optional website URL
            
        Returns:
            Dictionary with results and metadata
        """
        # 1. Parse intent
        intent = self.intent_parser.parse_intent(user_input, website_url)
        
        # 2. Execute appropriate scraper
        contacts = await self._execute_scraper(intent)
        
        # 3. Generate response
        response = self.intent_parser.generate_response(intent, len(contacts))
        
        return {
            "intent": intent.model_dump(),
            "contacts": contacts,
            "response": response,
            "timestamp": datetime.now().isoformat()
        }
    
    async def _execute_scraper(self, intent: SearchIntent) -> List[Dict[str, Any]]:
        """
        Execute the appropriate scraper based on intent.
        
        Args:
            intent: Parsed search intent
            
        Returns:
            List of contacts
        """
        if intent.scraper_type == "apollo":
            return await self._scrape_apollo(intent)
        elif intent.scraper_type == "website":
            return await self._scrape_website(intent)
        else:
            # Default to Apollo
            return await self._scrape_apollo(intent)
    
    async def _scrape_apollo(self, intent: SearchIntent) -> List[Dict[str, Any]]:
        """
        Scrape using Apollo.io API.
        Falls back to mock data if Apollo API is not available.
        """
        # Import here to avoid circular imports
        import sys
        from pathlib import Path
        sys.path.append(str(Path(__file__).parent.parent))

        # Try to use real Apollo API
        try:
            from scrapers.apollo_scraper import ApolloClient

            if os.getenv("APOLLO_API_KEY"):
                print("🔍 Using Apollo.io API...")
                client = ApolloClient()

                # Call Apollo API with parsed intent
                result = client.search_people(
                    query=intent.query if intent.query else None,
                    titles=intent.titles if intent.titles else None,
                    locations=intent.locations if intent.locations else None,
                    company_names=intent.companies if intent.companies else None,
                    per_page=min(intent.max_results, 100)
                )

                # Convert Contact objects to dicts
                contacts_dicts = [contact.model_dump() for contact in result.contacts]
                print(f"✅ Found {len(contacts_dicts)} contacts from Apollo.io")
                return contacts_dicts
        except Exception as e:
            print(f"⚠️  Apollo API failed: {e}")
            print("📦 Falling back to mock data...")

        # Fallback to mock data
        from cli.search_mock import filter_contacts
        import json

        mock_file = Path(__file__).parent.parent / "exports" / "demo_contacts.json"

        if mock_file.exists():
            with open(mock_file, 'r') as f:
                all_contacts = json.load(f)

            # Filter based on intent
            filtered = filter_contacts(
                all_contacts,
                query=intent.query,
                titles=intent.titles,
                companies=intent.companies,
                locations=intent.locations,
                tags=intent.tags
            )

            print(f"✅ Found {len(filtered[:intent.max_results])} contacts from mock data")
            return filtered[:intent.max_results]

        return []
    
    async def _scrape_website(self, intent: SearchIntent) -> List[Dict[str, Any]]:
        """Scrape contacts from a website"""
        # TODO: Implement website scraper
        # This would extract team/about pages and find contact info
        return []


if __name__ == "__main__":
    # Test the intent parser
    parser = IntentParser()
    
    test_inputs = [
        "Find CTOs at AI companies in San Francisco for partnership campaign",
        "Get investors in the FinTech space for fundraising",
        "Partnership outreach to SaaS CEOs in New York",
        "Find VPs of Sales at Series B startups in Austin"
    ]
    
    for user_input in test_inputs:
        print(f"\n{'='*60}")
        print(f"Input: {user_input}")
        print(f"{'='*60}")
        
        intent = parser.parse_intent(user_input)
        print(f"\nParsed Intent:")
        print(json.dumps(intent.model_dump(), indent=2))

