"""
AI Sales Pitch Generator Service

Generates personalized sales pitches for contacts using Claude AI.
Analyzes contact data (title, company, industry) and creates compelling,
contextual outreach messages.
"""

import os
from typing import Dict, Optional
from anthropic import Anthropic
import httpx
import logging

logger = logging.getLogger(__name__)


class AIPitchGenerator:
    """Service for generating AI-powered sales pitches"""
    
    def __init__(self, api_key: Optional[str] = None):
        """
        Initialize AI pitch generator
        
        Args:
            api_key: Anthropic API key (defaults to env var)
        """
        self.api_key = api_key or os.getenv("ANTHROPIC_API_KEY")
        if not self.api_key:
            raise ValueError("ANTHROPIC_API_KEY required")
        
        http_client = httpx.Client(timeout=60.0, follow_redirects=True)
        self.client = Anthropic(api_key=self.api_key, http_client=http_client)
        self.model = "claude-3-haiku-20240307"
    
    def generate_pitch(
        self,
        contact_data: Dict,
        product_description: Optional[str] = None,
        pitch_type: str = "connection_request"
    ) -> Dict:
        """
        Generate personalized sales pitch for a contact
        
        Args:
            contact_data: Contact information (name, title, company, etc.)
            product_description: Your product/service description
            pitch_type: Type of pitch (connection_request, email, linkedin_message)
            
        Returns:
            Dict with generated pitch and metadata
        """
        try:
            # Build context from contact data
            context = self._build_context(contact_data)
            
            # Generate pitch using Claude
            pitch = self._generate_with_claude(
                context=context,
                product_description=product_description,
                pitch_type=pitch_type
            )
            
            return {
                "success": True,
                "pitch": pitch,
                "contact_name": contact_data.get("name"),
                "pitch_type": pitch_type,
                "metadata": {
                    "title": contact_data.get("title"),
                    "company": contact_data.get("company"),
                    "industry": self._extract_industry(contact_data)
                }
            }
            
        except Exception as e:
            logger.error(f"Error generating pitch: {e}")
            return {
                "success": False,
                "error": str(e)
            }
    
    def _build_context(self, contact_data: Dict) -> str:
        """Build context string from contact data"""
        parts = []
        
        if contact_data.get("name"):
            parts.append(f"Name: {contact_data['name']}")
        
        if contact_data.get("title"):
            parts.append(f"Title: {contact_data['title']}")
        
        if contact_data.get("company"):
            parts.append(f"Company: {contact_data['company']}")
        
        if contact_data.get("company_name"):
            parts.append(f"Company: {contact_data['company_name']}")
        
        # Add search context (why they were found)
        if contact_data.get("search_query"):
            parts.append(f"Found via search: {contact_data['search_query']}")
        
        if contact_data.get("source_reason"):
            parts.append(f"Reason added: {contact_data['source_reason']}")
        
        # Extract industry from tags
        tags = contact_data.get("tags", [])
        if tags:
            industry_tags = [t for t in tags if t.startswith("industry:")]
            if industry_tags:
                industries = [t.replace("industry:", "") for t in industry_tags]
                parts.append(f"Industry: {', '.join(industries)}")
        
        # Add role/department info
        role_tags = [t for t in tags if t.startswith("role:") or t.startswith("dept:")]
        if role_tags:
            roles = [t.split(":")[-1].replace("_", " ").title() for t in role_tags]
            parts.append(f"Role/Department: {', '.join(roles)}")
        
        return "\n".join(parts)
    
    def _extract_industry(self, contact_data: Dict) -> Optional[str]:
        """Extract industry from contact tags"""
        tags = contact_data.get("tags", [])
        industry_tags = [t for t in tags if t.startswith("industry:")]
        if industry_tags:
            return industry_tags[0].replace("industry:", "").replace("_", " ").title()
        return None
    
    def _generate_with_claude(
        self,
        context: str,
        product_description: Optional[str],
        pitch_type: str
    ) -> str:
        """Generate pitch using Claude AI"""
        
        # Default product description if none provided
        if not product_description:
            product_description = "AI-powered sales automation and CRM platform that helps teams find, engage, and convert leads faster"
        
        # Build prompt based on pitch type
        if pitch_type == "connection_request":
            max_length = "MAXIMUM 280 characters (LinkedIn connection message limit is 300)"
            tone = "friendly, professional, and VERY concise"
            format_instructions = "CRITICAL: Keep under 280 characters total. Be brief and direct. One sentence intro, one sentence value, one sentence CTA."
        elif pitch_type == "email":
            max_length = "150-200 words"
            tone = "professional but personable"
            format_instructions = "Include a clear subject line, brief intro, value prop, and soft CTA."
        else:  # linkedin_message
            max_length = "200-250 words"
            tone = "conversational and helpful"
            format_instructions = "Start with context, provide value, end with question or CTA."
        
        prompt = f"""You are an expert sales development representative writing personalized outreach messages.

CONTACT INFORMATION:
{context}

YOUR OUTREACH CONTEXT:
{product_description}

TASK:
Write a {pitch_type.replace('_', ' ')} that:
1. Is personalized to this specific contact (use their name, title, company)
2. References WHY you're reaching out (based on the search context if provided)
3. Shows you understand their role and potential challenges
4. Clearly communicates value relevant to them
5. Has a clear, low-pressure call-to-action
6. Feels authentic and human (not salesy or generic)

REQUIREMENTS:
- Tone: {tone}
- Length: {max_length}
- {format_instructions}

IMPORTANT:
- Use their first name only (not "Mr./Ms.")
- If search context is provided, reference it naturally (e.g., "I'm reaching out to CTOs in the AI space...")
- Reference their specific role/company
- Don't use buzzwords or hype
- Be specific about value, not vague
- Make it feel like you actually researched them
- Keep it conversational and brief

Generate the message now:"""

        response = self.client.messages.create(
            model=self.model,
            max_tokens=500,
            messages=[{"role": "user", "content": prompt}]
        )
        
        # Extract text from response
        pitch = ""
        for block in response.content:
            if block.type == "text":
                pitch += block.text
        
        return pitch.strip()
    
    def generate_multiple_variations(
        self,
        contact_data: Dict,
        product_description: Optional[str] = None,
        count: int = 3
    ) -> Dict:
        """
        Generate multiple pitch variations for A/B testing
        
        Args:
            contact_data: Contact information
            product_description: Your product/service description
            count: Number of variations to generate
            
        Returns:
            Dict with list of pitch variations
        """
        variations = []
        
        for i in range(count):
            result = self.generate_pitch(
                contact_data=contact_data,
                product_description=product_description,
                pitch_type="connection_request"
            )
            
            if result["success"]:
                variations.append({
                    "id": i + 1,
                    "pitch": result["pitch"],
                    "length": len(result["pitch"])
                })
        
        return {
            "success": True,
            "variations": variations,
            "contact_name": contact_data.get("name")
        }


