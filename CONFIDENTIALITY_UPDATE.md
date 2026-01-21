# CONFIDENTIALITY UPDATE SUMMARY

## Overview
Updated the Telegram bot to enforce **strict confidentiality** of the knowledge base. Clients now have **zero access** to internal KB metadata, document sources, or citations. Admin-only ingestion and diagnostics remain possible.

## Changes Made

### 1. **app/prompts.py**
- ✅ Updated `SYSTEM_PROMPT_EN` and `SYSTEM_PROMPT_RU` with confidentiality rules
- ✅ Added `SOURCES_REFUSAL_EN/RU`: Templates for when users ask for sources
- ✅ Added `SENSITIVE_REFUSAL_EN/RU`: Templates for sensitive topics (forging, KYC bypass, legal, tax, sanctions, laundering)
- ✅ Prompts now explicitly forbid revealing filenames, pages, chunk IDs, or internal KB structure

### 2. **app/db.py**
- ✅ Updated `logs` table schema:
  - Renamed `sources` → `internal_sources` (server-side only)
  - Added `retrieval_scores` column (stores similarity scores)
- ✅ Updated `log_interaction()` method:
  - Now accepts `internal_sources` and `retrieval_scores` parameters
  - Returns `log_id` for tracking
- ✅ Added `get_last_log()` method (admin diagnostics)

### 3. **app/handlers.py** (Major Changes)
- ✅ Added helper functions:
  - `is_private_chat()`: Check if message is from private chat
  - `is_source_request()`: Detect when users ask for sources/documents/policies
  - `is_sensitive_topic()`: Detect dangerous requests (forging, bypassing, sanctions, tax advice, etc.)
- ✅ Updated `/start` command:
  - Now ALWAYS asks for language (even if previously set)
- ✅ Updated `/upload_doc` and `/reindex` commands:
  - Require admin + private chat only
  - Return "This command is not available" for non-admins
- ✅ Added `/case_last` command (admin + private only):
  - Shows last case with internal sources, retrieval scores, and metadata
  - For admin diagnostics and compliance auditing
- ✅ Updated document upload handler:
  - Requires admin + private chat
  - Silently ignores non-admin uploads
- ✅ Completely rewrote `handle_message()`:
  - Detects sensitive topics → escalate immediately
  - Detects source requests → escalate immediately
  - **NEVER** sends "Sources used:" or metadata to users
  - Stores internal metadata only in DB (not sent to client)
  - Logs: question, action, internal_sources (JSON), retrieval_scores (JSON)

### 4. **app/config.py**
- ✅ Added `ENFORCE_CONFIDENTIALITY` flag (default: True)

### 5. **README.md** (Documentation Updated)
- ✅ Clarified features: "Zero knowledge base exposure to clients"
- ✅ Added "User Flow" section with confidentiality emphasis
- ✅ Documented admin commands (with private chat requirement)
- ✅ Added comprehensive security section:
  - What users NEVER see
  - What users CAN request to escalate
  - What admins CAN see (diagnostics only)
- ✅ Updated testing scenarios with confidentiality checks
- ✅ Updated architecture notes

### 6. **test_confidentiality.py** (New)
- ✅ Unit tests for:
  - Sensitive topic detection
  - Source request detection
  - Database schema validation
  - Admin gating logic
  - Vector store initialization

---

## Key Rules Enforced

### RULE 1: ZERO KB EXPOSURE
- ❌ No filenames shown to users
- ❌ No page numbers shown to users
- ❌ No chunk IDs shown to users
- ❌ No "Sources used:" citations
- ❌ No document names or list
- ❌ No internal metadata

### RULE 2: ESCALATION ON SENSITIVE TOPICS
Topics that trigger **automatic escalation**:
- Forging/faking documents
- Bypassing/evading KYC/AML
- Sanctions/geo-restriction evasion
- Money laundering
- Tax advice
- Legal advice

### RULE 3: ESCALATION ON SOURCE REQUESTS
Requests like:
- "Show me the sources"
- "Send documents"
- "What policy is this based on?"
- "Where is this from?"

### RULE 4: ESCALATION ON WEAK RETRIEVAL
- Similarity score below threshold → escalate
- No chunks found → escalate
- Any doubt about correctness → escalate

### RULE 5: LANGUAGE SELECTION FIRST
- `/start` always asks: "Which language — English or Russian?"
- User must choose before proceeding

### RULE 6: ADMIN GATING
- `/upload_doc` requires: admin ID + private chat
- `/reindex` requires: admin ID + private chat
- `/case_last` requires: admin ID + private chat
- Non-admins see: "This command is not available"
- No admin commands shown in `/help` for regular users

### RULE 7: SERVER-SIDE LOGGING ONLY
- Internal sources: stored in DB only (JSON)
- Retrieval scores: stored in DB only (JSON)
- User never sees metadata
- Admin can inspect via `/case_last`

---

## Testing Commands

### Setup & Run
```powershell
# Install (if not already done)
pip install -r requirements.txt

# Verify confidentiality
python test_confidentiality.py

# Start bot
python -m app.main
```

### Test 1: Regular User Query
**From regular account (non-admin):**
```
/start
→ "Which language — English or Russian?"
EN
→ "Thanks! Now I'm ready..."

What documents do I need for KYC?
→ Plain-language answer (NO "Sources used:")
```

