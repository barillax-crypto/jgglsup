"""Document ingestion and chunking."""

import hashlib
import logging
import re
from pathlib import Path
from typing import Optional

from pypdf import PdfReader

from app.config import Config
from app.rag import get_rag_system

logger = logging.getLogger(__name__)


def chunk_text(text: str, chunk_size: int = 1000, overlap: int = 200) -> list[str]:
    """Split text into overlapping chunks."""
    chunks = []
    start = 0

    while start < len(text):
        end = start + chunk_size
        chunk = text[start:end]
        chunks.append(chunk)
        start = end - overlap

    return [c.strip() for c in chunks if c.strip()]


def extract_pdf_text(pdf_path: Path) -> dict[int, str]:
    """Extract text from PDF by page."""
    pages = {}
    try:
        reader = PdfReader(pdf_path)
        for page_num, page in enumerate(reader.pages, 1):
            text = page.extract_text()
            if text.strip():
                pages[page_num] = text
        logger.info(f"Extracted {len(pages)} pages from {pdf_path.name}")
    except Exception as e:
        logger.error(f"Error reading PDF {pdf_path}: {e}")
    return pages


def extract_text_file(text_path: Path) -> str:
    """Extract text from plain text file."""
    try:
        content = text_path.read_text(encoding="utf-8")
        logger.info(f"Read text file {text_path.name}")
        return content
    except Exception as e:
        logger.error(f"Error reading text file {text_path}: {e}")
        return ""


def create_chunk_id(filename: str, page: int, chunk_num: int) -> str:
    """Generate unique chunk ID."""
    data = f"{filename}:p{page}:c{chunk_num}".encode()
    return hashlib.md5(data).hexdigest()[:12]


async def ingest_document(file_path: Path) -> dict:
    """Ingest a single document (PDF or text)."""
    if not file_path.exists():
        raise FileNotFoundError(f"File not found: {file_path}")

    rag_system = get_rag_system()
    stats = {"file": file_path.name, "chunks_added": 0, "pages": 0}

    if file_path.suffix.lower() == ".pdf":
        pages = extract_pdf_text(file_path)
        stats["pages"] = len(pages)

        for page_num, page_text in pages.items():
            chunks = chunk_text(
                page_text,
                chunk_size=Config.RAG_CHUNK_SIZE,
                overlap=Config.RAG_CHUNK_OVERLAP,
            )

            for chunk_num, chunk in enumerate(chunks):
                chunk_id = create_chunk_id(file_path.name, page_num, chunk_num)
                await rag_system.add_chunk(
                    chunk_id=chunk_id,
                    text=chunk,
                    filename=file_path.name,
                    page=page_num,
                )
                stats["chunks_added"] += 1

    elif file_path.suffix.lower() in [".txt", ".md"]:
        text = extract_text_file(file_path)
        stats["pages"] = 1

        chunks = chunk_text(
            text,
            chunk_size=Config.RAG_CHUNK_SIZE,
            overlap=Config.RAG_CHUNK_OVERLAP,
        )

        for chunk_num, chunk in enumerate(chunks):
            chunk_id = create_chunk_id(file_path.name, 1, chunk_num)
            await rag_system.add_chunk(
                chunk_id=chunk_id,
                text=chunk,
                filename=file_path.name,
                page=1,
            )
            stats["chunks_added"] += 1

    logger.info(f"Ingested {file_path.name}: {stats['chunks_added']} chunks")
    return stats


async def reindex_all_documents() -> dict:
    """Rebuild index from all documents in data/docs/."""
    rag_system = get_rag_system()
    rag_system.clear()

    if not Config.DOCS_DIR.exists():
        logger.warning(f"Docs directory not found: {Config.DOCS_DIR}")
        return {"total_files": 0, "total_chunks": 0}

    all_stats = {"total_files": 0, "total_chunks": 0}
    supported_extensions = {".pdf", ".txt", ".md"}

    for file_path in Config.DOCS_DIR.iterdir():
        if file_path.is_file() and file_path.suffix.lower() in supported_extensions:
            try:
                stats = await ingest_document(file_path)
                all_stats["total_files"] += 1
                all_stats["total_chunks"] += stats["chunks_added"]
                logger.info(f"Added {stats['chunks_added']} chunks from {file_path.name}")
            except Exception as e:
                logger.error(f"Failed to ingest {file_path.name}: {e}")

    logger.info(
        f"Reindexed complete: {all_stats['total_files']} files, "
        f"{all_stats['total_chunks']} total chunks"
    )
    return all_stats
