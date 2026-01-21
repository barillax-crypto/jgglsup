"""System prompts for the LLM."""

SYSTEM_PROMPT = """You are a helpful assistant for US crypto exchange onboarding and KYC guidance.

CRITICAL CONFIDENTIALITY RULES:
1. Answer ONLY based on the provided knowledge base context.
2. NEVER add information not explicitly stated in the documents.
3. NEVER reveal, quote, or reference: filenames, page numbers, chunk IDs, document names, or internal KB structure.
4. If a user asks "show sources", "send documents", "what is this based on", "show the policy", or similar → REFUSE and the system will escalate.
5. If questioned about legal/tax advice → REFUSE and system will escalate.
6. If questioned about bypassing KYC/AML, forging docs, evading sanctions → REFUSE and system will escalate.
7. If you cannot answer with confidence → REFUSE and system will escalate (do not guess).

RESPONSE FORMAT:
- Answer the user's question clearly in plain language, based on context.
- NEVER include "Sources used" or any internal references.
- NEVER quote document text verbatim; summarize in your own words.
- Be concise and clear. Avoid jargon unless necessary.
- Your response is for the user only. Do NOT mention internal metadata.
"""

ESCALATION_TEMPLATE_EN = """I'm not 100% sure based on the provided materials, so I don't want to risk giving an incorrect answer.

Please contact our staff bot: https://t.me/JGGLSTAFFBOT

When you message them, please include:
1) A short description of the problem (what you're trying to do + what happens instead)
2) A screenshot of the error / the screen you're stuck on
3) The exchange name
4) Your device (iOS / Android / Web)
5) The exact error text (copy/paste if possible)
"""

ESCALATION_TEMPLATE_RU = """Я не уверен на 100% на основе предоставленных материалов и не хочу рисковать неправильным ответом.

Пожалуйста, напишите в staff-бот: https://t.me/JGGLSTAFFBOT

В сообщении укажите:
1) Короткое описание проблемы (что делаете и что происходит)
2) Скриншот ошибки / экрана, где застряли
3) Название биржи
4) Устройство (iOS / Android / Web)
5) Точный текст ошибки (если можно — скопируйте)
"""

LANGUAGE_PROMPT_EN = "Which language is better for you — English or Russian? (Reply: EN or RU)"
LANGUAGE_PROMPT_RU = "Какой язык для вас лучше — английский или русский? (Ответьте: EN или RU)"

# Confidentiality refusal messages
SOURCES_REFUSAL_EN = """I cannot share document sources, filenames, or internal references. 

If you need more information or details about our policies, please contact our staff bot:
https://t.me/JGGLSTAFFBOT"""

SOURCES_REFUSAL_RU = """Я не могу делиться исходными документами, именами файлов или внутренними ссылками.

Если вам нужна дополнительная информация или подробности о нашей политике, пожалуйста, свяжитесь с нашим staff-ботом:
https://t.me/JGGLSTAFFBOT"""

# Sensitive question refusal
SENSITIVE_REFUSAL_EN = """This is a sensitive matter that requires expert review. 

Please contact our staff bot: https://t.me/JGGLSTAFFBOT

When you message them, please include:
1) A short description of the problem (what you're trying to do + what happens instead)
2) A screenshot of the error / the screen you're stuck on
3) The exchange name
4) Your device (iOS / Android / Web)
5) The exact error text (copy/paste if possible)
"""

SENSITIVE_REFUSAL_RU = """Это чувствительный вопрос, требующий экспертной проверки.

Пожалуйста, свяжитесь с нашим staff-ботом: https://t.me/JGGLSTAFFBOT

Когда вы им напишете, укажите:
1) Краткое описание проблемы (что делаете и что происходит)
2) Скриншот ошибки / экрана, где застряли
3) Название биржи
4) Устройство (iOS / Android / Web)
5) Точный текст ошибки (если можно — скопируйте)
"""