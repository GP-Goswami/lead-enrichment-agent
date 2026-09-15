import logging
from typing import List
from fastapi import APIRouter, HTTPException, Query
from backend.app.schemas.enrichment import (
    EnrichmentRequest, 
    LeadEnrichmentResult, 
    BatchEnrichmentResponse,
    TeamMember
)
from backend.app.services.scraper import SeleniumScraper
from backend.app.services.preprocessor import convert_scraped_data_to_markdown
from backend.app.services.llm_extractor import LLMExtractor
from backend.app.services.search_fallback import search_linkedin_url, search_contact_emails
from backend.app.config import settings

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/v1", tags=["Lead Enrichment"])

scraper_service = SeleniumScraper()
llm_service = LLMExtractor()

@router.get("/health", summary="Health Check")
def health_check():
    return {
        "status": "online",
        "service": "Autonomous Lead Enrichment Agent API",
        "llm_provider": "NVIDIA NIM API",
        "base_url": settings.NVIDIA_BASE_URL,
        "model": settings.NVIDIA_MODEL_NAME,
        "scraper": "Selenium Headless WebDriver"
    }

def process_single_domain(domain: str) -> LeadEnrichmentResult:
    """Core enrichment pipeline execution for a single domain."""
    logger.info(f"Starting lead enrichment pipeline for: {domain}")
    
    # Step 1: Automated Browsing via Selenium
    scraped_pages, subpage_paths, scrape_err = scraper_service.scrape_domain(domain)
    
    # Step 2: Token Optimization & DOM to Markdown
    markdown_content = convert_scraped_data_to_markdown(scraped_pages)
    
    # Step 3: LLM Extraction (NVIDIA NIM API)
    raw_data, tokens, cost = llm_service.extract_lead_intelligence(domain, markdown_content)
    
    # Step 4: Fallback & Search Enhancements
    contact_points = raw_data.get("contact_points", [])
    if not contact_points:
        logger.info(f"No emails extracted directly from DOM. Running DuckDuckGo search fallback for {domain}...")
        company_name = raw_data.get("company_name", domain)
        fallback_emails = search_contact_emails(company_name)
        if fallback_emails:
            contact_points = fallback_emails

    key_leadership = []
    for member in raw_data.get("key_leadership", []):
        name = member.get("name", "")
        title = member.get("title", "")
        linkedin = member.get("linkedin_url")
        
        # If LinkedIn URL missing, trigger search fallback
        if name and not linkedin:
            company_name = raw_data.get("company_name", domain)
            logger.info(f"Searching LinkedIn URL fallback for {name} ({company_name})...")
            found_url = search_linkedin_url(name, company_name)
            if found_url:
                linkedin = found_url
                
        key_leadership.append(TeamMember(name=name, title=title, linkedin_url=linkedin))

    status_str = "success" if not scrape_err else "partial"

    return LeadEnrichmentResult(
        domain=domain,
        company_name=raw_data.get("company_name", domain.capitalize()),
        company_overview=raw_data.get("company_overview", "Information unavailable."),
        target_audience_icp=raw_data.get("target_audience_icp", "Target audience specification unavailable."),
        contact_points=contact_points,
        key_leadership=key_leadership,
        data_confidence_score=raw_data.get("data_confidence_score", 0.8),
        crawled_subpages=subpage_paths,
        tokens_used=tokens,
        estimated_cost_usd=cost,
        status=status_str,
        error_message=scrape_err
    )

@router.post("/enrich", response_model=LeadEnrichmentResult, summary="Enrich Single Domain")
def enrich_domain(request: EnrichmentRequest):
    if not request.domains:
        raise HTTPException(status_code=400, detail="Domain list cannot be empty.")
    target_domain = request.domains[0]
    return process_single_domain(target_domain)

@router.post("/enrich/batch", response_model=BatchEnrichmentResponse, summary="Enrich Multiple Domains Batch")
def enrich_domains_batch(request: EnrichmentRequest):
    if not request.domains:
        raise HTTPException(status_code=400, detail="Domain list cannot be empty.")
    
    results = []
    total_cost = 0.0

    # Sequential execution: Process one domain at a time for stable crawling & instant API responses
    for domain in request.domains:
        try:
            res = process_single_domain(domain)
            results.append(res)
            total_cost += res.estimated_cost_usd
        except Exception as e:
            logger.error(f"Error enriching domain {domain}: {e}")
            results.append(LeadEnrichmentResult(
                domain=domain,
                company_name=domain,
                company_overview="Extraction failed.",
                target_audience_icp="N/A",
                contact_points=[],
                key_leadership=[],
                data_confidence_score=0.0,
                crawled_subpages=[],
                tokens_used={"prompt_tokens": 0, "completion_tokens": 0, "total_tokens": 0},
                estimated_cost_usd=0.0,
                status="failed",
                error_message=str(e)
            ))

    return BatchEnrichmentResponse(
        total_processed=len(results),
        results=results,
        total_cost_usd=round(total_cost, 6)
    )


