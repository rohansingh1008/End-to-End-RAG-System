import numpy as np
from sentence_transformers import SentenceTransformer
from backend.app.config import EMBED_MODEL_NAME

class EmbeddingManager:
    def __init__(self, model_name: str = EMBED_MODEL_NAME):
        self.model = SentenceTransformer(model_name)

    def generate_embeddings(self, texts: list[str]) -> np.ndarray:
        return self.model.encode(texts, show_progress_bar=False)