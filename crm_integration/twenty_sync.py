"""
Twenty CRM Synchronization Service
Syncs Apollo scraper data with Twenty CRM via GraphQL API
"""

import requests
import json
from typing import List, Dict, Any, Optional
from datetime import datetime
import sys
from pathlib import Path

# Add parent directory to path for imports
sys.path.append(str(Path(__file__).parent.parent))

from scrapers.schemas import Contact


class TwentyCRMSync:
    """
    Synchronizes contact data with Twenty CRM.
    """
    
    def __init__(self, api_url: str = "http://localhost:3000/graphql", api_token: Optional[str] = None):
        """
        Initialize Twenty CRM sync client.
        
        Args:
            api_url: Twenty CRM GraphQL API URL
            api_token: Authentication token (get from Twenty CRM settings)
        """
        self.api_url = api_url
        self.api_token = api_token
        self.headers = {
            "Content-Type": "application/json",
        }
        if api_token:
            self.headers["Authorization"] = f"Bearer {api_token}"
    
    def _execute_graphql(self, query: str, variables: Optional[Dict] = None) -> Dict[str, Any]:
        """
        Execute a GraphQL query/mutation.
        
        Args:
            query: GraphQL query/mutation string
            variables: Variables for the query
            
        Returns:
            Response data
        """
        payload = {
            "query": query,
            "variables": variables or {}
        }
        
        try:
            response = requests.post(
                self.api_url,
                headers=self.headers,
                json=payload,
                timeout=30
            )
            response.raise_for_status()
            
            result = response.json()
            
            if "errors" in result:
                print(f"❌ GraphQL errors: {result['errors']}")
                return {"error": result["errors"]}
            
            return result.get("data", {})
            
        except requests.exceptions.RequestException as e:
            print(f"❌ Request failed: {e}")
            return {"error": str(e)}
    
    def create_person(self, contact: Contact) -> Optional[Dict[str, Any]]:
        """
        Create a person in Twenty CRM from a Contact.
        
        Args:
            contact: Contact object from Apollo scraper
            
        Returns:
            Created person data or None if failed
        """
        # Split name into first and last name
        name_parts = contact.name.split(" ", 1) if contact.name else ["", ""]
        first_name = name_parts[0]
        last_name = name_parts[1] if len(name_parts) > 1 else ""
        
        # Build mutation
        mutation = """
        mutation CreatePerson($data: PersonCreateInput!) {
            createPerson(data: $data) {
                id
                name {
                    firstName
                    lastName
                }
                emails {
                    primaryEmail
                }
                phones {
                    primaryPhoneNumber
                }
                jobTitle
                city
                linkedinLink {
                    primaryLinkUrl
                }
                companyId
                createdAt
            }
        }
        """
        
        # Build variables
        variables = {
            "data": {
                "name": {
                    "firstName": first_name,
                    "lastName": last_name
                },
                "jobTitle": contact.title or "",
                "city": contact.city or "",
            }
        }
        
        # Add email if available
        if contact.email:
            variables["data"]["emails"] = {
                "primaryEmail": contact.email
            }
        
        # Add phone if available
        if contact.phone:
            # Clean phone number
            phone_clean = contact.phone.replace("+", "").replace("-", "").replace(" ", "")
            variables["data"]["phones"] = {
                "primaryPhoneNumber": phone_clean,
                "primaryPhoneCountryCode": "US",  # Default to US
                "primaryPhoneCallingCode": "+1"
            }
        
        # Add LinkedIn URL if available
        if contact.linkedin_url:
            variables["data"]["linkedinLink"] = {
                "primaryLinkUrl": contact.linkedin_url,
                "primaryLinkLabel": "LinkedIn"
            }
        
        # Execute mutation
        result = self._execute_graphql(mutation, variables)
        
        if "error" in result:
            print(f"❌ Failed to create person: {contact.name}")
            return None
        
        person = result.get("createPerson")
        if person:
            print(f"✅ Created person: {contact.name} (ID: {person['id']})")
        
        return person
    
    def create_people_batch(self, contacts: List[Contact]) -> List[Dict[str, Any]]:
        """
        Create multiple people in Twenty CRM.
        
        Args:
            contacts: List of Contact objects
            
        Returns:
            List of created person data
        """
        # Build mutation for batch creation
        mutation = """
        mutation CreatePeople($data: [PersonCreateInput!]!) {
            createPeople(data: $data) {
                id
                name {
                    firstName
                    lastName
                }
                emails {
                    primaryEmail
                }
                jobTitle
                city
                linkedinLink {
                    primaryLinkUrl
                }
                createdAt
            }
        }
        """
        
        # Build data array
        people_data = []
        for contact in contacts:
            name_parts = contact.name.split(" ", 1) if contact.name else ["", ""]
            first_name = name_parts[0]
            last_name = name_parts[1] if len(name_parts) > 1 else ""
            
            person_data = {
                "name": {
                    "firstName": first_name,
                    "lastName": last_name
                },
                "jobTitle": contact.title or "",
                "city": contact.city or "",
            }
            
            if contact.email:
                person_data["emails"] = {
                    "primaryEmail": contact.email
                }
            
            if contact.phone:
                phone_clean = contact.phone.replace("+", "").replace("-", "").replace(" ", "")
                person_data["phones"] = {
                    "primaryPhoneNumber": phone_clean,
                    "primaryPhoneCountryCode": "US",
                    "primaryPhoneCallingCode": "+1"
                }
            
            if contact.linkedin_url:
                person_data["linkedinLink"] = {
                    "primaryLinkUrl": contact.linkedin_url,
                    "primaryLinkLabel": "LinkedIn"
                }
            
            people_data.append(person_data)
        
        # Execute mutation
        variables = {"data": people_data}
        result = self._execute_graphql(mutation, variables)
        
        if "error" in result:
            print(f"❌ Failed to create people batch")
            return []
        
        people = result.get("createPeople", [])
        print(f"✅ Created {len(people)} people in Twenty CRM")
        
        return people
    
    def search_people(self, query: Optional[str] = None, limit: int = 50) -> List[Dict[str, Any]]:
        """
        Search for people in Twenty CRM.
        
        Args:
            query: Search query
            limit: Maximum number of results
            
        Returns:
            List of people
        """
        graphql_query = """
        query SearchPeople($filter: PersonFilterInput, $limit: Int) {
            people(filter: $filter, limit: $limit) {
                edges {
                    node {
                        id
                        name {
                            firstName
                            lastName
                        }
                        emails {
                            primaryEmail
                        }
                        phones {
                            primaryPhoneNumber
                        }
                        jobTitle
                        city
                        linkedinLink {
                            primaryLinkUrl
                        }
                        companyId
                        createdAt
                    }
                }
            }
        }
        """
        
        variables = {"limit": limit}
        if query:
            variables["filter"] = {
                "name": {
                    "firstName": {"ilike": f"%{query}%"}
                }
            }
        
        result = self._execute_graphql(graphql_query, variables)
        
        if "error" in result:
            print(f"❌ Failed to search people")
            return []
        
        edges = result.get("people", {}).get("edges", [])
        people = [edge["node"] for edge in edges]
        
        return people


