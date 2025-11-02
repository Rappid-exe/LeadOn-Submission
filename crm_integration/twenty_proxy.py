"""
Twenty CRM Proxy Server
Proxies requests from Twenty CRM frontend to LeadOn backend
"""

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
import httpx
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(title="Twenty CRM Proxy")

# Enable CORS for Twenty CRM frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:4000", "http://localhost:3001"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

LEADON_BACKEND_URL = "http://localhost:8000"


@app.post("/api/lead-gen/search")
async def proxy_lead_gen_search(request: Request):
    """
    Proxy lead generation search requests from Twenty CRM to LeadOn backend
    """
    try:
        # Get the request body
        body = await request.json()
        query = body.get("query", "")
        
        logger.info(f"📥 Received search request: {query}")
        
        # Transform the request to LeadOn format
        leadon_request = {
            "message": query,
            "max_contacts": 25,
            "enrich_with_jobs": False
        }
        
        # Forward to LeadOn backend
        async with httpx.AsyncClient(timeout=120.0) as client:
            response = await client.post(
                f"{LEADON_BACKEND_URL}/api/chat",
                json=leadon_request
            )
            
            leadon_data = response.json()
            logger.info(f"✅ LeadOn response: {leadon_data}")
            
            # Transform response to Twenty CRM format
            twenty_response = {
                "message": leadon_data.get("response", "Search completed!"),
                "contactsAdded": leadon_data.get("contacts_added", 0),
                "contactsFound": leadon_data.get("contacts_found", 0)
            }
            
            return JSONResponse(content=twenty_response)
            
    except Exception as e:
        logger.error(f"❌ Error in proxy: {str(e)}")
        return JSONResponse(
            content={
                "message": f"Error: {str(e)}",
                "contactsAdded": 0,
                "contactsFound": 0
            },
            status_code=500
        )


@app.get("/health")
async def health():
    """Health check endpoint"""
    return {"status": "healthy", "service": "Twenty CRM Proxy"}


if __name__ == "__main__":
    import uvicorn
    logger.info("🚀 Starting Twenty CRM Proxy on port 3002...")
    logger.info(f"📡 Proxying to LeadOn backend at {LEADON_BACKEND_URL}")
    uvicorn.run(app, host="0.0.0.0", port=3002)

