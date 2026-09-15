import logging
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from backend.app.api.router import router
from backend.app.config import settings

# Configure logging format
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s"
)
logger = logging.getLogger("backend.main")

app = FastAPI(
    title="Autonomous Lead Enrichment Agent API",
    description="Asynchronous Lead Prospecting & Web Intelligence Agent using Selenium & NVIDIA NIM LLM API",
    version="1.0.0"
)

# Enable CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include API Router
app.include_router(router)

@app.get("/")
def root():
    return {
        "message": "Autonomous Lead Enrichment Agent API is running.",
        "docs_url": "/docs",
        "health_check": "/api/v1/health"
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("backend.app.main:app", host=settings.FASTAPI_HOST, port=settings.FASTAPI_PORT, reload=True)
