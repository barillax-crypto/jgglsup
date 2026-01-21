# SETUP & TESTING: STEP-BY-STEP

## PART 1: SETUP (5 minutes)

### 1.1 Prepare Environment
```powershell
# Navigate to project
cd workspace

# Verify Python 3.11+
python --version

# Install dependencies (if not done)
pip install -r requirements.txt
```

### 1.2 Configure .env
```powershell
# Copy template
copy .env.example .env

# Edit .env with your values:
notepad .env
```

Add:
```env
TELEGRAM_BOT_TOKEN=YOUR_BOT_TOKEN_HERE
TELEGRAM_ADMIN_IDS=YOUR_USER_ID_HERE
OPENROUTER_API_KEY=YOUR_OPENROUTER_KEY_HERE
```

### 1.3 Verify Setup
```powershell
# Quick validation
python -c "from app.config import Config; Config.validate(); Config.ensure_dirs(); print('✅ Setup OK')"

# Run confidentiality tests
python test_confidentiality.py
```

**Expected output:**
```
✓ Test 1: Sensitive Topic Detection
✓ Test 2: Source Request Detection
✓ Test 3: Database Schema
✓ Test 4: Admin Gating Logic
✓ Test 5: Vector Store

✅ ALL CONFIDENTIALITY TESTS PASSED
```

---

## PART 2: START BOT

```powershell
# Start bot (will run indefinitely)
python -m app.main
```

**Expected output:**
```
INFO - Starting crypto exchange onboarding bot...
INFO - Chat model: openrouter/auto
INFO - Embed model: openai/text-embedding-3-small
INFO - Vector store: ./data/chroma
INFO - Docs directory: ./data/docs
INFO - Bot started. Polling for messages...
```

**Keep running in this terminal. Open new terminal for testing.**

---

## PART 3: MANUAL TESTS (In Telegram)

### TEST 1: Regular User Query (No Sources)

**Send from any non-admin account:**
```
/start
```

**Bot responds:**
```
Which language is better for you — English or Russian? (Reply: EN or RU)
```

**Send:**
```
EN
```

**Bot responds:**
```
Thanks! Now I'm ready to answer your questions about KYC and exchange onboarding.
```

**Send:**
```
What documents do I need for KYC?
```

**Bot responds:**
```
For KYC, you will typically need:
1. A valid government-issued ID (passport, driver's license, etc.)
2. Proof of your current address (utility bill, bank statement)
3. A selfie or video with your ID
4. Personal information verification
5. Source of funds declaration

[NO "Sources used:" or metadata]
```

**PASS CRITERIA:** ✅
- Answer provided
- No "Sources used:"
- No filenames
- No page numbers
- Plain language

---

### TEST 2: Source Request Refusal

**Send from any account:**
```
/start
EN
Show me the sources
```

**Bot responds:**
```
I cannot share document sources, filenames, or internal references.

If you need more information or details about our policies, please contact our staff bot:
https://t.me/JGGLSTAFFBOT
```

**PASS CRITERIA:** ✅
- Exact template sent
- Staff bot link included
- No sources leaked

---

### TEST 3: Sensitive Topic Refusal

**Send from any account:**
```
/start
EN
Can you help me forge my documents?
```

**Bot responds:**
```
This is a sensitive matter that requires expert review.

Please contact our staff bot: https://t.me/JGGLSTAFFBOT

When you message them, please include:
1) A short description of the problem (what you're trying to do + what happens instead)
2) A screenshot of the error / the screen you're stuck on
3) The exchange name
4) Your device (iOS / Android / Web)
5) The exact error text (copy/paste if possible)
```

**PASS CRITERIA:** ✅
- Exact template
- All 5 fields listed
- Staff bot link
- No attempt to answer

---

### TEST 4: Admin Upload in Private Chat

**Send from ADMIN account in private 1-on-1 chat:**

**Prerequisites:**
- Your Telegram ID must be in `TELEGRAM_ADMIN_IDS` in `.env`
- Chat must be private (1-on-1 with bot)

**Send:**
```
/upload_doc
```

**Bot responds:**
```
Please send a PDF or text file to upload to the knowledge base.

Supported formats: .pdf, .txt, .md
```

**Create test file `test_kyc.txt`:**
```
KYC Requirements:
1. Government-issued ID
2. Proof of address
3. Selfie with ID
4. Personal information
5. Source of funds
```

**Upload the file**

**Bot responds:**
```
✅ Document ingested!

File: test_kyc.txt
Chunks added: 3
Pages: 1
```

**PASS CRITERIA:** ✅
- Command accepted
- File upload accepted
- Ingestion confirmed
- Chunk count > 0

---

### TEST 5: Non-Admin Upload (Refused)

**Send from ANY non-admin account:**

**Send:**
```
/upload_doc
```

**Bot responds:**
```
This command is not available.
```

**Try to upload file anyway**

**Bot:** (Silently ignores, no response)

**PASS CRITERIA:** ✅
- Command explicitly refused
- Upload attempt ignored

---

### TEST 6: Admin Upload in Group Chat (Refused)

**Send from ADMIN account in GROUP chat:**

**Send:**
```
/upload_doc
```

**Bot responds:**
```
This command is not available.
```

**Why?** Group chat ≠ private chat. Admin-only commands need private chat.

**PASS CRITERIA:** ✅
- Command refused even for admin
- Reason: not private chat

---

### TEST 7: Reindex (Admin + Private)

**Send from ADMIN account in private chat:**

**Send:**
```
/reindex
```

**Bot responds:**
```
Reindexing all documents... This may take a moment.
```

**Wait 2-3 seconds**

