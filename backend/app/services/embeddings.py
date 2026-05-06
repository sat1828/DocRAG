"""
Embedding service for text and multimodal embeddings.
"""
from typing import List, Union
import numpy as np
from sentence_transformers import SentenceTransformer
import structlog
import asyncio
from concurrent.futures import ThreadPoolExecutor

logger = structlog.get_logger()


class EmbeddingService:
    def __init__(self, model_name: str = "all-MiniLM-L6-v2"):
        logger.info("Loading embedding model", model=model_name)
        self.text_model = SentenceTransformer(model_name)
        self.embedding_dimension = 384
        logger.info("Embedding service initialized", dimension=self.embedding_dimension)

    def embed_text(self, texts: Union[str, List[str]]) -> np.ndarray:
        if isinstance(texts, str):
            texts = [texts]
        embeddings = self.text_model.encode(texts, show_progress_bar=False, convert_to_numpy=True, normalize_embeddings=True)
        return embeddings

    def embed_query(self, query: str) -> List[float]:
        embedding = self.text_model.encode([query], show_progress_bar=False, convert_to_numpy=True, normalize_embeddings=True)
        return embedding[0].tolist()

    async def batch_embed(self, texts: List[str], batch_size: int = 32) -> List[List[float]]:
        def encode_batch(batch):
            return self.text_model.encode(batch, show_progress_bar=False, convert_to_numpy=True, normalize_embeddings=True)

        loop = asyncio.get_event_loop()
        with ThreadPoolExecutor() as executor:
            tasks = []
            for i in range(0, len(texts), batch_size):
                batch = texts[i:i + batch_size]
                task = loop.run_in_executor(executor, encode_batch, batch)
                tasks.append(task)
            results = await asyncio.gather(*tasks)

        all_embeddings = []
        for batch_result in results:
            all_embeddings.extend(batch_result.tolist())
        return all_embeddings


embedding_service = EmbeddingService()
