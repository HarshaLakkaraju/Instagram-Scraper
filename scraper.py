# final_instascraper_inputjson.py
"""
Enhanced Instagram scraper with Modal Navigation for sequential post scraping
Now supports multiple usernames and proper session persistence

Usage:
  1) Create a .env file in same directory with:
       IG_USERNAME=your_username
       IG_PASSWORD=your_password
       HEADLESS=true_or_false  # optional
       CONTENT_TYPE=both       # posts, reels, or both
       POSTS_PER_PROFILE=4
       REELS_PER_PROFILE=2
  2) pip install python-dotenv selenium
  3) python final_instascraper_inputjson.py -u selenagomez natgeo instagram
"""

import json
import time
import random
import logging
import argparse
import pickle
import os
import sys
from datetime import datetime
from typing import List, Dict, Optional, Any
from selenium.webdriver.common.keys import Keys

# Selenium imports for browser automation and waiting
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.options import Options
from selenium.common.exceptions import TimeoutException, WebDriverException

# dotenv for loading credentials from .env
from dotenv import load_dotenv

# -----------------------------------------------------------------------------
# Configuration constants
# -----------------------------------------------------------------------------
DEFAULT_WAIT = 15
SHORT_WAIT = 5
POST_DISCOVERY_ATTEMPTS = 3
PROFILE_DELAY_MIN = 10
PROFILE_DELAY_MAX = 15
OUTPUT_DIR = "."
SHORT_WAIT_MIN = 4
SHORT_WAIT_MAX = 6

# Content type constants
CONTENT_POSTS = "posts"
CONTENT_REELS = "reels" 
CONTENT_BOTH = "both"

# Modal navigation constants
MODAL_NAVIGATION_ATTEMPTS = 3
MODAL_LOAD_WAIT = 8

# Session persistence
SESSION_FILE = "instagram_session.pkl"

