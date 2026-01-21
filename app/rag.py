"""RAG (Retrieval-Augmented Generation) system."""

import json
import logging
from typing import Optional

import chromadb
from chromadb.config import Settings

from app.config import Config
from app.openrouter import get_openrouter_client

logger = logging.getLogger(__name__)


class RAGSystem:
    """Vector store and retrieval system."""

    def __init__(self):
        """Initialize RAG system with Chroma."""
        settings = Settings(anonymized_telemetry=False)
        self.client = chromadb.PersistentClient(
            path=str(Config.CHROMA_PERSIST_DIR),
            settings=settings,
        )
        self.collection = self.client.get_or_create_collection(
            name="knowledge_base",
            metadata={"hnsw:space": "cosine"},
        )
        self.or_client = get_openrouter_client()

    async def add_chunk(
        self,
        chunk_id: str,
        text: str,
        filename: str,
        page: int = 1,
    ) -> None:
        """Add a text chunk to the vector store."""
        # Get embedding
        embedding = await self.or_client.embed(text)

        # Store in Chroma with metadata
        self.collection.add(
            ids=[chunk_id],
            embeddings=[embedding],
            documents=[text],
            metadatas=[
                {
                    "filename": filename,
                    "page": page,
                    "chunk_id": chunk_id,
                }
            ],
        )
        logger.debug(f"Added chunk {chunk_id} from {filename}:p{page}")

    async def retrieve(
        self,
        query: str,
        top_k: int = 5,
        threshold: float = 0.6,
    ) -> list[dict]:
        """Retrieve relevant chunks for a query."""
        # Get query embedding
        query_embedding = await self.or_client.embed(query)

        # Search in Chroma
        results = self.collection.query(
            query_embeddings=[query_embedding],
            n_results=top_k,
            include=["documents", "metadatas", "distances"],
        )

        if not results["ids"] or not results["ids"][0]:
            logger.info(f"No chunks found for query: {query}")
            return []

        # Convert distances to similarity scores (1 - distance for cosine)
        retrieved = []
        for i, chunk_id in enumerate(results["ids"][0]):
            distance = results["distances"][0][i]
            similarity = 1 - distance  # For cosine distance
            
            if similarity >= threshold:
                retrieved.append(
                    {
                        "chunk_id": chunk_id,
                        "text": results["documents"][0][i],
                        "metadata": results["metadatas"][0][i],
                        "similarity": similarity,
                    }
                )

        logger.info(
            f"Retrieved {len(retrieved)} chunks for query (threshold={threshold})"
        )
        return retrieved

    def clear(self) -> None:
        """Clear all data from vector store."""
        # Delete and recreate collection
        self.client.delete_collection(name="knowledge_base")
        self.collection = self.client.get_or_create_collection(
            name="knowledge_base",
            metadata={"hnsw:space": "cosine"},
        )
        logger.info("Cleared vector store")

    def get_collection_stats(self) -> dict:
        """Get vector store statistics."""
        count = self.collection.count()
        return {"total_chunks": count}


def get_rag_system() -> RAGSystem:
    """Get RAG system instance."""
    return RAGSystem()
