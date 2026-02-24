<!-- Use this file to provide workspace-specific custom instructions to Copilot. -->

# Telegram Sleep Calculator Bot

A Python Telegram bot using `python-telegram-bot` v21 that calculates optimal
sleep/wake times based on 90-minute sleep cycles.

## Key files
- `bot.py` – all bot handlers and sleep calculation logic
- `config.py` – bot token (never commit a real token)
- `requirements.txt` – `python-telegram-bot==21.6`

## Coding guidelines
- Use `python-telegram-bot` v21 async API (Application, ContextTypes, etc.)
- Keep all calculation logic in pure functions (no side effects)
- Parse time strings with `datetime.strptime` and support 12/24-hour formats
- Use `ConversationHandler` for multi-step flows
- Use `InlineKeyboardMarkup` for buttons
- All replies use `parse_mode="Markdown"`
