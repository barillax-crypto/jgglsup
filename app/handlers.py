"""Telegram bot message handlers."""

import json
import logging
from typing import Optional

from aiogram import F, Router
from aiogram.filters import Command
from aiogram.types import Message

from app.config import Config
from app.db import get_db
from app.ingest import ingest_document
from app.openrouter import get_openrouter_client
from app.prompts import (
    SYSTEM_PROMPT,
    ESCALATION_TEMPLATE,
    SOURCES_REFUSAL,
    SENSITIVE_REFUSAL,
)
from app.rag import get_rag_system

logger = logging.getLogger(__name__)

router = Router()


def is_admin(user_id: int) -> bool:
    """Check if user is admin."""
    return user_id in Config.TELEGRAM_ADMIN_IDS


def is_private_chat(message: Message) -> bool:
    """Check if message is from private chat."""
    return message.chat.type == "private"


def is_source_request(text: str) -> bool:
    """Detect if user is asking for sources or documents."""
    # Always ask for language, even if set (to reset)
    keywords = [
        "sources", "references", "links", "documentation", "docs",
        "where did you get", "source", "cite", "citation",
    ]
    text_lower = text.lower()
    return any(keyword in text_lower for keyword in keywords)


def is_sensitive_topic(text: str) -> bool:
    """Detect if user is asking about sensitive topics."""
    keywords = [
        "forging", "forge", "fake", "faking", "fake doc", "fake identity",
        "evading", "evade", "sanctions", "bypass", "bypassing", "circumvent",
        "laundering", "money launder", "aml", "kyc bypass", "skip kyc",
        "tax", "legal advice", "lawyer", "attorney", "law", "crypto law",
        "illegal", "legality", "legal question", "is it legal"
    ]
    text_lower = text.lower()
    return any(keyword in text_lower for keyword in keywords)


@router.message(Command("start"))
async def cmd_start(message: Message) -> None:
    """Handle /start command."""
    user_id = message.from_user.id
    db = get_db()
    user = db.get_user(user_id)

    if not user:
        # Create new user
        db.set_user_language(user_id, "en")

    await message.answer("Hi! My name is Jiggley. I'm an artificial intelligence assistant that will help you set everything up.")
    await message.answer("To get started, tell me: What exchange are you on? What step are you stuck on? Include an error message or screenshot if possible.")


@router.message(Command("help"))
async def cmd_help(message: Message) -> None:
    """Handle /help command."""
    help_text = (
        "I help with questions about US crypto exchange onboarding and KYC.\n\n"
        "Just ask a question and I'll try to answer based on the provided materials.\n"
        "If I'm not sure, I'll escalate to support.\n\n"
        "/upload_doc — Upload a document (admin only)\n"
        "/reindex — Reindex all documents (admin only)"
    )
    await message.answer(help_text)



@router.message(Command("upload_doc"))
async def cmd_upload_doc(message: Message) -> None:
    """Handle /upload_doc command (admin only, private chat)."""
    if not is_admin(message.from_user.id) or not is_private_chat(message):
        await message.answer("This command is not available.")
        return
    
    await message.answer("Send a PDF or TXT file.")


@router.message(Command("reindex"))
async def cmd_reindex(message: Message) -> None:
    """Handle /reindex command (admin only, private chat)."""
    if not is_admin(message.from_user.id) or not is_private_chat(message):
        await message.answer("This command is not available.")
        return

    await message.answer("Reindexing all documents... This may take a moment.")

    try:
        from app.ingest import reindex_all_documents

        stats = await reindex_all_documents()
        await message.answer(
            f"✅ Reindexing complete!\n\n"
            f"Files: {stats['total_files']}\n"
            f"Chunks: {stats['total_chunks']}"
        )
    except Exception as e:
        logger.error(f"Reindex failed: {e}")
        await message.answer(f"❌ Reindex failed: {e}")


@router.message(Command("case_last"))
async def cmd_case_last(message: Message) -> None:
    """Handle /case_last command (admin only, private chat). Show last case with internal sources."""
    if not is_admin(message.from_user.id) or not is_private_chat(message):
        await message.answer("This command is not available.")
        return

    db = get_db()
    # Get the admin's own user ID (message sender)
    log_entry = db.get_last_log(message.from_user.id)

    if not log_entry:
        await message.answer("No cases found.")
        return

    case_text = f"""📋 Last Case (Admin View)

**Question:** {log_entry['question']}
**Action:** {log_entry['action']}
**Time:** {log_entry['created_at']}

**Internal Sources:**
{log_entry['internal_sources'] or 'None'}

**Retrieval Scores:**
{log_entry['retrieval_scores'] or 'N/A'}
"""
    await message.answer(case_text, parse_mode="Markdown")


