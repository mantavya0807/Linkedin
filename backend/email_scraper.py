import os
import time
import re
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service as ChromeService
from selenium.common.exceptions import TimeoutException
from webdriver_manager.chrome import ChromeDriverManager
from email_filter import EmailFilter

class EmailScraper:
    def __init__(self):
        self.driver = None
        self.email_pattern = r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b'
        self.email_filter = EmailFilter()
        
    def start_browser(self):
        """Start browser with persistence for Prospeo login"""
        try:
            print("🌐 Starting browser for email scraping...")
            
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
            
            # Remove some flags that might trigger detection
            options.add_argument('--disable-features=VizDisplayCompositor')
            options.add_argument('--no-first-run')
            options.add_argument('--no-default-browser-check')
            
            # Use persistent profile to save Prospeo login session
            profile_path = os.path.join(os.getcwd(), "chrome_profile_prospeo")
            options.add_argument(f'--user-data-dir={profile_path}')
            print(f"ℹ️ Using Chrome profile: {os.path.abspath(profile_path)}")
            
            service = ChromeService(ChromeDriverManager().install())
            self.driver = webdriver.Chrome(service=service, options=options)
            
            # Execute script to hide automation detection
            self.driver.execute_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")
            
            print("✅ Browser started successfully")
            return True
            
        except Exception as e:
            print(f"❌ Browser startup failed: {e}")
            return False
    
    def setup_manual_login(self):
        """Open browser for manual login to Gmail, Prospeo, and LinkedIn"""
        try:
            if not self.driver:
                self.start_browser()
            
            print("\n🔐 MANUAL LOGIN SETUP")
            print("=" * 50)
            print("I'll open tabs for you to manually log in to:")
            print("1. Gmail (for authentication)")
            print("2. Prospeo (for email scraping)")
            print("3. LinkedIn (for outreach)")
            print("\nPlease log in to each service and then press Enter to continue...")
            
            # Open Gmail login
            print("\n🌐 Opening Gmail...")
            self.driver.get("https://accounts.google.com/signin")
            self.driver.execute_script("window.open('about:blank', '_blank');")
            
            # Switch to new tab and open Prospeo
            print("🌐 Opening Prospeo...")
            self.driver.switch_to.window(self.driver.window_handles[1])
            self.driver.get("https://prospeo.io/login")
            self.driver.execute_script("window.open('about:blank', '_blank');")
            
            # Switch to new tab and open LinkedIn
            print("🌐 Opening LinkedIn...")
            self.driver.switch_to.window(self.driver.window_handles[2])
            self.driver.get("https://www.linkedin.com/login")
            
            # Switch back to Gmail tab
            self.driver.switch_to.window(self.driver.window_handles[0])
            
            print("\n📋 INSTRUCTIONS:")
            print("1. Switch between tabs to log in to each service")
            print("2. Use your Gmail account for all logins if possible")
            print("3. Make sure you're fully logged in to each service")
            print("4. Come back to this terminal and press Enter when done")
            
            input("\n⏳ Press Enter when you've logged in to all services...")
            
            # Save cookies from all tabs
            self.save_login_cookies()
            
            print("✅ Login session saved! You can now use automated scraping.")
            return True
            
        except Exception as e:
            print(f"❌ Manual login setup failed: {e}")
            return False

    def save_login_cookies(self):
        """Save cookies from all login sessions"""
        try:
            import pickle
            profile_path = os.path.join(os.getcwd(), "chrome_profile_prospeo")
            cookies_file = os.path.join(profile_path, "saved_cookies.pkl")
            
            all_cookies = {}
            
            # Save Gmail cookies
            self.driver.switch_to.window(self.driver.window_handles[0])
            all_cookies['gmail'] = self.driver.get_cookies()
            print("💾 Saved Gmail cookies")
            
            # Save Prospeo cookies
            self.driver.switch_to.window(self.driver.window_handles[1])
            all_cookies['prospeo'] = self.driver.get_cookies()
            print("💾 Saved Prospeo cookies")
            
            # Save LinkedIn cookies
            self.driver.switch_to.window(self.driver.window_handles[2])
            all_cookies['linkedin'] = self.driver.get_cookies()
            print("💾 Saved LinkedIn cookies")
            
            # Save to file
            with open(cookies_file, 'wb') as f:
                pickle.dump(all_cookies, f)
            
            print(f"✅ All cookies saved to {cookies_file}")
            
        except Exception as e:
            print(f"❌ Failed to save cookies: {e}")

    def load_saved_cookies(self):
        """Load previously saved cookies"""
        try:
            import pickle
            profile_path = os.path.join(os.getcwd(), "chrome_profile_prospeo")
            cookies_file = os.path.join(profile_path, "saved_cookies.pkl")
            
            if not os.path.exists(cookies_file):
                print("ℹ️ No saved cookies found")
                return False
            
            with open(cookies_file, 'rb') as f:
                all_cookies = pickle.load(f)
            
            print("✅ Loaded saved cookies for all services")
            return all_cookies
            
        except Exception as e:
            print(f"❌ Failed to load cookies: {e}")
            return False
    
    def search_prospeo_emails(self, domain):
        """
        Scrape emails from Prospeo using the proven method from your original bot
        """
        if not self.driver:
            print("❌ Browser not started")
            return []

        try:
            print(f"🔍 Searching emails for {domain} on Prospeo...")
            
            # Navigate to Prospeo domain search
            self.driver.get("https://app.prospeo.io/domain-search")
            
            try:
                # Check if we're already logged in (search input should be visible)
                WebDriverWait(self.driver, 5).until(
                    EC.presence_of_element_located((By.CSS_SELECTOR, "input[name='company']"))
                )
                print("✅ Prospeo login session is active. Proceeding to search.")
            except TimeoutException:
                # Login required - pause for manual login
                print("\n⚠️ PROSPEO LOGIN REQUIRED")
                print("   The script will now pause. Please complete the login in the browser window.")
                input("   >>> After you have successfully logged in, press Enter to continue... <<<")
                
                print("\n✅ Resuming script. Navigating back to domain search...")
                self.driver.get("https://app.prospeo.io/domain-search")

            # Main scraping logic - updated selectors for current Prospeo interface
            input_field = WebDriverWait(self.driver, 15).until(
                EC.presence_of_element_located((By.CSS_SELECTOR, "input[name='company']"))
            )
            input_field.clear()
            input_field.send_keys(domain)
            print(f"   - Entered domain '{domain}'")

            # Look for the search/submit button near the input
            submit_button = WebDriverWait(self.driver, 10).until(
                EC.element_to_be_clickable((By.CSS_SELECTOR, "button.bg-red-500, button[type='submit'], .bg-red-500"))
            )
            self.driver.execute_script("arguments[0].click();", submit_button)
            print("   - Clicked search button")
            
            print("⏳ Waiting for search results (up to 90 seconds)...")
            # Wait for the loading animation to finish and results to appear
            try:
                WebDriverWait(self.driver, 90).until(
                    lambda driver: (
                        # Wait for search to complete (no more loading indicators)
                        "Searching..." not in driver.page_source and
                        "Loading..." not in driver.page_source and
                        (
                            driver.find_elements(By.CSS_SELECTOR, "div.css-b62m3t-container") or
                            driver.find_elements(By.CSS_SELECTOR, ".text-heading") or
                            driver.find_elements(By.CSS_SELECTOR, "[class*='email']") or
                            driver.find_elements(By.CSS_SELECTOR, "span[class*='text-md']") or
                            "No results found" in driver.page_source or
                            "emails found" in driver.page_source.lower()
                        )
                    )
                )
                print("✅ Initial results loaded.")
                
                # Wait additional time for all emails to render
                print("⏳ Waiting for email data to load...")
                time.sleep(20)  # Give extra time since this is dynamic content
                
                # Use a more robust check that doesn't rely on storing elements
                def check_for_emails(driver):
                    try:
                        # Check if page has emails by looking at page source
                        page_text = driver.page_source
                        if "No emails found" in page_text or "No results found" in page_text:
                            return True
                        
                        # Look for actual email addresses in the page
                        emails_found = len(re.findall(self.email_pattern, page_text))
                        print(f"   📊 Currently found {emails_found} emails on page")
                        return emails_found > 2  # Wait for a reasonable number of emails to load
                    except:
                        return False
                
                WebDriverWait(self.driver, 60).until(check_for_emails)
                print("✅ Email data loaded.")
                
            except TimeoutException:
                print("⚠️ Timeout waiting for results, but continuing...")
                # Additional wait for dynamic content
                print("⏳ Waiting additional 15 seconds for dynamic content...")
                WebDriverWait(self.driver, 15).until(lambda driver: True)  # Just wait
            
        except Exception as e:
            print(f"❌ Search phase failed: {e}")
            return []
            
        # Skip professional filter (was causing crashes)
        print("🔧 Skipping professional filter, will use AI to filter emails later...")
        
        # Scrape emails from results
        print("\n📧 Scraping emails from results...")
        
        # Wait specifically for email content to be loaded
        print("⏳ Waiting for email content to fully load...")
        try:
            def final_email_check(driver):
                try:
                    page_text = driver.page_source
                    return page_text.count('@') > 0 or "No emails found" in page_text
                except:
                    return False
            
            WebDriverWait(self.driver, 60).until(final_email_check)
            print("✅ Email content detected on page")
        except TimeoutException:
            print("⚠️ No email content detected, but continuing...")
            # Give it even more time as a final attempt
            print("⏳ Final wait attempt - 20 more seconds...")
            WebDriverWait(self.driver, 20).until(lambda driver: True)
        
        # Debug: Print page source snippet to understand structure
        print("🔍 Debugging page structure...")
        
        # Check current URL and page title for debugging
        current_url = self.driver.current_url
        page_title = self.driver.title
        print(f"   - Current URL: {current_url}")
        print(f"   - Page title: {page_title}")
        
        # Get initial page source
        page_source = self.driver.page_source
        
        # Check if we're actually on a results page
        if "domain-search" not in current_url:
            print(f"   ⚠️ Not on expected results page! Trying direct navigation...")
            # Try to navigate to results page manually
            results_url = f"https://app.prospeo.io/domain-search?domain={domain}"
            print(f"   🔄 Navigating to: {results_url}")
            self.driver.get(results_url)
            time.sleep(10)  # Wait for page to load
            print(f"   - New URL: {self.driver.current_url}")
            page_source = self.driver.page_source  # Refresh page source
        
        # Save page source for debugging
        try:
            with open("debug_search_page.html", "w", encoding="utf-8") as f:
                f.write(page_source)
            print("   💾 Page source saved to debug_search_page.html")
        except:
            pass
        
        # Check if we can find emails in the page source first
        all_emails_on_page = re.findall(self.email_pattern, page_source)
        print(f"   - Total emails found in page source: {len(all_emails_on_page)}")
        
        if all_emails_on_page:
            print(f"   - All emails found: {all_emails_on_page}")
            domain_emails = [email for email in all_emails_on_page if domain.lower() in email.lower()]
            print(f"   - Domain-specific emails in page source: {len(domain_emails)}")
            if domain_emails:
                for email in domain_emails[:3]:  # Show first 3
                    print(f"     - {email}")
        else:
            print("   - No emails found in page source at all")
        
        # Check for specific indicators that results loaded
        if "emails found" in page_source.lower():
            print("   ✅ Page contains 'emails found' indicator")
        if f"{domain}" in page_source:
            print(f"   ✅ Page contains domain '{domain}'")
        
        # Look for the specific LinkedIn email pattern from your screenshot
        linkedin_email_pattern = r'[a-zA-Z0-9._%+-]+@linkedin\.com'
        linkedin_emails = re.findall(linkedin_email_pattern, page_source)
        if linkedin_emails:
            print(f"   🎯 Found LinkedIn emails: {linkedin_emails}")
            
        # Save page source for debugging if needed
        if all_emails_on_page and not domain_emails:
            print("   💾 Saving page source for debugging...")
            with open('debug_prospeo_page.html', 'w', encoding='utf-8') as f:
                f.write(page_source)
            print("   💾 Page source saved to debug_prospeo_page.html")
        
        # Try the specific email selector first based on the actual Prospeo structure
        email_selectors = [
            "span.text-heading.text-md.font-light",  # Primary selector for Prospeo emails
            "span.text-heading",  # Backup without full class
            ".text-heading",
            "[class*='text-md']",
            "span[class*='font-light']",
            "*[class*='email']",
            "div[class*='result']",
            "td",
            "span",
            "div"
        ]
        
        found_emails = set()
        email_elements = []
        best_selector = None
        
        print("🔍 Testing email selectors...")
        for selector in email_selectors:
            try:
                # Re-find elements each time to avoid stale references
                elements = self.driver.find_elements(By.CSS_SELECTOR, selector)
                # Count elements that actually contain email addresses
                email_count = 0
                actual_emails = []
                
                for elem in elements:
                    try:
                        elem_text = elem.text.strip()
                        if '@' in elem_text and '.' in elem_text:
                            # Validate it's actually an email format
                            if re.match(r'^[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}$', elem_text):
                                email_count += 1
                                actual_emails.append(elem_text)
                    except:
                        continue  # Skip stale elements
                
                if email_count > 0:
                    print(f"   ✅ Found {email_count} valid emails with selector: {selector}")
                    for email in actual_emails[:3]:  # Show first 3
                        print(f"      📧 {email}")
                    best_selector = selector
                    found_emails.update(actual_emails)
                    break
                elif elements:
                    print(f"   - Found {len(elements)} elements (no emails) with selector: {selector}")
            except Exception as e:
                print(f"   ❌ Error with selector {selector}: {e}")
                continue
        
        if not best_selector or not found_emails:
            print("   - No email elements found with any selector. Trying page source fallback...")
            # Fallback: search entire page source for emails
            page_source = self.driver.page_source
            matches = re.findall(self.email_pattern, page_source)
            print(f"   - Found {len(matches)} emails in page source")
            
            for email in matches:
                # Add all emails first, then we'll filter by domain later
                found_emails.add(email.lower())
        
        # Return ALL emails found (AI will filter them later)
        if found_emails:
            all_emails_list = list(found_emails)
            print(f"📧 Found {len(all_emails_list)} total emails from {domain}")
            if all_emails_list:
                print(f"   ✅ Sample: {all_emails_list[:3]}{'...' if len(all_emails_list) > 3 else ''}")
            return all_emails_list
        else:
            print(f"📧 No emails found for {domain}")
            return []
    
    def clean_domain(self, domain_input):
        """Clean and validate domain - same as original"""
        domain = domain_input.strip().lower()
        domain = domain.replace('https://', '').replace('http://', '').replace('www.', '')
        domain = domain.split('/')[0]
        
        if '.' not in domain:
            return None
        
        return domain
    
    def find_emails(self, domain):
        """Main method to find emails - now uses Prospeo with AI filtering"""
        clean_domain = self.clean_domain(domain)
        if not clean_domain:
            print(f"❌ Invalid domain: {domain}")
            return []
        
        try:
            # Start browser
            if not self.start_browser():
                return []
            
            # Search Prospeo for ALL emails (not just domain-specific)
            all_emails = self.search_prospeo_emails(clean_domain)
            
            if not all_emails:
                print("\n🔍 Browser left open for debugging - close manually when done")
                return []
            
            # Filter emails using AI to identify real people
            print(f"\n🤖 AI filtering {len(all_emails)} emails...")
            filter_result = self.email_filter.filter_emails(all_emails, clean_domain)
            
            real_people_emails = filter_result.get('real_people', [])
            support_emails = filter_result.get('support_emails', [])
            analysis = filter_result.get('analysis', '')
            
            print(f"✅ AI Analysis: {analysis}")
            print(f"� Found {len(real_people_emails)} real people emails")
            print(f"🤖 Filtered out {len(support_emails)} support/generic emails")
            
            if real_people_emails:
                print(f"   Sample real people: {real_people_emails[:3]}{'...' if len(real_people_emails) > 3 else ''}")
            
            # Close browser on success
            self.close_browser()
            
            return real_people_emails
            
        except Exception as e:
            print(f"❌ Email scraping failed: {e}")
            # Close browser on error
            self.close_browser()
            return []
    
    def close_browser(self):
        """Close browser safely"""
        try:
            if self.driver:
                print("🔴 Closing email scraping browser...")
                self.driver.quit()
        except Exception as e:
            print(f"❌ Error closing browser: {e}")