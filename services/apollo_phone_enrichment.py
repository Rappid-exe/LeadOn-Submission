"""
Apollo Phone Enrichment Service

Uses Apollo.io API credits to enrich contacts with phone numbers.
This is useful for Telegram campaigns where phone numbers are required.
"""

import os
import logging
import requests
from typing import List, Dict, Optional
from dotenv import load_dotenv

load_dotenv()
logger = logging.getLogger(__name__)


class ApolloPhoneEnrichment:
    """Service to enrich contacts with phone numbers using Apollo API"""
    
    def __init__(self, api_key: Optional[str] = None):
        """
        Initialize Apollo phone enrichment service
        
        Args:
            api_key: Apollo API key (defaults to env variable)
        """
        self.api_key = api_key or os.getenv('APOLLO_API_KEY')
        self.base_url = "https://api.apollo.io/v1"
        
        if not self.api_key:
            logger.warning("⚠️  Apollo API key not found. Phone enrichment will not work.")
    
    def enrich_contact_phone(self, contact: Dict) -> Dict:
        """
        Enrich a single contact with phone number from Apollo
        
        Args:
            contact: Contact dict with 'email' or 'first_name', 'last_name', 'company'
            
        Returns:
            Dict with enrichment result:
            {
                'success': bool,
                'phone': str or None,
                'credits_used': int,
                'error': str or None
            }
        """
        if not self.api_key:
            return {
                'success': False,
                'phone': None,
                'credits_used': 0,
                'error': 'Apollo API key not configured'
            }
        
        # If contact already has phone, skip
        if contact.get('phone'):
            return {
                'success': True,
                'phone': contact['phone'],
                'credits_used': 0,
                'error': None
            }
        
        try:
            # Try to find person by email first (most accurate)
            if contact.get('email'):
                result = self._search_by_email(contact['email'])
                if result['success']:
                    return result
            
            # Fallback: search by name and company
            if contact.get('first_name') and contact.get('company'):
                result = self._search_by_name_company(
                    first_name=contact['first_name'],
                    last_name=contact.get('last_name', ''),
                    company=contact['company']
                )
                return result
            
            return {
                'success': False,
                'phone': None,
                'credits_used': 0,
                'error': 'Insufficient contact information (need email or name+company)'
            }
            
        except Exception as e:
            logger.error(f"Error enriching contact: {e}")
            return {
                'success': False,
                'phone': None,
                'credits_used': 0,
                'error': str(e)
            }
    
    def _search_by_email(self, email: str) -> Dict:
        """Search Apollo for person by email"""
        try:
            url = f"{self.base_url}/people/match"
            headers = {
                'Content-Type': 'application/json',
                'Cache-Control': 'no-cache',
                'X-Api-Key': self.api_key
            }
            
            data = {
                'email': email,
                'reveal_personal_emails': True,
                'reveal_phone_number': True
            }
            
            response = requests.post(url, json=data, headers=headers, timeout=10)
            
            if response.status_code == 200:
                result = response.json()
                person = result.get('person', {})
                phone = person.get('phone_numbers', [])
                
                if phone and len(phone) > 0:
                    # Get first phone number
                    phone_number = phone[0].get('raw_number') or phone[0].get('sanitized_number')
                    
                    logger.info(f"✅ Found phone for {email}: {phone_number}")
                    return {
                        'success': True,
                        'phone': phone_number,
                        'credits_used': 1,
                        'error': None
                    }
                else:
                    return {
                        'success': False,
                        'phone': None,
                        'credits_used': 1,
                        'error': 'No phone number found in Apollo'
                    }
            else:
                logger.error(f"Apollo API error: {response.status_code} - {response.text}")
                return {
                    'success': False,
                    'phone': None,
                    'credits_used': 0,
                    'error': f'Apollo API error: {response.status_code}'
                }
                
        except Exception as e:
            logger.error(f"Error searching by email: {e}")
            return {
                'success': False,
                'phone': None,
                'credits_used': 0,
                'error': str(e)
            }
    
    def _search_by_name_company(self, first_name: str, last_name: str, company: str) -> Dict:
        """Search Apollo for person by name and company"""
        try:
            url = f"{self.base_url}/people/search"
            headers = {
                'Content-Type': 'application/json',
                'Cache-Control': 'no-cache',
                'X-Api-Key': self.api_key
            }
            
            data = {
                'first_name': first_name,
                'last_name': last_name,
                'organization_names': [company],
                'page': 1,
                'per_page': 1,
                'reveal_phone_number': True
            }
            
            response = requests.post(url, json=data, headers=headers, timeout=10)
            
            if response.status_code == 200:
                result = response.json()
                people = result.get('people', [])
                
                if people and len(people) > 0:
                    person = people[0]
                    phone = person.get('phone_numbers', [])
                    
                    if phone and len(phone) > 0:
                        phone_number = phone[0].get('raw_number') or phone[0].get('sanitized_number')
                        
                        logger.info(f"✅ Found phone for {first_name} {last_name} at {company}: {phone_number}")
                        return {
                            'success': True,
                            'phone': phone_number,
                            'credits_used': 1,
                            'error': None
                        }
                    else:
                        return {
                            'success': False,
                            'phone': None,
                            'credits_used': 1,
                            'error': 'No phone number found in Apollo'
                        }
                else:
                    return {
                        'success': False,
                        'phone': None,
                        'credits_used': 1,
                        'error': 'Person not found in Apollo'
                    }
            else:
                logger.error(f"Apollo API error: {response.status_code} - {response.text}")
                return {
                    'success': False,
                    'phone': None,
                    'credits_used': 0,
                    'error': f'Apollo API error: {response.status_code}'
                }
                
        except Exception as e:
            logger.error(f"Error searching by name/company: {e}")
            return {
                'success': False,
                'phone': None,
                'credits_used': 0,
                'error': str(e)
            }
    
    def enrich_contacts_batch(self, contacts: List[Dict]) -> Dict:
        """
        Enrich multiple contacts with phone numbers
        
        Args:
            contacts: List of contact dicts
            
        Returns:
            Dict with batch results:
            {
                'total': int,
                'enriched': int,
                'failed': int,
                'already_had_phone': int,
                'credits_used': int,
                'results': List[Dict]
            }
        """
        results = {
            'total': len(contacts),
            'enriched': 0,
            'failed': 0,
            'already_had_phone': 0,
            'credits_used': 0,
            'results': []
        }
        
        for contact in contacts:
            result = self.enrich_contact_phone(contact)
            
            if result['success']:
                if result['credits_used'] == 0:
                    results['already_had_phone'] += 1
                else:
                    results['enriched'] += 1
            else:
                results['failed'] += 1
            
            results['credits_used'] += result['credits_used']
            results['results'].append({
                'contact_id': contact.get('id'),
                'email': contact.get('email'),
                'phone': result['phone'],
                'success': result['success'],
                'error': result['error']
            })
        
        logger.info(f"📊 Batch enrichment complete: {results['enriched']} enriched, "
                   f"{results['failed']} failed, {results['credits_used']} credits used")
        
        return results

