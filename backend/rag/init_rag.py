import os
from pathlib import Path
from rag.resume_processor import ResumeProcessor
from rag.agent import RAGAgent

class RAGSystem:
    def __init__(self, openai_api_key: str):
        self.openai_api_key = openai_api_key
        self.vector_store = None
        self.agent = None
        self.vector_store_path = Path(__file__).parent / "vector_store"
    
    def initialize(self, resume_pdf_path: str, force_rebuild: bool = False):
        """Initialize the RAG system"""
        print("Initializing RAG system...")
        
        # Check if vector store exists
        if self.vector_store_path.exists() and not force_rebuild:
            print("Loading existing vector store...")
            try:
                self.vector_store = ResumeProcessor.load_vector_store(
                    str(self.vector_store_path),
                    self.openai_api_key
                )
            except Exception as e:
                print(f"Error loading vector store: {e}")
                print("Rebuilding vector store...")
                force_rebuild = True
        
        # Build vector store if needed
        if not self.vector_store or force_rebuild:
            if not os.path.exists(resume_pdf_path):
                raise FileNotFoundError(f"Resume PDF not found at {resume_pdf_path}")
            
            print("Processing resume and creating vector store...")
            processor = ResumeProcessor(resume_pdf_path, self.openai_api_key)
            self.vector_store = processor.process_resume()
            
            # Save vector store
            os.makedirs(self.vector_store_path, exist_ok=True)
            processor.save_vector_store(str(self.vector_store_path))
        
        # Initialize agent
        print("Initializing RAG agent...")
        self.agent = RAGAgent(self.vector_store, self.openai_api_key, model_name="gpt-4")
        print("RAG system ready!")
    
    def chat(self, message: str, session_id: str) -> str:
        """Send a message to the agent"""
        if not self.agent:
            raise RuntimeError("RAG system not initialized. Call initialize() first.")
        return self.agent.chat(message, session_id)
    
    def get_history(self, session_id: str):
        """Get chat history"""
        if not self.agent:
            return []
        return self.agent.get_chat_history(session_id)