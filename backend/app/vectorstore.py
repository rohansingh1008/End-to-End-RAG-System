import shutil
import uuid
import chromadb
from .config import BASE_TEMP_DIR

class SessionVectorStore:
    def __init__(self, session_id: str):
        self.session_id = session_id
        self.session_path = BASE_TEMP_DIR / session_id
        self.client = chromadb.PersistentClient(path=str(self.session_path))
        self.collection = self.client.get_or_create_collection(
            name=f"session_{session_id}"
        )

    def add_documents(self, documents: list, embeddings: list):
        ids = [f"doc_{uuid.uuid4().hex[:8]}" for _ in range(len(documents))]
        texts = [doc.page_content for doc in documents]
        metadatas = [dict(doc.metadata) for doc in documents]
        
        self.collection.add(
            ids=ids,
            embeddings=[e.tolist() for e in embeddings],
            metadatas=metadatas,
            documents=texts
        )

    def cleanup(self):
        del self.client
        if self.session_path.exists():
            shutil.rmtree(self.session_path, ignore_errors=True)