def sync_apollo_to_twenty(contacts: List[Contact], api_token: Optional[str] = None) -> bool:
    """
    Sync Apollo scraper contacts to Twenty CRM.
    
    Args:
        contacts: List of contacts from Apollo scraper
        api_token: Twenty CRM API token
        
    Returns:
        True if successful, False otherwise
    """
    print(f"\n🔄 Syncing {len(contacts)} contacts to Twenty CRM...")
    
    sync = TwentyCRMSync(api_token=api_token)
    
    # Create people in batches of 10
    batch_size = 10
    total_created = 0
    
    for i in range(0, len(contacts), batch_size):
        batch = contacts[i:i + batch_size]
        created = sync.create_people_batch(batch)
        total_created += len(created)
    
    print(f"\n✅ Successfully synced {total_created}/{len(contacts)} contacts to Twenty CRM!")
    return total_created > 0


if __name__ == "__main__":
    # Test the sync
    print("Twenty CRM Sync Service")
    print("=" * 50)
    
    # Load mock contacts
    mock_file = Path(__file__).parent.parent / "exports" / "demo_contacts.json"
    
    if mock_file.exists():
        with open(mock_file, 'r') as f:
            data = json.load(f)
            contacts = [Contact(**c) for c in data]
        
        print(f"Loaded {len(contacts)} contacts from mock data")
        
        # Sync to Twenty CRM (requires Twenty CRM to be running)
        api_token = input("Enter your Twenty CRM API token (or press Enter to skip): ").strip()
        
        if api_token:
            sync_apollo_to_twenty(contacts[:5], api_token)  # Test with 5 contacts
        else:
            print("⚠️  No API token provided. Skipping sync.")
            print("To get an API token:")
            print("1. Start Twenty CRM: cd CRM/twenty && yarn start")
            print("2. Login to Twenty CRM")
            print("3. Go to Settings > API Keys")
            print("4. Create a new API key")
    else:
        print(f"❌ Mock data file not found: {mock_file}")

