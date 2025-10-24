from typing import Dict, Any, List, Annotated
from langchain_community.vectorstores import FAISS
# Removed HuggingFaceHub; using direct Inference API calls
from sentence_transformers import SentenceTransformer
from sentence_transformers.util import cos_sim
import numpy as np
import requests
import os
import json
import re
from langchain.schema import HumanMessage, AIMessage
from langgraph.graph import StateGraph, END
from langgraph.graph.message import add_messages
from typing_extensions import TypedDict

# Define the state for our agent
class AgentState(TypedDict):
    messages: Annotated[list, add_messages]
    context: str
    session_id: str

class RAGAgent:
    def __init__(self, vector_store: FAISS, openrouter_api_key: str | None = None, model_name: str = "openai/gpt-oss-20b:free"):
        self.vector_store = vector_store
        self.model_name = model_name
        self.openrouter_api_key = openrouter_api_key or os.environ.get("OPENROUTER_API_KEY")
        self.api_url = "https://openrouter.ai/api/v1/chat/completions"
        # Local encoder for retrieval (fast and free)
        self.st_model = SentenceTransformer("all-MiniLM-L6-v2")
        # Precompute embeddings for all stored chunks once
        self.chunks: List[str] = []
        self.chunk_embeddings = None
        try:
            # Extract all documents from the LangChain FAISS docstore
            docs = []
            if hasattr(self.vector_store, "docstore") and hasattr(self.vector_store.docstore, "_dict"):
                docs = list(self.vector_store.docstore._dict.values())
            self.chunks = [getattr(d, "page_content", None) for d in docs if getattr(d, "page_content", None)]
            if self.chunks:
                self.chunk_embeddings = self.st_model.encode(self.chunks, convert_to_tensor=True)
        except Exception as e:
            print(f"[RAG] Failed to precompute chunk embeddings: {e}")
        self.graph = self._build_graph()
        self.session_memory: Dict[str, List] = {}
    
    def retrieve_context(self, state: AgentState) -> AgentState:
        """Retrieve relevant context using sentence-transformers (cosine sim)."""
        # Get the last user message
        last_message = state["messages"][-1]
        query = last_message.content if hasattr(last_message, 'content') else str(last_message)
        
        context = ""
        try:
            if self.chunks and self.chunk_embeddings is not None:
                query_embedding = self.st_model.encode(query, convert_to_tensor=True)
                scores = cos_sim(query_embedding, self.chunk_embeddings)
                # scores shape: (1, N)
                k = min(3, len(self.chunks))
                top_idx = scores.squeeze(0).argsort(descending=True)[:k]
                retrieved = [self.chunks[int(i)] for i in top_idx]
                context = "\n\n".join(retrieved)
            else:
                # Fallback to FAISS search if precomputed chunks missing
                docs = self.vector_store.similarity_search(query, k=3)
                context = "\n\n".join([doc.page_content for doc in docs])
        except Exception as e:
            print(f"[RAG] retrieve_context error, falling back to empty context: {e}")

        state["context"] = context
        return state
    
    def _format_prompt(self, system_prompt: str, messages: List[Any]) -> str:
        """Flatten chat history into a single prompt for text-generation models."""
        lines: List[str] = [system_prompt.strip(), "", "Conversation:"]
        for msg in messages[-5:]:
            role = None
            content = None
            if isinstance(msg, HumanMessage) or getattr(msg, 'role', None) == 'user':
                role = "User"
                content = msg.content if hasattr(msg, 'content') else str(msg)
            elif isinstance(msg, AIMessage) or getattr(msg, 'role', None) == 'assistant':
                role = "Assistant"
                content = msg.content if hasattr(msg, 'content') else str(msg)
            if role and content:
                lines.append(f"{role}: {content}")
        lines.append("Assistant:")
        return "\n".join(lines)

    def generate_response(self, state: AgentState) -> AgentState:
        """Generate response via OpenRouter Chat Completions using DeepSeek."""
        context = state.get("context", "")
        messages = state["messages"]
        # Last user question
        last_user = next((m for m in reversed(messages) if isinstance(m, HumanMessage) or getattr(m, 'role', None) == 'user'), None)
        question = last_user.content if last_user and hasattr(last_user, 'content') else ""

        # Persona + context prompt
        system_instructions = (
            "You are Tejas M responding directly to someone asking about you. "
            "Keep replies short (2-3 sentences), friendly, and natural. "
            "If a request is disallowed or harassing, politely refuse in plain text. "
            "Output must be human‑readable plain text only. Do not include any special tokens, BOS/EOS markers, or markdown. "
            "Canonical profile: You are a full‑stack engineer (frontend and backend). When discussing your work at Fynd, explicitly describe full‑stack responsibilities; never imply you handled only frontend. If retrieved context conflicts with this, prefer this canonical profile."
            "Personal touch: When the user asks about you as a person or your background, add one short, natural sentence (at most 1) "
            "that mentions you also enjoy sports, traveling, and learning about tech. Only add this if it feels relevant to the question."
        )
        prompt = (
            f"{system_instructions}\n\n"
            f"Context:\n{context}\n\n"
            f"Question: {question}\n"
            f"Answer:"
        )

        headers = {
            "Content-Type": "application/json",
            "Accept": "application/json",
        }
        if self.openrouter_api_key:
            headers["Authorization"] = f"Bearer {self.openrouter_api_key}"
        # Optional but recommended headers per OpenRouter docs
        if os.environ.get("OPENROUTER_SITE_URL"):
            headers["HTTP-Referer"] = os.environ["OPENROUTER_SITE_URL"]
        if os.environ.get("OPENROUTER_APP_NAME"):
            headers["X-Title"] = os.environ["OPENROUTER_APP_NAME"]

        payload = {
            "model": self.model_name,
            "temperature": 0.9,
            "top_p": 0.9,
            "max_tokens": 300,
            "messages": [
                {"role": "system", "content": system_instructions},
                {"role": "user", "content": prompt},
            ],
        }

        try:
            resp = requests.post(self.api_url, headers=headers, json=payload, timeout=120)
            if resp.status_code >= 400:
                raise RuntimeError(f"OpenRouter API {resp.status_code}: {resp.text[:300]}")
            data = resp.json()
            content = (
                data.get("choices", [{}])[0]
                .get("message", {})
                .get("content")
                or str(data)
            )
            text = self._to_display_text(content)
        except Exception as e:
            print(f"[RAG] OpenRouter generate_response error: {e}")
            text = "Sorry, I had trouble generating a response just now. Please try again."

        state["messages"].append(AIMessage(content=text))
        return state
    
    def _clean_text(self, text: str) -> str:
        """Strip common special tokens BOS/EOS and model boundary markers."""
        patterns = [
            r"<\|begin[_\s]*of[_\s]*sentence\|>",
            r"<\|end[_\s]*of[_\s]*sentence\|>",
            r"<\|begin[_\s]*of[_\s]*text\|>",
            r"<\|end[_\s]*of[_\s]*text\|>",
            r"<s>", r"</s>",
            r"<｜begin▁of▁sentence｜>",
            r"<｜end▁of▁sentence｜>",
        ]
        out = text or ""
        for p in patterns:
            out = re.sub(p, "", out, flags=re.IGNORECASE)
        return out.strip()

    def _to_display_text(self, raw: str) -> str:
        """If the model returned JSON, show its message; otherwise show cleaned text."""
        if not raw:
            return ""
        s = raw.strip()
        # Remove code fences
        if s.startswith("```"):
            s = s.strip("`\n ")
        # Try parse as JSON (handles policy/error blocks)
        try:
            obj = json.loads(s)
            if isinstance(obj, dict):
                msg = obj.get("message") or obj.get("content") or s
                return self._clean_text(str(msg))
        except json.JSONDecodeError:
            # Attempt to extract first JSON object if surrounded by extra text
            start = s.find("{")
            end = s.rfind("}")
            if start != -1 and end != -1 and end > start:
                snippet = s[start:end+1]
                try:
                    obj = json.loads(snippet)
                    if isinstance(obj, dict):
                        msg = obj.get("message") or obj.get("content") or snippet
                        return self._clean_text(str(msg))
                except Exception:
                    pass
        # Fall back to cleaned plain text
        return self._clean_text(s)

    def _build_graph(self) -> StateGraph:
        """Build the LangGraph workflow"""
        workflow = StateGraph(AgentState)
        
        # Add nodes
        workflow.add_node("retrieve", self.retrieve_context)
        workflow.add_node("generate", self.generate_response)
        
        # Add edges
        workflow.set_entry_point("retrieve")
        workflow.add_edge("retrieve", "generate")
        workflow.add_edge("generate", END)
        
        return workflow.compile()
    
    def chat(self, message: str, session_id: str) -> str:
        """Main chat method"""
        # Get or create session history
        if session_id not in self.session_memory:
            self.session_memory[session_id] = []
        
        # Add user message to history
        self.session_memory[session_id].append(HumanMessage(content=message))
        
        # Prepare state
        state = {
            "messages": self.session_memory[session_id].copy(),
            "context": "",
            "session_id": session_id
        }
        
        # Run the graph
        result = self.graph.invoke(state)
        
        # Update session memory with AI response
        self.session_memory[session_id].append(result["messages"][-1])
        
        # Return the AI response
        return result["messages"][-1].content
    
    def get_chat_history(self, session_id: str) -> List[Dict[str, str]]:
        """Get chat history for a session"""
        if session_id not in self.session_memory:
            return []
        
        history = []
        for msg in self.session_memory[session_id]:
            if isinstance(msg, HumanMessage):
                history.append({"role": "user", "content": msg.content})
            elif isinstance(msg, AIMessage):
                history.append({"role": "assistant", "content": msg.content})
        
        return history