# -----------------------------------------------------------------------------
# InstagramScraperWithLogin class
# -----------------------------------------------------------------------------
class InstagramScraperWithLogin:
    """
    Enhanced Instagram scraper with modal navigation for sequential post scraping
    """

    def __init__(self, headless: bool = False, wait_timeout: int = DEFAULT_WAIT, quiet: bool = False):
        """
        Initialize logger, driver, and explicit wait instance.
        """
        self.quiet = quiet
        self.setup_logging()
        if not quiet:
            self.logger.info("Initializing InstagramScraperWithLogin (Modal Navigation)...")

        # Setup browser driver
        self.driver = self.setup_driver(headless)
        # Explicit wait helper used across the class
        self.wait = WebDriverWait(self.driver, wait_timeout)

        if not quiet:
            self.logger.info("InstagramScraper initialized with Modal Navigation")

    # --------------------------- Logging -----------------------------------
    def setup_logging(self) -> None:
        """
        Configure logging to file and console with timestamped filename.
        """
        if self.quiet:
            # Disable all logging in quiet mode
            logging.basicConfig(level=logging.WARNING)
            self.logger = logging.getLogger(__name__)
            self.logger.setLevel(logging.WARNING)
            return

        ts = datetime.now().strftime("%Y%m%d_%H%M%S")
        log_path = os.path.join(OUTPUT_DIR, f"instagram_scraper_{ts}.log")

        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(levelname)s - %(message)s',
            handlers=[
                logging.FileHandler(log_path, encoding='utf-8'),
                logging.StreamHandler()
            ]
        )
        self.logger = logging.getLogger(__name__)
        self.logger.info(f"Logging started - file: {log_path}")

    # --------------------------- Driver Setup ------------------------------
    def setup_driver(self, headless: bool) -> webdriver.Chrome:
        """
        Build and return a configured Chrome WebDriver instance.
        """
        if not self.quiet:
            self.logger.info("Setting up Chrome driver...")
        chrome_options = Options()

        # Headless option (modern Chrome uses "--headless=new")
        if headless:
            chrome_options.add_argument("--headless=new")
            if not self.quiet:
                self.logger.info("Headless mode enabled")
        else:
            if not self.quiet:
                self.logger.info("Headless mode disabled (visible browser)")

        # Common arguments to improve stability and reduce crashes in containers
        chrome_options.add_argument("--no-sandbox")
        chrome_options.add_argument("--disable-dev-shm-usage")
        chrome_options.add_argument("--disable-blink-features=AutomationControlled")
        chrome_options.add_argument("--disable-features=IsolateOrigins,site-per-process")
        chrome_options.add_argument("--window-size=1920,1080")

        # Set a recent desktop-like user agent to reduce bot detection
        chrome_options.add_argument(
            "--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
            "AppleWebKit/537.36 (KHTML, like Gecko) "
            "Chrome/120.0.0.0 Safari/537.36"
        )

        # Avoid automation extension flags
        chrome_options.add_experimental_option("excludeSwitches", ["enable-automation"])
        chrome_options.add_experimental_option("useAutomationExtension", False)

        # Instantiate driver
        try:
            driver = webdriver.Chrome(options=chrome_options)
            # More robust stealth injection using CDP - set navigator.webdriver to undefined
            try:
                driver.execute_cdp_cmd(
                    "Page.addScriptToEvaluateOnNewDocument",
                    {
                        "source": "Object.defineProperty(navigator, 'webdriver', {get: () => undefined})"
                    }
                )
            except Exception:
                # Not critical — log and continue
                if not self.quiet:
                    self.logger.debug("CDP stealth script injection failed (non-critical)")

            # Set a sensible page load timeout (so driver.get doesn't hang forever)
            driver.set_page_load_timeout(30)
            if not self.quiet:
                self.logger.info("Chrome driver setup completed")
            return driver

        except WebDriverException as e:
            if not self.quiet:
                self.logger.error(f"Failed to start Chrome driver: {e}")
            raise

    # --------------------------- Session Management ------------------------
    def save_session(self) -> bool:
        """
        Save current session cookies to file for future use
        """
        try:
            # Ensure we're on Instagram domain to get proper cookies
            self.driver.get("https://www.instagram.com/")
            time.sleep(2)
            
            cookies = self.driver.get_cookies()
            session_data = {
                'cookies': cookies,
                'saved_at': datetime.now().isoformat(),
                'user_agent': self.driver.execute_script("return navigator.userAgent;")
            }
            
            with open(SESSION_FILE, 'wb') as f:
                pickle.dump(session_data, f)
                
            if not self.quiet:
                self.logger.info(f"Session saved to {SESSION_FILE} with {len(cookies)} cookies")
            return True
        except Exception as e:
            if not self.quiet:
                self.logger.error(f"Failed to save session: {e}")
            return False

    def load_session(self) -> bool:
        """
        Load session cookies from file and check if still valid
        """
        try:
            if not os.path.exists(SESSION_FILE):
                if not self.quiet:
                    self.logger.info("No session file found")
                return False

            with open(SESSION_FILE, 'rb') as f:
                session_data = pickle.load(f)
            # Navigate to Instagram first
            self.driver.get("https://www.instagram.com/")
            time.sleep(2)
            
            # Clear existing cookies and load saved ones
            self.driver.delete_all_cookies()
            
            for cookie in session_data['cookies']:
                try:
                    self.driver.add_cookie(cookie)
                except Exception as e:
                    if not self.quiet:
                        self.logger.debug(f"Could not add cookie: {e}")
                    continue

            # Refresh to apply cookies
            self.driver.refresh()
            time.sleep(3)

            # Check if we're logged in by trying to access a protected page
            return self._check_login_status()

        except Exception as e:
            if not self.quiet:
                self.logger.error(f"Failed to load session: {e}")
            # Clean up invalid session file
            try:
                #the session will be added with the list of cookies
                
                os.remove(SESSION_FILE)
            except:
                pass
            return False

    def _check_login_status(self) -> bool:
        """Check if we're properly logged in"""
        try:
            # Try multiple indicators of being logged in
            indicators = [
                "//input[@aria-label='Search']",
                "//a[contains(@href, '/direct/inbox/')]",
                "//span[contains(text(), 'Home')]",
                "//div[contains(text(), 'Search')]"
            ]
            
            for indicator in indicators:
                try:
                    WebDriverWait(self.driver, 5).until(
                        EC.presence_of_element_located((By.XPATH, indicator))
                    )
                    if not self.quiet:
                        self.logger.info("Session loaded successfully - logged in detected")
                    return True
                except TimeoutException:
                    continue
            
            # If no indicators found, check if we're redirected to login page
            current_url = self.driver.current_url
            if "accounts/login" in current_url or "login" in current_url:
                if not self.quiet:
                    self.logger.info("Session expired - redirected to login page")
                return False
                
            # If we're on Instagram but not logged in, try to check for login prompts
            try:
                login_elements = self.driver.find_elements(By.XPATH, "//button[contains(text(), 'Log in')]")
                if login_elements:
                    if not self.quiet:
                        self.logger.info("Session expired - login button present")
                    return False
            except:
                pass
                
            # Conservative approach - if we can't confirm login, assume not logged in
            if not self.quiet:
                self.logger.info("Cannot confirm login status - assuming session expired")
            return False
            
        except Exception as e:
            if not self.quiet:
                self.logger.debug(f"Error checking login status: {e}")
            return False

    # --------------------------- Login ------------------------------------
    def login(self, username: str, password: str, use_session: bool = True) -> bool:
        """
        Login to Instagram using provided credentials or saved session.
        Returns True when login appears successful, False otherwise.
        """
        # Try to load existing session first
        if use_session and self.load_session():
            return True

        if not self.quiet:
            self.logger.info(f"Attempting fresh login as: {username}")

        try:
            # Clear any existing cookies first
            self.driver.delete_all_cookies()
            
            # Open the login page and wait for the username field
            self.driver.get("https://www.instagram.com/accounts/login/")
            time.sleep(2)
            
            # Wait for the username input to appear
            self.wait.until(EC.presence_of_element_located((By.NAME, "username")))

            # Fill in username/password fields
            username_field = self.driver.find_element(By.NAME, "username")
            username_field.clear()
            username_field.send_keys(username)
            if not self.quiet:
                self.logger.debug("Entered username")

            password_field = self.driver.find_element(By.NAME, "password")
            password_field.clear()
            password_field.send_keys(password)
            if not self.quiet:
                self.logger.debug("Entered password")

            # Click the login submit button (type='submit')
            login_button = self.driver.find_element(By.XPATH, "//button[@type='submit']")
            login_button.click()
            if not self.quiet:
                self.logger.info("Login submitted - waiting for post-login state")
            time.sleep(random.uniform(2.0, 3.0))

            # Handle possible login challenges
            current_url = self.driver.current_url
            
            # Check for various post-login states
            if "challenge" in current_url or "two_factor" in current_url:
                if not self.quiet:
                    self.logger.warning("Login challenge detected - manual intervention may be required")
                # Wait a bit longer for challenge
                time.sleep(5)
            
            # Wait for either the home page to load or for a login error
            try:
                # Wait for indicators of successful login
                WebDriverWait(self.driver, 15).until(
                    lambda driver: any([
                        driver.find_elements(By.XPATH, "//input[@aria-label='Search']"),
                        driver.find_elements(By.XPATH, "//a[contains(@href, '/direct/inbox/')]"),
                        driver.find_elements(By.XPATH, "//span[contains(text(), 'Home')]")
                    ])
                )
                
                if not self.quiet:
                    self.logger.info("Login successful - home page detected")
                
                # Save session for future use
                if use_session:
                    self.save_session()
                return True
                
            except TimeoutException:
                # Check if login failed
                try:
                    error_element = self.driver.find_element(By.ID, "slfErrorAlert")
                    if error_element:
                        if not self.quiet:
                            self.logger.error("Login failed - incorrect credentials")
                        return False
                except:
                    pass
                    
                # If we're not on login page but no home page elements, check current URL
                current_url = self.driver.current_url
                if "accounts/login" in current_url:
                    if not self.quiet:
                        self.logger.error("Login failed - still on login page")
                    return False
                else:
                    # We're not on login page but couldn't find home elements - conservative approach
                    if not self.quiet:
                        self.logger.warning("Unclear login status - proceeding cautiously")
                    # Still save session as we might be logged in
                    if use_session:
                        self.save_session()
                    return True

        except Exception as e:
            if not self.quiet:
                self.logger.error(f"Login encountered an exception: {e}")
            return False

    # --------------------------- Enhanced Profile Scrape ---------------------------
    def scrape_profile_content(self, username: str, num_posts: int = 3, num_reels: int = 3, 
                             content_type: str = CONTENT_BOTH) -> Dict[str, Any]:
        """
        Enhanced: Scrape posts AND/OR reels from user's profile using modal navigation for posts.
        """
        if not self.quiet:
            self.logger.info(f"STARTING ENHANCED SCRAPE FOR: {username} (posts: {num_posts}, reels: {num_reels})")
        profile_url = f"https://www.instagram.com/{username}/"
        
        profile_data = {
            "username": username,
            "profile_url": profile_url,
            "scraped_at": datetime.now().isoformat(),
            "posts": [],
            "reels": []
        }

        try:
            # Navigate to profile
            self.driver.get(profile_url)
            if not self.quiet:
                self.logger.info(f"Navigated to {profile_url}")

            # Wait for profile to load properly
            if not self._wait_for_profile_load():
                if not self.quiet:
                    self.logger.error(f"Profile failed to load: {username}")
                return profile_data

            # Check for redirects to login (session might have expired during scraping)
            current_url = self.driver.current_url
            if "accounts/login" in current_url or "challenge" in current_url:
                if not self.quiet:
                    self.logger.error("Redirected to login/challenge page - session may have expired")
                return profile_data

            # Scrape posts using modal navigation
            if content_type in [CONTENT_POSTS, CONTENT_BOTH] and num_posts > 0:
                posts_data = self.scrape_posts_via_modal_navigation(username, num_posts)
                profile_data["posts"] = posts_data
                if not self.quiet:
                    self.logger.info(f"Modal navigation: {len(posts_data)} posts collected")

            # Scrape reels using traditional method
            if content_type in [CONTENT_REELS, CONTENT_BOTH] and num_reels > 0:
                reels_data = self.scrape_reels_traditional(num_reels)
                profile_data["reels"] = reels_data
                if not self.quiet:
                    self.logger.info(f"Traditional method: {len(reels_data)} reels collected")

            return profile_data

        except Exception as e:
            if not self.quiet:
                self.logger.error(f"ERROR scraping {username}: {e}")
            return profile_data

    def _wait_for_profile_load(self) -> bool:
        """Wait for profile to load properly"""
        try:
            # Wait for either posts or profile header to appear
            WebDriverWait(self.driver, 15).until(
                lambda driver: any([
                    driver.find_elements(By.XPATH, "//a[contains(@href, '/p/')]"),
                    driver.find_elements(By.XPATH, "//a[contains(@href, '/reel/')]"),
                    driver.find_elements(By.XPATH, "//header"),
                    driver.find_elements(By.TAG_NAME, "article")
                ])
            )
            return True
        except TimeoutException:
            if not self.quiet:
                self.logger.warning("Profile load timeout - proceeding anyway")
            return True  # Continue and try to scrape what's available

    # --------------------------- Modal Navigation for Posts ---------------------------
    def scrape_posts_via_modal_navigation(self, username: str, num_posts: int = 3) -> List[Dict]:
        """
        NEW: Scrape posts by opening the first post and using right arrow navigation.
        This ensures we get posts in the correct chronological order.
        """
        if not self.quiet:
            self.logger.info(f"Starting modal navigation scraping for {username} (target: {num_posts} posts)")
        
        posts_data = []
        
        try:
            # Click on the first post to open modal
            first_post_clicked = self._click_first_post()
            if not first_post_clicked:
                if not self.quiet:
                    self.logger.error(f"Could not click first post for {username}")
                return posts_data

            # Wait for modal to load and get initial post
            time.sleep(random.uniform(2.0, 3.0))
            
            # Navigate through posts using right arrow
            posts_data = self._navigate_posts_via_arrows(num_posts)
            
            # Close modal when done
            self._close_modal()
            
            if not self.quiet:
                self.logger.info(f"Modal navigation completed: {len(posts_data)} posts collected")
            return posts_data

        except Exception as e:
            if not self.quiet:
                self.logger.error(f"Modal navigation failed for {username}: {e}")
            # Ensure modal is closed on error
            try:
                self._close_modal()
            except:
                pass
            return posts_data

    def _click_first_post(self) -> bool:
        """Click the first post in the profile grid to open modal"""
        try:
            # Multiple strategies to find and click first post
            selectors = [
                # Primary selector for post thumbnails
                "//article//a[contains(@href, '/p/')]",
                "//div[contains(@class, '_aagw')]//a",  # Post container
                "//a[contains(@href, '/p/')][1]",  # First post link
            ]
            
            for selector in selectors:
                try:
                    first_post = WebDriverWait(self.driver, 8).until(
                        EC.element_to_be_clickable((By.XPATH, selector))
                    )
                    first_post.click()
                    if not self.quiet:
                        self.logger.debug("Successfully clicked first post")
                    return True
                except (TimeoutException, Exception):
                    continue
            
            if not self.quiet:
                self.logger.warning("Could not find clickable first post with any selector")
            return False
            
        except Exception as e:
            if not self.quiet:
                self.logger.error(f"Error clicking first post: {e}")
            return False

    def _navigate_posts_via_arrows(self, num_posts: int) -> List[Dict]:
        """
        Navigate through posts using right arrow key or next button
        Returns list of post data in chronological order
        """
        posts_data = []
        attempts = 0
        max_attempts = num_posts + 2  # Allow some extra attempts
        
        while len(posts_data) < num_posts and attempts < max_attempts:
            attempts += 1
            try:
                # Get current post URL from modal
                current_post_url = self._get_current_modal_post_url()
                if current_post_url and current_post_url not in [p.get('content_url') for p in posts_data]:
                    
                    post_data = {
                        "content_url": current_post_url,
                        "content_id": self.extract_content_id(current_post_url),
                        "scraped_at": datetime.now().isoformat(),
                        "content_type": "post",
                        "order": len(posts_data) + 1
                    }
                    posts_data.append(post_data)
                    if not self.quiet:
                        self.logger.debug(f"Collected post {len(posts_data)}: {post_data['content_id']}")
                
                # Stop if we have enough posts
                if len(posts_data) >= num_posts:
                    break
                    
                # Navigate to next post
                if not self._go_to_next_post():
                    if not self.quiet:
                        self.logger.debug("No next post available")
                    break
                    
                # Wait for next post to load
                time.sleep(random.uniform(1.5, 2.5))
                
            except Exception as e:
                if not self.quiet:
                    self.logger.debug(f"Error during post navigation attempt {attempts}: {e}")
                break
        
        return posts_data

    def _get_current_modal_post_url(self) -> Optional[str]:
        """Get the current post URL from the modal"""
        try:
            # Get the current URL from browser address bar
            current_url = self.driver.current_url
            
            # Check if we're in a post modal (URL contains '/p/')
            if "/p/" not in current_url:
                return None
                
            # Clean the URL by removing any unwanted segments
            clean_url = current_url.split('/liked_by')[0].split('/comments')[0].split('/tagged')[0].split('?')[0]
            
            # Ensure it ends with just the post ID (no trailing unwanted segments)
            if not clean_url.endswith('/'):
                clean_url += '/'
                
            if not self.quiet:
                self.logger.debug(f"Extracted clean post URL: {clean_url}")
            return clean_url
            
        except Exception as e:
            if not self.quiet:
                self.logger.debug(f"Error getting modal URL from browser: {e}")
            return None

    def _go_to_next_post(self) -> bool:
        """
        Navigate to next post using right arrow button or keyboard
        Returns True if successful, False if no next post
        """
        try:
            # Strategy 1: Click next button (right arrow)
            next_button_selectors = [
                "//button[contains(@class, '_acah')]",  # Right arrow button
                "//button[contains(@class, '_aade')]",  # Alternative next button
                "//button[.//*[local-name()='svg']]",   # SVG arrow button
            ]
            
            for selector in next_button_selectors:
                try:
                    next_btn = WebDriverWait(self.driver, 3).until(
                        EC.element_to_be_clickable((By.XPATH, selector))
                    )
                    next_btn.click()
                    if not self.quiet:
                        self.logger.debug("Clicked next button successfully")
                    return True
                except (TimeoutException, Exception):
                    continue
            
            # Strategy 2: Use keyboard right arrow (fallback)
            try:
                body = self.driver.find_element(By.TAG_NAME, 'body')
                body.send_keys(Keys.ARROW_RIGHT)
                if not self.quiet:
                    self.logger.debug("Used keyboard right arrow")
                return True
            except Exception:
                pass
                
            # Strategy 3: JavaScript click on next element
            try:
                self.driver.execute_script("""
                    var nextBtn = document.querySelector('button[class*="_acah"], button[class*="_aade"]');
                    if (nextBtn) nextBtn.click();
                """)
                if not self.quiet:
                    self.logger.debug("Used JavaScript click for next button")
                return True
            except Exception:
                pass
                
            if not self.quiet:
                self.logger.debug("No next post navigation method worked")
            return False
            
        except Exception as e:
            if not self.quiet:
                self.logger.debug(f"Error navigating to next post: {e}")
            return False

    def _close_modal(self) -> bool:
        """Close the post modal"""
        try:
            # Multiple close button selectors
            close_selectors = [
                "//button[contains(@class, '_acab')]",  # X button
                "//button[.//*[local-name()='svg']][@aria-label='Close']",
                "//div[contains(@role, 'button')][@aria-label='Close']",
            ]
            
            for selector in close_selectors:
                try:
                    close_btn = WebDriverWait(self.driver, 3).until(
                        EC.element_to_be_clickable((By.XPATH, selector))
                    )
                    close_btn.click()
                    if not self.quiet:
                        self.logger.debug("Modal closed successfully")
                    return True
                except (TimeoutException, Exception):
                    continue
            
            # Fallback: ESC key
            try:
                body = self.driver.find_element(By.TAG_NAME, 'body')
                body.send_keys(Keys.ESCAPE)
                if not self.quiet:
                    self.logger.debug("Used ESC key to close modal")
                return True
            except Exception:
                pass
                
            return False
            
        except Exception as e:
            if not self.quiet:
                self.logger.debug(f"Error closing modal: {e}")
            return False

    # --------------------------- Traditional Reels Scraping ---------------------------
    def scrape_reels_traditional(self, num_reels: int = 3) -> List[Dict]:
        """
        Scrape reels using traditional link discovery method
        """
        if not self.quiet:
            self.logger.info(f"Starting traditional reels scraping (target: {num_reels} reels)")
        
        reels_data = []
        
        try:
            # Find reel URLs using traditional method
            reel_urls = self._find_reel_urls(num_reels)
            
            for i, reel_url in enumerate(reel_urls):
                time.sleep(random.uniform(0.2, 0.7))
                reel_item = {
                    "content_url": reel_url,
                    "content_id": self.extract_content_id(reel_url),
                    "scraped_at": datetime.now().isoformat(),
                    "content_type": "reel",
                    "order": i + 1
                }
                reels_data.append(reel_item)
            
            if not self.quiet:
                self.logger.info(f"Traditional reels scraping completed: {len(reels_data)} reels collected")
            return reels_data
            
        except Exception as e:
            if not self.quiet:
                self.logger.error(f"Traditional reels scraping failed: {e}")
            return reels_data

    def _find_reel_urls(self, max_reels: int) -> List[str]:
        """
        Discover reel URLs on the current profile page.
        """
        if not self.quiet:
            self.logger.info("Starting reel discovery...")

        reel_urls = []

        try:
            # Wait until some anchors are present to avoid empty discovery
            try:
                short_wait_time = random.uniform(SHORT_WAIT_MIN, SHORT_WAIT_MAX)
                short_wait = WebDriverWait(self.driver, short_wait_time) 
                short_wait.until(EC.presence_of_all_elements_located((By.TAG_NAME, "a")))
            except TimeoutException:
                if not self.quiet:
                    self.logger.debug("No anchors found within SHORT_WAIT; attempting to fetch any anchors available")

            # Collect hrefs from all anchor elements
            anchors = self.driver.find_elements(By.TAG_NAME, "a")
            ordered_reel_urls = []
            
            for a in anchors:
                try:
                    href = a.get_attribute("href")
                    if href and "/reel/" in href and href not in ordered_reel_urls:
                        ordered_reel_urls.append(href)
                        if len(ordered_reel_urls) >= max_reels:
                            break
                except Exception:
                    continue

            reel_urls = ordered_reel_urls
            if not self.quiet:
                self.logger.info(f"Discovered {len(reel_urls)} reel URL(s)")
            return reel_urls

        except Exception as e:
            if not self.quiet:
                self.logger.error(f"_find_reel_urls encountered an exception: {e}")
            return reel_urls

    # --------------------------- Utility Methods ---------------------------
    def extract_content_id(self, content_url: str) -> str:
        """
        Extract the canonical short-code from post OR reel URL.
        Enhanced version with reels support.
        """
        try:
            if "/p/" in content_url:
                content_id = content_url.split("/p/")[1].split("/")[0]
            elif "/reel/" in content_url:
                content_id = content_url.split("/reel/")[1].split("/")[0]
            else:
                content_id = "unknown"
            
            if not self.quiet:
                self.logger.debug(f"Extracted content id: {content_id}")
            return content_id
        except Exception:
            if not self.quiet:
                self.logger.debug("Could not extract content id from URL")
            return "unknown"

    # --------------------------- Multiple Profiles Scrape ----------------------------
    def scrape_multiple_profiles(self, usernames: List[str], posts_per_profile: int = 4, 
                               reels_per_profile: int = 2, content_type: str = CONTENT_BOTH) -> Dict[str, Any]:
        """
        Scrape multiple profiles and return combined results as JSON
        """
        if not self.quiet:
            self.logger.info(f"STARTING MULTI-PROFILE SCRAPE: {len(usernames)} users")
        
        all_results = {
            "profiles": [],
            "summary": {
                "total_profiles": len(usernames),
                "successful_profiles": 0,
                "total_posts": 0,
                "total_reels": 0,
                "scraped_at": datetime.now().isoformat()
            }
        }

        for i, username in enumerate(usernames, 1):
            if not self.quiet:
                self.logger.info(f"Scraping profile {i}/{len(usernames)}: {username}")
            
            start_time = time.time()
            profile_data = self.scrape_profile_content(
                username, 
                num_posts=posts_per_profile, 
                num_reels=reels_per_profile, 
                content_type=content_type
            )
            elapsed = time.time() - start_time

            # Create individual profile result
            profile_result = {
                "profile": profile_data,
                "summary": {
                    "username": username,
                    "posts_count": len(profile_data.get("posts", [])),
                    "reels_count": len(profile_data.get("reels", [])),
                    "scraping_time_seconds": round(elapsed, 2),
                    "success": len(profile_data.get("posts", [])) > 0 or len(profile_data.get("reels", [])) > 0
                }
            }

            # Update combined results
            all_results["profiles"].append(profile_result)
            
            if profile_result["summary"]["success"]:
                all_results["summary"]["successful_profiles"] += 1
                all_results["summary"]["total_posts"] += profile_result["summary"]["posts_count"]
                all_results["summary"]["total_reels"] += profile_result["summary"]["reels_count"]
                if not self.quiet:
                    self.logger.info(f"SUCCESS: {username} - {profile_result['summary']['posts_count']} posts, {profile_result['summary']['reels_count']} reels in {elapsed:.2f}s")
            else:
                if not self.quiet:
                    self.logger.warning(f"FAILED/EMPTY: {username} (completed in {elapsed:.2f}s)")

            # Add delay between profiles (except for the last one)
            if i < len(usernames):
                delay = random.randint(PROFILE_DELAY_MIN, PROFILE_DELAY_MAX)
                if not self.quiet:
                    self.logger.info(f"Waiting {delay}s before next profile")
                time.sleep(delay)

        # Calculate success rate
        total = all_results["summary"]["total_profiles"]
        success_count = all_results["summary"]["successful_profiles"]
        all_results["summary"]["success_rate"] = round((success_count / total * 100) if total else 0.0, 2)

        if not self.quiet:
            self.logger.info(f"MULTI-PROFILE SCRAPE COMPLETE: {success_count}/{total} successful")
        return all_results

    # --------------------------- Close -----------------------------------
    def close(self) -> None:
        """
        Close the WebDriver and clean up resources.
        """
        if not self.quiet:
            self.logger.info("Closing browser...")
        try:
            if self.driver:
                self.driver.quit()
                if not self.quiet:
                    self.logger.info("Browser closed")
        except Exception as e:
            if not self.quiet:
                self.logger.debug(f"Exception during driver.quit(): {e}")

