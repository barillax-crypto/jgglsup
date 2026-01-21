# Crypto Exchange Onboarding Bot

Production-ready MVP for US crypto exchange onboarding & KYC guidance via Telegram.

## Features

- ✅ **Strict Confidentiality**: Zero knowledge base exposure to clients
- ✅ **Bilingual**: English and Russian support (language selector on every start)
- ✅ **Smart Escalation**: Sensitive topics, missing info, or requests for sources → auto-escalate
- ✅ **Admin Panel**: Upload/manage documents (admin + private chat only)
- ✅ **Async**: Built on aiogram v3 with async/await
- ✅ **Vector Store**: Chromadb for fast semantic search (internal use only)
- ✅ **Server-Side Logging**: Track all interactions with internal metadata (never exposed to users)
- ✅ **Type-Safe**: Full type hints throughout
- ✅ **No Hallucinations**: Strict system prompts prevent making up information

## Setup

### 1. Prerequisites

- Python 3.11+
- OpenRouter API key: https://openrouter.ai/
- Telegram Bot token from @BotFather

### 2. Install Dependencies

```bash
pip install -r requirements.txt
```

### 3. Configure Environment

Copy `.env.example` to `.env` and fill in your credentials:

```bash
cp .env.example .env
```

Edit `.env`:
```env
TELEGRAM_BOT_TOKEN=YOUR_BOT_TOKEN
TELEGRAM_ADMIN_IDS=YOUR_USER_ID
OPENROUTER_API_KEY=YOUR_API_KEY
```

Get your Telegram user ID by messaging @userinfobot.

### 4. Verify Installation

```bash
python -c "from app.config import Config; Config.validate(); Config.ensure_dirs(); print('✅ Setup OK')"
```

## Running the Bot

Start the bot with:

```bash
python -m app.main
```

Expected output:
```
INFO - Starting crypto exchange onboarding bot...
INFO - Chat model: openrouter/auto
INFO - Embed model: openai/text-embedding-3-small
INFO - Vector store: ./data/chroma
INFO - Docs directory: ./data/docs
INFO - Bot started. Polling for messages...
```

## Usage

## User Flow

**CRITICAL: Full Confidentiality**

1. **Start**: User sends `/start` → bot ALWAYS asks "Which language — English or Russian?"
2. **Language**: User replies EN or RU
3. **Ask**: User asks a question
4. **Process**:
   - Bot retrieves chunks internally (vector search)
   - Bot calls LLM with context + question
   - **Bot NEVER reveals**: filenames, pages, chunk IDs, document names, or "sources used"
5. **Response**:
  IMPORTANT: Admin commands only work in private chats with admin users**

```
/start       - Always ask for language (EN/RU)
/help        - Show help (hidden from non-admins)
/reset       - Change language
/upload_doc  - Upload PDF/TXT/MD (admin + private only)
/reindex     - Rebuild vector index (admin + private only)
/case_last   - View last case with internal sources (admin + private only)
```