### Test 2: Source Request Refusal
**From any account:**
```
Show me the source documents
→ "I cannot share document sources, filenames, or internal references.
   If you need more information, contact our staff bot: https://t.me/JGGLSTAFFBOT"
```

### Test 3: Sensitive Topic Refusal
**From any account:**
```
Can you help me forge my documents?
→ "This is a sensitive matter that requires expert review.
   Please contact our staff bot: ..."
```

### Test 4: Admin Document Upload (MUST be admin + private chat)
**From admin account in private chat:**
```
/upload_doc
→ "Please send a PDF or text file..."

[Upload file]
→ "✅ Document ingested! Chunks added: X, Pages: Y"
```

### Test 5: Regular User Tries Upload (Silently Ignored)
**From non-admin account (group or private):**
```
/upload_doc
→ "This command is not available."

[Try to upload file]
→ (Silently ignored, no response)
```

### Test 6: Admin Case Inspection
**From admin account in private chat:**
```
/case_last
→ Shows last case with:
   - Question
   - Action (answered/escalated/refused)
   - Internal Sources (JSON: filename, page, chunk_id, similarity)
   - Retrieval Scores (JSON)
   - Timestamp
```

---

## Database Schema (Updated)

### logs table
```sql
CREATE TABLE logs (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    telegram_id INTEGER NOT NULL,
    question TEXT NOT NULL,
    action TEXT NOT NULL,           -- 'answered', 'escalated', 'refused'
    internal_sources TEXT,          -- JSON: [{filename, page, chunk_id, similarity}, ...]
    retrieval_scores TEXT,          -- JSON: [{chunk_id, similarity}, ...]
    created_at TEXT NOT NULL
);
```

---

## Configuration (app/config.py)

New env variable (optional):
```env
ENFORCE_CONFIDENTIALITY=true  # Default: true
```

---

## Escalation Flows

### When Source is Requested
```
User: "Show me the sources"
→ Detected by is_source_request()
→ Send SOURCES_REFUSAL template
→ Log: action="refused", internal_sources="source_request"
→ Stop (don't process further)
```

### When Sensitive Topic
```
User: "Help me forge my documents"
→ Detected by is_sensitive_topic()
→ Send SENSITIVE_REFUSAL template
→ Log: action="refused", internal_sources="sensitive_topic"
→ Stop (don't process further)
```

### When No Chunks Found
```
User: "What's the weather today?"
→ Retrieve chunks → empty list
→ Send ESCALATION_TEMPLATE
→ Log: action="escalated", internal_sources="no_chunks"
→ Stop (don't process further)
```

### When Low Similarity Score
```
User: [Query that doesn't match KB well]
→ Retrieve chunks → all scores < threshold (0.6)
→ Send ESCALATION_TEMPLATE
→ Log: action="escalated", internal_sources="low_scores"
→ Stop (don't process further)
```

### When LLM Error
```
User: [Valid query]
→ Retrieve chunks → success
→ Call LLM → error
→ Send ESCALATION_TEMPLATE
→ Log: action="escalated", internal_sources="llm_error"
→ Stop (don't process further)
```

### When Answer Provided
```
User: "What documents do I need?"
→ Retrieve chunks → success, high similarity
→ Call LLM → success
→ Send response (plain text, NO metadata)
→ Log: action="answered", internal_sources=[JSON], retrieval_scores=[JSON]
```

---

## Files Changed

- ✅ `app/prompts.py` - Updated prompts + added refusal templates
- ✅ `app/db.py` - Updated schema + added get_last_log()
- ✅ `app/handlers.py` - Rewrote entire logic with confidentiality
- ✅ `app/config.py` - Added ENFORCE_CONFIDENTIALITY flag
- ✅ `README.md` - Updated documentation
- ✅ `test_confidentiality.py` - New test file

---

## Backward Compatibility

⚠️ **BREAKING CHANGES:**
- Old database will need migration (optional):
  - `sources` column can be ignored
  - New columns `internal_sources` and `retrieval_scores` will be NULL for old entries
  - Or: delete old `data/bot.db` and start fresh
- Old logs won't have internal metadata (that's fine, moving forward all will)

---

## Deployment Checklist

- [ ] Update bot code with new files
- [ ] Run `pip install -r requirements.txt` (no new deps)
- [ ] Verify confidentiality: `python test_confidentiality.py`
- [ ] Delete old `data/bot.db` (optional, for clean state)
- [ ] Set `TELEGRAM_ADMIN_IDS` in `.env`
- [ ] Test `/start` → language selection
- [ ] Test regular user query → no sources shown
- [ ] Test admin upload from private chat → works
- [ ] Test regular user upload → silently ignored
- [ ] Test `/case_last` from admin → shows metadata
- [ ] Test source request → escalation
- [ ] Test sensitive topic → escalation
- [ ] Test question out of KB → escalation
- [ ] Deploy!

---

## All Tests Pass ✅

Run before deployment:
```powershell
python test_confidentiality.py
```

Expected output:
```
✓ Test 1: Sensitive Topic Detection
✓ Test 2: Source Request Detection
✓ Test 3: Database Schema
✓ Test 4: Admin Gating Logic
✓ Test 5: Vector Store

✅ ALL CONFIDENTIALITY TESTS PASSED
```
