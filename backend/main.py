print(">>> start", flush=True)
from backend.app.loader import UniversalDocumentLoader
print(">>> loader ok", flush=True)
from backend.app.retriever import SessionRetriever
print(">>> retriever ok", flush=True)
from backend.app.splitter import DocumentSplitter
print(">>> splitter ok", flush=True)
from backend.app.vectorstore import SessionVectorStore
print(">>> vectorstore ok", flush=True)
import logging
import os
import shutil
import traceback
from pathlib import Path
from fastapi import FastAPI, File, Form, HTTPException, Request, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from pydantic import BaseModel

# Internal imports (relative to the backend directory)
from backend.app.config import EMBED_MODEL_NAME
from backend.app.loader import UniversalDocumentLoader
from backend.app.retriever import SessionRetriever
from backend.app.splitter import DocumentSplitter
from backend.app.vectorstore import SessionVectorStore

app = FastAPI(title="Ephemeral Multi-Format RAG API")

BASE_TEMP_DIR = Path("temp_uploads")
BASE_TEMP_DIR.mkdir(parents=True, exist_ok=True)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


logging.basicConfig(level=logging.INFO)


@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
  error_trace = traceback.format_exc()
  print("\n" + "=" * 60)
  print("EXPLICIT BACKEND TRACEBACK:")
  print(error_trace)
  print("=" * 60 + "\n")
  return JSONResponse(status_code=500, content={"detail": str(exc)})


ACTIVE_SESSIONS = {}


_embedding_manager = None
_llm = None


def get_embedding_manager():
  """Lazy load EmbeddingManager on first request."""
  global _embedding_manager
  if _embedding_manager is None:
    from backend.app.embedding import EmbeddingManager

    _embedding_manager = EmbeddingManager()
  return _embedding_manager


def get_llm():
  """Lazy load Groq LLM on first request."""
  global _llm
  if _llm is None:
    from backend.app.llm import get_groq_llm

    _llm = get_groq_llm()
  return _llm


class QueryRequest(BaseModel):
  session_id: str
  query: str


@app.post("/upload")
async def upload_and_process(
    session_id: str = Form(...), file: UploadFile = File(...)
):
  session_dir = BASE_TEMP_DIR / session_id
  session_dir.mkdir(parents=True, exist_ok=True)
  file_path = session_dir / file.filename

  with open(file_path, "wb") as buffer:
    shutil.copyfileobj(file.file, buffer)

  try:
    docs = UniversalDocumentLoader.load_file(str(file_path), file.filename)
    splitter = DocumentSplitter()
    chunks = splitter.split(docs)

    embed_mgr = get_embedding_manager()
    embeddings = embed_mgr.generate_embeddings([c.page_content for c in chunks])
    vstore = SessionVectorStore(session_id)
    vstore.add_documents(chunks, embeddings)

    ACTIVE_SESSIONS[session_id] = {
        "vstore": vstore,
        "retriever": SessionRetriever(vstore, embed_mgr),
    }

    return {
        "status": "success",
        "session_id": session_id,
        "filename": file.filename,
        "pages_loaded": len(docs),
        "chunks_created": len(chunks),
    }
  except Exception as e:
    raise HTTPException(status_code=500, detail=str(e))
  finally:
    if file_path.exists():
      os.remove(file_path)


@app.post("/query")
async def query_rag(req: QueryRequest):
  if req.session_id not in ACTIVE_SESSIONS:
    raise HTTPException(
        status_code=404,
        detail="Session expired or not found. Upload a document first.",
    )

  retriever = ACTIVE_SESSIONS[req.session_id]["retriever"]
  results = retriever.retrieve(req.query, top_k=3)

  if not results:
    return {
        "answer": "No relevant context found in uploaded document.",
        "sources": [],
    }

  context = "\n\n".join([r["content"] for r in results])
  prompt = (
      f"Use the context below to answer accurately:\nContext:\n{context}\n\nQuestion:"
      f" {req.query}\nAnswer:"
  )

  llm_instance = get_llm()
  response = llm_instance.invoke([prompt])
  return {
      "answer": response.content,
      "sources": [r["metadata"] for r in results],
  }


@app.delete("/session/{session_id}")
async def end_session(session_id: str):
  if session_id in ACTIVE_SESSIONS:
    ACTIVE_SESSIONS[session_id]["vstore"].cleanup()
    del ACTIVE_SESSIONS[session_id]
  return {"status": "cleared"}