# -----------------------------------------------------------------------------
# Command-line argument parsing
# -----------------------------------------------------------------------------
def parse_arguments():
    """Parse command-line arguments"""
    parser = argparse.ArgumentParser(description='Instagram Scraper for multiple users')
    parser.add_argument('-u', '--users', required=True, nargs='+', 
                       help='Instagram usernames to scrape (space-separated)')
    parser.add_argument('-p', '--posts', type=int, default=4, 
                       help='Number of posts to scrape per profile (default: 4)')
    parser.add_argument('-r', '--reels', type=int, default=2, 
                       help='Number of reels to scrape per profile (default: 2)')
    parser.add_argument('-t', '--type', choices=['posts', 'reels', 'both'], default='both', 
                       help='Content type to scrape (default: both)')
    parser.add_argument('--no-session', action='store_true', 
                       help='Disable session persistence (force fresh login)')
    parser.add_argument('--quiet', action='store_true',
                       help='Suppress all logging output (only JSON output)')
    
    return parser.parse_args()

# -----------------------------------------------------------------------------
# Main entrypoint
# -----------------------------------------------------------------------------
def main():
    """
    Enhanced main function is with support for multiple usernames and proper session persistence
    """
    # Parse command-line arguments
    args = parse_arguments()
    
    # Load environment variables from .env in current directory
    load_dotenv()
    IG_USERNAME = os.getenv("IG_USERNAME")
    IG_PASSWORD = os.getenv("IG_PASSWORD")
    HEADLESS_ENV = os.getenv("HEADLESS", "false").lower()
    HEADLESS = HEADLESS_ENV in ("1", "true", "yes")
    
    # Use command-line arguments
    CONTENT_TYPE = args.type
    POSTS_PER_PROFILE = args.posts
    REELS_PER_PROFILE = args.reels
    TARGET_USERS = args.users
    USE_SESSION = not args.no_session
    QUIET_MODE = args.quiet

    if not IG_USERNAME or not IG_PASSWORD:
        if not QUIET_MODE:
            print("ERROR: IG_USERNAME and IG_PASSWORD must be set in a .env file in the script directory.", file=sys.stderr)
            print("Create a .env file with:", file=sys.stderr)
            print("IG_USERNAME=your_username", file=sys.stderr)
            print("IG_PASSWORD=your_password", file=sys.stderr)
        sys.exit(1)

    scraper = None
    try:
        # Initialize scraper with the chosen headless setting
        scraper = InstagramScraperWithLogin(headless=HEADLESS, quiet=QUIET_MODE)

        # Attempt login (with session persistence)
        if not QUIET_MODE:
            print("Attempting login...", file=sys.stderr)
        ok = scraper.login(IG_USERNAME, IG_PASSWORD, use_session=USE_SESSION)
        if not ok:
            if not QUIET_MODE:
                print("Login failed. Please check credentials or account challenge.", file=sys.stderr)
            sys.exit(1)

        # Small pause after login for stability
        time.sleep(random.uniform(2.4, 4.0))

        # Scrape multiple profiles
        results = scraper.scrape_multiple_profiles(
            usernames=TARGET_USERS,
            posts_per_profile=POSTS_PER_PROFILE,
            reels_per_profile=REELS_PER_PROFILE,
            content_type=CONTENT_TYPE
        )

        # Output results as JSON to stdout
        json.dump(results, sys.stdout, indent=2, ensure_ascii=False)
        sys.stdout.write('\n')  # Add newline at the end

    except Exception as e:
        if not QUIET_MODE:
            print(f"Critical error: {e}", file=sys.stderr)
        sys.exit(1)
    finally:
        if scraper:
            scraper.close()

if __name__ == "__main__":
    main()



''' this file handles instagram scraping 
with session persistence and enhanced scraping methods ''' 
