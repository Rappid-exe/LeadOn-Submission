"""
LinkedIn Automation Service - Integrates LinkedIn bot with CRM

Provides:
- Like posts for contacts
- Send connection requests
- Track automation status in database
"""

import sys
from pathlib import Path
from typing import List, Dict, Optional
from datetime import datetime
import logging

# Add parent directory to path to import linkedin_automation
parent_dir = Path(__file__).parent.parent.parent
sys.path.append(str(parent_dir))

from linkedin_automation.linkedin_bot import LinkedInBot
from database.db_manager import DatabaseManager
from database.models import Contact

logger = logging.getLogger(__name__)


class LinkedInAutomationService:
    """Service for running LinkedIn automation on CRM contacts"""
    
    def __init__(self, db_manager: DatabaseManager):
        """
        Initialize LinkedIn automation service
        
        Args:
            db_manager: Database manager instance
        """
        self.db = db_manager
        self.bot = None
        self.is_connected = False
    
    def connect(self, headless: bool = True) -> bool:
        """
        Connect to LinkedIn
        
        Args:
            headless: Run browser in headless mode
            
        Returns:
            True if connected successfully
        """
        try:
            logger.info("🤖 Initializing LinkedIn bot...")
            self.bot = LinkedInBot(headless=headless)
            
            if self.bot.start():
                self.is_connected = True
                logger.info("✅ LinkedIn bot connected")
                return True
            else:
                logger.error("❌ Failed to connect LinkedIn bot")
                return False
                
        except Exception as e:
            logger.error(f"❌ Error connecting LinkedIn bot: {e}")
            return False
    
    def disconnect(self):
        """Disconnect from LinkedIn"""
        if self.bot:
            self.bot.stop()
            self.is_connected = False
            logger.info("🛑 LinkedIn bot disconnected")
    
    def run_campaign(
        self,
        contact_ids: List[int],
        actions: List[str] = ["like_posts", "send_connection"],
        like_count: int = 3,
        connection_message: Optional[str] = None
    ) -> Dict:
        """
        Run LinkedIn automation campaign for multiple contacts
        
        Args:
            contact_ids: List of contact IDs from database
            actions: List of actions to perform (like_posts, send_connection)
            like_count: Number of posts to like
            connection_message: Optional message for connection request
            
        Returns:
            Campaign results dictionary
        """
        if not self.is_connected:
            if not self.connect():
                return {
                    "success": False,
                    "error": "Failed to connect to LinkedIn"
                }
        
        results = {
            "total": len(contact_ids),
            "successful": 0,
            "failed": 0,
            "skipped": 0,
            "details": []
        }
        
        # Get contacts from database
        session = self.db.get_session()
        
        try:
            for contact_id in contact_ids:
                contact = session.query(Contact).filter(Contact.id == contact_id).first()
                
                if not contact:
                    logger.warning(f"⚠️  Contact {contact_id} not found")
                    results["skipped"] += 1
                    continue
                
                if not contact.linkedin_url:
                    logger.warning(f"⚠️  Contact {contact.name} has no LinkedIn URL")
                    results["skipped"] += 1
                    results["details"].append({
                        "contact_id": contact_id,
                        "name": contact.name,
                        "status": "skipped",
                        "reason": "No LinkedIn URL"
                    })
                    continue
                
                # Run automation for this contact
                logger.info(f"\n{'='*60}")
                logger.info(f"Processing: {contact.name} ({contact.title} at {contact.company_name})")
                logger.info(f"{'='*60}")
                
                contact_result = self._run_contact_automation(
                    contact=contact,
                    actions=actions,
                    like_count=like_count,
                    connection_message=connection_message
                )
                
                # Update database
                self._update_contact_status(session, contact, contact_result)
                
                # Add to results
                results["details"].append(contact_result)
                
                if contact_result["status"] == "success":
                    results["successful"] += 1
                else:
                    results["failed"] += 1
            
            session.commit()
            
        except Exception as e:
            logger.error(f"❌ Campaign error: {e}")
            session.rollback()
            results["error"] = str(e)
        finally:
            session.close()
        
        return results
    
    def _run_contact_automation(
        self,
        contact: Contact,
        actions: List[str],
        like_count: int,
        connection_message: Optional[str]
    ) -> Dict:
        """
        Run automation for a single contact
        
        Returns:
            Result dictionary with status and details
        """
        result = {
            "contact_id": contact.id,
            "name": contact.name,
            "linkedin_url": contact.linkedin_url,
            "status": "success",
            "actions_completed": [],
            "actions_failed": [],
            "errors": []
        }
        
        try:
            # Action 1: Like posts
            if "like_posts" in actions:
                logger.info(f"👍 Liking {like_count} posts...")
                like_result = self.bot.like_posts(contact.linkedin_url, max_posts=like_count)
                
                if like_result["status"] == "success":
                    result["actions_completed"].append(f"liked_{like_result['posts_liked']}_posts")
                    logger.info(f"✅ Liked {like_result['posts_liked']} posts")
                else:
                    result["actions_failed"].append("like_posts")
                    result["errors"].extend(like_result.get("errors", []))
                    logger.warning(f"⚠️  Failed to like posts")
            
            # Action 2: Send connection request
            if "send_connection" in actions:
                logger.info(f"🤝 Sending connection request...")
                
                # Use provided message or default
                message = connection_message
                if not message:
                    # Simple default message
                    message = f"Hi {contact.name.split()[0]}, I'd like to connect with you on LinkedIn."
                
                connect_result = self.bot.connect(contact.linkedin_url, message)
                
                if connect_result["status"] == "success":
                    result["actions_completed"].append("connection_sent")
                    result["connection_message"] = message
                    logger.info(f"✅ Connection request sent")
                elif connect_result["status"] == "already_connected":
                    result["actions_completed"].append("already_connected")
                    logger.info(f"ℹ️  Already connected")
                else:
                    result["actions_failed"].append("send_connection")
                    result["errors"].extend(connect_result.get("errors", []))
                    logger.warning(f"⚠️  Failed to send connection")
            
            # Determine overall status
            if result["actions_failed"]:
                result["status"] = "partial" if result["actions_completed"] else "failed"
            
        except Exception as e:
            result["status"] = "failed"
            result["errors"].append(str(e))
            logger.error(f"❌ Error processing contact: {e}")
        
        return result
    
    def _update_contact_status(self, session, contact: Contact, result: Dict):
        """Update contact record with automation results"""
        try:
            # Update workflow stage
            if "connection_sent" in result["actions_completed"]:
                contact.workflow_stage = "reaching_out"
                contact.last_action = "Sent LinkedIn connection request"
                contact.last_action_date = datetime.utcnow()
            elif "already_connected" in result["actions_completed"]:
                contact.workflow_stage = "connected"
            
            # Update automation notes
            notes = []
            if result["actions_completed"]:
                notes.append(f"Completed: {', '.join(result['actions_completed'])}")
            if result["actions_failed"]:
                notes.append(f"Failed: {', '.join(result['actions_failed'])}")
            if result.get("errors"):
                notes.append(f"Errors: {'; '.join(result['errors'][:2])}")  # First 2 errors
            
            if notes:
                existing_notes = contact.automation_notes or ""
                new_note = f"[{datetime.utcnow().strftime('%Y-%m-%d %H:%M')}] {' | '.join(notes)}"
                contact.automation_notes = f"{existing_notes}\n{new_note}".strip()
            
            logger.info(f"✅ Updated contact status in database")
            
        except Exception as e:
            logger.error(f"⚠️  Failed to update contact status: {e}")


