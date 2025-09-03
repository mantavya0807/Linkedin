import os
import time
import re
from urllib.parse import quote
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service as ChromeService
from selenium.webdriver.common.keys import Keys
from selenium.common.exceptions import TimeoutException, NoSuchElementException
from webdriver_manager.chrome import ChromeDriverManager
from dotenv import load_dotenv

load_dotenv()

class LinkedInService:
    def __init__(self):
        self.driver = None
        self.linkedin_email = os.getenv('LINKEDIN_EMAIL')
        self.linkedin_password = os.getenv('LINKEDIN_PASSWORD')
        self.connected_profiles = set()
        
        if not self.linkedin_email or not self.linkedin_password:
            print("❌ LinkedIn credentials not configured")
    
    def extract_name_from_email(self, email):
        """Extract likely person name from email address with improved logic"""
        try:
            # Get the part before @
            local_part = email.split('@')[0]
            
            # Enhanced patterns for extracting names
            patterns = [
                r'^([a-z]+)\.([a-z]+)$',      # firstname.lastname
                r'^([a-z]+)\.([a-z]+)\.([a-z]+)$', # firstname.middle.lastname  
                r'^([a-z]+)\.([a-z])\.([a-z]+)$',  # firstname.m.lastname
                r'^([a-z]+)_([a-z]+)$',       # firstname_lastname
                r'^([a-z]+)-([a-z]+)$',       # firstname-lastname
            ]
            
            for pattern in patterns:
                match = re.match(pattern, local_part.lower())
                if match:
                    groups = match.groups()
                    if len(groups) == 2:
                        first, last = groups
                        # Better validation for names
                        if len(first) >= 2 and len(last) >= 2:
                            return f"{first.title()} {last.title()}"
                    elif len(groups) == 3:
                        first, middle, last = groups
                        if len(first) >= 2 and len(last) >= 2:
                            return f"{first.title()} {last.title()}"
            
            # For names like 'jucano', 'magolden', etc. - treat as single names
            if len(local_part) >= 4 and local_part.isalpha():
                # Check if it's a likely single concatenated name
                common_prefixes = ['mc', 'mac', 'van', 'de', 'la', 'le']
                
                # Try to intelligently split concatenated names
                # Look for pattern: common first names + rest
                first_names = ['james', 'john', 'robert', 'michael', 'william', 'david', 'richard', 'thomas', 'charles', 'christopher',
                              'daniel', 'matthew', 'anthony', 'mark', 'donald', 'steven', 'paul', 'andrew', 'joshua', 'kenneth',
                              'mary', 'patricia', 'jennifer', 'linda', 'elizabeth', 'barbara', 'susan', 'jessica', 'sarah', 'karen',
                              'nancy', 'lisa', 'betty', 'helen', 'sandra', 'donna', 'carol', 'ruth', 'sharon', 'michelle']
                
                # Check if starts with a common first name
                for fname in first_names:
                    if local_part.lower().startswith(fname) and len(local_part) > len(fname) + 2:
                        first = fname
                        last = local_part[len(fname):]
                        return f"{first.title()} {last.title()}"
                
                # For emails like 'jucano@tesla.com' - just return as single name
                # This is better than splitting into 'J Ucano'
                return local_part.title()
            
            return None
            
        except Exception as e:
            print(f"❌ Error extracting name from {email}: {e}")
            return None
    
    def start_browser(self):
        """Start Chrome browser with persistent profile for LinkedIn"""
        try:
            print("🌐 Starting LinkedIn browser...")
            
            options = Options()
            
            # Remove automation detection flags
            options.add_argument('--disable-blink-features=AutomationControlled')
            options.add_experimental_option("excludeSwitches", ["enable-automation"])
            options.add_experimental_option('useAutomationExtension', False)
            
            # Add realistic user agent
            options.add_argument('--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36')
            
            # Use dedicated LinkedIn profile (separate from Prospeo)
            profile_path = os.path.join(os.getcwd(), "chrome_profile_linkedin")
            options.add_argument(f'--user-data-dir={profile_path}')
            
            # Standard options
            options.add_argument('--no-sandbox')
            options.add_argument('--disable-dev-shm-usage')
            options.add_argument('--start-maximized')
            options.add_argument('--disable-logging')
            options.add_argument('--log-level=3')
            options.add_experimental_option('excludeSwitches', ['enable-logging'])
            
            service = ChromeService(ChromeDriverManager().install())
            self.driver = webdriver.Chrome(service=service, options=options)
            
            # Execute script to hide automation detection
            self.driver.execute_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")
            
            print("✅ LinkedIn browser started successfully")
            return True
            
        except Exception as e:
            print(f"❌ LinkedIn browser startup failed: {e}")
            return False
    
    def login_to_linkedin(self):
        """Log in to LinkedIn (or check if already logged in)"""
        try:
            print("🔐 Checking LinkedIn login status...")
            
            # Go to LinkedIn
            self.driver.get("https://www.linkedin.com")
            time.sleep(5)
            
            # Check if already logged in by looking for common logged-in elements
            logged_in_indicators = [
                "feed",
                "mynetwork", 
                "messaging",
                "notifications"
            ]
            
            current_url = self.driver.current_url.lower()
            page_source = self.driver.page_source.lower()
            
            # Check URL indicators
            for indicator in logged_in_indicators:
                if indicator in current_url:
                    print("✅ Already logged in to LinkedIn (URL check)")
                    return True
            
            # Check for logout link or profile menu as indicators of being logged in
            if ("sign out" in page_source or 
                "global-nav__me" in page_source or 
                'data-control-name="identity_welcome_message"' in page_source):
                print("✅ Already logged in to LinkedIn (element check)")
                return True
            
            # If we see a login form, we need to log in
            login_elements = self.driver.find_elements(By.ID, "username")
            if login_elements:
                print("🔑 Login required - LinkedIn session expired")
                print("⚠️ Please log in manually in the browser window")
                print("   1. Use the same Google account you used before")
                print("   2. Complete any 2FA if required")
                print("   3. Make sure you reach the LinkedIn feed/homepage")
                input("   >>> After logging in successfully, press Enter to continue...")
                
                # Verify login was successful
                time.sleep(3)
                self.driver.get("https://www.linkedin.com/feed")
                time.sleep(3)
                
                if "feed" in self.driver.current_url or "sign out" in self.driver.page_source.lower():
                    print("✅ Login verified successfully")
                    return True
                else:
                    print("❌ Login verification failed")
                    return False
            
            print("✅ LinkedIn session ready")
            return True
            
        except Exception as e:
            print(f"❌ LinkedIn login check failed: {e}")
            print(">>> Please ensure you're logged in, then press Enter to continue...")
            input()
            return True
    
    def search_and_connect_to_people(self, email_list, company_name, max_connections=10):
        """Main function to search for people by email and send connection requests"""
        try:
            print(f"\n🔗 Starting LinkedIn automation for {company_name}")
            print(f"📧 Processing {len(email_list)} emails...")
            
            if not self.start_browser():
                return 0
            
            if not self.login_to_linkedin():
                return 0
            
            connections_sent = 0
            
            for i, email in enumerate(email_list[:max_connections], 1):
                print(f"\n👤 ({i}/{min(len(email_list), max_connections)}) Processing: {email}")
                
                # Extract name from email
                person_name = self.extract_name_from_email(email)
                if not person_name:
                    print(f"   ❌ Could not extract name from {email}")
                    continue
                
                print(f"   📝 Extracted name: {person_name}")
                
                # Check if browser is still active
                try:
                    current_url = self.driver.current_url
                    print(f"   🌐 Browser active on: {current_url[:50]}...")
                except Exception as e:
                    print(f"   ❌ Browser session lost: {e}")
                    print(f"   🔄 Restarting browser...")
                    if not self.start_browser() or not self.login_to_linkedin():
                        print(f"   ❌ Could not restart browser session")
                        break
                
                # Search for the person on LinkedIn
                if self.search_person_and_connect(person_name, company_name, email):
                    connections_sent += 1
                    print(f"   ✅ Connection request sent to {person_name}")
                    # Wait between requests to avoid being flagged
                    time.sleep(8)
                else:
                    print(f"   ❌ Failed to connect with {person_name}")
                
                # Small delay between searches
                time.sleep(3)
            
            print(f"\n📊 LinkedIn automation complete!")
            print(f"   ✅ Connection requests sent: {connections_sent}")
            print(f"   📧 Emails processed: {len(email_list[:max_connections])}")
            
            return {
                'connections_sent': connections_sent,
                'emails_processed': len(email_list[:max_connections]),
                'results': {}  # Could add individual results here if needed
            }
            
        except Exception as e:
            print(f"❌ LinkedIn automation failed: {e}")
            return 0
        finally:
            if self.driver:
                print("🔄 Keeping browser open for manual inspection...")
                input("Press Enter to close browser...")
                try:
                    self.driver.quit()
                except:
                    pass
    
    def search_person_and_connect(self, person_name, company_name, email):
        """Search for a specific person and send connection request"""
        try:
            # Create search query
            search_query = f"{person_name} {company_name}"
            print(f"   🔍 Searching LinkedIn for: {search_query}")
            
            # Go to LinkedIn search
            search_url = f"https://www.linkedin.com/search/results/people/?keywords={quote(search_query)}"
            self.driver.get(search_url)
            time.sleep(3)
            
            # Wait for search results to load
            try:
                WebDriverWait(self.driver, 10).until(
                    EC.presence_of_element_located((By.CSS_SELECTOR, ".search-results-container, .search-results, .entity-result"))
                )
                print("   ✅ Search results loaded")
            except TimeoutException:
                print("   ⚠️ Search results not loading, continuing...")
            
            # Look for profile cards with updated selectors for current LinkedIn
            profile_cards = self.driver.find_elements(By.CSS_SELECTOR, 
                ".entity-result, .reusable-search__result-container, [data-view-name='search-entity-result']")
            
            if not profile_cards:
                # Try alternative selectors
                profile_cards = self.driver.find_elements(By.CSS_SELECTOR, 
                    ".search-result, .search-entity-result, .search-result__wrapper")
                
            if not profile_cards:
                # Try even more generic selector
                profile_cards = self.driver.find_elements(By.XPATH, 
                    "//div[contains(@class, 'entity-result') or contains(@class, 'search-result')]")
            
            # NEW: Try the actual structure we found
            if not profile_cards:
                profile_cards = self.driver.find_elements(By.CSS_SELECTOR, 
                    ".search-results-container .artdeco-card")
            
            if not profile_cards:
                print(f"   ❌ No search results found for {person_name}")
                print(f"   🔍 Current URL: {self.driver.current_url}")
                print(f"   📄 Page title: {self.driver.title}")
                # Save page source for debugging
                with open("debug_linkedin_search.html", "w", encoding="utf-8") as f:
                    f.write(self.driver.page_source)
                print(f"   💾 Page source saved to debug_linkedin_search.html")
                return False
            
            print(f"   📋 Found {len(profile_cards)} potential matches")
            
            # Try to find the right person and connect
            for i, card in enumerate(profile_cards[:3]):  # Check first 3 results
                try:
                    # Look for the person's name in the card
                    name_elements = card.find_elements(By.CSS_SELECTOR, 
                        "a[data-control-name='search_srp_result'] span[aria-hidden='true'], .entity-result__title-text a span[aria-hidden='true']")
                    
                    # NEW: Try the actual selector we found in HTML
                    if not name_elements:
                        name_elements = card.find_elements(By.CSS_SELECTOR, 
                            "a[data-test-app-aware-link] span[aria-hidden='true']")
                    
                    if not name_elements:
                        continue
                        
                    found_name = name_elements[0].text
                    print(f"   👤 Checking profile {i+1}: {found_name}")
                    
                    # Check if this looks like our person
                    if self.names_match(person_name, found_name):
                        print(f"   ✅ Found matching profile: {found_name}")
                        
                        # Strategy 1: Look for direct Connect button
                        connect_buttons = card.find_elements(By.XPATH, 
                            ".//button[contains(text(), 'Connect') or contains(@aria-label, 'Connect')]")
                        
                        if connect_buttons:
                            print(f"   🔗 Found Connect button - sending direct connection request...")
                            return self.send_connection_request(connect_buttons[0], found_name)
                        
                        # Strategy 2: Only Message button - need to visit profile
                        message_buttons = card.find_elements(By.XPATH, 
                            ".//button[contains(text(), 'Message') or contains(@aria-label, 'Message')]")
                        
                        # NEW: Also try the exact selector we found in HTML analysis
                        if not message_buttons:
                            message_buttons = card.find_elements(By.CSS_SELECTOR, 
                                "button.artdeco-button--secondary[aria-label*='Message']")
                        
                        if message_buttons:
                            print(f"   � Found Message button - visiting profile for Connect option...")
                            
                            # Get profile link
                            profile_links = card.find_elements(By.CSS_SELECTOR, 
                                "a[data-control-name='search_srp_result'], .entity-result__title-text a")
                            
                            # NEW: Try the actual selector we found in HTML
                            if not profile_links:
                                profile_links = card.find_elements(By.CSS_SELECTOR, 
                                    "a[data-test-app-aware-link]")
                                profile_links = card.find_elements(By.CSS_SELECTOR, 
                                    "a[data-test-app-aware-link]")
                            
                            if profile_links:
                                profile_url = profile_links[0].get_attribute('href')
                                return self.visit_profile_and_connect(profile_url, found_name)
                        
                        # Strategy 3: Look for "More" button to expand options
                        more_buttons = card.find_elements(By.XPATH, 
                            ".//button[contains(@aria-label, 'More actions') or contains(text(), 'More')]")
                        
                        if more_buttons:
                            print(f"   ⚙️ Found More button - expanding options...")
                            self.driver.execute_script("arguments[0].click();", more_buttons[0])
                            time.sleep(2)
                            
                            # Look for Connect in the dropdown - it's a div with role="button", not a button!
                            dropdown_connect = self.driver.find_elements(By.CSS_SELECTOR, 
                                "div[role='button'][aria-label*='connect' i], .artdeco-dropdown__item[aria-label*='connect' i]")
                            
                            if not dropdown_connect:
                                # Fallback to text-based search
                                dropdown_connect = self.driver.find_elements(By.XPATH, 
                                    "//div[@role='button'][contains(text(), 'Connect')] | //div[contains(@class, 'artdeco-dropdown__item')][contains(text(), 'Connect')]")
                            
                            if dropdown_connect:
                                print(f"   🔗 Found Connect in dropdown...")
                                self.driver.execute_script("arguments[0].click();", dropdown_connect[0])
                                time.sleep(2)
                                return self.handle_connection_request_modal(found_name)
                        
                        print(f"   ❌ No Connect option found for {found_name}")
                    
                except Exception as card_error:
                    print(f"   ⚠️ Error processing profile card {i+1}: {card_error}")
                    continue
            
            print(f"   ❌ Could not find or connect to {person_name}")
            return False
            
        except Exception as e:
            print(f"   ❌ Error searching for {person_name}: {e}")
            return False
    
    def names_match(self, extracted_name, linkedin_name):
        """Conservative name matching - only matches when we're reasonably confident"""
        try:
            # Normalize names for comparison
            extracted_lower = extracted_name.lower().strip()
            linkedin_lower = linkedin_name.lower().strip()
            
            # Direct match
            if extracted_lower == linkedin_lower:
                return True
            
            # Split names into parts
            extracted_parts = extracted_lower.split()
            linkedin_parts = linkedin_lower.split()
            
            # For single word extracted names, be more conservative
            if len(extracted_parts) == 1:
                extracted_word = extracted_parts[0]
                
                # Need at least 4 characters for matching
                if len(extracted_word) < 4:
                    return False
                
                # Check for strong substring matches
                for linkedin_part in linkedin_parts:
                    # Must be a significant portion of either name
                    if extracted_word in linkedin_part:
                        # Extracted name should be at least 60% of LinkedIn name part
                        if len(extracted_word) >= len(linkedin_part) * 0.6:
                            return True
                    elif linkedin_part in extracted_word:
                        # LinkedIn part should be at least 60% of extracted name
                        if len(linkedin_part) >= len(extracted_word) * 0.6:
                            return True
                    
                    # Special case: common name abbreviations
                    abbreviations = {
                        'mike': 'michael',
                        'mike': 'mikhail', 
                        'bob': 'robert',
                        'jim': 'james',
                        'bill': 'william',
                        'dave': 'david',
                        'steve': 'steven',
                        'chris': 'christopher',
                        'matt': 'matthew',
                        'alex': 'alexander'
                    }
                    
                    if extracted_word in abbreviations:
                        if abbreviations[extracted_word] in linkedin_part:
                            return True
                    
                    # Reverse lookup for abbreviations
                    for abbrev, full_name in abbreviations.items():
                        if full_name == extracted_word and abbrev in linkedin_part:
                            return True
                            
                return False
            
            # For multi-part names, use the original logic
            if len(extracted_parts) >= 2 and len(linkedin_parts) >= 2:
                # Check if first and last names match (allowing for middle names, etc.)
                first_match = any(extracted_parts[0] in part or part in extracted_parts[0] for part in linkedin_parts)
                last_match = any(extracted_parts[-1] in part or part in extracted_parts[-1] for part in linkedin_parts)
                return first_match and last_match
            
            return False
            
        except Exception as e:
            print(f"   ⚠️ Error in name matching: {e}")
            return False
    
    def handle_connection_modal(self):
        """Handle the connection request modal that appears after clicking Connect"""
        try:
            # Wait for modal to appear
            time.sleep(2)
            
            # Look for "Send without a note" button (most common)
            send_buttons = self.driver.find_elements(By.XPATH, 
                "//button[contains(text(), 'Send without a note') or contains(@aria-label, 'Send without a note')]")
            
            if send_buttons:
                self.driver.execute_script("arguments[0].click();", send_buttons[0])
                print("   ✅ Sent connection without note")
                return True
            
            # Look for "Send now" button
            send_now_buttons = self.driver.find_elements(By.XPATH,
                "//button[contains(text(), 'Send now') or contains(@aria-label, 'Send now')]")
            
            if send_now_buttons:
                self.driver.execute_script("arguments[0].click();", send_now_buttons[0])
                print("   ✅ Sent connection request")
                return True
            
            # Look for generic "Send" button
            send_generic = self.driver.find_elements(By.XPATH, "//button[contains(text(), 'Send')]")
            if send_generic:
                self.driver.execute_script("arguments[0].click();", send_generic[0])
                print("   ✅ Sent connection request")
                return True
            
            print("   ❌ Could not find Send button in modal")
            return False
            
        except Exception as e:
            print(f"   ❌ Error handling connection modal: {e}")
            return False
    
    def connect_from_profile_page(self, person_name):
        """Try to connect from the person's profile page"""
        try:
            # Look for Connect button on profile page
            connect_buttons = self.driver.find_elements(By.XPATH,
                "//button[contains(text(), 'Connect') or contains(@aria-label, 'Connect')]")
            
            if connect_buttons:
                print(f"   🔗 Found Connect button on profile page")
                self.driver.execute_script("arguments[0].click();", connect_buttons[0])
                time.sleep(2)
                
                # Handle the modal
                if self.handle_connection_modal():
                    return True
            
            # Look for "More" button that might reveal Connect option
            more_buttons = self.driver.find_elements(By.XPATH,
                "//button[contains(text(), 'More') or contains(@aria-label, 'More')]")
            
            if more_buttons:
                print(f"   📋 Found More button, clicking to reveal options...")
                self.driver.execute_script("arguments[0].click();", more_buttons[0])
                time.sleep(2)
                
                # Now look for Connect in dropdown
                dropdown_connect = self.driver.find_elements(By.XPATH,
                    "//button[contains(text(), 'Connect') or contains(@aria-label, 'Connect')]")
                
                if dropdown_connect:
                    print(f"   🔗 Found Connect in More dropdown")
                    self.driver.execute_script("arguments[0].click();", dropdown_connect[0])
                    time.sleep(2)
                    
                    if self.handle_connection_modal():
                        return True
            
            print(f"   ❌ Could not find Connect option on {person_name}'s profile")
            return False
            
        except Exception as e:
            print(f"   ❌ Error connecting from profile page: {e}")
            return False
    
    def send_connection_request(self, connect_button, person_name):
        """Send connection request using the connect button"""
        try:
            print(f"   🔗 Clicking Connect button...")
            self.driver.execute_script("arguments[0].click();", connect_button)
            time.sleep(2)
            
            # Use the new modal handler
            return self.handle_connection_request_modal(person_name)
            
        except Exception as e:
            print(f"   ❌ Error sending connection request: {e}")
            return False

    def visit_profile_and_connect(self, profile_url, person_name):
        """Visit person's profile page and look for Connect button"""
        try:
            print(f"   🌐 Visiting profile: {profile_url}")
            self.driver.get(profile_url)
            time.sleep(3)
            
            # Look for Connect button on profile page
            connect_buttons = self.driver.find_elements(By.XPATH, 
                "//button[contains(text(), 'Connect') or contains(@aria-label, 'Connect')]")
            
            if connect_buttons:
                return self.send_connection_request(connect_buttons[0], person_name)
            
            # Look for "More" button on profile - try multiple selectors
            more_buttons = self.driver.find_elements(By.XPATH, 
                "//button[contains(@aria-label, 'More actions') or contains(text(), 'More')]")
            
            # Also try the specific class we found in debugging
            if not more_buttons:
                more_buttons = self.driver.find_elements(By.CSS_SELECTOR, 
                    "button.artdeco-dropdown__trigger")
            
            if more_buttons:
                print(f"   ⚙️ Clicking More actions on profile...")
                # Scroll into view first
                self.driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", more_buttons[0])
                time.sleep(1)
                
                # Click the More button
                self.driver.execute_script("arguments[0].click();", more_buttons[0])
                time.sleep(2)  # Give dropdown time to appear
                
                # Look for Connect in dropdown - it's a div with role="button", not a button!
                dropdown_selectors = [
                    "div[role='button'][aria-label*='connect' i]",
                    ".artdeco-dropdown__item[aria-label*='connect' i]",
                    "//div[@role='button'][contains(@aria-label, 'connect')]",
                    "//div[contains(@class, 'artdeco-dropdown__item')][contains(@aria-label, 'connect')]",
                    "//div[@role='button'][contains(text(), 'Connect')]",
                    "//div[contains(@class, 'artdeco-dropdown__item')][contains(text(), 'Connect')]"
                ]
                
                dropdown_connect = None
                for selector in dropdown_selectors:
                    try:
                        if selector.startswith("//"):
                            # XPath selector
                            dropdown_connect = self.driver.find_elements(By.XPATH, selector)
                        else:
                            # CSS selector
                            dropdown_connect = self.driver.find_elements(By.CSS_SELECTOR, selector)
                        
                        if dropdown_connect:
                            print(f"   ✅ Found Connect in dropdown with selector: {selector}")
                            break
                    except:
                        continue
                
                if dropdown_connect and len(dropdown_connect) > 0:
                    print(f"   🔗 Clicking Connect from More dropdown...")
                    self.driver.execute_script("arguments[0].click();", dropdown_connect[0])
                    time.sleep(2)
                    return self.handle_connection_request_modal(person_name)
                else:
                    print(f"   ❌ Connect option not found in More dropdown")
            
            print(f"   ❌ No Connect option found on {person_name}'s profile")
            return False
            
        except Exception as e:
            print(f"   ❌ Error visiting profile: {e}")
            return False
    
    def handle_connection_request_modal(self, person_name):
        """Handle the connection request modal that appears after clicking Connect"""
        try:
            # Wait for modal to appear
            modal_wait = WebDriverWait(self.driver, 5)
            
            # Look for connection modal
            modal_selectors = [
                ".artdeco-modal",
                "[role='dialog']",
                ".send-invite-modal",
                ".connect-modal"
            ]
            
            modal = None
            for selector in modal_selectors:
                try:
                    modal = modal_wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, selector)))
                    print(f"   ✅ Connection modal found with selector: {selector}")
                    break
                except:
                    continue
            
            if modal:
                # Look for "Send" or "Connect" button in modal
                send_buttons = self.driver.find_elements(By.XPATH, 
                    "//button[contains(text(), 'Send') or contains(text(), 'Connect') or contains(@aria-label, 'Send')]")
                
                if send_buttons:
                    print(f"   📤 Sending connection request to {person_name}...")
                    send_buttons[0].click()
                    time.sleep(2)
                    
                    # Check for success indicators
                    success_indicators = [
                        "Invitation sent",
                        "Connection request sent", 
                        "Pending"
                    ]
                    
                    page_text = self.driver.page_source.lower()
                    for indicator in success_indicators:
                        if indicator.lower() in page_text:
                            print(f"   ✅ Connection request sent successfully to {person_name}")
                            return True
                    
                    print(f"   ✅ Connection request likely sent to {person_name}")
                    return True
                else:
                    print(f"   ❌ Could not find Send button in connection modal")
                    return False
            else:
                print(f"   ❌ Connection modal not found")
                return False
                
        except Exception as e:
            print(f"   ❌ Error handling connection modal: {e}")
            return False
    
    def close_modal(self):
        """Close any open modal dialogs"""
        try:
            close_buttons = self.driver.find_elements(By.CSS_SELECTOR, 
                "[aria-label='Dismiss'], .artdeco-modal__dismiss, [data-control-name='overlay.close_conversation_window']")
            
            if close_buttons:
                close_buttons[0].click()
                time.sleep(1)
        except Exception as e:
            return None
    
    def start_browser(self):
        """Start Chrome browser with persistence"""
        try:
            print("🌐 Starting LinkedIn browser...")
            
            options = Options()
            
            # Remove automation detection flags
            options.add_argument('--disable-blink-features=AutomationControlled')
            options.add_experimental_option("excludeSwitches", ["enable-automation"])
            options.add_experimental_option('useAutomationExtension', False)
            
            # Add realistic user agent
            options.add_argument('--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36')
            
            # Standard options
            options.add_argument('--no-sandbox')
            options.add_argument('--disable-dev-shm-usage')
            options.add_argument('--start-maximized')
            options.add_argument('--disable-logging')
            options.add_argument('--log-level=3')
            options.add_experimental_option('excludeSwitches', ['enable-logging'])
            
            # Use persistent profile (should be same as email scraper if we want shared sessions)
            profile_path = os.path.join(os.getcwd(), "chrome_profile_linkedin")
            options.add_argument(f'--user-data-dir={profile_path}')
            
            service = ChromeService(ChromeDriverManager().install())
            self.driver = webdriver.Chrome(service=service, options=options)
            
            # Execute script to hide automation detection
            self.driver.execute_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")
            
            print("✅ LinkedIn browser started successfully")
            return True
            
        except Exception as e:
            print(f"❌ Browser startup failed: {e}")
            return False

    def search_people_by_emails(self, email_list, company_name, max_connections=5):
        """Search for people on LinkedIn based on their email addresses"""
        print(f"\n🔍 Searching LinkedIn for people from {company_name}")
        print(f"📧 Processing {len(email_list)} email addresses...")
        
        connections_sent = 0
        people_found = []
        
        if not self.start_browser():
            return []
        
        try:
            # Go to LinkedIn and check if logged in
            self.driver.get("https://www.linkedin.com")
            time.sleep(3)
            
            # Check if we need to login
            if "feed" not in self.driver.current_url and "in/m" not in self.driver.current_url:
                print("❗ LinkedIn login required")
                print("   Please log in manually and then press Enter...")
                input("   >>> After logging in, press Enter to continue <<<")
            
            for email in email_list[:10]:  # Process first 10 emails
                if connections_sent >= max_connections:
                    break
                    
                # Extract name from email
                person_name = self.extract_name_from_email(email)
                if not person_name:
                    print(f"   ❌ Could not extract name from {email}")
                    continue
                
                print(f"\n🔍 Searching for: {person_name} at {company_name}")
                
                # Search on LinkedIn
                search_query = f"{person_name} {company_name}"
                result = self.search_and_connect(search_query, person_name, email)
                
                if result:
                    people_found.append({
                        'email': email,
                        'name': person_name,
                        'linkedin_url': result.get('profile_url'),
                        'connected': result.get('connected', False)
                    })
                    
                    if result.get('connected'):
                        connections_sent += 1
                        print(f"✅ Connection sent to {person_name}")
                        time.sleep(5)  # Wait between connections
                    
                # Wait between searches to avoid rate limiting
                time.sleep(3)
                
        except Exception as e:
            print(f"❌ LinkedIn automation error: {e}")
        
        print(f"\n📊 LinkedIn Results:")
        print(f"   👥 People found: {len(people_found)}")
        print(f"   🔗 Connections sent: {connections_sent}")
        
        return people_found
    
    def search_and_connect(self, search_query, person_name, email):
        """Search for a specific person and attempt to connect"""
        try:
            # Go to LinkedIn search
            encoded_query = quote(search_query)
            search_url = f"https://www.linkedin.com/search/results/people/?keywords={encoded_query}"
            
            self.driver.get(search_url)
            time.sleep(3)
            
            # Look for search results
            results = self.driver.find_elements(By.CSS_SELECTOR, ".reusable-search__result-container")
            
            if not results:
                print(f"   ❌ No search results found for {person_name}")
                return None
                
            # Check first few results for exact name match
            for result in results[:3]:
                try:
                    # Get profile link and name
                    profile_link = result.find_element(By.CSS_SELECTOR, "a.app-aware-link")
                    profile_url = profile_link.get_attribute('href')
                    
                    # Get name from result
                    name_element = result.find_element(By.CSS_SELECTOR, ".entity-result__title-text a span[aria-hidden='true']")
                    result_name = name_element.text.strip()
                    
                    print(f"   🔍 Found: {result_name}")
                    
                    # Click on profile
                    self.driver.execute_script("arguments[0].click();", profile_link)
                    time.sleep(3)
                    
                    # Try to connect
                    connected = self.attempt_connection()
                    
                    return {
                        'profile_url': profile_url,
                        'name': result_name,
                        'connected': connected
                    }
                    
                except Exception as e:
                    print(f"   ❌ Error processing result: {e}")
                    continue
            
            return None
            
        except Exception as e:
            print(f"   ❌ Search failed for {person_name}: {e}")
            return None
    
    def linkedin_login(self):
        """Login to LinkedIn with session persistence"""
        try:
            self.driver.get("https://www.linkedin.com/login")
            time.sleep(3)
            
            # Check if already logged in
            if "feed" in self.driver.current_url or "mynetwork" in self.driver.current_url:
                print("✅ Already logged in to LinkedIn")
                return True
            
            # Login process
            email_field = WebDriverWait(self.driver, 10).until(
                EC.presence_of_element_located((By.ID, "username"))
            )
            password_field = self.driver.find_element(By.ID, "password")
            
            email_field.clear()
            email_field.send_keys(self.linkedin_email)
            password_field.clear()
            password_field.send_keys(self.linkedin_password)
            
            login_button = self.driver.find_element(By.CSS_SELECTOR, "button[type='submit']")
            login_button.click()
            
            # Wait for login to complete
            WebDriverWait(self.driver, 15).until(
                lambda driver: "feed" in driver.current_url or "mynetwork" in driver.current_url
            )
            
            print("✅ LinkedIn login successful")
            return True
            
        except Exception as e:
            print(f"❌ LinkedIn login failed: {e}")
            return False
    
    def find_company_people_page(self, company_name):
        """Find company's LinkedIn people page via Google search"""
        try:
            print(f"🔎 Finding LinkedIn page for '{company_name}'...")
            
            # Google search for company LinkedIn page
            encoded_query = quote(f"{company_name} site:linkedin.com/company")
            search_url = f"https://www.google.com/search?q={encoded_query}"
            
            self.driver.get(search_url)
            time.sleep(3)
            
            # Handle potential CAPTCHA
            try:
                first_result = WebDriverWait(self.driver, 10).until(
                    EC.presence_of_element_located((By.CSS_SELECTOR, "#search a"))
                )
            except TimeoutException:
                print("❗ Google CAPTCHA detected. Please solve manually...")
                input("Press Enter after solving CAPTCHA...")
                first_result = WebDriverWait(self.driver, 60).until(
                    EC.presence_of_element_located((By.CSS_SELECTOR, "#search a"))
                )
            
            company_url = first_result.get_attribute('href')
            
            if "linkedin.com/company/" not in company_url:
                print("❌ Could not find LinkedIn company page")
                return None
            
            # Convert to people page URL
            people_url = company_url.split('?')[0].strip('/') + "/people/"
            print(f"✅ Found people page: {people_url}")
            return people_url
            
        except Exception as e:
            print(f"❌ Error finding company page: {e}")
            return None
    
    def send_connection_requests(self, people_url, max_connections=5):
        """Send LinkedIn connection requests"""
        connections_sent = 0
        
        try:
            self.driver.get(people_url)
            time.sleep(3)
            
            # Search for different roles
            search_keywords = ["Software Engineer", "Recruiter", "Talent Acquisition"]
            
            for keyword in search_keywords:
                if connections_sent >= max_connections:
                    break
                
                try:
                    print(f"🔗 Searching for '{keyword}'...")
                    
                    # Find search input
                    search_input = WebDriverWait(self.driver, 10).until(
                        EC.presence_of_element_located((By.ID, "people-search-keywords"))
                    )
                    search_input.clear()
                    search_input.send_keys(keyword)
                    search_input.send_keys(Keys.RETURN)
                    time.sleep(3)
                    
                    # Get profile cards
                    profile_cards = self.driver.find_elements(By.CSS_SELECTOR, "li.org-people-profile-card__profile-card-spacing")
                    
                    # Process each profile
                    for card in profile_cards[:3]:  # Limit per keyword
                        if connections_sent >= max_connections:
                            break
                        
                        try:
                            # Get profile URL
                            link_element = card.find_element(By.CSS_SELECTOR, "a.link-without-visited-state")
                            profile_url = link_element.get_attribute('href')
                            
                            if profile_url in self.connected_profiles:
                                continue
                            
                            # Visit profile and attempt connection
                            print(f"   Visiting profile...")
                            self.driver.get(profile_url)
                            self.connected_profiles.add(profile_url)
                            time.sleep(2)
                            
                            if self.attempt_connection():
                                connections_sent += 1
                                print(f"   ✅ Connection sent ({connections_sent}/{max_connections})")
                            
                            time.sleep(3)  # Delay between connections
                            
                        except Exception as e:
                            print(f"   ❌ Error with profile: {str(e)[:50]}...")
                            continue
                    
                except Exception as e:
                    print(f"❌ Error searching for '{keyword}': {e}")
                    continue
            
        except Exception as e:
            print(f"❌ Error in connection process: {e}")
        
        return connections_sent
    
    def attempt_connection(self):
        """Attempt to send connection request"""
        try:
            # Wait for page to load
            WebDriverWait(self.driver, 10).until(
                EC.presence_of_element_located((By.TAG_NAME, "main"))
            )
            time.sleep(2)
            
            # Check if already connected/pending
            if self.driver.find_elements(By.XPATH, "//button[contains(@aria-label, 'Pending')]"):
                print("   - Already pending")
                return False
            
            # Look for Connect button
            connect_buttons = self.driver.find_elements(By.XPATH, "//button[contains(text(), 'Connect')]")
            
            for button in connect_buttons:
                try:
                    aria_label = button.get_attribute('aria-label') or ''
                    if 'invite' in aria_label.lower():
                        self.driver.execute_script("arguments[0].click();", button)
                        time.sleep(1)
                        
                        # Click "Send without a note"
                        send_selectors = [
                            "//button[@aria-label='Send without a note']",
                            "//button[contains(@aria-label, 'Send without')]",
                            "//button[contains(text(), 'Send without a note')]"
                        ]
                        
                        for selector in send_selectors:
                            try:
                                send_button = WebDriverWait(self.driver, 3).until(
                                    EC.element_to_be_clickable((By.XPATH, selector))
                                )
                                send_button.click()
                                return True
                            except:
                                continue
                        
                        return False
                        
                except Exception as e:
                    continue
            
            print("   - No Connect button found")
            return False
            
        except Exception as e:
            print(f"   - Connection attempt failed: {str(e)[:50]}...")
            return False
    
    def run_linkedin_outreach(self, company_name, max_connections=5):
        """Complete LinkedIn outreach process"""
        if not self.linkedin_email or not self.linkedin_password:
            print("❌ LinkedIn credentials not configured")
            return 0
        
        try:
            if not self.start_browser():
                return 0
            
            if not self.linkedin_login():
                return 0
            
            people_url = self.find_company_people_page(company_name)
            if not people_url:
                return 0
            
            connections_sent = self.send_connection_requests(people_url, max_connections)
            
            return connections_sent
            
        except Exception as e:
            print(f"❌ LinkedIn outreach failed: {e}")
            return 0
        finally:
            self.close_browser()
    
    def close_browser(self):
        """Close browser safely"""
        try:
            if self.driver:
                print("🔴 Closing browser...")
                self.driver.quit()
        except Exception as e:
            print(f"❌ Error closing browser: {e}")