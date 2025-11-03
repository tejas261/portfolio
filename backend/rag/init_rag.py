import os
from pathlib import Path
from typing import Any, Dict, List

from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain_core.documents import Document
from langchain_community.embeddings import SentenceTransformerEmbeddings
from langchain_community.vectorstores import FAISS

from rag.agent import RAGAgent
from rag.loaders import build_documents_from_data_dir


class RAGSystem:
    def __init__(self, openrouter_api_key: str | None = None, model_name: str | None = None):
        self.openrouter_api_key = openrouter_api_key
        self.model_name = model_name or "openai/gpt-oss-20b:free"
        self.vector_store: FAISS | None = None
        self.agent: RAGAgent | None = None
        self.vector_store_path = Path(__file__).parent / "vector_store"
        self.embedding_model_name = "sentence-transformers/all-MiniLM-L6-v2"

    def _chunk_documents(self, docs: List[Document]) -> List[Document]:
        splitter = RecursiveCharacterTextSplitter(
            chunk_size=800,
            chunk_overlap=150,
            separators=["\n\n", "\n", " ", ""],
        )
        chunks = splitter.split_documents(docs)

        # Prefix each chunk with a short source header so the model can ground answers
        prefixed: List[Document] = []
        for d in chunks:
            meta = d.metadata or {}
            filename = meta.get("filename")
            if not filename:
                src = meta.get("source")
                if isinstance(src, str):
                    try:
                        filename = Path(src).name
                    except Exception:
                        filename = src
            typ = meta.get("type", "doc")
            header = f"Source: {filename or 'unknown'} ({typ})\n"
            prefixed.append(Document(page_content=f"{header}{d.page_content}", metadata=meta))
        return prefixed

    def _build_store(self, data_dir: Path) -> FAISS:
        docs = build_documents_from_data_dir(data_dir)
        if not docs:
            raise ValueError(f"No documents found in {data_dir}")

        chunks = self._chunk_documents(docs)
        embeddings = SentenceTransformerEmbeddings(model_name=self.embedding_model_name)
        store = FAISS.from_documents(chunks, embeddings)

        # Persist vector store
        os.makedirs(self.vector_store_path, exist_ok=True)
        store.save_local(str(self.vector_store_path))
        return store

    def initialize(self, data_dir: str, force_rebuild: bool = False):
        """Initialize or (optionally) rebuild the RAG vector store from the data directory."""
        print("Initializing RAG system...")
        data_path = Path(data_dir)

        def build_store():
            print(f"Indexing data directory: {data_path}")
            return self._build_store(data_path)

        # Load existing if present
        if self.vector_store_path.exists() and not force_rebuild:
            print("Loading existing vector store...")
            try:
                embeddings = SentenceTransformerEmbeddings(model_name=self.embedding_model_name)
                self.vector_store = FAISS.load_local(
                    str(self.vector_store_path),
                    embeddings,
                    allow_dangerous_deserialization=True,
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

    def reindex(self, data_dir: str):
        """Force rebuild the vector store from the provided data directory."""
        self.initialize(data_dir, force_rebuild=True)

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

    def get_sources_summary(self) -> Dict[str, Any]:
        """Return a summary of indexed documents by type and file."""
        if not self.vector_store:
            return {"total": 0, "by_type": {}, "files": {}}
        try:
            docs = []
            if hasattr(self.vector_store, "docstore") and hasattr(self.vector_store.docstore, "_dict"):
                docs = list(self.vector_store.docstore._dict.values())

            by_type: Dict[str, int] = {}
            files: Dict[str, int] = {}
            for d in docs:
                meta = getattr(d, "metadata", {}) or {}
                t = meta.get("type", "unknown")
                f = meta.get("filename") or meta.get("source") or "unknown"
                by_type[t] = by_type.get(t, 0) + 1
                files[f] = files.get(f, 0) + 1

            return {"total": len(docs), "by_type": by_type, "files": files}
        except Exception as e:
            print(f"[RAG] sources_summary error: {e}")
            return {"total": 0, "by_type": {}, "files": {}}
