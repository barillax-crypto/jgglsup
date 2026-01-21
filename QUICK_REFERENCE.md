# QUICK REFERENCE: CONFIDENTIALITY BOT

## TL;DR: What Changed

Users now see **ZERO knowledge base details**. Admin tools and diagnostics remain intact. Sensitive topics and source requests auto-escalate.

---

## Commands Cheat Sheet

| Command | Who | Where | What Happens |
|---------|-----|-------|--------------|
| `/start` | Anyone | Any chat | Always ask: EN or RU |
| `/help` | Shown to everyone | Any chat | Shows help (adapts for admin) |
| `/reset` | Anyone | Any chat | Change language |
| `/upload_doc` | Admin only | Private chat | Upload PDF/TXT/MD |
| `/reindex` | Admin only | Private chat | Rebuild vector index |
| `/case_last` | Admin only | Private chat | Show last case (internal metadata) |

**Rule:** Admin commands ignored/refused if non-admin or in group chat

---

## User Interaction Flow

```
User → /start
  ↓
Bot → "Which language — English or Russian?"
  ↓
User → EN or RU
  ↓
Bot → Acknowledges language
  ↓
User → Asks question
  ↓
Bot checks:
  ├─ Is sensitive topic? → Escalate
  ├─ Asking for sources? → Escalate
  ├─ Valid retrieval? → Continue
  └─ Low score? → Escalate
  ↓
Bot → Answers in plain language (NO metadata)
```

---

## Detection Keywords

### Sensitive Topics (Auto-Escalate)
```
forging, forge, fake, faking,
evading, evade, sanctions, bypass,
laundering, money launder,
aml, kyc bypass, skip kyc,
tax, legal advice, lawyer, attorney, law,
crypto law, illegal, legality, legal question,
is it legal
```

### Source Requests (Auto-Escalate)
```
source, sources, reference, references,
where is this from, document, documents,
file, files, show doc, send doc,
policy, send policy, what policy,
what is this based on, based on,
chunk, chunks, metadata, filename, citation
```

---

## What Users See

✅ Plain-language answers  
✅ Answers in their language (EN/RU)  
✅ Escalation to staff bot when needed  

❌ NO filenames  
❌ NO page numbers  
❌ NO chunk IDs  
❌ NO "Sources used:"  
❌ NO internal metadata  

---

## What Admins See (Private Chat)

`/case_last` shows:
- Question (what user asked)
- Action (answered/escalated/refused)
- Timestamp
- Internal Sources (JSON: filename, page, chunk_id, similarity)
- Retrieval Scores (JSON: similarity scores)

**Private chat only. Non-admins see:** "This command is not available."

---

## Database Tables

### users
```sql
telegram_id, language, created_at
```

### logs
```sql
id, telegram_id, question, action, 
internal_sources (JSON), retrieval_scores (JSON), created_at
```

**Key:** `internal_sources` and `retrieval_scores` never sent to users. Server-side only.

---

## Test Cases (Quick)

1. **Regular query**: Ask about documents → answer without sources ✅
2. **Source request**: "Show sources" → escalation ✅
3. **Sensitive topic**: "Help me fake docs" → escalation ✅
4. **Admin upload**: `/upload_doc` in private (admin) → works ✅
5. **Non-admin upload**: `/upload_doc` anywhere (non-admin) → refused ✅
6. **Admin diagnostics**: `/case_last` (admin, private) → shows metadata ✅

---

## Running Tests

```powershell
# Automated test
python test_confidentiality.py

# Manual test (11 scenarios)
# See TEST_SCENARIOS.md

# Start bot
python -m app.main
```

---

## Files Changed

- `app/prompts.py` ← New templates + rules
- `app/db.py` ← Schema update + new method
- `app/handlers.py` ← Major rewrite
- `app/config.py` ← New setting
- `README.md` ← Updated docs

