from fastapi import FastAPI, APIRouter, HTTPException
from fastapi.responses import FileResponse
from dotenv import load_dotenv
from starlette.middleware.cors import CORSMiddleware
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
import os
import logging
import requests
from pathlib import Path
from datetime import datetime, timezone
from models.chat import ChatRequest, ChatResponse
from rag.init_rag import RAGSystem


# Configure logging first
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

ROOT_DIR = Path(__file__).parent
load_dotenv(ROOT_DIR / '.env')

# Initialize RAG System
rag_system = None
openrouter_key = os.environ.get('OPENROUTER_API_KEY')
try:
    # Override model via env if desired
    model_name = os.environ.get('OPENROUTER_MODEL', 'openai/gpt-oss-20b:free')
    rag_system = RAGSystem(openrouter_api_key=openrouter_key, model_name=model_name)
    data_dir = ROOT_DIR / 'data'
    rag_system.initialize(str(data_dir))
    logging.info(f"RAG system initialized successfully with model: {model_name}")
except Exception as e:
    logging.error(f"Failed to initialize RAG system: {e}")
    rag_system = None

# Create the main app without a prefix
app = FastAPI(redirect_slashes=False)

# Middleware to normalize trailing slashes (e.g., /api/chat/ -> /api/chat)
class StripTrailingSlashMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        path = request.scope.get("path", "")
        if len(path) > 1 and path.endswith("/"):
            request.scope["path"] = path.rstrip("/")
        return await call_next(request)

app.add_middleware(StripTrailingSlashMiddleware)

# Create a router with the /api prefix
api_router = APIRouter(prefix="/api", redirect_slashes=False)

# Health check endpoint (no trailing slash path)
@api_router.get("")
async def root():
    return {"message": "Portfolio API is running", "status": "healthy"}

# Download resume
@api_router.get("/resume")
async def download_resume():
    resume_path = ROOT_DIR / 'data' / 'resume.pdf'
    if not resume_path.exists():
        raise HTTPException(status_code=404, detail="Resume not found")
    return FileResponse(
        path=str(resume_path),
        filename="resume.pdf",
        media_type="application/pdf",
    )

# Chat endpoints
@api_router.post("/chat", response_model=ChatResponse)
async def chat(request: ChatRequest):
    """Chat with AI assistant about Tejas's portfolio"""
    if not rag_system:
        raise HTTPException(status_code=503, detail="RAG system not initialized. Please check OPENROUTER_API_KEY.")
    
    try:
        response = rag_system.chat(request.message, request.session_id)
        return ChatResponse(
            response=response,
            session_id=request.session_id,
            timestamp=datetime.now(timezone.utc)
        )
    except Exception as e:
        import traceback
        tb = traceback.format_exc()
        logger.error(f"Error in chat endpoint: {e}\n{tb}")
        raise HTTPException(status_code=500, detail=f"Error processing chat: {str(e)}")

@api_router.get("/chat/history/{session_id}")
async def get_chat_history(session_id: str):
    """Get chat history for a session"""
    if not rag_system:
        raise HTTPException(status_code=503, detail="RAG system not initialized.")
    
    try:
        history = rag_system.get_history(session_id)
        return {"session_id": session_id, "messages": history}
    except Exception as e:
        logger.error(f"Error getting chat history: {e}")
        raise HTTPException(status_code=500, detail=f"Error getting history: {str(e)}")

@api_router.get("/debug/openrouter")
async def debug_openrouter():
    """Call OpenRouter with the configured model and return raw response."""
    if not rag_system:
        raise HTTPException(status_code=503, detail="RAG system not initialized.")
    model = os.environ.get('OPENROUTER_MODEL', 'deepseek/deepseek-chat-v3.1:free')
    key = os.environ.get('OPENROUTER_API_KEY')
    url = "https://openrouter.ai/api/v1/chat/completions"
    headers = {"Content-Type": "application/json", "Accept": "application/json"}
    if key:
        headers["Authorization"] = f"Bearer {key}"
    if os.environ.get("OPENROUTER_SITE_URL"):
        headers["HTTP-Referer"] = os.environ["OPENROUTER_SITE_URL"]
    if os.environ.get("OPENROUTER_APP_NAME"):
        headers["X-Title"] = os.environ["OPENROUTER_APP_NAME"]
    payload = {
        "model": model,
        "messages": [
            {"role": "system", "content": "You are a helpful assistant."},
            {"role": "user", "content": "Hello from /debug/openrouter"},
        ],
        "max_tokens": 50,
    }
    try:
        resp = requests.post(url, headers=headers, json=payload, timeout=60)
        return {
            "model": model,
            "status": resp.status_code,
            "api_url": url,
            "raw": resp.text[:2000],
        }
    except Exception as e:
        logger.error(f"OpenRouter debug failed: {e}")
        raise HTTPException(status_code=500, detail=f"OpenRouter debug failed: {e}")

# RAG management endpoints
@api_router.post("/rag/reindex")
async def rag_reindex():
    """Force reindex of the data directory."""
    if not rag_system:
        raise HTTPException(status_code=503, detail="RAG system not initialized.")
    try:
        data_dir = ROOT_DIR / 'data'
        rag_system.reindex(str(data_dir))
        return {"status": "reindexed", "summary": rag_system.get_sources_summary()}
    except Exception as e:
        logger.error(f"Error reindexing: {e}")
        raise HTTPException(status_code=500, detail=f"Error reindexing: {str(e)}")

@api_router.get("/rag/sources")
async def rag_sources():
    """Summary of indexed sources"""
    if not rag_system:
        raise HTTPException(status_code=503, detail="RAG system not initialized.")
    try:
        return rag_system.get_sources_summary()
    except Exception as e:
        logger.error(f"Error getting sources: {e}")
        raise HTTPException(status_code=500, detail=f"Error getting sources: {str(e)}")

# Simple root OK route
@app.get("/")
def root_ok():
    return {"status": "ok"}

# Include the router in the main app
app.include_router(api_router)

_origins_raw = os.environ.get('CORS_ORIGINS', '')
_origins = [o.strip() for o in _origins_raw.split(',') if o.strip()]
if not _origins:
    _origins = ["*"]
_allow_creds = False if "*" in _origins else True

app.add_middleware(
    CORSMiddleware,
    allow_credentials=_allow_creds,
    allow_origins=_origins,
    allow_methods=["*"],
    allow_headers=["*"],
)

# No shutdown hooks required currently
