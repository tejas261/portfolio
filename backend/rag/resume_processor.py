from pypdf import PdfReader
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain_community.embeddings import SentenceTransformerEmbeddings
from langchain_community.vectorstores import FAISS
from typing import List

class ResumeProcessor:
    def __init__(self, pdf_path: str, embedding_model: str = "sentence-transformers/all-MiniLM-L6-v2"):
        self.pdf_path = pdf_path
        # Use local sentence-transformers via LangChain community (no API key required)
        self.embeddings = SentenceTransformerEmbeddings(model_name=embedding_model)
        self.vector_store = None
        
    def extract_text_from_pdf(self) -> str:
        """Extract text from PDF file"""
        try:
            reader = PdfReader(self.pdf_path)
            text = ""
            for page in reader.pages:
                text += page.extract_text()
            return text
        except Exception as e:
            print(f"Error extracting text from PDF: {e}")
            return ""
    
    def chunk_text(self, text: str) -> List[str]:
        """Split text into chunks for embedding"""
        text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=1000,
            chunk_overlap=200,
            length_function=len,
            separators=["\n\n", "\n", " ", ""]
        )
        chunks = text_splitter.split_text(text)
        return chunks
    
    def create_vector_store(self, chunks: List[str]) -> FAISS:
        """Create FAISS vector store from text chunks"""
        self.vector_store = FAISS.from_texts(chunks, self.embeddings)
        return self.vector_store
    
    def process_resume(self) -> FAISS:
        """Main method to process resume and create vector store"""
        print("Extracting text from resume...")
        text = self.extract_text_from_pdf()
        
        if not text:
            raise ValueError("No text extracted from PDF")
        
        print(f"Extracted {len(text)} characters")
        print("Chunking text...")
        chunks = self.chunk_text(text)
        print(f"Created {len(chunks)} chunks")
        
        print("Creating vector store...")
        vector_store = self.create_vector_store(chunks)
        print("Vector store created successfully!")
        
        return vector_store
    
    def save_vector_store(self, save_path: str):
        """Save vector store to disk"""
        if self.vector_store:
            self.vector_store.save_local(save_path)
            print(f"Vector store saved to {save_path}")
    
    @classmethod
    def load_vector_store(cls, load_path: str, embedding_model: str = "sentence-transformers/all-MiniLM-L6-v2") -> FAISS:
        """Load vector store from disk"""
        embeddings = SentenceTransformerEmbeddings(model_name=embedding_model)
        vector_store = FAISS.load_local(load_path, embeddings, allow_dangerous_deserialization=True)
        print(f"Vector store loaded from {load_path}")
        return vector_store