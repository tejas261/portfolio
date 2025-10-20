# 🤖 AI-Powered Portfolio

A modern, intelligent portfolio application featuring a RAG-based (Retrieval Augmented Generation) conversational AI assistant powered by GPT-4, LangChain, and LangGraph.

![Tech Stack](https://img.shields.io/badge/Frontend-React-61DAFB?logo=react)
![Backend](https://img.shields.io/badge/Backend-FastAPI-009688?logo=fastapi)
![AI](https://img.shields.io/badge/AI-GPT--4-412991?logo=openai)
![Database](https://img.shields.io/badge/Database-MongoDB-47A248?logo=mongodb)

## ✨ Features

### 📋 Portfolio View

- **Dynamic Experience Timeline** - Showcase your professional journey
- **Project Highlights** - Feature your best work with impact metrics
- **Skills Matrix** - Categorized technical skills
- **Education & Certifications** - Academic background
- **Contact Information** - Easy ways to connect

### 💬 AI Chat Assistant

- **GPT-4 Powered** - Intelligent, context-aware responses
- **RAG System** - Answers based on your actual resume content
- **Conversation Memory** - Maintains context across the session
- **Session Persistence** - UUID-based session tracking
- **Graceful Fallback** - Mock responses if API is unavailable

## 🏗️ Architecture

### Backend (Python + FastAPI)

- **LangGraph Agent** - Conversational AI with state management
- **LangChain** - LLM orchestration and chains
- **FAISS Vector Store** - Semantic search over resume content
- **OpenAI Embeddings** - High-quality text embeddings
- **PyPDF** - Resume PDF processing
- **MongoDB** - Data persistence

### Frontend (React)

- **React 19** - Modern UI library
- **Tailwind CSS** - Utility-first styling
- **Shadcn UI** - Beautiful component library
- **Axios** - HTTP client
- **Lucide Icons** - Modern icon set

## 🚀 Quick Start

### Prerequisites

- Node.js (v16+)
- Python (v3.9+)
- MongoDB (local or cloud)
- OpenAI API Key

### 1. Clone & Setup

```bash
# Clone the repository
cd portfolio

# Setup backend
cd backend
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
pip install -r requirements.txt
cp .env.example .env
# Edit .env and add your OPENAI_API_KEY and MongoDB credentials

# Setup frontend
cd ../frontend
npm install --legacy-peer-deps
cp .env.example .env
# Edit .env if needed (default backend URL is http://localhost:8000)
```

### 2. Add Your Resume

Place your resume PDF at:

```
backend/data/resume.pdf
```

### 3. Run the Application

**Option A: Using startup scripts (recommended)**

```bash
# Terminal 1 - Backend
./start-backend.sh

# Terminal 2 - Frontend
./start-frontend.sh
```

**Option B: Manual start**

```bash
# Terminal 1 - Backend
cd backend
source venv/bin/activate
uvicorn server:app --reload --host 0.0.0.0 --port 8000

# Terminal 2 - Frontend
cd frontend
npm start
```

### 4. Access the Application

- **Frontend**: http://localhost:3000
- **Backend API**: http://localhost:8000
- **API Docs**: http://localhost:8000/docs

## 🧪 Testing the RAG System

Run the test script to verify everything works:

```bash
cd backend
source venv/bin/activate
python test_rag.py
```

This will:

- ✅ Check for OpenAI API key
- ✅ Verify resume PDF exists
- ✅ Initialize the RAG system
- ✅ Test chat functionality
- ✅ Verify conversation history

## 📁 Project Structure

```
portfolio/
├── backend/
│   ├── data/
│   │   └── resume.pdf              # Your resume (add this!)
│   ├── models/
│   │   └── chat.py                 # Pydantic models
│   ├── rag/
│   │   ├── agent.py                # LangGraph conversational agent
│   │   ├── init_rag.py             # RAG system coordinator
│   │   ├── resume_processor.py     # PDF processing & embeddings
│   │   └── vector_store/           # FAISS index (auto-generated)
│   ├── .env                        # Environment variables
│   ├── .env.example                # Example environment config
│   ├── requirements.txt            # Python dependencies
│   ├── server.py                   # FastAPI application
│   └── test_rag.py                 # RAG system tests
├── frontend/
│   ├── public/
│   ├── src/
│   │   ├── components/
│   │   │   └── ui/                 # Shadcn UI components
│   │   ├── data/
│   │   │   └── mock.js             # Portfolio data & fallback responses
│   │   ├── hooks/
│   │   ├── lib/
│   │   ├── pages/
│   │   │   ├── ChatView.jsx        # AI chat interface
│   │   │   └── PortfolioView.jsx   # Portfolio display
│   │   ├── App.js
│   │   └── index.js
│   ├── .env                        # Frontend environment variables
│   ├── .env.example                # Example frontend config
│   └── package.json
├── .gitignore
├── README.md
├── SETUP.md                        # Detailed setup guide
├── start-backend.sh                # Backend startup script
└── start-frontend.sh               # Frontend startup script
```

## 🔧 Configuration

### Backend (.env)

```bash
OPENAI_API_KEY=sk-...              # Required: Your OpenAI API key
MONGO_URL=mongodb://localhost:27017 # Your MongoDB connection string
DB_NAME=portfolio_db                # Database name
CORS_ORIGINS=http://localhost:3000  # Allowed origins
PORT=8000                           # Backend port
```

### Frontend (.env)

```bash
REACT_APP_BACKEND_URL=http://localhost:8000  # Backend API URL
```

## 🎯 API Endpoints

### Chat

- `POST /api/chat` - Send a message to the AI assistant

  ```json
  {
    "message": "What are your skills?",
    "session_id": "unique-session-id"
  }
  ```

- `GET /api/chat/history/{session_id}` - Get conversation history

### Status

- `GET /api/` - Health check
- `GET /api/status` - Get status checks
- `POST /api/status` - Create status check

## 🤖 How the RAG System Works

1. **Resume Processing**

   - PDF is loaded and text is extracted
   - Text is split into chunks (1000 chars with 200 overlap)
   - Each chunk is embedded using OpenAI embeddings
   - Embeddings are stored in FAISS vector database

2. **Query Processing**

   - User asks a question in the chat
   - Question is embedded using same model
   - Top 3 most relevant chunks are retrieved via semantic search
   - Retrieved context is passed to GPT-4

3. **Response Generation**
   - LangGraph agent orchestrates the workflow
   - GPT-4 generates response using retrieved context
   - Conversation history is maintained per session
   - Response is returned to the user

## 🛠️ Customization

### Update Portfolio Data

Edit `frontend/src/data/mock.js` to customize:

- Personal information
- Experience timeline
- Projects
- Skills
- Education
- Mock chat responses (fallback)

### Modify Chat Behavior

Edit `backend/rag/agent.py` to customize:

- System prompt
- Temperature
- Number of retrieved chunks
- Conversation history length
- LLM model (default: GPT-4)

## 🐛 Troubleshooting

See [SETUP.md](SETUP.md) for detailed troubleshooting guide.

**Common Issues:**

1. **RAG system not initialized**

   - Verify `OPENAI_API_KEY` is set
   - Ensure resume.pdf exists
   - Check backend logs

2. **Frontend can't connect to backend**

   - Verify backend is running on port 8000
   - Check `REACT_APP_BACKEND_URL` in frontend .env
   - App will fall back to mock responses

3. **npm install fails**
   - Use `--legacy-peer-deps` flag
   - Clear cache: `npm cache clean --force`

## 📚 Tech Stack Details

- **FastAPI** - Modern Python web framework
- **LangChain** - LLM application framework
- **LangGraph** - Stateful agent orchestration
- **OpenAI GPT-4** - Large language model
- **FAISS** - Vector similarity search
- **MongoDB** - NoSQL database
- **React** - UI library
- **Tailwind CSS** - Utility-first CSS
- **Shadcn UI** - Component library

## 📄 License

MIT License - feel free to use this for your own portfolio!

## 🤝 Contributing

This is a personal portfolio template, but suggestions and improvements are welcome!

## 📧 Contact

For questions about this project, check out the AI Chat feature - it's built to answer questions about the portfolio! 😉

---

**Built with ❤️ using GPT-4, LangChain, and React**
