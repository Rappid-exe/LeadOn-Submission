import time
import random
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, NoSuchElementException


def endorse_skills(driver, profile_url: str, max_skills: int = 3):
    """
    Endorse skills on a LinkedIn profile
    
    Args:
        driver: Selenium WebDriver instance
        profile_url: LinkedIn profile URL
        max_skills: Maximum number of skills to endorse
    
    Returns:
        dict: Action result with status and details
    """
    result = {
        "action": "endorse_skills",
        "profile_url": profile_url,
        "skills_endorsed": 0,
        "status": "failed",
        "errors": []
    }
    
    try:
        print(f"\n→ Navigating to profile: {profile_url}")
        driver.get(profile_url)
        time.sleep(random.uniform(3, 5))
        
        # Scroll to skills section
        driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
        time.sleep(random.uniform(2, 3))
        
        # Look for skills section
        try:
            skills_section = WebDriverWait(driver, 10).until(
                EC.presence_of_element_located((By.XPATH, "//section[contains(@id, 'skills')]"))
            )
            driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", skills_section)
            time.sleep(random.uniform(2, 3))
        except TimeoutException:
            result["errors"].append("Skills section not found")
            print("✗ Skills section not found")
            return result
        
        # Find endorse buttons (+ icon buttons)
        endorse_buttons = driver.find_elements(By.XPATH, "//button[contains(@aria-label, 'Endorse')]")
        
        if not endorse_buttons:
            result["errors"].append("No skills available to endorse")
            print("✗ No endorsable skills found")
            return result
        
        skills_to_endorse = min(len(endorse_buttons), max_skills)
        
        for i in range(skills_to_endorse):
            try:
                # Re-find buttons to avoid stale element
                endorse_buttons = driver.find_elements(By.XPATH, "//button[contains(@aria-label, 'Endorse')]")
                
                if i >= len(endorse_buttons):
                    break
                
                button = endorse_buttons[i]
                driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", button)
                time.sleep(random.uniform(1, 2))
                
                button.click()
                result["skills_endorsed"] += 1
                print(f"✓ Endorsed skill {i + 1}/{skills_to_endorse}")
                
                # Human-like delay between endorsements
                time.sleep(random.uniform(3, 6))
                
            except Exception as e:
                result["errors"].append(f"Failed to endorse skill {i + 1}: {str(e)}")
                print(f"✗ Error endorsing skill {i + 1}: {e}")
        
        if result["skills_endorsed"] > 0:
            result["status"] = "success"
        
    except Exception as e:
        result["errors"].append(f"General error: {str(e)}")
        print(f"✗ Error in endorse_skills: {e}")
    
    return result
