"""
FastAPI backend for LeadOn CRM integration.
Connects Apollo scraper to Twenty CRM and provides search interface.
"""

from fastapi import FastAPI, HTTPException, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse, FileResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel
from typing import List, Optional, Dict, Any
import json
from pathlib import Path
from datetime import datetime
import sys

# Add parent directory to path
sys.path.append(str(Path(__file__).parent.parent))

from scrapers.schemas import Contact
from scrapers.apollo_scraper import ApolloClient
from cli.search_mock import load_mock_contacts, filter_contacts

app = FastAPI(
    title="LeadOn CRM API",
    description="Sales workflow automation with Apollo.io integration",
    version="1.0.0"
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# In-memory storage (replace with Twenty CRM API later)
contacts_db: List[Contact] = []


class SearchRequest(BaseModel):
    """Search request model"""
    query: Optional[str] = None
    titles: Optional[List[str]] = None
    companies: Optional[List[str]] = None
    locations: Optional[List[str]] = None
    tags: Optional[List[str]] = None
    limit: int = 25
    use_mock: bool = True  # Use mock data by default (free plan)


class SearchResponse(BaseModel):
    """Search response model"""
    contacts: List[Contact]
    total: int
    query: Optional[str]
    timestamp: datetime


class ActionLog(BaseModel):
    """Action log model"""
    contact_id: str
    action_type: str
    action_details: Dict[str, Any]
    timestamp: datetime
    status: str = "completed"


# Initialize with mock data
def init_contacts():
    """Load initial mock contacts"""
    global contacts_db
    try:
        contacts_db = load_mock_contacts()
        print(f"✓ Loaded {len(contacts_db)} mock contacts")
    except Exception as e:
        print(f"Warning: Could not load mock contacts: {e}")
        contacts_db = []


@app.on_event("startup")
async def startup_event():
    """Initialize on startup"""
    init_contacts()


@app.get("/", response_class=HTMLResponse)
async def root():
    """Serve frontend HTML"""
    html_path = Path(__file__).parent / "frontend" / "index.html"
    if html_path.exists():
        with open(html_path, 'r', encoding='utf-8') as f:
            return f.read()
    return """
    <html>
        <body>
            <h1>LeadOn CRM API</h1>
            <p>API is running!</p>
            <ul>
                <li><a href="/docs">API Documentation</a></li>
                <li><a href="/api/health">Health Check</a></li>
                <li><a href="/api/stats">Statistics</a></li>
            </ul>
        </body>
    </html>
    """


@app.get("/api/health")
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "contacts_loaded": len(contacts_db),
        "timestamp": datetime.now().isoformat()
    }


@app.post("/api/contacts/search", response_model=SearchResponse)
async def search_contacts(request: SearchRequest):
    """
    Search for contacts using Apollo.io or mock data.
    
    If use_mock=True (default), searches mock data.
    If use_mock=False, attempts to use Apollo.io API (requires paid plan).
    """
    try:
        if request.use_mock:
            # Use mock data
            filtered = filter_contacts(
                contacts_db,
                query=request.query,
                titles=request.titles,
                companies=request.companies,
                locations=request.locations,
                tags=request.tags
            )
            results = filtered[:request.limit]
            
            return SearchResponse(
                contacts=results,
                total=len(filtered),
                query=request.query,
                timestamp=datetime.now()
            )
        else:
            # Try Apollo.io API (will fail on free plan)
            try:
                client = ApolloClient()
                result = client.search_people(
                    query=request.query,
                    titles=request.titles,
                    locations=request.locations,
                    limit=request.limit
                )
                
                return SearchResponse(
                    contacts=result.contacts,
                    total=result.total_results,
                    query=request.query,
                    timestamp=datetime.now()
                )
            except Exception as e:
                raise HTTPException(
                    status_code=503,
                    detail=f"Apollo.io API not available (free plan). Use use_mock=true. Error: {str(e)}"
                )
                
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/contacts", response_model=List[Contact])
async def get_all_contacts(
    skip: int = 0,
    limit: int = 100,
    tags: Optional[str] = None
):
    """
    Get all contacts with pagination.
    
    Query params:
    - skip: Number of records to skip
    - limit: Maximum number of records to return
    - tags: Comma-separated tags to filter by
    """
    filtered = contacts_db
    
    if tags:
        tag_list = [t.strip() for t in tags.split(",")]
        filtered = [
            c for c in filtered
            if any(tag in c.tags for tag in tag_list)
        ]
    
    return filtered[skip:skip + limit]