def test_generator():
    """Test the AI pitch generator"""
    print("=" * 70)
    print("AI Sales Pitch Generator Test")
    print("=" * 70)
    print()
    
    # Test contact data
    contact = {
        "name": "Sarah Chen",
        "title": "VP of Sales",
        "company": "TechCorp Inc",
        "tags": ["role:vp", "dept:sales", "industry:saas", "seniority:VP Level"]
    }
    
    print("Contact:")
    print(f"  Name: {contact['name']}")
    print(f"  Title: {contact['title']}")
    print(f"  Company: {contact['company']}")
    print(f"  Tags: {', '.join(contact['tags'])}")
    print()
    
    # Initialize generator
    generator = AIPitchGenerator()
    
    # Generate pitch
    print("Generating personalized pitch...")
    print()
    
    result = generator.generate_pitch(
        contact_data=contact,
        product_description="AI-powered sales automation platform that helps teams automate outreach and close deals faster",
        pitch_type="connection_request"
    )
    
    if result["success"]:
        print("=" * 70)
        print("GENERATED PITCH:")
        print("=" * 70)
        print()
        print(result["pitch"])
        print()
        print(f"Length: {len(result['pitch'])} characters")
        print()
    else:
        print(f"Error: {result['error']}")
    
    # Generate variations
    print()
    print("Generating 3 variations...")
    print()
    
    variations_result = generator.generate_multiple_variations(
        contact_data=contact,
        count=3
    )
    
    if variations_result["success"]:
        for var in variations_result["variations"]:
            print(f"--- Variation {var['id']} ({var['length']} chars) ---")
            print(var["pitch"])
            print()


if __name__ == "__main__":
    test_generator()
