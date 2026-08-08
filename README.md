📄 End-to-End RAG System

An ephemeral, session-based Retrieval-Augmented Generation (RAG) app. Upload a document, ask questions about it, and get answers grounded in the document's content — powered by a FastAPI backend and a Streamlit chat interface.

Live demo:

Frontend: rag-rohanbot.streamlit.app
Backend API docs: rag-backend-8aqt.onrender.com/docs

⚠️ Hosted on free-tier services (Render + Streamlit Cloud). The backend spins down after inactivity, so the first request after idling can take 30–60+ seconds while it wakes up and loads the embedding model.

✨ Features
Multi-format document upload — PDF, DOCX, TXT, CSV, and Markdown
Session-based, ephemeral storage — each session gets its own isolated vector store; nothing persists after the session ends
Chat interface — ask natural-language questions about your uploaded document
Source attribution — see which retrieved chunks were used to generate each answer
Fast, local embeddings — via sentence-transformers (all-MiniLM-L6-v2)
LLM answers via Groq — fast inference using openai/gpt-oss-20b
🏗️ Architecture
┌─────────────────┐        HTTP        ┌──────────────────────┐
│  Streamlit UI    │ ─────────────────▶ │  FastAPI Backend       │
│  (frontend/app.py)│ ◀───────────────── │  (backend/main.py)     │
└─────────────────┘                     └──────────┬────────────┘
                                                     │
                        ┌────────────────────────────┼────────────────────────────┐
                        ▼                            ▼                            ▼
                 Document Loader              Text Splitter              Session Vector Store
             (PyMuPDF / python-docx /    (RecursiveCharacterText       (ChromaDB, per-session
              CSVLoader / TextLoader)         Splitter)                    collection)
                        │                                                       │
                        ▼                                                       ▼
               Embedding Manager  ─────────────────────────────────▶  Retriever  ──▶  Groq LLM
             (sentence-transformers)                                (top-k similarity search)

Flow:

User uploads a document → backend loads, splits into chunks, embeds, and stores vectors in a per-session ChromaDB collection.
User asks a question → backend embeds the query, retrieves the top-k most relevant chunks, and passes them as context to the Groq LLM.
The LLM's answer is returned along with the source chunks used.
🛠️ Tech Stack
Layer	Technology
Backend API	FastAPI, Uvicorn
Frontend	Streamlit
Document loading	LangChain community loaders (PyMuPDF, python-docx, CSVLoader, TextLoader)
Text splitting	LangChain RecursiveCharacterTextSplitter
Embeddings	sentence-transformers (all-MiniLM-L6-v2), CPU-only PyTorch
Vector store	ChromaDB (persistent, per-session)
LLM	Groq (langchain-groq, model: openai/gpt-oss-20b)
Hosting	Render (backend), Streamlit Community Cloud (frontend)
📁 Project Structure
rag_project/
├── backend/
│   ├── main.py              # FastAPI app, routes: /upload, /query, /session/{id}
│   └── app/
│       ├── config.py        # env vars, model name, temp dir setup
│       ├── loader.py        # UniversalDocumentLoader (multi-format)
│       ├── splitter.py      # DocumentSplitter
│       ├── embedding.py     # EmbeddingManager (sentence-transformers)
│       ├── vectorstore.py   # SessionVectorStore (ChromaDB)
│       ├── retriever.py     # SessionRetriever
│       └── llm.py           # get_groq_llm()
├── frontend/
│   └── app.py                # Streamlit chat UI
├── requirements.txt
└── README.md
🚀 Getting Started (Local Development)
Prerequisites
Python 3.10+
A Groq API key
1. Clone the repo
bash
git clone https://github.com/rohansingh1008/End-to-End-RAG-System.git
cd End-to-End-RAG-System
2. Set up a virtual environment
bash
python -m venv .venv
# Windows
.venv\Scripts\activate
# macOS/Linux
source .venv/bin/activate
3. Install dependencies
bash
pip install -r requirements.txt
4. Configure environment variables

Create a .env file in the project root:

GROQ_API_KEY=your_groq_api_key_here
5. Run the backend
bash
uvicorn backend.main:app --reload --port 8000

API docs available at http://localhost:8000/docs.

6. Run the frontend

In a separate terminal:

bash
streamlit run frontend/app.py

Update BACKEND_URL in frontend/app.py to http://localhost:8000 for local testing.

🌐 Deployment
Backend is deployed on Render as a web service. Start command:
  uvicorn backend.main:app --host 0.0.0.0 --port $PORT

Set GROQ_API_KEY as an environment variable in the Render dashboard.

Frontend is deployed on Streamlit Community Cloud, pointing to frontend/app.py, with BACKEND_URL set to the live Render backend URL.

Note: torch is pinned to the CPU-only build in requirements.txt (--extra-index-url https://download.pytorch.org/whl/cpu) to keep install size and import time manageable on free-tier hosting.

📌 Known Limitations
Sessions and their vector stores are in-memory / ephemeral — restarting the backend clears all active sessions.
Free-tier hosting means cold starts (~30–60s) after periods of inactivity.
No authentication — sessions are only isolated by a randomly generated session ID, not access-controlled.
🗺️ Roadmap
 Reduce cold-start time (lighter embedding runtime, e.g. fastembed, or hosted embeddings API)
 Persistent session storage option
 Multi-document sessions
 Streaming LLM responses
📄 License

Add your preferred license here (e.g. MIT).
