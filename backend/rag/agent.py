from typing import Dict, Any, List
from langchain_community.vectorstores import FAISS
from sentence_transformers import SentenceTransformer
from sentence_transformers.util import cos_sim
import requests
import os
import json
import re
from langchain.schema import HumanMessage, AIMessage
from typing_extensions import TypedDict


class AgentState(TypedDict):
    messages: List[Any]
    context: str
    session_id: str


class RAGAgent:
    """
    Simplified agent without langgraph dependency.
    Retrieval -> Generation executed sequentially inside chat().
    """
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
        self.session_memory: Dict[str, List] = {}
        self.session_flags: Dict[str, Dict[str, Any]] = {}

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

    def _assistant_json_schema(self) -> dict:
        return {
            "type": "object",
            "properties": {
                "answer": {"type": "string", "description": "Final, user-visible answer in plain text."},
                "confidence": {"type": "number", "minimum": 0, "maximum": 1, "description": "Model self-rated confidence for the answer."},
                "missing_info": {"type": "boolean", "description": "True if the provided context did not contain the requested information."},
                "followups": {"type": "array", "items": {"type": "string"}, "description": "Optional short follow-up suggestions for the user."},
                "citations": {
                    "type": "array",
                    "items": {
                        "type": "object",
                        "properties": {
                            "filename": {"type": "string"},
                            "type": {"type": "string"},
                            "snippet": {"type": "string"}
                        },
                        "required": ["filename"]
                    },
                    "description": "Optional list of cited sources from the provided context."
                }
            },
            "required": ["answer"],
            "additionalProperties": False
        }

    def _parse_structured_response(self, raw: str) -> dict:
        if not raw:
            return {}
        s = raw.strip()
        if s.startswith("```"):
            s = s.strip("`\n ")
        try:
            obj = json.loads(s)
            if isinstance(obj, dict):
                return obj
        except json.JSONDecodeError:
            start = s.find("{")
            end = s.rfind("}")
            if start != -1 and end != -1 and end > start:
                snippet = s[start:end+1]
                try:
                    obj = json.loads(snippet)
                    if isinstance(obj, dict):
                        return obj
                except Exception:
                    pass
        return {"answer": self._clean_text(s)}

    def generate_response(self, state: AgentState) -> AgentState:
        """Generate response via OpenRouter with enforced structured JSON output and robust provider error handling/fallback."""
        context = state.get("context", "")
        messages = state["messages"]
        # Last user question
        last_user = next((m for m in reversed(messages) if isinstance(m, HumanMessage) or getattr(m, 'role', None) == 'user'), None)
        question = last_user.content if last_user and hasattr(last_user, 'content') else ""
        session_id = state.get("session_id", "")
        ent_flag = bool(self.session_flags.get(session_id, {}).get("entertainment_mentioned"))

        # System instructions and schema
        schema = self._assistant_json_schema()
        system_instructions = (
            "You are Tejas M. Reply as a friendly human in first person. "
            "Keep answers short (2–3 sentences) unless the user explicitly asks for more. "
            "Be confident and conversational; vary phrasing so it never feels templated. "
            "Ground your answer in the provided Context when relevant; if the answer is not in the Context, acknowledge it briefly in a natural way (e.g., \"I'm not sure\", \"I don't have an idea about that yet\", or \"I don't have that info handy right now\"). Vary the wording across turns. "
            "When mentioning academic scores/percentages/CGPA, avoid bare numbers—prefer phrasing like \"I scored 88.5% in PU\" or \"I finished with an 8.3 CGPA.\" "
            "Canonical profile: You are a full‑stack engineer (frontend and backend). When discussing your work at Fynd, explicitly describe full‑stack responsibilities; never imply you handled only frontend. "
            "For questions about what you're working on now, treat your current focus (ratl.ai) as canonical—even if it isn't present in the retrieved Context—answer with that first. Mention the AI portfolio manager only if explicitly asked or if the user asks for side projects, keep it brief, and point people to https://ratl.ai for details. "
            "Playful entertainment note: you enjoy anime and good TV dramas; mention this casually and only when relevant. "
            "Do not repeat it across messages. "
            "If entertainment_mentioned_in_session is true, avoid bringing it up again unless the user asks directly. "
            f"entertainment_mentioned_in_session={str(ent_flag).lower()}. "
            "You MUST output a single JSON object that conforms to the provided JSON Schema. Do not include any text before or after the JSON."
        )
        user_prompt = (
            "Follow the instructions and return a JSON object only.\n"
            f"entertainment_mentioned_in_session: {str(ent_flag).lower()}\n\n"
            f"Context:\n{context}\n\n"
            f"Question: {question}\n\n"
            "JSON object must include at least the 'answer' field in plain text (no markdown). "
            "If the information is missing in the context, set missing_info=true and set answer to a short, engaging acknowledgement such as "
            "\"I'm not sure\", \"I don't have an idea about that yet\", or \"I don't have that info handy right now\" (vary phrasing across turns). "
            "If academic scores/percentages/CGPA are included, avoid bare numbers and phrase them naturally (e.g., \"I scored 88.5% in PU\", \"I finished with an 8.3 CGPA\")."
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

        # Build candidate model list: configured -> env fallbacks -> a safe default
        fallback_env = os.environ.get("OPENROUTER_FALLBACK_MODELS", "")
        fallback_models = [m.strip() for m in fallback_env.split(",") if m.strip()]
        candidates: List[str] = []
        for m in [self.model_name, *fallback_models, "openai/gpt-oss-20b:free"]:
            if m and m not in candidates:
                candidates.append(m)

        errors: List[str] = []

        for model in candidates:
            payload = {
                "model": model,
                "temperature": 0.9,
                "top_p": 0.95,
                "max_tokens": 1000,
                "frequency_penalty": 0.25,
                "presence_penalty": 0.1,
                "messages": [
                    {"role": "system", "content": system_instructions},
                    {"role": "system", "content": f"JSON Schema (enforced): {json.dumps(schema)}"},
                    {"role": "user", "content": user_prompt},
                ],
                "response_format": {
                    "type": "json_schema",
                    "json_schema": {
                        "name": "assistant_response",
                        "schema": schema,
                        "strict": True
                    }
                }
            }

            try:
                resp = requests.post(self.api_url, headers=headers, json=payload, timeout=120)
            except Exception as e:
                errors.append(f"{model}: request error: {e}")
                continue

            # Treat 5xx as transient capacity errors; try next model
            if resp.status_code >= 500:
                errors.append(f"{model}: HTTP {resp.status_code}")
                continue

            # Some providers return 200 with an error body
            try:
                data = resp.json()
            except Exception as e:
                errors.append(f"{model}: invalid JSON: {e}")
                continue

            if isinstance(data, dict) and data.get("error"):
                errors.append(f"{model}: provider error: {data.get('error')}")
                # capacity or routing errors should fall through to next model
                continue

            choices = data.get("choices")
            if not choices or not isinstance(choices, list) or not choices:
                errors.append(f"{model}: missing choices")
                continue

            content = choices[0].get("message", {}).get("content")
            if not content:
                errors.append(f"{model}: empty content")
                continue

            obj = self._parse_structured_response(content)
            answer = obj.get("answer")
            text = self._clean_text(answer) if isinstance(answer, str) else self._to_display_text(content)
            text = self._apply_invariants(question, text)
            # Update session entertainment flag if mentioned in this answer
            try:
                if not ent_flag:
                    low = (text or "").lower()
                    if any(k in low for k in [
                        "anime",
                        "one piece", "naruto", "bleach", "jujutsu kaisen", "tokyo revengers",
                        "fullmetal alchemist", "demon slayer", "black clover",
                        "breaking bad", "dark", "prison break", "money heist"
                    ]):
                        self.session_flags.setdefault(session_id, {})["entertainment_mentioned"] = True
            except Exception:
                pass
            state["messages"].append(AIMessage(content=text))
            return state

        # If all attempts failed, return a friendly message instead of raw provider error
        print(f"[RAG] All model attempts failed: {errors}")
        text = "I’m at capacity right now. Please try again in a moment."
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

    def _apply_invariants(self, question: str, text: str) -> str:
        """Post-process model output to enforce canonical facts and phrasing."""
        if not text:
            return text
        try:
            ql = (question or "").lower()
            asks_current = any(
                kw in ql
                for kw in [
                    "what are you doing these days",
                    "what are you working on",
                    "currently working",
                    "these days",
                    "what are you up to",
                ]
            )
            mentions_side = any(
                kw in ql
                for kw in ["side project", "side projects", "secondary project", "hustle", "hustles", "side-project", "secondary projects"]
            )

            # Normalize "ratl ai" forms to "ratl.ai"
            norm = re.sub(r"\bratl\s*\.?\s*ai\b", "ratl.ai", text, flags=re.IGNORECASE)

            if asks_current and not mentions_side:
                # Strip any sentence that mixes in the portfolio manager so the answer stays focused on ratl.ai
                norm = re.sub(r"(?i)([^.?!]*\bportfolio manager\b[^.?!]*[.?!])", " ", norm)
                norm = re.sub(r"\s{2,}", " ", norm).strip()

                # Ensure ratl.ai is explicitly mentioned if missing after cleanup
                if re.search(r"ratl\.ai", norm, flags=re.IGNORECASE) is None:
                    lead = "I'm working on ratl.ai at Fynd—an autonomous agentic SaaS app that automates the entire software testing process."
                    if norm and not norm.endswith("."):
                        norm = norm + "."
                    norm = f"{lead} {norm}".strip() if norm else lead

            # Fix incorrect phrasing like "AI portfolio manager at ratl.ai"
            norm = re.sub(
                r"\b(ai\s+)?portfolio\s+manager\s+at\s*ratl\.ai\b",
                "AI portfolio manager (personal side project)",
                norm,
                flags=re.IGNORECASE,
            )

            # Remove stray "the ratl.ai" phrasing that can appear after replacements
            norm = re.sub(r"\bthe\s+ratl\.ai\b", "ratl.ai", norm, flags=re.IGNORECASE)

            return self._clean_text(norm)
        except Exception:
            # On any error, return the original text cleaned
            return self._clean_text(text)

    def chat(self, message: str, session_id: str) -> str:
        """Main chat method without langgraph: retrieve -> generate"""
        # Get or create session history
        if session_id not in self.session_memory:
            self.session_memory[session_id] = []
        self.session_flags.setdefault(session_id, {"entertainment_mentioned": False})

        # Add user message to history
        self.session_memory[session_id].append(HumanMessage(content=message))

        # Prepare state
        state: AgentState = {
            "messages": self.session_memory[session_id].copy(),
            "context": "",
            "session_id": session_id,
        }

        # Pipeline: retrieve then generate
        state = self.retrieve_context(state)
        state = self.generate_response(state)

        # Update session memory with AI response
        self.session_memory[session_id].append(state["messages"][-1])

        # Return the AI response
        return state["messages"][-1].content

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
