# 😴 Telegram Sleep Calculator Bot

A Telegram bot that calculates **optimal sleep and wake-up times** based on 90-minute sleep cycles so you always wake up feeling refreshed.

---

## Features

| Command | Description |
|---------|-------------|
| `/start` | Show the interactive main menu |
| `/wake` | Enter a wake-up time → get ideal bedtimes |
| `/sleep` | Enter a bedtime → get ideal wake-up times |
| `/now` | Calculate wake times if you sleep right now |
| `/info` | Learn about sleep cycles |
| `/help` | Show help |

- **Inline buttons** for one-tap access to every feature  
- Supports common time formats: `7:30 AM`, `07:30`, `22:00`, `11 pm`  
- Calculates 4–6 full 90-minute cycles (6 h – 9 h of sleep)  
- Automatically accounts for the ~14 minutes it takes to fall asleep  

---

## Setup

### 1. Create a Telegram bot

1. Open Telegram and message **@BotFather**
2. Send `/newbot` and follow the prompts
3. Copy the **API token** you receive

### 2. Clone / open the project

```
cd d:\Vscode\sleepbot
```

### 3. Create & activate a virtual environment

```powershell
python -m venv .venv
.venv\Scripts\Activate.ps1
```

### 4. Install dependencies

```powershell
pip install -r requirements.txt
```

### 5. Add your bot token

Open `config.py` and replace the placeholder:

```python
BOT_TOKEN = "YOUR_TELEGRAM_BOT_TOKEN_HERE"
```

### 6. Run the bot

```powershell
python bot.py
```

---

## Project Structure

```
sleepbot/
├── bot.py          # Main bot logic
├── config.py       # Bot token (keep private!)
├── requirements.txt
├── .gitignore
└── README.md
```

---

## How Sleep Cycles Work

Your sleep consists of repeated **~90-minute cycles**. Waking up *between* cycles (not in the middle of deep sleep) means you feel alert and rested.

| Cycles | Sleep Time |
|--------|-----------|
| 4      | 6 hours   |
| 5      | 7.5 hours |
| 6      | 9 hours   |

> ⚠️ **Never share your `config.py` or bot token publicly.**