@router.message(F.document)
async def handle_document(message: Message) -> None:
    """Handle document uploads (admin only, private chat)."""
    if not is_admin(message.from_user.id) or not is_private_chat(message):
        return  # Silently ignore non-admin doc uploads

    if not message.document:
        await message.answer("No document found.")
        return

    file_name = message.document.file_name
    if not file_name:
        await message.answer("Document has no filename.")
        return

    supported = {".pdf", ".txt", ".md"}
    if not any(file_name.endswith(ext) for ext in supported):
        await message.answer("Unsupported file type.")
        return

    try:
        # Download file
        file_info = await message.bot.get_file(message.document.file_id)
        file_path = Config.DOCS_DIR / file_name
        await message.bot.download_file(file_info.file_path, destination=str(file_path))

        logger.info(f"Downloaded document: {file_name}")

        # Ingest
        stats = await ingest_document(file_path)
        
        # Return confidential response - no file details, chunks, or pages exposed
        await message.answer("Document uploaded and indexed successfully.")
        logger.info(f"Ingested {file_name}: {stats['chunks_added']} chunks from {stats['pages']} pages")

    except Exception as e:
        logger.error(f"Failed to process document: {e}")
        await message.answer(
            "Upload failed. Please contact staff bot: https://t.me/JGGLSTAFFBOT"
        )


@router.message(F.text)
async def handle_message(message: Message) -> None:
    """Handle text messages."""
    user_id = message.from_user.id
    user_text = message.text.strip()
    db = get_db()
    user = db.get_user(user_id)

    # Create user if not exists
    if not user:
        db.set_user_language(user_id, "en")

    # Check for sensitive/banned topics
    if is_sensitive_topic(user_text):
        logger.warning(f"Sensitive topic detected from user {user_id}: {user_text[:50]}")
        await message.answer(SENSITIVE_REFUSAL)
        db.log_interaction(user_id, user_text, "refused", internal_sources="sensitive_topic")
        return

    # Check for source/document requests
    if is_source_request(user_text):
        logger.info(f"Source request from user {user_id}: {user_text[:50]}")
        await message.answer(SOURCES_REFUSAL)
        db.log_interaction(user_id, user_text, "refused", internal_sources="source_request")
        return

    # Retrieve relevant chunks
    rag_system = get_rag_system()
    try:
        retrieved_chunks = await rag_system.retrieve(
            query=user_text,
            top_k=Config.RAG_TOP_K,
            threshold=Config.RAG_SIMILARITY_THRESHOLD,
        )
    except Exception as e:
        logger.error(f"RAG retrieval failed: {e}")
        await message.answer(ESCALATION_TEMPLATE)
        db.log_interaction(user_id, user_text, "escalated", internal_sources="retrieval_error")
        return

    # Check if we have relevant chunks
    if not retrieved_chunks:
        logger.info(f"No chunks retrieved for user {user_id}: {user_text}")
        await message.answer(ESCALATION_TEMPLATE)
        db.log_interaction(user_id, user_text, "escalated", internal_sources="no_chunks")
        return

    # Build context from retrieved chunks (internal only, NOT for user)
    context = "\n\n".join(
        [
            f"[{chunk['metadata']['filename']}:p{chunk['metadata']['page']}]\n{chunk['text']}"
            for chunk in retrieved_chunks
        ]
    )

    # Store internal metadata for logging (NOT sent to user)
    internal_sources = json.dumps([
        {
            "filename": chunk['metadata']['filename'],
            "page": chunk['metadata']['page'],
            "chunk_id": chunk['metadata']['chunk_id'],
            "similarity": chunk['similarity'],
        }
        for chunk in retrieved_chunks
    ])

    retrieval_scores = json.dumps([
        {
            "chunk_id": chunk['metadata']['chunk_id'],
            "similarity": round(chunk['similarity'], 3),
        }
        for chunk in retrieved_chunks
    ])

    # Call LLM
    or_client = get_openrouter_client()
    try:
        messages = [
            {"role": "system", "content": SYSTEM_PROMPT},
            {
                "role": "user",
                "content": f"Context from knowledge base:\n\n{context}\n\n---\n\nUser question: {user_text}",
            },
        ]

        response = await or_client.chat(
            messages=messages,
            temperature=0.5,
            max_tokens=500,
        )

        # Send response WITHOUT sources/metadata to user
        await message.answer(response)

        # Log interaction with internal metadata (server-side only)
        db.log_interaction(
            user_id,
            user_text,
            "answered",
            internal_sources=internal_sources,
            retrieval_scores=retrieval_scores,
        )
        logger.info(f"Answered user {user_id}: {user_text[:50]}...")

    except Exception as e:
        logger.error(f"LLM call failed: {e}")
        await message.answer(ESCALATION_TEMPLATE)
        db.log_interaction(
            user_id,
            user_text,
            "escalated",
            internal_sources="llm_error",
        )


@router.message()
async def handle_unknown(message: Message) -> None:
    """Handle unknown message types."""
    await message.answer("I understand text messages only. Please type your question.")
