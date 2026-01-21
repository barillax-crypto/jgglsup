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
    LANGUAGE_PROMPT_EN,
    LANGUAGE_PROMPT_RU,
    SYSTEM_PROMPT_EN,
    SYSTEM_PROMPT_RU,
    ESCALATION_TEMPLATE_EN,
    ESCALATION_TEMPLATE_RU,
    SOURCES_REFUSAL_EN,
    SOURCES_REFUSAL_RU,
    SENSITIVE_REFUSAL_EN,
    SENSITIVE_REFUSAL_RU,
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

    if user and user["language"]:
        # User already set language
        await message.answer("You're already set up! Ask me anything about KYC and onboarding.")
    else:
        # Ask for language
        await message.answer(LANGUAGE_PROMPT_EN)


@router.message(Command("help"))
async def cmd_help(message: Message) -> None:
    """Handle /help command."""
    db = get_db()
    user = db.get_user(message.from_user.id)

    if user and user["language"] == "ru":
        help_text = (
            "Я помогаю с вопросами о регистрации на крипто-бирже в США и KYC.\n\n"
            "Просто задайте вопрос, и я постараюсь ответить на основе предоставленных материалов.\n"
            "Если я не уверен, я передам вас в поддержку.\n\n"
            "/reset — изменить язык"
        )
    else:
        help_text = (
            "I help with questions about US crypto exchange onboarding and KYC.\n\n"
            "Just ask a question and I'll try to answer based on the provided materials.\n"
            "If I'm not sure, I'll escalate to support.\n\n"
            "/reset — change language"
        )

    await message.answer(help_text)


@router.message(Command("reset"))
async def cmd_reset(message: Message) -> None:
    """Handle /reset command to change language."""
    db = get_db()
    db.set_user_language(message.from_user.id, "")
    await message.answer(LANGUAGE_PROMPT_EN)


@router.message(Command("upload_doc"))
async def cmd_upload_doc(message: Message) -> None:
    """Handle /upload_doc command (admin only, private chat)."""
    if not is_admin(message.from_user.id) or not is_private_chat(message):
        await message.answer(
            "This command is not available.\n"
            "Supported formats: .pdf, .txt, .md"
        )


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
        await message.answer(f"Unsupported file type. Supported: {', '.join(supported)}")
        return

    try:
        await message.answer(f"Processing {file_name}...")

        # Download file
        file_info = await message.bot.get_file(message.document.file_id)
        file_path = Config.DOCS_DIR / file_name
        await message.bot.download_file(file_info.file_path, destination=str(file_path))

        logger.info(f"Downloaded document: {file_name}")

        # Ingest
        stats = await ingest_document(file_path)
        await message.answer(
            f"✅ Document ingested!\n\n"
            f"File: {file_name}\n"
            f"Chunks added: {stats['chunks_added']}\n"
            f"Pages: {stats['pages']}"
        )
        logger.info(f"Ingested {file_name}: {stats['chunks_added']} chunks from {stats['pages']} pages")

    except Exception as e:
        logger.error(f"Failed to process document: {e}")
        await message.answer(f"❌ Error processing document: {e}")


@router.message(F.text)
async def handle_message(message: Message) -> None:
    """Handle text messages."""
    user_id = message.from_user.id
    user_text = message.text.strip()
    db = get_db()
    user = db.get_user(user_id)

    # Handle language selection
    if not user or not user["language"]:
        if user_text.upper() in ["EN", "RU"]:
            language = "en" if user_text.upper() == "EN" else "ru"
            db.set_user_language(user_id, language)

            if language == "ru":
                await message.answer(
                    "Спасибо! Теперь я готов ответить на ваши вопросы о KYC и регистрации на бирже."
                )
            else:
                await message.answer(
                    "Thanks! Now I'm ready to answer your questions about KYC and exchange onboarding."
                )
        else:
            await message.answer(LANGUAGE_PROMPT_EN)
        return

    language = user["language"]
    is_russian = language == "ru"

    # Check for sensitive/banned topics
    if is_sensitive_topic(user_text):
        logger.warning(f"Sensitive topic detected from user {user_id}: {user_text[:50]}")
        refusal = SENSITIVE_REFUSAL_RU if is_russian else SENSITIVE_REFUSAL_EN
        await message.answer(refusal)
        db.log_interaction(user_id, user_text, "refused", internal_sources="sensitive_topic")
        return

    # Check for source/document requests
    if is_source_request(user_text):
        logger.info(f"Source request from user {user_id}: {user_text[:50]}")
        refusal = SOURCES_REFUSAL_RU if is_russian else SOURCES_REFUSAL_EN
        await message.answer(refusal)
        db.log_interaction(user_id, user_text, "refused", internal_sources="source_request")
        return

    # Get system prompt and templates
    system_prompt = SYSTEM_PROMPT_RU if is_russian else SYSTEM_PROMPT_EN
    escalation_template = ESCALATION_TEMPLATE_RU if is_russian else ESCALATION_TEMPLATE_EN

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
        await message.answer(escalation_template)
        db.log_interaction(user_id, user_text, "escalated", internal_sources="retrieval_error")
        return

    # Check if we have relevant chunks
    if not retrieved_chunks:
        logger.info(f"No chunks retrieved for user {user_id}: {user_text}")
        await message.answer(escalation_template)
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
            {"role": "system", "content": system_prompt},
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
        await message.answer(escalation_template)
        db.log_interaction(
            user_id,
            user_text,
            "escalated",
            internal_sources="llm_error",
        )


@router.message()
async def handle_unknown(message: Message) -> None:
    """Handle unknown message types."""
    db = get_db()
    user = db.get_user(message.from_user.id)

    if user and user["language"] == "ru":
        await message.answer("Я понимаю только текстовые сообщения. Пожалуйста, напишите вопрос.")
    else:
        await message.answer("I understand text messages only. Please type your question.")