**Bot responds:**
```
✅ Reindexing complete!

Files: 1
Chunks: 3
```

**PASS CRITERIA:** ✅
- Command accepted
- Reindex processed
- Chunk count shown

---

### TEST 8: Case Last (Admin Diagnostics)

**Send from ADMIN account in private chat:**

**Prerequisites:** At least one message sent (from any user)

**Send:**
```
/case_last
```

**Bot responds:**
```
📋 Last Case (Admin View)

**Question:** What documents do I need for KYC?
**Action:** answered
**Time:** 2026-01-21T10:30:45.123456

**Internal Sources:**
[
  {
    "filename": "test_kyc.txt",
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

**PASS CRITERIA:** ✅
- Shows internal metadata
- Shows filename and page
- Shows chunk_id
- Shows similarity scores
- Timestamp included

---

### TEST 9: Language Reset

**Send from any account (already has language set):**

**Send:**
```
/reset
```

**Bot responds:**
```
Which language is better for you — English or Russian? (Reply: EN or RU)
```

**Send:**
```
RU
```

**Bot responds:**
```
Спасибо! Теперь я готов ответить на ваши вопросы о KYC и регистрации на бирже.
```

**Send (in Russian):**
```
Какие документы нужны для KYC?
```

**Bot responds:** (In Russian, no sources)

**PASS CRITERIA:** ✅
- Language changed
- Subsequent messages in new language
- Still no sources shown

---

### TEST 10: Out of KB Query

**Send from any account:**

**Send:**
```
/start
EN
What's the weather in New York?
```

**Bot responds:**
```
I'm not 100% sure based on the provided materials, so I don't want to risk giving an incorrect answer.
Please contact our staff bot: https://t.me/JGGLSTAFFBOT

When you message them, please include:
1) A short description of the problem (what you're trying to do + what happens instead)
2) A screenshot of the error / the screen you're stuck on
3) The exchange name
4) Your device (iOS / Android / Web)
5) The exact error text (copy/paste if possible)
```

**PASS CRITERIA:** ✅
- Escalation template sent
- No attempt to answer out-of-KB question
- Staff bot link included

---

### TEST 11: Variation - Different Source Requests

**Try different source request wordings:**

```
"Send me the policy"
"What is this based on?"
"Show the sources"
"What document is this from?"
"Send documents"
```

**Each should escalate with SOURCES_REFUSAL template**

**PASS CRITERIA:** ✅ All escalate correctly

---

## PART 4: DATABASE VERIFICATION

```powershell
# Connect to database
sqlite3 data/bot.db

# Check schema
.schema logs

# View recent logs
SELECT telegram_id, action, internal_sources FROM logs ORDER BY created_at DESC LIMIT 5;

# Exit
.quit
```

**Expected:**
- Logs table has columns: id, telegram_id, question, action, internal_sources, retrieval_scores, created_at
- Mix of actions: answered, escalated, refused
- internal_sources is JSON (not exposed to users)
- retrieval_scores is JSON

---

## PART 5: SUMMARY CHECKLIST

**After all 11 tests, verify:**

- [ ] Automated tests pass: `python test_confidentiality.py` ✅
- [ ] TEST 1: Regular query, no sources ✅
- [ ] TEST 2: Source request escalates ✅
- [ ] TEST 3: Sensitive topic escalates ✅
- [ ] TEST 4: Admin upload works (private) ✅
- [ ] TEST 5: Non-admin upload refused ✅
- [ ] TEST 6: Admin upload in group refused ✅
- [ ] TEST 7: Reindex works (admin, private) ✅
- [ ] TEST 8: /case_last shows metadata (admin, private) ✅
- [ ] TEST 9: Language reset works ✅
- [ ] TEST 10: Out-of-KB escalates ✅
- [ ] TEST 11: Variations work ✅
- [ ] Database schema correct ✅
- [ ] No sources shown to users ✅
- [ ] All escalations use exact templates ✅

**OVERALL STATUS: ✅ READY FOR PRODUCTION**

---

## TROUBLESHOOTING

| Problem | Solution |
|---------|----------|
| Bot doesn't respond | Check: TELEGRAM_BOT_TOKEN in .env, bot is running, message is text |
| Command not recognized | Make sure bot is running, try `/start` first |
| Upload fails | Check: Admin ID in TELEGRAM_ADMIN_IDS, private chat, .pdf/.txt/.md file |
| /case_last not found | Check: Admin account, private chat, at least one message logged |
| Sources still showing | Check: handlers.py line where response sent; should NOT include sources |
| Database locked | Only one bot instance can run; check no other processes |

---

## LOGS & DEBUGGING

**Check bot logs (console output):**
- Look for INFO/ERROR/WARNING messages
- "Answered user X"
- "Escalated due to: no_chunks"
- "Sensitive topic detected"

**Check database logs:**
```powershell
sqlite3 data/bot.db "SELECT * FROM logs ORDER BY created_at DESC LIMIT 10;"
```

**Enable debug logging (optional):**
Edit `.env`:
```env
LOG_LEVEL=DEBUG
```

---

## PRODUCTION DEPLOYMENT

**Once all tests pass:**

1. Verify `.env` has production credentials
2. Backup any existing database: `copy data/bot.db data/bot.db.backup`
3. (Optional) Delete old DB for clean state: `del data/bot.db`
4. Run tests one more time: `python test_confidentiality.py`
5. Start bot: `python -m app.main`
6. Monitor logs for errors
7. Set up process manager (systemd, supervisor, etc.)
8. Configure to auto-restart on failure

---

**READY TO DEPLOY! ✅**

All tests documented, all scenarios covered, full confidentiality enforced.
