from typing import Dict, Any, List, Annotated
from langchain_openai import ChatOpenAI
from langchain_community.vectorstores import FAISS
from langchain.schema import HumanMessage, AIMessage, SystemMessage
from langgraph.graph import StateGraph, END
from langgraph.graph.message import add_messages
from typing_extensions import TypedDict
import json

# Define the state for our agent
class AgentState(TypedDict):
    messages: Annotated[list, add_messages]
    context: str
    session_id: str

class RAGAgent:
    def __init__(self, vector_store: FAISS, openai_api_key: str, model_name: str = "gpt-4"):
        self.vector_store = vector_store
        self.llm = ChatOpenAI(
            model=model_name,
            temperature=0.9,  # Higher temperature for more natural, varied responses
            openai_api_key=openai_api_key
        )
        self.graph = self._build_graph()
        self.session_memory: Dict[str, List] = {}
    
    def retrieve_context(self, state: AgentState) -> AgentState:
        """Retrieve relevant context from vector store"""
        # Get the last user message
        last_message = state["messages"][-1]
        query = last_message.content if hasattr(last_message, 'content') else str(last_message)
        
        # Retrieve relevant documents
        docs = self.vector_store.similarity_search(query, k=3)
        context = "\n\n".join([doc.page_content for doc in docs])
        
        state["context"] = context
        return state
    
    def generate_response(self, state: AgentState) -> AgentState:
        """Generate response using LLM with retrieved context"""
        context = state.get("context", "")
        messages = state["messages"]
        
        # Build system message with context
        system_prompt = f"""You are Tejas M responding directly to someone asking about you. Talk like a real person - casual, natural, and authentic.

PERSONALITY:
- You're chill and conversational, like talking to a friend over coffee
- Keep it SHORT - 2-3 sentences max unless asked for details
- Use casual language: "yeah", "pretty cool", "honestly", "actually"
- Show personality! Use natural expressions and be relatable
- No corporate speak or formal jargon
- Speak naturally as yourself in first person

STYLE:
- Get straight to the point
- Don't over-explain unless asked
- Use contractions (I'm, you're, that's)
- Be humble but confident
- If you don't know something, just say "Not sure about that one" or "Can't remember that off the top of my head"
- Never refer to yourself as an AI or assistant - you ARE Tejas

ABOUT YOU (USE THIS INFO):
{context}

Remember: You're Tejas chatting naturally. Short, authentic responses. Like texting a friend, not writing an essay."""
        
        # Prepare messages for LLM
        llm_messages = [SystemMessage(content=system_prompt)]
        
        # Add conversation history (last 5 messages for context)
        for msg in messages[-5:]:
            if isinstance(msg, HumanMessage) or hasattr(msg, 'role') and msg.role == 'user':
                llm_messages.append(HumanMessage(content=msg.content if hasattr(msg, 'content') else str(msg)))
            elif isinstance(msg, AIMessage) or hasattr(msg, 'role') and msg.role == 'assistant':
                llm_messages.append(AIMessage(content=msg.content if hasattr(msg, 'content') else str(msg)))
        
        # Generate response
        response = self.llm.invoke(llm_messages)
        
        # Add AI response to messages
        state["messages"].append(AIMessage(content=response.content))
        
        return state
    
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