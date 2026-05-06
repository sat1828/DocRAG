"""
ChromaDB service for vector storage and similarity search.
"""
import chromadb
from chromadb.config import Settings as ChromaSettings
from typing import List, Dict, Any, Optional
import structlog

from app.core.config import settings

logger = structlog.get_logger()


class ChromaService:
    def __init__(self, persist_dir: str = None):
        self.persist_dir = persist_dir or settings.CHROMA_PERSIST_DIR
        self.client = chromadb.PersistentClient(
            path=self.persist_dir,
            settings=ChromaSettings(anonymized_telemetry=False)
        )
        logger.info("ChromaDB initialized", persist_dir=self.persist_dir)

    def get_or_create_collection(self, collection_name: str):
        return self.client.get_or_create_collection(
            name=collection_name,
            metadata={"hnsw:space": "cosine"}
        )

    def add_documents(self, collection_name: str, ids: List[str], embeddings: List[List[float]], metadatas: List[Dict[str, Any]], documents: List[str]) -> None:
        collection = self.get_or_create_collection(collection_name)
        collection.add(ids=ids, embeddings=embeddings, metadatas=metadatas, documents=documents)
        logger.info("Added documents to ChromaDB", collection=collection_name, count=len(ids))

    def query(self, collection_name: str, query_embedding: List[float], filter: Dict[str, Any], n_results: int = 10):
        try:
            collection = self.get_or_create_collection(collection_name)
            results = collection.query(
                query_embeddings=[query_embedding],
                where=filter,
                n_results=n_results,
                include=["documents", "metadatas", "distances"]
            )
            return results
        except Exception as e:
            logger.error("ChromaDB query failed", error=str(e))
            return {"ids": [[]], "documents": [[]], "metadatas": [[]], "distances": [[]]}

    def delete_collection(self, collection_name: str) -> None:
        try:
            self.client.delete_collection(name=collection_name)
        except Exception as e:
            logger.warning("Failed to delete collection", error=str(e))

    def delete_documents(self, collection_name: str, filter: Dict[str, Any]) -> None:
        try:
            collection = self.get_or_create_collection(collection_name)
            collection.delete(where=filter)
        except Exception as e:
            logger.error("Failed to delete documents", error=str(e))

    def get_collection_stats(self, collection_name: str):
        try:
            collection = self.get_or_create_collection(collection_name)
            return {"count": collection.count(), "name": collection_name}
        except Exception as e:
            logger.error("Failed to get collection stats", error=str(e))
            return {"count": 0, "name": collection_name}


chroma_service = ChromaService()
