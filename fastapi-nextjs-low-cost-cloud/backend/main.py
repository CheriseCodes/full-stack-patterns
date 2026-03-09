from fastapi import FastAPI, Header, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import os
from dotenv import load_dotenv
import requests
from supabase import create_client, Client


load_dotenv()

supabase: Client = create_client(
    os.getenv("SUPABASE_URL"),
    os.getenv("SUPABASE_KEY")
)


def verify_supabase_jwt(token: str) -> dict:
  """
  Verify the Supabase JWT using either the project's JWT secret (HS256)
  or the project's JWKS endpoint (RS256), depending on the token header.
  Validates signature, audience, issuer, and standard time claims.
  """
  try:
     decoded = supabase.auth.get_claims(token)['claims']
  except Exception as e:
      raise HTTPException(
          status_code=status.HTTP_401_UNAUTHORIZED,
          detail=f"Invalid Supabase access token: {str(e)}",
      )

  return decoded

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
    
    # Basic auth guard – require a Bearer token from Supabase
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Missing or invalid Authorization header",
        )

    access_token = authorization.replace("Bearer ", "").strip()

    # First, cryptographically verify the JWT (signature, issuer, audience, exp/nbf)
    decoded = verify_supabase_jwt(access_token)
    user_id = str(decoded.get("sub") or decoded.get("user_metadata")['id'])
    if not user_id:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Supabase token does not contain a user identifier",
        )

    query = request.query

    # Create a Supabase client scoped to this user's session so RLS/auth.uid() work
    user_supabase = create_client(
        os.getenv("SUPABASE_URL"),
        os.getenv("SUPABASE_KEY")
    )

    try:
        user_supabase.auth.set_session(access_token, "")
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=f"Failed to set Supabase session: {str(e)}",
        )

    # Create conversation for the authenticated user
    conversation = user_supabase.table("conversations").insert({
        "user_id": user_id,
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

        results = data.get("results") or []
        if results:
            first_result = results[0]
            response_content = f"Found: {first_result.get('name')}"
            user_supabase.table("messages").insert({
                "conversation_id": conversation_id,
                "role": "assistant",
                "content": response_content
            }).execute()

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
            user_supabase.table("messages").insert({
                "conversation_id": conversation_id,
                "role": "assistant",
                "content": "No results found"
            }).execute()

            return {
                "success": True,
                "query": query,
                "found": False,
                "message": "No results found"
            }

    except Exception as e:
        user_supabase.table("messages").insert({
            "conversation_id": conversation_id,
            "role": "assistant",
            "content": f"Error calling TMDB: {str(e)}"
        }).execute()

        return {
            "error": str(e),
            "query": query,
            "message": "Failed to connect to TMDB"
        }