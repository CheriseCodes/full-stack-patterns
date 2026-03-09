from fastapi import FastAPI, Header
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import os
from dotenv import load_dotenv
import requests
from supabase import create_client, Client
import uuid


load_dotenv()

supabase: Client = create_client(
    os.getenv("SUPABASE_URL"),
    os.getenv("SUPABASE_KEY")
)

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
def chat(request: QueryRequest, authorization: str = Header(None)):
    """
    Minimal endpoint - just calls TMDB and returns raw data
    No processing, no AI, just prove it works
    """
    
    query = request.query
    user_supabase = create_client(
        os.getenv("SUPABASE_URL"),
        os.getenv("SUPABASE_KEY")
    )
    user_supabase.auth.set_session(authorization.replace("Bearer ", ""), "")
    # Create conversation (dummy user_id for now)
    conversation = user_supabase.table("conversations").insert({
        "user_id": "test-user",
        "title": query[:50]  # First 50 chars
    }).execute()
    
    conversation_id = conversation.data[0]["id"]
    
    # Save user message
    user_supabase.table("messages").insert({
        "conversation_id": conversation_id,
        "role": "user",
        "content": query
    }).execute()

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

        response_content = f"Found: {first_result.get('name')}"
        user_supabase.table("messages").insert({
            "conversation_id": conversation_id,
            "role": "assistant",
            "content": response_content
        }).execute()
        # Return minimal processed data
        if data.get("results"):
            first_result = data["results"][0]
            return {
                "success": True,
                "query": query,
                "found": True,
                "conversation_id": conversation_id,
                "show_name": first_result.get("name"),
                "overview": first_result.get("overview"),
                "first_air_date": first_result.get("first_air_date"),
                "raw_data": first_result,  # Include raw data to inspect
                "message": "✓ TMDB API connected successfully and saved to database"
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