import logging
import re
import time
from typing import Dict, List, Tuple
from urllib.parse import urljoin, urlparse

import httpx
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from webdriver_manager.chrome import ChromeDriverManager

from backend.app.config import settings

logger = logging.getLogger(__name__)

SUBPAGE_PATTERNS = [
    r"/about", r"/team", r"/company", r"/contact", r"/pricing", 
    r"/leadership", r"/about-us", r"/our-team", r"/founders"
]

def normalize_domain(domain: str) -> str:
    domain = domain.strip().lower()
    if not domain.startswith("http://") and not domain.startswith("https://"):
        domain = f"https://{domain}"
    return domain

import tempfile

def create_selenium_driver() -> webdriver.Chrome:
    options = Options()
    options.page_load_strategy = 'eager'  # DOM interactive state - ultra fast
    if settings.SELENIUM_HEADLESS:
        options.add_argument("--headless=new")
    options.add_argument("--disable-gpu")
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    options.add_argument("--disable-blink-features=AutomationControlled")
    options.add_argument(f"--user-data-dir={tempfile.mkdtemp()}")
    options.add_argument("user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36")
    
    # Try using ChromeDriverManager
    try:
        service = Service(ChromeDriverManager().install())
        driver = webdriver.Chrome(service=service, options=options)
    except Exception as e:
        logger.warning(f"ChromeDriverManager failed, attempting default webdriver launch: {e}")
        driver = webdriver.Chrome(options=options)
        
    driver.set_page_load_timeout(8)
    return driver

def clean_dom_via_javascript(driver: webdriver.Chrome):
    """Strips non-content tags and job listing widgets directly inside Selenium browser memory."""
    js_script = """
    const selectors = ['script', 'style', 'svg', 'iframe', 'noscript', 'nav', 'footer', 'header', '.job-card', '.job-list', '.careers-section'];
    selectors.forEach(selector => {
        document.querySelectorAll(selector).forEach(el => el.remove());
    });
    """
    try:
        driver.execute_script(js_script)
    except Exception as e:
        logger.warning(f"Error cleaning DOM via JS: {e}")

class SeleniumScraper:
    def __init__(self):
        pass

    def scrape_domain(self, target_domain: str) -> Tuple[Dict[str, str], List[str], str]:
        """
        Scrapes homepage and subpages using Selenium.
        Extracts meta tags (description, title) and body text.
        """
        url = normalize_domain(target_domain)
        base_netloc = urlparse(url).netloc
        scraped_pages: Dict[str, str] = {}
        crawled_subpages: List[str] = []
        error_msg = None

        driver = None
        try:
            driver = create_selenium_driver()
            logger.info(f"Navigating to homepage: {url}")
            driver.get(url)
            time.sleep(0.5)  # Allow JS rendering to settle
            
            # Extract Meta Description & Title
            meta_desc = ""
            try:
                meta_el = driver.find_element(By.XPATH, "//meta[@name='description' or @property='og:description']")
                meta_desc = meta_el.get_attribute("content") or ""
            except Exception:
                pass
                
            clean_dom_via_javascript(driver)
            homepage_text = driver.find_element(By.TAG_NAME, "body").text
            
            # Filter out lines related to job postings
            filtered_lines = [
                line for line in homepage_text.splitlines()
                if not any(k in line.lower() for k in ["view job", "inr 15000", "monthly", "sharepoint administrator", "b2b contractual"])
            ]
            homepage_clean = "\n".join(filtered_lines)
            
            if meta_desc:
                homepage_clean = f"Meta Description: {meta_desc}\n\n" + homepage_clean
                
            scraped_pages["/"] = homepage_clean
            crawled_subpages.append("/")

            # Discover dynamic subpage links from loaded DOM
            discovered_links: List[str] = []
            anchors = driver.find_elements(By.TAG_NAME, "a")
            for anchor in anchors:
                try:
                    href = anchor.get_attribute("href")
                    if href:
                        parsed = urlparse(href)
                        if parsed.netloc == base_netloc or not parsed.netloc:
                            path = parsed.path
                            if any(re.search(pattern, path, re.IGNORECASE) for pattern in SUBPAGE_PATTERNS):
                                full_link = urljoin(url, path)
                                if full_link not in discovered_links and path != "/":
                                    discovered_links.append(full_link)
                except Exception:
                    continue

            logger.info(f"Discovered relevant subpages for {target_domain}: {discovered_links}")

            # Crawl discovered subpages via fast, non-blocking HTTP requests (prevents Cloudflare hangs)
            with httpx.Client(timeout=4.0, follow_redirects=True, headers={
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36"
            }) as http_client:
                for subpage_url in discovered_links[:settings.MAX_SUBPAGES_PER_DOMAIN]:
                    try:
                        sub_path = urlparse(subpage_url).path
                        logger.info(f"Fetching subpage via HTTP: {subpage_url}")
                        sub_resp = http_client.get(subpage_url)
                        if sub_resp.status_code == 200:
                            scraped_pages[sub_path] = sub_resp.text
                            crawled_subpages.append(sub_path)
                    except Exception as sub_err:
                        logger.warning(f"Failed subpage fetch {subpage_url}: {sub_err}")

        except Exception as err:
            logger.error(f"Selenium scraping failed for {target_domain}: {err}. Falling back to HTTPX...")
            error_msg = f"Selenium warning: {str(err)}"
            # Fallback HTTPX
            fallback_pages, fallback_paths = self._fallback_httpx_scrape(url)
            if fallback_pages:
                scraped_pages.update(fallback_pages)
                crawled_subpages.extend(fallback_paths)

        finally:
            if driver:
                try:
                    driver.quit()
                except Exception:
                    pass

        return scraped_pages, crawled_subpages, error_msg

    def _fallback_httpx_scrape(self, url: str) -> Tuple[Dict[str, str], List[str]]:
        scraped = {}
        paths = []
        try:
            with httpx.Client(timeout=10.0, follow_redirects=True, headers={
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) Chrome/122.0.0.0 Safari/537.36"
            }) as client:
                resp = client.get(url)
                if resp.status_code == 200:
                    scraped["/"] = resp.text
                    paths.append("/")
        except Exception as e:
            logger.error(f"HTTPX fallback failed for {url}: {e}")
        return scraped, paths
