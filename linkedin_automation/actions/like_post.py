import time
import random
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, NoSuchElementException


def like_recent_posts(driver, profile_url: str, max_posts: int = 3):
    """
    Navigate to a LinkedIn profile and like recent posts
    
    Args:
        driver: Selenium WebDriver instance
        profile_url: LinkedIn profile URL
        max_posts: Maximum number of posts to like
    
    Returns:
        dict: Action result with status and details
    """
    result = {
        "action": "like_posts",
        "profile_url": profile_url,
        "posts_liked": 0,
        "status": "failed",
        "errors": []
    }
    
    try:
        # Try going directly to recent activity page
        base_url = profile_url.rstrip('/')
        activity_url = f"{base_url}/recent-activity/all/"
        
        print(f"\n→ Navigating to activity page: {activity_url}")
        driver.get(activity_url)
        time.sleep(random.uniform(4, 6))
        
        # Scroll down to load posts
        for i in range(3):
            driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
            time.sleep(random.uniform(1, 2))
            print(f"Scrolled {i+1}/3 times to load posts")
        
        # Find like buttons - try multiple selectors
        like_buttons = []
        
        # Method 1: React button with aria-pressed false
        like_buttons = driver.find_elements(By.CSS_SELECTOR, "button[aria-label*='React'][aria-pressed='false']")
        print(f"Method 1 (React aria-pressed): Found {len(like_buttons)} buttons")
        
        # Method 2: Like button with aria-pressed false
        if not like_buttons:
            like_buttons = driver.find_elements(By.CSS_SELECTOR, "button[aria-label*='Like'][aria-pressed='false']")
            print(f"Method 2 (Like aria-pressed): Found {len(like_buttons)} buttons")
        
        # Method 3: Any reaction button
        if not like_buttons:
            like_buttons = driver.find_elements(By.CSS_SELECTOR, "button.react-button__trigger")
            print(f"Method 3 (react-button class): Found {len(like_buttons)} buttons")
        
        # Method 4: Look for SVG icons in buttons
        if not like_buttons:
            all_buttons = driver.find_elements(By.TAG_NAME, "button")
            for btn in all_buttons:
                aria_label = btn.get_attribute("aria-label") or ""
                if "like" in aria_label.lower() or "react" in aria_label.lower():
                    aria_pressed = btn.get_attribute("aria-pressed")
                    if aria_pressed == "false" or aria_pressed is None:
                        like_buttons.append(btn)
            print(f"Method 4 (manual search): Found {len(like_buttons)} buttons")
        
        # Method 5: Screenshot for debugging
        if not like_buttons:
            try:
                driver.save_screenshot("debug_no_posts.png")
                print("⚠ Saved screenshot to debug_no_posts.png")
            except:
                pass
        
        if not like_buttons:
            result["errors"].append("No posts found to like")
            print("✗ No unliked posts found after trying all methods")
            return result
        
        print(f"✓ Total like buttons found: {len(like_buttons)}")
        
        posts_to_like = min(len(like_buttons), max_posts)
        
        for i in range(posts_to_like):
            try:
                # Re-find buttons to avoid stale element
                like_buttons = driver.find_elements(By.CSS_SELECTOR, "button[aria-label*='React'][aria-pressed='false']")
                
                if i >= len(like_buttons):
                    break
                
                button = like_buttons[i]
                
                # Scroll to button
                driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", button)
                time.sleep(random.uniform(1, 2))
                
                # Use JavaScript click to avoid interception issues
                try:
                    driver.execute_script("arguments[0].click();", button)
                    result["posts_liked"] += 1
                    print(f"✓ Liked post {i + 1}/{posts_to_like}")
                except:
                    # Fallback to regular click
                    button.click()
                    result["posts_liked"] += 1
                    print(f"✓ Liked post {i + 1}/{posts_to_like}")
                
                # Human-like delay between likes
                time.sleep(random.uniform(5, 10))
                
            except Exception as e:
                result["errors"].append(f"Failed to like post {i + 1}: {str(e)}")
                print(f"✗ Error liking post {i + 1}: {e}")
        
        if result["posts_liked"] > 0:
            result["status"] = "success"
        
    except Exception as e:
        result["errors"].append(f"General error: {str(e)}")
        print(f"✗ Error in like_recent_posts: {e}")
    
    return result
