import os
import time
import random
from dotenv import load_dotenv
from .session_manager import SessionManager
from .actions.like_post import like_recent_posts
from .actions.endorse_skills import endorse_skills
from .actions.send_connection import send_connection_request


class LinkedInBot:
    """Main LinkedIn automation bot"""
    
    def __init__(self, email: str = None, password: str = None, headless: bool = False):
        load_dotenv()
        
        self.email = email or os.getenv("LINKEDIN_EMAIL")
        self.password = password or os.getenv("LINKEDIN_PASSWORD")
        
        if not self.email or not self.password:
            raise ValueError("LinkedIn credentials not provided")
        
        self.session_manager = SessionManager(self.email, self.password, headless)
        self.driver = None
        self.actions_performed = []
    
    def start(self):
        """Start the bot session"""
        print("=" * 60)
        print("LinkedIn Automation Bot Starting...")
        print("=" * 60)
        
        success = self.session_manager.start_session()
        if success:
            self.driver = self.session_manager.driver
            return True
        return False
    
    def like_posts(self, profile_url: str, max_posts: int = 3):
        """Like recent posts on a profile"""
        if not self.driver:
            raise RuntimeError("Bot not started. Call start() first.")
        
        result = like_recent_posts(self.driver, profile_url, max_posts)
        self.actions_performed.append(result)
        
        # Random delay after action
        time.sleep(random.uniform(5, 15))
        return result
    
    def endorse(self, profile_url: str, max_skills: int = 3):
        """Endorse skills on a profile"""
        if not self.driver:
            raise RuntimeError("Bot not started. Call start() first.")
        
        result = endorse_skills(self.driver, profile_url, max_skills)
        self.actions_performed.append(result)
        
        # Random delay after action
        time.sleep(random.uniform(5, 15))
        return result
    
    def connect(self, profile_url: str, message: str = None):
        """Send connection request to a profile"""
        if not self.driver:
            raise RuntimeError("Bot not started. Call start() first.")
        
        result = send_connection_request(self.driver, profile_url, message)
        self.actions_performed.append(result)
        
        # Random delay after action
        time.sleep(random.uniform(10, 20))
        return result
    
    def run_engagement_sequence(self, profile_url: str, include_connection: bool = False, connection_message: str = None):
        """
        Run a full engagement sequence on a profile:
        1. Like posts
        2. Endorse skills
        3. (Optional) Send connection request
        """
        print(f"\n{'=' * 60}")
        print(f"Starting engagement sequence for: {profile_url}")
        print(f"{'=' * 60}")
        
        results = []
        
        # Step 1: Like posts
        print("\n[1/3] Liking recent posts...")
        like_result = self.like_posts(profile_url, max_posts=2)
        results.append(like_result)
        
        # Step 2: Endorse skills
        print("\n[2/3] Endorsing skills...")
        endorse_result = self.endorse(profile_url, max_skills=3)
        results.append(endorse_result)
        
        # Step 3: Send connection (optional)
        if include_connection:
            print("\n[3/3] Sending connection request...")
            connect_result = self.connect(profile_url, connection_message)
            results.append(connect_result)
        else:
            print("\n[3/3] Skipping connection request")
        
        print(f"\n{'=' * 60}")
        print("Engagement sequence completed!")
        print(f"{'=' * 60}")
        
        return results
    
    def get_action_summary(self):
        """Get summary of all actions performed"""
        summary = {
            "total_actions": len(self.actions_performed),
            "successful_actions": sum(1 for a in self.actions_performed if a["status"] == "success"),
            "failed_actions": sum(1 for a in self.actions_performed if a["status"] == "failed"),
            "actions": self.actions_performed
        }
        return summary
    
    def stop(self):
        """Stop the bot and close browser"""
        print("\n" + "=" * 60)
        print("Stopping bot...")
        
        summary = self.get_action_summary()
        print(f"Total actions: {summary['total_actions']}")
        print(f"Successful: {summary['successful_actions']}")
        print(f"Failed: {summary['failed_actions']}")
        
        self.session_manager.close()
        print("=" * 60)


if __name__ == "__main__":
    # Example usage
    bot = LinkedInBot(headless=False)
    
    try:
        if bot.start():
            # Example: Engage with a profile
            profile = "https://www.linkedin.com/in/example-profile/"
            
            # Option 1: Run full sequence
            bot.run_engagement_sequence(
                profile_url=profile,
                include_connection=True,
                connection_message="Hi! I'd love to connect and learn more about your work."
            )
            
            # Option 2: Individual actions
            # bot.like_posts(profile, max_posts=3)
            # bot.endorse(profile, max_skills=3)
            # bot.connect(profile, "Hi! Let's connect!")
            
    finally:
        bot.stop()