def test_service():
    """Test the LinkedIn automation service"""
    from database.db_manager import get_db_manager
    
    print("=" * 70)
    print("LinkedIn Automation Service Test")
    print("=" * 70)
    print()
    
    # Initialize
    db = get_db_manager()
    service = LinkedInAutomationService(db)
    
    # Get a contact to test with
    session = db.get_session()
    contact = session.query(Contact).filter(Contact.linkedin_url.isnot(None)).first()
    session.close()
    
    if not contact:
        print("❌ No contacts with LinkedIn URLs found")
        print("   Add some contacts first using the CRM search")
        return
    
    print(f"Testing with contact: {contact.name}")
    print(f"LinkedIn: {contact.linkedin_url}")
    print()
    
    # Run campaign
    print("Starting campaign...")
    results = service.run_campaign(
        contact_ids=[contact.id],
        actions=["like_posts", "send_connection"],
        like_count=2,
        connection_message="Hi! I'd like to connect with you."
    )
    
    # Display results
    print()
    print("=" * 70)
    print("RESULTS")
    print("=" * 70)
    print()
    print(f"Total: {results['total']}")
    print(f"Successful: {results['successful']}")
    print(f"Failed: {results['failed']}")
    print(f"Skipped: {results['skipped']}")
    
    if results.get('details'):
        print()
        print("Details:")
        for detail in results['details']:
            print(f"\n  {detail['name']}:")
            print(f"    Status: {detail['status']}")
            print(f"    Completed: {detail['actions_completed']}")
            if detail['actions_failed']:
                print(f"    Failed: {detail['actions_failed']}")
    
    # Cleanup
    service.disconnect()


if __name__ == "__main__":
    test_service()
