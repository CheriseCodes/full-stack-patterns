from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import os
from dotenv import load_dotenv
import requests

load_dotenv()

app = FastAPI()

# CORS - allow frontend to call backend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "*.vercel.app"],  # Add Vercel domain later
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class QueryRequest(BaseModel):
    query: str

@app.get("/")
def read_root():
    return {
        "status": "Backend is running",
        "message": "Send POST to /api/chat to query"
    }

@app.get("/health")
def health_check():
    return {"status": "healthy"}

@app.post("/api/chat")
def chat(request: QueryRequest):
    """
    Minimal endpoint - just calls TMDB and returns raw data
    No processing, no AI, just prove it works
    """
    
    query = request.query
    tmdb_api_key = os.getenv("TMDB_API_KEY")
    
    if not tmdb_api_key:
        return {
            "error": "TMDB_API_KEY not configured",
            "query": query
        }
    
    # Simple TMDB search
    try:
        response = requests.get(
            "https://api.themoviedb.org/3/search/tv",
            params={
                "api_key": tmdb_api_key,
                "query": query
            },
            timeout=10
        )
        
        data = response.json()
        
        # Return minimal processed data
        if data.get("results"):
            first_result = data["results"][0]
            return {
                "success": True,
                "query": query,
                "found": True,
                "show_name": first_result.get("name"),
                "overview": first_result.get("overview"),
                "first_air_date": first_result.get("first_air_date"),
                "raw_data": first_result,  # Include raw data to inspect
                "message": "✓ TMDB API connected successfully"
            }
        else:
            return {
                "success": True,
                "query": query,
                "found": False,
                "message": "No results found"
            }
            
    except Exception as e:
        return {
            "error": str(e),
            "query": query,
            "message": "Failed to connect to TMDB"
        }