import os
from pathlib import Path
from rag.resume_processor import ResumeProcessor
from rag.agent import RAGAgent

class RAGSystem:
    def __init__(self, openrouter_api_key: str | None = None, model_name: str | None = None):
        self.openrouter_api_key = openrouter_api_key
        self.model_name = model_name or "openai/gpt-oss-20b:free"
        self.vector_store = None
        self.agent = None
        self.vector_store_path = Path(__file__).parent / "vector_store"
    
    def initialize(self, resume_pdf_path: str, force_rebuild: bool = False):
        """Initialize the RAG system"""
        print("Initializing RAG system...")

        # Helper to (re)build the vector store
        def build_store():
            if not os.path.exists(resume_pdf_path):
                raise FileNotFoundError(f"Resume PDF not found at {resume_pdf_path}")
            print("Processing resume and creating vector store...")
            # Use OpenAI embeddings (original impl) so index dimension is stable
            processor = ResumeProcessor(resume_pdf_path, os.environ.get('OPENAI_API_KEY', ''))
            store = processor.process_resume()
            os.makedirs(self.vector_store_path, exist_ok=True)
            processor.save_vector_store(str(self.vector_store_path))
            return store

        # Load existing if present
        if self.vector_store_path.exists() and not force_rebuild:
            print("Loading existing vector store...")
            try:
                self.vector_store = ResumeProcessor.load_vector_store(
                    str(self.vector_store_path), os.environ.get('OPENAI_API_KEY', '')
                )
            except Exception as e:
                print(f"Error loading vector store: {e}")
                print("Rebuilding vector store...")
                force_rebuild = True

        # Build if needed
        if not self.vector_store or force_rebuild:
            self.vector_store = build_store()

        # Validate embedding dimension matches FAISS index dimension
        try:
            test_vec = self.vector_store.embedding_function.embed_query("test")
            index_dim = getattr(self.vector_store.index, "d", None)
            embed_dim = len(test_vec) if hasattr(test_vec, "__len__") else None
            print(f"[RAG] FAISS index dim={index_dim}, embedding dim={embed_dim}")
            if index_dim and embed_dim and index_dim != embed_dim:
                print("[RAG] Dimension mismatch detected. Rebuilding vector store...")
                self.vector_store = build_store()
                test_vec = self.vector_store.embedding_function.embed_query("test")
                index_dim = getattr(self.vector_store.index, "d", None)
                embed_dim = len(test_vec) if hasattr(test_vec, "__len__") else None
                print(f"[RAG] After rebuild: FAISS index dim={index_dim}, embedding dim={embed_dim}")
        except Exception as e:
            print(f"[RAG] Warning: failed to validate vector store dimensions: {e}")

        # Initialize agent
        print("Initializing RAG agent...")
        self.agent = RAGAgent(
            self.vector_store,
            openrouter_api_key=self.openrouter_api_key,
            model_name=self.model_name,
        )
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