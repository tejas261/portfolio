from fastapi import FastAPI, APIRouter, HTTPException
from dotenv import load_dotenv
from starlette.middleware.cors import CORSMiddleware
import os
import logging
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
openai_api_key = os.environ.get('OPENAI_API_KEY')
if openai_api_key:
    try:
        rag_system = RAGSystem(openai_api_key)
        resume_path = ROOT_DIR / 'data' / 'resume.pdf'
        rag_system.initialize(str(resume_path))
        logging.info("RAG system initialized successfully")
    except Exception as e:
        logging.error(f"Failed to initialize RAG system: {e}")
        rag_system = None
else:
    logging.warning("OPENAI_API_KEY not found. RAG system will not be available.")

# Create the main app without a prefix
app = FastAPI()

# Create a router with the /api prefix
api_router = APIRouter(prefix="/api")

# Health check endpoint
@api_router.get("/")
async def root():
    return {"message": "Portfolio API is running", "status": "healthy"}

# Chat endpoints
@api_router.post("/chat", response_model=ChatResponse)
async def chat(request: ChatRequest):
    """Chat with AI assistant about Tejas's portfolio"""
    if not rag_system:
        raise HTTPException(status_code=503, detail="RAG system not initialized. Please check OPENAI_API_KEY.")
    
    try:
        response = rag_system.chat(request.message, request.session_id)
        return ChatResponse(
            response=response,
            session_id=request.session_id,
            timestamp=datetime.now(timezone.utc)
        )
    except Exception as e:
        logger.error(f"Error in chat endpoint: {e}")
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

# Include the router in the main app
app.include_router(api_router)

app.add_middleware(
    CORSMiddleware,
    allow_credentials=True,
    allow_origins=os.environ.get('CORS_ORIGINS', '*').split(','),
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.on_event("shutdown")
async def shutdown_db_client():
    client.close()