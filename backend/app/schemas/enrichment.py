from typing import List, Optional, Dict
from pydantic import BaseModel, Field

class TeamMember(BaseModel):
    name: str = Field(..., description="Full name of the team member or executive")
    title: str = Field(..., description="Designation or role (e.g., Founder, CEO, CTO)")
    linkedin_url: Optional[str] = Field(None, description="LinkedIn profile URL if discoverable")

class LeadEnrichmentResult(BaseModel):
    domain: str = Field(..., description="Target domain (e.g., postman.com)")
    company_name: str = Field(..., description="Official name of the company")
    company_overview: str = Field(..., description="Concise 2-sentence summary of what the company does")
    target_audience_icp: str = Field(..., description="Ideal Customer Profile / Target Audience description")
    contact_points: List[str] = Field(default_factory=list, description="Public email addresses or contact points found")
    key_leadership: List[TeamMember] = Field(default_factory=list, description="Key executives or founders")
    data_confidence_score: float = Field(..., ge=0.0, le=1.0, description="Score between 0.0 and 1.0 evaluating quality/completeness")
    crawled_subpages: List[str] = Field(default_factory=list, description="List of subpage paths successfully scraped")
    tokens_used: Dict[str, int] = Field(default_factory=lambda: {"prompt_tokens": 0, "completion_tokens": 0, "total_tokens": 0})
    estimated_cost_usd: float = Field(0.0, description="Estimated API cost in USD")
    status: str = Field("success", description="Status of extraction (success / partial / failed)")
    error_message: Optional[str] = Field(None, description="Error details if scraping failed")

class EnrichmentRequest(BaseModel):
    domains: List[str] = Field(..., min_items=1, description="List of company domains to enrich (e.g. ['postman.com', 'supabase.com'])")

class BatchEnrichmentResponse(BaseModel):
    total_processed: int
    results: List[LeadEnrichmentResult]
    total_cost_usd: float
