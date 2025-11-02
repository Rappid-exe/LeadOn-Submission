import time
import random
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, NoSuchElementException


def send_connection_request(driver, profile_url: str, message: str = None):
    """
    Send a connection request to a LinkedIn profile
    
    Args:
        driver: Selenium WebDriver instance
        profile_url: LinkedIn profile URL
        message: Optional personalized message (max 300 chars)
    
    Returns:
        dict: Action result with status and details
    """
    result = {
        "action": "send_connection",
        "profile_url": profile_url,
        "status": "failed",
        "message_sent": False,
        "errors": []
    }
    
    try:
        print(f"\n→ Navigating to profile: {profile_url}")
        driver.get(profile_url)
        time.sleep(random.uniform(3, 5))
        
        # Look for "Connect" button - try multiple approaches
        connect_clicked = False
        
        # Method 1: Try direct Connect button
        try:
            connect_button = driver.find_element(By.XPATH, "//button[contains(@aria-label, 'Invite') or contains(., 'Connect')]")
            driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", connect_button)
            time.sleep(random.uniform(1, 2))
            connect_button.click()
            connect_clicked = True
            print("✓ Clicked Connect button (direct)")
            time.sleep(random.uniform(2, 3))
        except:
            print("⚠ Direct Connect button not found, trying More menu...")
        
        # Method 2: Try "More" dropdown (three dots)
        if not connect_clicked:
            try:
                # Find More button - try multiple selectors
                more_button = None
                try:
                    more_button = driver.find_element(By.XPATH, "//button[contains(text(), 'More')]")
                except:
                    try:
                        more_button = driver.find_element(By.XPATH, "//button[@aria-label='More']")
                    except:
                        try:
                            more_button = driver.find_element(By.XPATH, "//button[contains(@aria-label, 'More actions')]")
                        except:
                            # Try finding by class
                            buttons = driver.find_elements(By.TAG_NAME, "button")
                            for btn in buttons:
                                if "more" in btn.text.lower():
                                    more_button = btn
                                    break
                
                if more_button:
                    # Scroll to button and wait
                    driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", more_button)
                    time.sleep(random.uniform(1, 2))
                    
                    # Click using JavaScript to avoid interactability issues
                    driver.execute_script("arguments[0].click();", more_button)
                    print("✓ Clicked More menu")
                    time.sleep(random.uniform(2, 4))
                    
                    # Wait for dropdown to appear and find Connect option
                    connect_option = None
                    
                    # Debug: Print all dropdown items
                    try:
                        all_dropdown_items = driver.find_elements(By.XPATH, "//div[contains(@class, 'artdeco-dropdown')]//span")
                        print(f"Found {len(all_dropdown_items)} items in dropdown:")
                        for item in all_dropdown_items[:10]:  # Print first 10
                            text = item.text.strip()
                            if text:
                                print(f"  - '{text}'")
                    except:
                        pass
                    
                    try:
                        # Method 1: Look for exact "Connect" text
                        connect_option = driver.find_element(By.XPATH, "//div[contains(@class, 'artdeco-dropdown__content')]//span[text()='Connect']")
                        print("Found Connect using method 1")
                    except:
                        try:
                            # Method 2: Look for contains Connect
                            connect_option = driver.find_element(By.XPATH, "//div[contains(@class, 'artdeco-dropdown')]//span[contains(text(), 'Connect')]")
                            print("Found Connect using method 2")
                        except:
                            try:
                                # Method 3: Look in list items
                                connect_option = driver.find_element(By.XPATH, "//li//span[text()='Connect']")
                                print("Found Connect using method 3")
                            except:
                                try:
                                    # Method 4: Search all visible elements
                                    all_elements = driver.find_elements(By.XPATH, "//*[text()='Connect']")
                                    for elem in all_elements:
                                        if elem.is_displayed():
                                            connect_option = elem
                                            print("Found Connect using method 4")
                                            break
                                except:
                                    pass
                    
                    if connect_option:
                        # Scroll to option and click
                        driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", connect_option)
                        time.sleep(random.uniform(0.5, 1))
                        driver.execute_script("arguments[0].click();", connect_option)
                        connect_clicked = True
                        print("✓ Clicked Connect from More menu")
                        time.sleep(random.uniform(2, 3))
                    else:
                        print("⚠ Could not find Connect option in dropdown")
                else:
                    print("⚠ Could not find More button")
            except Exception as e:
                print(f"⚠ Error with More menu: {e}")
        
        # If still not clicked, save screenshot and return
        if not connect_clicked:
            try:
                driver.save_screenshot("debug_no_connect.png")
                print("⚠ Saved screenshot to debug_no_connect.png")
            except:
                pass
            result["errors"].append("Connect button not found - may already be connected")
            print("✗ Connect button not found after trying all methods")
            return result
        
        # Wait for connection modal to appear
        print("Waiting for connection modal...")
        time.sleep(random.uniform(4, 6))
        
        # Check if modal appeared - look for the specific invitation modal
        modal_appeared = False
        try:
            # Look for the "Add a note to your invitation?" heading or the specific buttons
            try:
                # Check for "Send without a note" button - this is the key indicator
                send_without_note_btn = driver.find_element(By.XPATH, "//button[contains(text(), 'Send without a note')]")
                if send_without_note_btn.is_displayed():
                    modal_appeared = True
                    print("✓ Found invitation modal (detected 'Send without a note' button)")
            except:
                pass
            
            if not modal_appeared:
                # Try looking for "Add a note" button
                try:
                    add_note_btn = driver.find_element(By.XPATH, "//button[contains(text(), 'Add a note')]")
                    if add_note_btn.is_displayed():
                        modal_appeared = True
                        print("✓ Found invitation modal (detected 'Add a note' button)")
                except:
                    pass
            
            if not modal_appeared:
                # Try looking for the modal heading
                try:
                    heading = driver.find_element(By.XPATH, "//*[contains(text(), 'Add a note to your invitation')]")
                    if heading.is_displayed():
                        modal_appeared = True
                        print("✓ Found invitation modal (detected heading)")
                except:
                    pass
            
            # Debug: Print all visible buttons
            if modal_appeared:
                all_buttons = driver.find_elements(By.TAG_NAME, "button")
                print("Visible buttons in page:")
                for btn in all_buttons:
                    if btn.is_displayed():
                        text = btn.text.strip()
                        if text:
                            print(f"  - '{text}'")
                    
        except Exception as e:
            print(f"Debug error: {e}")
        
        # If no modal appeared, check if already connected
        if not modal_appeared:
            print("⚠ No modal appeared - checking if already connected...")
            
            # Debug: Save screenshot and print page source
            try:
                driver.save_screenshot("debug_after_connect_click.png")
                print("📸 Saved screenshot: debug_after_connect_click.png")
            except:
                pass
            
            # Debug: Print all buttons on page
            print("\n🔍 Debugging - All buttons on page:")
            try:
                all_buttons = driver.find_elements(By.TAG_NAME, "button")
                for btn in all_buttons[:20]:  # First 20 buttons
                    try:
                        if btn.is_displayed():
                            text = btn.text.strip()
                            aria_label = btn.get_attribute("aria-label")
                            if text or aria_label:
                                print(f"  Button: text='{text}' aria-label='{aria_label}'")
                    except:
                        pass
            except Exception as e:
                print(f"  Error listing buttons: {e}")
            
            try:
                pending_button = driver.find_element(By.XPATH, "//button[contains(@aria-label, 'Pending')]")
                if pending_button:
                    # Check if this is a NEW pending (we just sent it) or OLD pending
                    # If we clicked Connect and now see Pending, it means we just sent it!
                    if connect_clicked:
                        result["status"] = "success"
                        print("✓ Connection request sent! (Button changed to Pending)")
                        return result
                    else:
                        result["status"] = "already_connected"
                        result["errors"].append("Already sent connection request (Pending)")
                        print("⚠ Connection already pending")
                        return result
            except:
                print("  No 'Pending' button found")
            
            result["status"] = "failed"
            result["errors"].append("No confirmation modal appeared")
            print("✗ No modal appeared after clicking Connect")
            return result
        
        # Now handle the modal - check if we want to add a note
        if message and modal_appeared:
            try:
                # Look for "Add a note" button - try multiple selectors
                add_note_button = None
                try:
                    add_note_button = driver.find_element(By.XPATH, "//button[contains(@aria-label, 'Add a note')]")
                except:
                    try:
                        add_note_button = driver.find_element(By.XPATH, "//button[contains(text(), 'Add a note')]")
                    except:
                        pass
                
                if add_note_button:
                    driver.execute_script("arguments[0].click();", add_note_button)
                    print("✓ Clicked 'Add a note'")
                    time.sleep(random.uniform(1, 2))
                    
                    # Type message - try multiple selectors
                    message_field = None
                    try:
                        message_field = driver.find_element(By.NAME, "message")
                    except:
                        try:
                            message_field = driver.find_element(By.ID, "custom-message")
                        except:
                            try:
                                message_field = driver.find_element(By.XPATH, "//textarea")
                            except:
                                pass
                    
                    if message_field:
                        # Truncate message if too long
                        if len(message) > 300:
                            message = message[:297] + "..."
                        
                        message_field.send_keys(message)
                        result["message_sent"] = True
                        print(f"✓ Typed message ({len(message)} chars)")
                        time.sleep(random.uniform(1, 2))
                    else:
                        print("⚠ Could not find message field")
                else:
                    print("⚠ Could not find 'Add a note' button")
                
            except Exception as e:
                print(f"⚠ Could not add note: {e}")
        
        # Click "Send" button - try multiple approaches
        # If we have a message, look for "Send" button
        # If no message, look for "Send without a note" or just "Send"
        send_clicked = False
        
        if not message:
            # Try to click "Send without a note" first
            try:
                send_without_note = driver.find_element(By.XPATH, "//button[contains(., 'Send without a note') or contains(@aria-label, 'Send without a note')]")
                driver.execute_script("arguments[0].click();", send_without_note)
                send_clicked = True
                print("✓ Clicked 'Send without a note'")
                time.sleep(random.uniform(2, 3))
                result["status"] = "success"
                print("✓ Connection request sent!")
                return result
            except Exception as e:
                print(f"⚠ Could not find 'Send without a note' button: {e}")
        
        try:
            # Method 1: Look for Send button with aria-label
            try:
                send_button = driver.find_element(By.XPATH, "//button[contains(@aria-label, 'Send')]")
                driver.execute_script("arguments[0].click();", send_button)
                send_clicked = True
                print("✓ Clicked Send (method 1)")
            except:
                pass
            
            # Method 2: Look for button with "Send" text
            if not send_clicked:
                try:
                    send_button = driver.find_element(By.XPATH, "//button[contains(., 'Send') and not(contains(., 'without'))]")
                    driver.execute_script("arguments[0].click();", send_button)
                    send_clicked = True
                    print("✓ Clicked Send (method 2)")
                except:
                    pass
            
            # Method 3: Look for primary button in modal
            if not send_clicked:
                try:
                    send_button = driver.find_element(By.XPATH, "//div[contains(@role, 'dialog')]//button[contains(@class, 'artdeco-button--primary')]")
                    driver.execute_script("arguments[0].click();", send_button)
                    send_clicked = True
                    print("✓ Clicked Send (method 3)")
                except:
                    pass
            
            if send_clicked:
                time.sleep(random.uniform(2, 3))
                result["status"] = "success"
                print("✓ Connection request sent!")
            else:
                # Save screenshot for debugging
                try:
                    driver.save_screenshot("debug_no_send.png")
                    print("⚠ Saved screenshot to debug_no_send.png")
                except:
                    pass
                result["errors"].append("Send button not found")
                print("✗ Could not find Send button after trying all methods")
            
        except Exception as e:
            result["errors"].append(f"Error clicking Send: {str(e)}")
            print(f"✗ Error clicking Send button: {e}")
    
    except Exception as e:
        result["errors"].append(f"General error: {str(e)}")
        print(f"✗ Error in send_connection_request: {e}")
    
    return result
