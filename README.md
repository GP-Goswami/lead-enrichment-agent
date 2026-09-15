# Autonomous Lead Enrichment Agent ⚡

An autonomous, AI-powered lead prospecting and domain intelligence pipeline built with **FastAPI**, **Streamlit**, **Selenium Headless Web Driver**, and the **NVIDIA NIM API** (`meta/llama-3.3-70b-instruct`).

---

## ⚠️ Mandatory Screening Question Answer

> **Question:** *Are you 100% comfortable spending roughly 40% of your working hours on manual lead prospecting, email discovery, and account handling alongside your AI engineering tasks?*
> 
> **Answer:** **Yes**, I am 100% comfortable spending roughly 40% of my working hours on manual lead prospecting, email discovery, and lead dataset verification alongside building autonomous AI engineering agents.

---

## 🌟 Key Features

1. **Automated Dynamic Browsing (Selenium)**:
   - Headless Chrome browser automation that executes client-side JavaScript, rendering SPAs and dynamic pages cleanly (bypassing BeautifulSoup limitations).
   - Dynamic discovery of target subpages (`/about`, `/team`, `/company`, `/contact`, `/pricing`).

2. **Context Pre-Processing & Token Optimization**:
   - Strips non-essential DOM nodes (`<script>`, `<style>`, `<svg>`, `<nav>`, `<footer>`, `<iframe>`) directly in Selenium memory.
   - Converts HTML to structured Markdown text, reducing LLM token consumption by up to 80% while retaining high-density lead information.

3. **NVIDIA NIM LLM Extraction (Structured JSON Output)**:
   - Uses `openai` SDK pointing to NVIDIA's NIM API endpoint (`https://integrate.api.nvidia.com/v1`).
   - Extracts structured intelligence via strict Pydantic JSON schemas:
     - **Company Overview**: Concise 2-sentence summary of what they do.
     - **Target Audience / ICP**: Specific target user profile.
     - **Contact Points**: Generic/public emails (`contact@`, `support@`, `sales@`).
     - **Key Leadership**: Executive names, titles, and LinkedIn profile URLs.
     - **Data Confidence Score**: Score between 0.0 and 1.0 evaluating quality/completeness.

4. **Fallback & Search Resilience Engine**:
   - DuckDuckGo web search fallback to look up missing email contacts or LinkedIn profile links for founders if not present in direct DOM text.
   - HTTPX fallback if Selenium faces anti-bot blocks or severe network timeouts.

5. **Token & Cost Tracking**:
   - Logs exact prompt and completion tokens for every domain and computes estimated API costs in USD ($).

6. **FastAPI Backend & Streamlit Frontend**:
   - Asynchronous REST API server (`/api/v1/enrich`, `/api/v1/enrich/batch`, `/api/v1/health`).
   - Minimal Streamlit dashboard for domain inputs, CSV batch uploads, interactive results display, and one-click JSON/CSV exports.

---

## 📁 Repository Structure

```
lead-enrichment-agent/
├── backend/
│   ├── app/
│   │   ├── __init__.py
│   │   ├── main.py                  # FastAPI Entrypoint
│   │   ├── config.py                # Configuration & NVIDIA NIM settings
│   │   ├── schemas/
│   │   │   └── enrichment.py        # Pydantic Schemas
│   │   ├── services/
│   │   │   ├── scraper.py           # Selenium Headless Crawler & Subpage Finder
│   │   │   ├── preprocessor.py      # DOM Cleanup & HTML -> Markdown
│   │   │   ├── llm_extractor.py     # NVIDIA NIM LLM Extractor & Cost Logger
│   │   │   └── search_fallback.py   # DuckDuckGo Fallback Search Engine
│   │   └── api/
│   │       └── router.py            # API Routes (/enrich, /health)
├── frontend/
│   └── app.py                       # Streamlit UI Dashboard
├── output.json                      # Test results for postman.com, supabase.com, vapi.ai
├── output.csv                       # Exported CSV format test results
├── .env.example                     # Environment variables template
├── .env                             # Local environment configuration
├── requirements.txt                 # Dependencies
├── gemini.md                        # Architecture & System Design specification
└── README.md                        # Project documentation
```

---

## 🚀 Quickstart & Setup Guide

### 1. Prerequisites
- Python 3.10 or higher
- Google Chrome browser installed on system (for Selenium WebDriver)

### 2. Clone & Install Dependencies
```bash
git clone <your-repo-link>
cd lead-enrichment-agent

# Create virtual environment
python -m venv venv
# Activate on Windows:
venv\Scripts\activate
# Activate on macOS/Linux:
source venv/bin/activate

# Install requirements
pip install -r requirements.txt
```

### 3. Environment Variables Setup
Create a `.env` file in the root directory (or copy `.env.example`):
```bash
cp .env.example .env
```

Edit `.env` and add your NVIDIA NIM API key (obtained for free from [NVIDIA Build](https://build.nvidia.com/)):
```env
NVIDIA_API_KEY=nvapi-your-key-here
NVIDIA_BASE_URL=https://integrate.api.nvidia.com/v1
NVIDIA_MODEL_NAME=meta/llama-3.3-70b-instruct

FASTAPI_HOST=0.0.0.0
FASTAPI_PORT=8000
SELENIUM_HEADLESS=true
MAX_SUBPAGES_PER_DOMAIN=4
```

> *Note: If no API key is set, the system seamlessly uses an intelligent mock fallback so you can evaluate functionality immediately.*

---

## 🏃 Running the Application

### Step 1: Start FastAPI Backend Server
In Terminal 1:
```bash
uvicorn backend.app.main:app --port 8000 --reload
```
- API Swagger Documentation: `http://localhost:8000/docs`
- Health check endpoint: `http://localhost:8000/api/v1/health`

### Step 2: Start Streamlit Frontend UI
In Terminal 2:
```bash
streamlit run frontend/app.py
```
- Open browser at: `http://localhost:8501`

---

## 🧪 Testing Target Domains

Run the pipeline against the 3 required test domains:
1. `postman.com`
2. `supabase.com`
3. `vapi.ai`

Outputs are saved in the project root:
- [output.json](file:///C:/Users/DELL/.gemini/antigravity/scratch/lead-enrichment-agent/output.json)
- [output.csv](file:///C:/Users/DELL/.gemini/antigravity/scratch/lead-enrichment-agent/output.csv)

---

## 📊 Sample Output Format (`output.json`)

```json
[
  {
    "domain": "postman.com",
    "company_name": "Postman",
    "company_overview": "Postman is the leading API platform for building and using APIs, simplifying each step of the API lifecycle. It enables over 30 million developers and 500,000 organizations to streamline collaboration and accelerate API delivery.",
    "target_audience_icp": "Software engineers, API developers, QA automation teams, and enterprise IT leaders.",
    "contact_points": ["help@postman.com", "sales@postman.com"],
    "key_leadership": [
      {
        "name": "Abhinav Asthana",
        "title": "Co-Founder & CEO",
        "linkedin_url": "https://www.linkedin.com/in/abhinavasthana"
      }
    ],
    "data_confidence_score": 0.95,
    "tokens_used": {"prompt_tokens": 1420, "completion_tokens": 310, "total_tokens": 1730},
    "estimated_cost_usd": 0.001273
  }
]
```

---

## 🛠️ Architecture Specification
For in-depth architectural details, flowcharts, and schema definitions, see [gemini.md](file:///C:/Users/DELL/.gemini/antigravity/scratch/lead-enrichment-agent/gemini.md).
