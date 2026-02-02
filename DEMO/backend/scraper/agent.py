import logging
import random
import time
import re
import json
import os
import undetected_chromedriver as uc
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.action_chains import ActionChains

# Import ProxyManager
try:
    from backend.core.proxies import ProxyManager
except ImportError:
    # Fallback for direct testing
    import sys
    sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))
    from backend.core.proxies import ProxyManager

class ScraperAgent:
    def __init__(self, headless=False, proxy_manager: ProxyManager = None):
        self.logger = logging.getLogger(__name__)
        self.proxy_manager = proxy_manager
        self.selectors = self._load_selectors()
        self.driver = self._init_driver(headless)
        self.logger.info(f"ScraperAgent initialized (Headless: {headless})")
        self._inject_stealth()

    def _load_selectors(self):
        try:
            path = os.path.join(os.path.dirname(__file__), 'selectors.json')
            with open(path, 'r') as f:
                return json.load(f)
        except Exception as e:
            self.logger.error(f"Failed to load selectors: {e}")
            # Fallback defaults
            return {
                "feed": "//div[@role='feed']",
                "consent_accept": "//button//span[contains(text(), 'Accept')]/..",
                "consent_accept_aria": "//button[contains(@aria-label, 'Accept')]",
                "card_css": "div[role='article']",
                "card_link_css": "a",
                "captcha_sitekey": "[data-sitekey]",
                "captcha_submit_id": "recaptcha-demo-submit",
                "captcha_submit_css": "input[type='submit']"
            }

    def _init_driver(self, headless):
        options = uc.ChromeOptions()
        if headless:
            options.add_argument('--headless=new')

        # Basic stability options
        options.add_argument('--no-sandbox')
        options.add_argument('--disable-dev-shm-usage')
        options.add_argument('--start-maximized')
        options.add_argument('--disable-popup-blocking')
        options.add_argument('--lang=en-US')
        
        # COST MANAGEMENT: Block images to save bandwidth
        chrome_prefs = {
            "profile.managed_default_content_settings.images": 2,
            "profile.default_content_setting_values.notifications": 2
        }
        options.add_experimental_option("prefs", chrome_prefs)
        
        # Proxy Injection
        if self.proxy_manager:
            proxy = self.proxy_manager.get_next_proxy()
            if proxy:
                self.logger.info(f"Using proxy: {proxy}")
                options.add_argument(f'--proxy-server={proxy}')

        try:
            # version_main=None allows generic version matching
            driver = uc.Chrome(options=options, use_subprocess=True, version_main=None)
        except Exception as e:
            self.logger.error(f"Failed to initialize UC driver: {e}")
            raise e
        
        return driver

    def _inject_stealth(self):
        """
        Injects JavaScript to spoof Canvas, WebGL, and AudioContext fingerprints.
        This is crucial for avoiding detection by advanced anti-bots.
        """
        stealth_js = """
        // 1. Spoof WebGL Vendor/Renderer
        try {
            const getParameter = WebGLRenderingContext.prototype.getParameter;
            WebGLRenderingContext.prototype.getParameter = function(parameter) {
                if (parameter === 37445) return 'Intel Inc.'; // UNMASKED_VENDOR_WEBGL
                if (parameter === 37446) return 'Intel Iris OpenGL Engine'; // UNMASKED_RENDERER_WEBGL
                return getParameter(parameter);
            };
        } catch (e) {}

        // 2. Add noise to Canvas
        try {
            const toDataURL = HTMLCanvasElement.prototype.toDataURL;
            HTMLCanvasElement.prototype.toDataURL = function(type) {
                const context = this.getContext('2d');
                if (context) {
                    const shift = Math.floor(Math.random() * 10) - 5;
                    context.fillStyle = 'rgba(255,255,255,0.01)'; 
                    context.fillRect(0, 0, 1, 1); // Draw 1px invisible noise
                }
                return toDataURL.apply(this, arguments);
            };
        } catch (e) {}

        // 3. Spoof Hardware Concurrency (if needed)
        Object.defineProperty(navigator, 'hardwareConcurrency', { get: () => 8 });
        
        // 4. Spoof Languages
        Object.defineProperty(navigator, 'languages', { get: () => ['en-US', 'en'] });
        
        // 5. Hide WebDriver (UC does this, but redundancy helps)
        Object.defineProperty(navigator, 'webdriver', { get: () => undefined });
        """
        try:
            self.driver.execute_cdp_cmd("Page.addScriptToEvaluateOnNewDocument", {
                "source": stealth_js
            })
            self.logger.info("Stealth scripts injected via CDP.")
        except Exception as e:
            self.logger.warning(f"Failed to inject CDP stealth scripts: {e}")

    def random_sleep(self, min_s=2, max_s=5):
        time.sleep(random.uniform(min_s, max_s))

    def _human_mouse_move(self):
        """Simulates tiny random mouse movements."""
        try:
            action = ActionChains(self.driver)
            # Move by small offset
            x_offset = random.randint(-5, 5)
            y_offset = random.randint(-5, 5)
            action.move_by_offset(x_offset, y_offset).perform()
        except:
            pass

    def human_scroll(self, element):
        """
        Simulates human variable scrolling (including pauses and scroll-backs).
        """
        try:
            total_height = self.driver.execute_script("return arguments[0].scrollHeight", element)
            current_pos = 0
            consecutive_no_change = 0

            # Safety limit
            start_time = time.time()
            max_scroll_time = 120 # 2 minutes max scroll

            while current_pos < total_height and (time.time() - start_time) < max_scroll_time:
                step = random.randint(300, 700)
                current_pos += step
                self.driver.execute_script(f"arguments[0].scrollTo(0, {current_pos});", element)
                
                # HUMAN BEHAVIOR: Random small scroll up (reading behavior)
                if random.random() < 0.2: # 20% chance
                    scroll_up = random.randint(50, 150)
                    self.driver.execute_script(f"arguments[0].scrollBy(0, -{scroll_up});", element)
                    time.sleep(0.5)
                    self.driver.execute_script(f"arguments[0].scrollBy(0, {scroll_up});", element)

                # HUMAN BEHAVIOR: Random mouse move
                if random.random() < 0.3:
                    self._human_mouse_move()

                # Random pause
                self.random_sleep(0.8, 2.0)
                
                new_height = self.driver.execute_script("return arguments[0].scrollHeight", element)
                if new_height > total_height:
                    total_height = new_height
                    consecutive_no_change = 0
                elif current_pos >= total_height:
                    # Try to trigger load by verifying bottom
                    consecutive_no_change += 1
                
                # Check for "End of list" text visibility
                # Can be enhanced with actual element check if selector known
                if consecutive_no_change > 3:
                     if "reached the end" in self.driver.page_source:
                         break
                     
                if consecutive_no_change > 6:
                    break
        except Exception as e:
            self.logger.warning(f"Scroll error: {e}")

    def search_area(self, lat, lon, query="restaurants"):
        try:
            # We construct the URL with the query
            url = f"https://www.google.com/maps/search/{query}/@{lat},{lon},16z"
            self.driver.get(url)
            self.random_sleep(3, 5)

            self._handle_consent()

            # Wait for Feed OR Captcha
            xpath_feed = self.selectors['feed']
            try:
                # Check for "Sorry" page (Captcha)
                if "google.com/sorry" in self.driver.current_url:
                    self.logger.warning("Google Captcha Detected!")
                    if self._handle_captcha():
                        self.logger.info("Captcha solved. Retrying search...")
                        return self.search_area(lat, lon, query) # Recursive retry
                    else:
                        self.logger.error("Failed to solve captcha.")
                        return []

                WebDriverWait(self.driver, 20).until(
                    EC.presence_of_element_located((By.XPATH, xpath_feed))
                )
                feed = self.driver.find_element(By.XPATH, xpath_feed)
            except Exception as e:
                # Double check for captcha if timeout
                if "sorry" in self.driver.current_url or "CAPTCHA" in self.driver.page_source:
                     self.logger.warning("Google Captcha Detected (Timeout)!")
                     if self._handle_captcha():
                        return self.search_area(lat, lon, query)

                self.logger.warning(f"No feed found or timeout. {e}")
                return []

            self.logger.info("Feed loaded. Scrolling...")
            self.human_scroll(feed)
            self.random_sleep(2, 3)

            return self.extract_detailed_results(feed)

        except Exception as e:
            self.logger.error(f"Search failed: {e}")
            return []

    def _handle_captcha(self):
        """
        Attempts to solve CAPTCHA using 2Captcha.
        """
        from backend.core.config_manager import ConfigManager
        from backend.core.captcha_solver import CaptchaSolver
        
        cfg = ConfigManager()
        api_key = cfg.get_captcha_key()
        
        if not api_key:
            self.logger.error("Captcha detected but no API key configured. Manual intervention required or rotate proxy.")
            # Optionally wait for manual solve if visible mode?
            time.sleep(60) 
            return False
            
        solver = CaptchaSolver(api_key)
        
        try:
            # Find sitekey
            sitekey_elem = self.driver.find_element(By.CSS_SELECTOR, self.selectors.get('captcha_sitekey', "[data-sitekey]"))
            sitekey = sitekey_elem.get_attribute("data-sitekey")
            
            if not sitekey:
                self.logger.error("Could not find sitekey.")
                return False
                
            token = solver.solve_recaptcha_v2(sitekey, self.driver.current_url)
            if token:
                # Inject token
                js = f'document.getElementById("g-recaptcha-response").innerHTML="{token}";'
                self.driver.execute_script(js)
                self.random_sleep(1, 2)
                
                # Click submit
                submit_id = self.selectors.get('captcha_submit_id', "recaptcha-demo-submit")
                try:
                    submit_btn = self.driver.find_element(By.ID, submit_id)
                except:
                    submit_btn = None

                if not submit_btn:
                     submit_css = self.selectors.get('captcha_submit_css', "input[type='submit']")
                     submit_btn = self.driver.find_element(By.CSS_SELECTOR, submit_css)
                     
                if submit_btn:
                    submit_btn.click()
                    self.random_sleep(5, 10)
                    return True
        except Exception as e:
            self.logger.error(f"Captcha solve failed: {e}")
            
        return False

    def _handle_consent(self):
        try:
            buttons = self.driver.find_elements(By.XPATH, self.selectors['consent_accept']) 
            if not buttons:
                 buttons = self.driver.find_elements(By.XPATH, self.selectors['consent_accept_aria'])

            if buttons:
                buttons[0].click()
                self.random_sleep(1, 2)
        except:
            pass

    def extract_detailed_results(self, feed_element):
        results = []
        cards = feed_element.find_elements(By.CSS_SELECTOR, self.selectors['card_css'])
        self.logger.info(f"Parsing {len(cards)} cards...")

        for card in cards:
            try:
                # 1. Link & Coords
                href = None
                coords = None
                try:
                    link_elem = card.find_element(By.CSS_SELECTOR, self.selectors['card_link_css'])
                    href = link_elem.get_attribute("href")
                    coords = self._parse_coords_from_url(href)
                except: pass
                
                # Extract Place ID (data-id attribute usually on div[role='article'] or a parent? It varies. 
                # Ideally, we look for it on the card itself, but if not checking href CID.
                # Usually Google maps uses `data-result-index` or similar. The `data-id` might not be exposed.
                # A robust ID is the `CID` inside the URL or hex string.
                # Let's try to parse CID from URL if possible, or use href as ID.
                place_id = None
                if href:
                    # Generic strategy: Use the unique part of the URL or the href itself as ID
                    # Or try to extract `data-result-id` attribute logic if known.
                    # Best valid approach: Use the href. It's unique per business.
                    place_id = href.split('?')[0] # Remove query params mostly
                
                # 2. Name
                aria_label = card.get_attribute("aria-label")
                name = aria_label if aria_label else ""
                
                # 3. Text Content Breakdown
                text_content = card.text.split('\n')
                # Fallback name
                if not name and text_content:
                    name = text_content[0]

                # 4. Rating & Reviews Parsing
                rating, reviews, category = None, 0, None
                for line in text_content:
                    # Match: 4.5(2.1K) or 4.5(500)
                    match = re.search(r'(\d[\.,]\d)\s*\(([\d\.Kk]+)\)', line)
                    if match:
                        rating = float(match.group(1).replace(',', '.'))
                        reviews_str = match.group(2)
                        
                        # Parse K notation
                        multiplier = 1
                        if 'k' in reviews_str.lower():
                            multiplier = 1000
                            reviews_str = reviews_str.lower().replace('k', '')
                        elif 'm' in reviews_str.lower():
                            multiplier = 1000000
                            reviews_str = reviews_str.lower().replace('m', '')
                            
                        try:
                            reviews = int(float(reviews_str) * multiplier)
                        except:
                            reviews = 0
                            
                        # Category extraction attempt (often " · Category · ")
                        parts = line.split('·')
                        if len(parts) > 1:
                            for p in parts:
                                p = p.strip()
                                if not re.search(r'\(\d+\)', p) and '$' not in p:
                                    category = p
                                    break
                        break
                
                # 5. Place Type Detection
                place_type = self._detect_place_type(category, name)

                # 6. Address / Phone
                address = ""
                phone = None
                for line in text_content[2:]:
                    if "Open" not in line and "Closed" not in line and "Dine-in" not in line and "Takeout" not in line:
                         # Check if line looks like a phone number
                         if self._is_phone(line):
                             phone = line
                         else:
                             address += line + " "

                results.append({
                    "name": name,
                    "address_raw": address.strip(),
                    "category": category,
                    "rating": rating,
                    "reviews": reviews,
                    "latitude": coords[0] if coords else None,
                    "longitude": coords[1] if coords else None,
                    "url": href,
                    "phone": phone,
                    "place_type": place_type,
                    "place_id": place_id # NEW field
                })

            except Exception as e:
                continue
        
        return results

    def _parse_coords_from_url(self, url):
        if not url: return None
        try:
            match = re.search(r'@([-.\d]+),([-.\d]+)', url)
            if match:
                return (float(match.group(1)), float(match.group(2)))
            match_3d = re.search(r'!3d([-.\d]+)!4d([-.\d]+)', url)
            if match_3d:
                return (float(match_3d.group(1)), float(match_3d.group(2)))
        except: pass
        return None

    def _is_phone(self, text):
        # Basic heuristic: contains at least 7 digits and some format chars
        digits = re.sub(r'\D', '', text)
        if len(digits) >= 7 and len(digits) <= 15:
            # Check for allowed chars only (digits, space, +, -, ., (, ))
            if re.match(r'^[\d\s\+\-\.\(\)]+$', text):
                return True
        return False

    def _detect_place_type(self, category, name):
        if not category: return "Unknown"
        
        # Residence Blacklist/Heuristics
        residence_keywords = [
            "Apartment", "Condominium", "Housing", "Home", "Residential", 
            "Building", "Complex", "Dormitory", "Unit", "Estate",
            "Private", "Subdivision", "Village", "Tower", "Residencia",
            "Condo", "Townhome", "Loft", "Manor", "Villa"
        ]
        
        # Business Indicators (Safelist)
        business_keywords = [
            "Office", "Agency", "Consultant", "Store", "Shop", "Restaurant",
            "Cafe", "Service", "Company", "LLC", "Inc", "Group", "Studio",
            "Clinic", "Practice", "Center", "School", "Hotel"
        ]

        cat_lower = category.lower()
        name_lower = name.lower()

        # Strong Business Signal
        for kw in business_keywords:
            if kw.lower() in cat_lower or kw.lower() in name_lower:
                return "Business"

        # Strong Residence Signal
        for kw in residence_keywords:
            if kw.lower() in cat_lower:
                return "Residence"
                
        # Heuristic: If name looks like a person's name (placeholder logic)
        # Often impossible to know for sure without StreetView or detailed meta.
        # Default to Business if it has a category.
        return "Business"

    def close(self):
        try:
            self.driver.quit()
        except: pass

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    agent = ScraperAgent(headless=False)
    try:
        data = agent.search_area(40.7128, -74.0060, "Pizza")
        print(json.dumps(data, indent=2))
    finally:
        agent.close()
