# BEFORE vs AFTER COMPARISON

## User Experience

### BEFORE: Knowledge Base Exposed
```
User: "What documents do I need?"
Bot: "For KYC, you will need:
1. Valid government-issued ID
2. Proof of address
...
Sources used: test_kyc.txt:p1"
```
❌ Problem: Source info exposed! User learns internal KB structure.

### AFTER: Strict Confidentiality
```
User: "What documents do I need?"
Bot: "For KYC, you will typically need:
1. A valid government-issued ID
2. Proof of your current address
..."
```
✅ No sources revealed. User gets plain-language answer only.

---

## Source Requests

### BEFORE: No Handling
```
User: "Show me the sources"
Bot: (No specific handling, might respond with generic answer or confusion)
```

### AFTER: Immediate Escalation
```
User: "Show me the sources"
Bot: "I cannot share document sources, filenames, or internal references.
If you need more information, contact our staff bot: https://t.me/JGGLSTAFFBOT"
(logs: refused, source_request)
```

---

## Sensitive Topics

### BEFORE: No Handling
```
User: "How can I forge my documents?"
Bot: (Tries to answer or escalates without specific logic)
```

### AFTER: Automatic Refusal
```
User: "How can I forge my documents?"
Bot: "This is a sensitive matter that requires expert review.
Please contact our staff bot: https://t.me/JGGLSTAFFBOT
When you message them, please include: ..."
(logs: refused, sensitive_topic)
```

---

## Admin Commands

### BEFORE: Works Anywhere
```
User sends /upload_doc in group chat
Bot: Accepts and processes (security risk!)
```

### AFTER: Admin + Private Chat Only
```
User (non-admin) sends /upload_doc
Bot: "This command is not available."

Admin sends /upload_doc in group chat
Bot: "This command is not available."

Admin sends /upload_doc in private chat
Bot: "Please send a PDF or text file..."
```

---

## Database Logging

### BEFORE
```sql
logs(id, telegram_id, question, action, sources, created_at)
-- "sources" might expose filenames
```

### AFTER
```sql
logs(id, telegram_id, question, action, internal_sources, retrieval_scores, created_at)
-- "internal_sources" is JSON (server-side only, never shown to users)
-- "retrieval_scores" stores similarity metrics
-- Regular users never see these columns
```

---

## Admin Diagnostics

### BEFORE: No Diagnostics
No way to inspect individual cases.

### AFTER: /case_last Command
```
Admin sends: /case_last
Bot returns:
📋 Last Case (Admin View)

**Question:** What documents do I need?
**Action:** answered
**Time:** 2026-01-21T10:30:45.123456

**Internal Sources:**
[{
  "filename": "test_kyc.txt",
  "page": 1,
  "chunk_id": "abc123def456",
  "similarity": 0.923
}]

**Retrieval Scores:**
[{"chunk_id": "abc123def456", "similarity": 0.923}]
```
✅ Admins can audit and debug without exposing to users.

---

## System Prompts

### BEFORE
```
"Always cite your sources (filename and page number if available)."
"End with: 'Sources used: [list of sources]'"
"If you made any assumptions, add: 'What I'm assuming: [assumptions]'"
```

### AFTER
```
"NEVER reveal, quote, or reference: filenames, page numbers, chunk IDs, 
 document names, or internal KB structure."

"NEVER include 'Sources used' or any internal references."

"If user asks for sources/docs → REFUSE (system will escalate)"

"If you cannot answer with confidence → REFUSE (system will escalate)"

"Your response is for the user only. Do NOT mention internal metadata."
```

---

## Escalation Rules

### BEFORE
```
- No chunks found → escalate
- Low similarity → escalate
- LLM error → escalate
(No special handling for sensitive topics or source requests)
```

### AFTER
```
- Source request detected → escalate (immediately)
- Sensitive topic detected → escalate (immediately)
- No chunks found → escalate
- Low similarity → escalate
- LLM error → escalate
```

---

## Handler Flow

### BEFORE: handle_message()
```
1. Get user language
2. Retrieve chunks
3. Call LLM
4. Send response WITH sources
5. Log with "sources" field
```

### AFTER: handle_message()
```
1. Get user language
2. Check: is_sensitive_topic() → escalate if true
3. Check: is_source_request() → escalate if true
4. Retrieve chunks
5. If no chunks or low score → escalate
6. Call LLM
7. Send response WITHOUT any metadata
8. Log with "internal_sources" and "retrieval_scores" (JSON, server-side)
```

---

## Language Selection

### BEFORE
```
/start → if user already set language, skip question
```

### AFTER
```
/start → ALWAYS ask language (even if previously set)
Forces re-confirmation on each session start
```

---

## What's Visible to Users

### BEFORE
```
Commands: /start, /help, /reset, /upload_doc, /reindex
(Regular users could see admin commands)
```

### AFTER
```
Regular users: /start, /help, /reset
Admins (private chat): /start, /help, /reset, /upload_doc, /reindex, /case_last
(Admin commands silently hidden from non-admins)
```

---

## Summary

| Aspect | Before | After |
|--------|--------|-------|
| **Sources Visible** | Yes (citations shown) | No (zero exposure) |
| **Source Requests** | No handling | Auto-escalate |
| **Sensitive Topics** | No detection | Auto-escalate |
| **Admin Gating** | No validation | Requires admin + private |
| **Diagnostics** | None | `/case_last` (admin only) |
| **Language Selection** | Optional re-ask | Always ask on /start |
| **Database** | Exposed sources | Internal metadata only |
| **System Prompt** | Cites sources | Forbids disclosing KB |
| **Confidentiality** | Low | Strict ✅ |

