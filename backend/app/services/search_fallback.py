import logging
from typing import List, Optional

try:
    from ddgs import DDGS
except ImportError:
    from duckduckgo_search import DDGS

logger = logging.getLogger(__name__)

def search_linkedin_url(person_name: str, company_name: str) -> Optional[str]:
    """Uses DuckDuckGo to search for a key leader's LinkedIn profile URL if missing."""
    query = f"{person_name} {company_name} site:linkedin.com/in/"
    try:
        with DDGS(timeout=4) as ddgs:
            results = list(ddgs.text(query, max_results=3))
            for res in results:
                href = res.get("href", "")
                if "linkedin.com/in/" in href:
                    return href
    except Exception as e:
        logger.warning(f"DuckDuckGo LinkedIn search error for {person_name}: {e}")
    return None

def search_contact_emails(company_name: str) -> List[str]:
    """Uses DuckDuckGo to discover public email addresses if none found on domain."""
    query = f'"{company_name}" "contact@" OR "sales@" OR "support@"'
    found_emails = set()
    try:
        with DDGS(timeout=4) as ddgs:
            results = list(ddgs.text(query, max_results=3))
            for res in results:
                snippet = res.get("body", "") + " " + res.get("title", "")
                import re
                emails = re.findall(r'[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}', snippet)
                for email in emails:
                    if not email.endswith(".png") and not email.endswith(".jpg"):
                        found_emails.add(email.lower())
    except Exception as e:
        logger.warning(f"DuckDuckGo contact search error for {company_name}: {e}")
    return list(found_emails)