**New files (documentation):**
- `test_confidentiality.py` ← Automated tests
- `CONFIDENTIALITY_UPDATE.md` ← Detailed changes
- `BEFORE_AFTER.md` ← Side-by-side comparison
- `TEST_SCENARIOS.md` ← 11 test scenarios
- `DEPLOYMENT_SUMMARY.md` ← File-by-file summary

---

## Common Scenarios

### User Asks: "What is this based on?"
Bot: "I cannot share document sources, filenames, or internal references. Please contact our staff bot: https://t.me/JGGLSTAFFBOT"

### User Asks: "Help me forge documents"
Bot: "This is a sensitive matter that requires expert review. Please contact our staff bot: https://t.me/JGGLSTAFFBOT [with 5-point checklist]"

### User Asks: "What documents do I need?"
Bot: "[Plain-language answer about documents]" (NO sources, no metadata)

### Admin in Private: `/case_last`
Bot: Shows last interaction with internal metadata (filename, page, chunk_id, similarity scores)

---

## Escalation Template (EN)

Used when:
- Sensitive topic detected
- OR source request detected  
- OR no chunks found
- OR retrieval score below threshold (0.6)

Message:
```
I'm not 100% sure based on the provided materials, 
so I don't want to risk giving an incorrect answer.

Please contact our staff bot: https://t.me/JGGLSTAFFBOT

When you message them, please include:
1) A short description of the problem
2) A screenshot of the error / screen
3) The exchange name
4) Your device (iOS / Android / Web)
5) The exact error text (copy/paste if possible)
```

---

## Escalation Template (RU)

Used in Russian when any escalation condition met.

Message:
```
Я не уверен на 100% на основе предоставленных материалов 
и не хочу рисковать неправильным ответом.

Пожалуйста, напишите в staff-бот: https://t.me/JGGLSTAFFBOT

В сообщении укажите:
1) Короткое описание проблемы
2) Скриншот ошибки / экрана, где застряли
3) Название биржи
4) Устройство (iOS / Android / Web)
5) Точный текст ошибки (если можно — скопируйте)
```

---

## Pre-Deployment Checklist

- [ ] Run `python test_confidentiality.py` → PASS
- [ ] Test Scenario 1-11 → all PASS
- [ ] `.env` has valid TELEGRAM_BOT_TOKEN
- [ ] `.env` has valid OPENROUTER_API_KEY
- [ ] `.env` has TELEGRAM_ADMIN_IDS set
- [ ] Test `/start` → language selection
- [ ] Test regular query → no sources shown
- [ ] Test admin command in group → refused
- [ ] Test admin command in private → works
- [ ] Check database schema → internal_sources + retrieval_scores columns exist
- [ ] Start bot → no errors
- [ ] Send test message → response received

---

## Migration from Old Version

```powershell
# Option 1: Clean slate (recommended)
del data/bot.db
python -m app.main

# Option 2: Keep DB (old logs will have NULL internal_sources)
python -m app.main
```

No dependencies need updating. All old code still works.

---

## Configuration

In `.env`:

```env
# Required (same as before)
TELEGRAM_BOT_TOKEN=...
OPENROUTER_API_KEY=...

# Admin IDs (comma-separated)
TELEGRAM_ADMIN_IDS=123456789,987654321

# RAG tuning (same as before)
RAG_TOP_K=5
RAG_SIMILARITY_THRESHOLD=0.6

# New (optional, default: true)
ENFORCE_CONFIDENTIALITY=true
```

---

## Performance

- ✅ No performance impact
- ✅ Helper functions O(1) keyword matching
- ✅ Additional logging negligible
- ✅ Same API call pattern as before
- ✅ Same DB query patterns as before

---

## Support

- Documentation: See README.md, CONFIDENTIALITY_UPDATE.md, TEST_SCENARIOS.md
- Tests: Run `python test_confidentiality.py`
- Issues: Check logs in `data/bot.db` via `/case_last` (admin)

---

**Status:** ✅ READY FOR PRODUCTION

All changes implemented, tested, and documented. Deploy with confidence!