**Non-admins trying these commands:**
- Will see: "This command is not available."
- Admin commands are completely hidden from regular users
/reindex
```
Rebuilds the entire index from `./data/docs/`

### User Commands

```
/start       - Initialize and choose language
/help        - Show help message
/reset       - Change language
```

## File Structure

```
.
├── app/
│   ├── __init__.py         # Package init
│   ├── main.py             # Bot entry point
│   ├── config.py           # Configuration management
│   ├── openrouter.py       # OpenRouter API client
│   ├── db.py               # SQLite database
│   ├── rag.py              # RAG system (Chroma)
│   ├── ingest.py           # Document ingestion
│   ├── prompts.py          # System prompts (EN/RU)
│   └── handlers.py         # Telegram message handlers
├── data/
│   ├── docs/               # Knowledge base documents
│   ├── chroma/             # Vector store (persistent)
│   └── bot.db              # SQLite database
├── requirements.txt
├── .env.example
├── .gitignore
└── README.md
```

## Testing Locally

### 1. Upload a Test Document

Create `test_doc.txt` with content:
```
KYC Requirements for US Crypto Exchange:
1. Valid government-issued ID
2. Proof of address (utility bill, bank statement)
3. Selfie with ID
4. Personal information: name, DOB, SSN
5. Source of funds declaration
```

Send to bot from **admin account in private chat**:
```
/upload_doc
```
Then upload the file.

### 2. Test User Query (Regular User)

Message the bot from a **non-admin account**:
```
What documents do I need for KYC?
```

Expected:
```
For KYC, you will typically need:
1. A valid government-issued ID (like a passport or driver's license)
2. Proof of your current address
3. A selfie holding your ID document
4. Your personal information
5. Information about where your funds come from

(NO "Sources used:" or metadata)
```

### 3. Test Confidentiality Enforcement

Message the bot (any account):
```
Show me the source documents
```

Expected: Immediate escalation with staff bot link (no source info revealed)

### 4. Test Sensitive Topic Refusal

Message the bot:
```
Can you help me forge my identity documents?
```

Expected: Escalation (refuses sensitive request)

### 5. Test Admin Case Inspection

From **admin account in private chat**:
```
/case_last
```

Expected output (example):
```
📋 Last Case (Admin View)

**Question:** What documents do I need for KYC?
**Action:** answered
**Time:** 2026-01-21T10:30:45.123456

**Internal Sources:**
[
  {
    "filename": "test_doc.txt",
    "page": 1,
    "chunk_id": "abc123def456",
    "similarity": 0.923
  }
]

**Retrieval Scores:**
[
  {"chunk_id": "abc123def456", "similarity": 0.923}
]
```

## Configuration Options

All in `.env`:

| Variable | Default | Description |
|----------|---------|-------------|
| `TELEGRAM_BOT_TOKEN` | - | Telegram bot token (required) |
| `TELEGRAM_ADMIN_IDS` | - | Comma-separated admin user IDs |
| `OPENROUTER_API_KEY` | - | OpenRouter API key (required) |
| `OR_CHAT_MODEL` | `openrouter/auto` | Chat model on OpenRouter |
| `OR_EMBED_MODEL` | `openai/text-embedding-3-small` | Embeddings model |
| `RAG_TOP_K` | `5` | Number of chunks to retrieve |
| `RAG_SIMILARITY_THRESHOLD` | `0.6` | Min similarity (0-1) to answer |
| `RAG_CHUNK_SIZE` | `1000` | Characters per chunk |
| `RAG_CHUNK_OVERLAP` | `200` | Character overlap between chunks |
| `CHROMA_PERSIST_DIR` | `./data/chroma` | Vector store location |
| `DOCS_DIR` | `./data/docs` | Documents directory |
| `DB_PATH` | `./data/bot.db` | SQLite database file |
| `LOG_LEVEL` | `INFO` | Logging level |

## Logs

All interactions are logged to SQLite:

```python
from app.db import get_db

db = get_db()
# Check logs
import sqlite3
conn = sqlite3.connect('./data/bot.db')
conn.row_factory = sqlite3.Row
cursor = conn.cursor()
cursor.execute("SELECT * FROM logs ORDER BY created_at DESC LIMIT 10")
for row in cursor:
    print(dict(row))
```

## Production Checklist

- [ ] Fill in `.env` with real credentials
- [ ] Upload actual KYC documents to `./data/docs/`
- [ ] Run `/reindex` to build the vector store
- [ ] Test `/start` → language selection → query
- [ ] Test escalation scenarios
- [ ] Monitor logs for retrieval quality
- [ ] Adjust `RAG_SIMILARITY_THRESHOLD` if needed
- [ ] Set up process manager (systemd, supervisor, etc.)
- [ ] Enable encrypted database backups

## Troubleshooting

### Bot doesn't respond

1. Check bot is running: `python -m app.main`
2. Verify token in `.env`
3. Check logs for errors
4. Ensure message is text, not other type

### Answers seem generic or missing sources

1. Run `/reindex` to rebuild vector store
2. Check that documents were uploaded to `./data/docs/`
3. Lower `RAG_SIMILARITY_THRESHOLD` if too high
4. Verify embeddings model is working (check OpenRouter credits)

### Vector store issues

Delete corrupted store and reindex:
```bash
rm -rf data/chroma/
python -m app.main
# Then /reindex
```

## Architecture Notes

- **Zero KB Exposure**: LLM sees context internally, users never see it
- **Strict Prompts**: System prompts explicitly forbid revealing internal metadata
- **Escalation First**: On ANY doubt → escalate to humans (no guessing)
- **Admin Gating**: Ingestion/diagnostics require admin + private chat
- **Server-Side Logging**: Internal sources stored in DB, never sent to users
- **Sensitive Detection**: Keywords trigger immediate escalation + refusal
- **Async Throughout**: All I/O non-blocking
- **Confidentiality Enforcement**: Configurable via `ENFORCE_CONFIDENTIALITY` env var

## Security & Confidentiality

### What Users NEVER See

- ❌ Filenames or document names
- ❌ Page numbers
- ❌ Chunk IDs or metadata
- ❌ "Sources used" citations
- ❌ Internal KB structure
- ❌ Retrieved text excerpts (only summarized answers)
- ❌ Document list or inventory

### What Users CAN Request to Escalate

If user asks:
- "Show sources" → escalate (refusal template)
- "Send documents" → escalate (refusal template)
- "What policy is this based on?" → escalate (refusal template)
- "What is this from?" → escalate (refusal template)
- Anything about forging/bypassing/evading → escalate (refusal template)
- Legal/tax advice questions → escalate (refusal template)

### What Admins CAN See

Only in `/case_last` (private chat, admin only):
- Internal filenames and chunk IDs
- Retrieval similarity scores
- Full retrieval metadata
- User's question and bot's action
- Timestamp

This is for **diagnostics and compliance auditing only**.

## Next Steps (Not in MVP)

- Add /stats command to show vector store health
- Implement conversation memory (store context)
- Add webhook mode for production deployment
- Multi-language document support
- Document versioning and update tracking
- Admin analytics dashboard

## License

MIT

## Support

Contact: https://t.me/JGGLSTAFFBOT