@app.get("/api/contacts/{contact_id}", response_model=Contact)
async def get_contact(contact_id: str):
    """Get a specific contact by ID"""
    # For mock data, use name as ID
    for contact in contacts_db:
        if contact.name.lower().replace(" ", "-") == contact_id.lower():
            return contact
    
    raise HTTPException(status_code=404, detail="Contact not found")


@app.post("/api/contacts", response_model=Contact)
async def create_contact(contact: Contact):
    """Create a new contact"""
    # Check for duplicates
    for existing in contacts_db:
        if existing.email == contact.email or existing.linkedin_url == contact.linkedin_url:
            raise HTTPException(
                status_code=409,
                detail="Contact already exists with this email or LinkedIn URL"
            )
    
    # Add timestamps
    contact.created_at = datetime.now()
    contact.last_updated = datetime.now()
    
    contacts_db.append(contact)
    
    return contact


@app.put("/api/contacts/{contact_id}", response_model=Contact)
async def update_contact(contact_id: str, contact: Contact):
    """Update an existing contact"""
    for i, existing in enumerate(contacts_db):
        if existing.name.lower().replace(" ", "-") == contact_id.lower():
            contact.last_updated = datetime.now()
            contacts_db[i] = contact
            return contact
    
    raise HTTPException(status_code=404, detail="Contact not found")


@app.delete("/api/contacts/{contact_id}")
async def delete_contact(contact_id: str):
    """Delete a contact"""
    global contacts_db
    
    for i, contact in enumerate(contacts_db):
        if contact.name.lower().replace(" ", "-") == contact_id.lower():
            deleted = contacts_db.pop(i)
            return {"message": "Contact deleted", "contact": deleted.name}
    
    raise HTTPException(status_code=404, detail="Contact not found")


# Action logging endpoints
actions_db: List[ActionLog] = []


@app.post("/api/actions", response_model=ActionLog)
async def log_action(action: ActionLog):
    """Log a LinkedIn automation action"""
    actions_db.append(action)
    return action


@app.get("/api/actions", response_model=List[ActionLog])
async def get_actions(
    contact_id: Optional[str] = None,
    action_type: Optional[str] = None,
    limit: int = 100
):
    """Get action logs with optional filters"""
    filtered = actions_db
    
    if contact_id:
        filtered = [a for a in filtered if a.contact_id == contact_id]
    
    if action_type:
        filtered = [a for a in filtered if a.action_type == action_type]
    
    return filtered[:limit]


@app.get("/api/stats")
async def get_stats():
    """Get CRM statistics"""
    # Count by tags
    tags_count = {}
    for contact in contacts_db:
        for tag in contact.tags:
            tags_count[tag] = tags_count.get(tag, 0) + 1
    
    # Count by company
    companies_count = {}
    for contact in contacts_db:
        if contact.company:
            companies_count[contact.company] = companies_count.get(contact.company, 0) + 1
    
    # Count by location
    locations_count = {}
    for contact in contacts_db:
        if contact.city and contact.state:
            loc = f"{contact.city}, {contact.state}"
            locations_count[loc] = locations_count.get(loc, 0) + 1
    
    return {
        "total_contacts": len(contacts_db),
        "total_actions": len(actions_db),
        "top_tags": dict(sorted(tags_count.items(), key=lambda x: x[1], reverse=True)[:10]),
        "top_companies": dict(sorted(companies_count.items(), key=lambda x: x[1], reverse=True)[:10]),
        "top_locations": dict(sorted(locations_count.items(), key=lambda x: x[1], reverse=True)[:10]),
        "timestamp": datetime.now().isoformat()
    }


@app.post("/api/import/mock")
async def import_mock_data():
    """Reload mock data"""
    global contacts_db
    init_contacts()
    return {
        "message": "Mock data imported",
        "count": len(contacts_db)
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)

