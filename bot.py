"""
Telegram Sleep Calculator Bot
Calculates optimal sleep/wake times based on 90-minute sleep cycles.
"""

import asyncio
import logging
from datetime import datetime, timedelta
import pytz
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    Application,
    CommandHandler,
    CallbackQueryHandler,
    MessageHandler,
    filters,
    ContextTypes,
    ConversationHandler,
)
import os

BOT_TOKEN = os.environ["BOT_TOKEN"]

# ── Logging ──────────────────────────────────────────────────────────────────
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO,
)
logger = logging.getLogger(__name__)

# ── Constants ─────────────────────────────────────────────────────────────────
SLEEP_CYCLE_MINUTES = 90       # one full sleep cycle
FALL_ASLEEP_MINUTES = 14       # average time to fall asleep
MIN_CYCLES = 4                 # minimum healthy cycles  (6 h)
MAX_CYCLES = 6                 # maximum recommended cycles (9 h)
LOCAL_TZ = pytz.timezone("Asia/Bangkok")  # UTC+7 (Hanoi, Bangkok, Jakarta)

# Conversation states
WAITING_FOR_WAKE_TIME = 1
WAITING_FOR_SLEEP_TIME = 2


# ── Helper functions ──────────────────────────────────────────────────────────

def now_local() -> datetime:
    """Return the current time in the local timezone (UTC+7)."""
    return datetime.now(LOCAL_TZ).replace(tzinfo=None)

def calculate_bedtimes(wake_time: datetime) -> list[datetime]:
    """Return a list of ideal bedtimes for a given wake-up time."""
    bedtimes = []
    for cycles in range(MAX_CYCLES, MIN_CYCLES - 1, -1):
        total_sleep = timedelta(minutes=cycles * SLEEP_CYCLE_MINUTES + FALL_ASLEEP_MINUTES)
        bedtime = wake_time - total_sleep
        bedtimes.append((bedtime, cycles))
    return bedtimes


def calculate_wake_times(sleep_time: datetime) -> list[datetime]:
    """Return a list of ideal wake-up times for a given bedtime."""
    wake_times = []
    fall_asleep_time = sleep_time + timedelta(minutes=FALL_ASLEEP_MINUTES)
    for cycles in range(MIN_CYCLES, MAX_CYCLES + 1):
        total_sleep = timedelta(minutes=cycles * SLEEP_CYCLE_MINUTES)
        wake_time = fall_asleep_time + total_sleep
        wake_times.append((wake_time, cycles))
    return wake_times


def format_time(dt: datetime) -> str:
    return dt.strftime("%I:%M %p")


def cycles_to_hours(cycles: int) -> str:
    hours = (cycles * SLEEP_CYCLE_MINUTES) / 60
    return f"{hours:.1f}h"


def parse_time(text: str) -> datetime | None:
    """Parse common time formats (e.g. '7:30', '7:30 AM', '22:00')."""
    text = text.strip()
    formats = ["%I:%M %p", "%I:%M%p", "%H:%M", "%I %p", "%I%p"]
    now = now_local()
    for fmt in formats:
        try:
            t = datetime.strptime(text, fmt)
            return now.replace(hour=t.hour, minute=t.minute, second=0, microsecond=0)
        except ValueError:
            continue
    return None


def build_bedtime_message(bedtimes: list, wake_time: datetime) -> str:
    lines = [
        f"⏰ Wake-up time: *{format_time(wake_time)}*\n",
        "🛏 Recommended bedtimes (fall asleep at):\n",
    ]
    emojis = ["🥇", "🥈", "🥉", "🏅", "🎖", "⭐"]
    for i, (bedtime, cycles) in enumerate(bedtimes):
        emoji = emojis[i] if i < len(emojis) else "•"
        lines.append(
            f"{emoji} *{format_time(bedtime)}*  —  {cycles} cycles ({cycles_to_hours(cycles)})"
        )
    lines.append("\n💡 Each cycle lasts ~90 minutes.")
    lines.append(f"⏳ +{FALL_ASLEEP_MINUTES} min to fall asleep is already included.")
    return "\n".join(lines)


def build_wake_message(wake_times: list, sleep_time: datetime) -> str:
    lines = [
        f"🛏 Bedtime: *{format_time(sleep_time)}*\n",
        "⏰ Recommended wake-up times:\n",
    ]
    emojis = ["🥇", "🥈", "🥉", "🏅", "🎖", "⭐"]
    for i, (wake_time, cycles) in enumerate(wake_times):
        emoji = emojis[i] if i < len(emojis) else "•"
        lines.append(
            f"{emoji} *{format_time(wake_time)}*  —  {cycles} cycles ({cycles_to_hours(cycles)})"
        )
    lines.append("\n💡 Each cycle lasts ~90 minutes.")
    lines.append(f"⏳ +{FALL_ASLEEP_MINUTES} min to fall asleep is already included.")
    return "\n".join(lines)


def main_menu_keyboard() -> InlineKeyboardMarkup:
    keyboard = [
        [
            InlineKeyboardButton("⏰ I want to WAKE UP at…", callback_data="ask_wake"),
        ],
        [
            InlineKeyboardButton("🛏 I'm going to BED at…", callback_data="ask_sleep"),
        ],
        [
            InlineKeyboardButton("😴 Sleep NOW", callback_data="sleep_now"),
        ],
        [
            InlineKeyboardButton("ℹ️ About sleep cycles", callback_data="info"),
        ],
    ]
    return InlineKeyboardMarkup(keyboard)


# ── Command handlers ──────────────────────────────────────────────────────────

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    text = (
        "👋 Welcome to *Sleep Calculator Bot*!\n\n"
        "I use 90-minute sleep cycles to help you wake up feeling refreshed.\n\n"
        "What would you like to do?"
    )
    await update.message.reply_text(
        text, parse_mode="Markdown", reply_markup=main_menu_keyboard()
    )


async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    text = (
        "*Sleep Calculator Bot – Help*\n\n"
        "📌 *Commands*\n"
        "/start – Show the main menu\n"
        "/wake – Calculate bedtimes for a desired wake-up time\n"
        "/sleep – Calculate wake-up times for a given bedtime\n"
        "/now – Calculate wake-up times if you sleep right now\n"
        "/info – Learn about sleep cycles\n"
        "/help – Show this message\n\n"
        "📌 *Time formats accepted*\n"
        "`7:30 AM`  `7:30 am`  `07:30`  `22:00`"
    )
    await update.message.reply_text(text, parse_mode="Markdown")


async def wake_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    await update.message.reply_text(
        "⏰ What time do you want to *wake up*?\n\nExamples: `7:00 AM`, `06:30`, `7:30 am`",
        parse_mode="Markdown",
    )
    return WAITING_FOR_WAKE_TIME


async def sleep_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    await update.message.reply_text(
        "🛏 What time are you planning to *go to bed*?\n\nExamples: `10:30 PM`, `22:30`, `11 pm`",
        parse_mode="Markdown",
    )
    return WAITING_FOR_SLEEP_TIME


async def now_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    now = now_local()
    wake_times = calculate_wake_times(now)
    msg = build_wake_message(wake_times, now)
    await update.message.reply_text(msg, parse_mode="Markdown", reply_markup=main_menu_keyboard())


async def info_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    text = (
        "🧠 *About Sleep Cycles*\n\n"
        "Your sleep consists of repeated ~90-minute cycles, each containing:\n"
        "• Light sleep\n"
        "• Deep sleep (REM)\n\n"
        "Waking up *between* cycles (not in the middle) means you feel rested.\n\n"
        "✅ *Ideal sleep* = 4–6 full cycles\n"
        "⏰ *6 cycles* = 9 hours  (most refreshing)\n"
        "⏰ *5 cycles* = 7.5 hours (recommended)\n"
        "⏰ *4 cycles* = 6 hours   (minimum)\n\n"
        "💡 An average person takes ~14 minutes to fall asleep, so that's built into every calculation."
    )
    await update.message.reply_text(text, parse_mode="Markdown", reply_markup=main_menu_keyboard())


# ── Conversation handlers ─────────────────────────────────────────────────────

async def receive_wake_time(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    user_input = update.message.text
    wake_time = parse_time(user_input)
    if wake_time is None:
        await update.message.reply_text(
            "❌ I couldn't understand that time.\nTry formats like `7:30 AM`, `07:30`, or `22:00`.",
            parse_mode="Markdown",
        )
        return WAITING_FOR_WAKE_TIME

    bedtimes = calculate_bedtimes(wake_time)
    msg = build_bedtime_message(bedtimes, wake_time)
    await update.message.reply_text(msg, parse_mode="Markdown", reply_markup=main_menu_keyboard())
    return ConversationHandler.END


async def receive_sleep_time(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    user_input = update.message.text
    sleep_time = parse_time(user_input)
    if sleep_time is None:
        await update.message.reply_text(
            "❌ I couldn't understand that time.\nTry formats like `10:30 PM`, `22:30`, or `23:00`.",
            parse_mode="Markdown",
        )
        return WAITING_FOR_SLEEP_TIME

    wake_times = calculate_wake_times(sleep_time)
    msg = build_wake_message(wake_times, sleep_time)
    await update.message.reply_text(msg, parse_mode="Markdown", reply_markup=main_menu_keyboard())
    return ConversationHandler.END


async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    await update.message.reply_text("❌ Cancelled.", reply_markup=main_menu_keyboard())
    return ConversationHandler.END


# ── Callback query handler (inline buttons) ───────────────────────────────────

async def button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    query = update.callback_query
    await query.answer()

    if query.data == "ask_wake":
        await query.message.reply_text(
            "⏰ What time do you want to *wake up*?\n\nExamples: `7:00 AM`, `06:30`, `7:30 am`",
            parse_mode="Markdown",
        )
        context.user_data["expecting"] = "wake"
        return WAITING_FOR_WAKE_TIME

    elif query.data == "ask_sleep":
        await query.message.reply_text(
            "🛏 What time are you planning to *go to bed*?\n\nExamples: `10:30 PM`, `22:30`, `11 pm`",
            parse_mode="Markdown",
        )
        context.user_data["expecting"] = "sleep"
        return WAITING_FOR_SLEEP_TIME

    elif query.data == "sleep_now":
        now = now_local()
        wake_times = calculate_wake_times(now)
        msg = build_wake_message(wake_times, now)
        await query.message.reply_text(msg, parse_mode="Markdown", reply_markup=main_menu_keyboard())
        return ConversationHandler.END

    elif query.data == "info":
        text = (
            "🧠 *About Sleep Cycles*\n\n"
            "Your sleep consists of repeated ~90-minute cycles, each containing:\n"
            "• Light sleep\n"
            "• Deep sleep (REM)\n\n"
            "Waking up *between* cycles (not in the middle) means you feel rested.\n\n"
            "✅ *Ideal sleep* = 4–6 full cycles\n"
            "⏰ *6 cycles* = 9 hours  (most refreshing)\n"
            "⏰ *5 cycles* = 7.5 hours (recommended)\n"
            "⏰ *4 cycles* = 6 hours   (minimum)\n\n"
            "💡 An average person takes ~14 minutes to fall asleep, so that's built into every calculation."
        )
        await query.message.reply_text(text, parse_mode="Markdown", reply_markup=main_menu_keyboard())
        return ConversationHandler.END

    return ConversationHandler.END


async def message_router(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Route free-text messages based on what the bot is currently expecting."""
    expecting = context.user_data.get("expecting")
    if expecting == "wake":
        context.user_data.pop("expecting", None)
        return await receive_wake_time(update, context)
    elif expecting == "sleep":
        context.user_data.pop("expecting", None)
        return await receive_sleep_time(update, context)
    else:
        # Default: try to parse as a time and calculate both options
        parsed = parse_time(update.message.text)
        if parsed:
            bedtimes = calculate_bedtimes(parsed)
            wake_times = calculate_wake_times(parsed)
            msg = (
                build_bedtime_message(bedtimes, parsed)
                + "\n\n────────────────────\n\n"
                + build_wake_message(wake_times, parsed)
            )
            await update.message.reply_text(msg, parse_mode="Markdown", reply_markup=main_menu_keyboard())
        else:
            await update.message.reply_text(
                "🤔 I didn't understand that. Use /start to open the menu or type a time like `7:30 AM`.",
                parse_mode="Markdown",
                reply_markup=main_menu_keyboard(),
            )
    return ConversationHandler.END


# ── Main ──────────────────────────────────────────────────────────────────────

def main() -> None:
    asyncio.set_event_loop(asyncio.new_event_loop())
    app = Application.builder().token(BOT_TOKEN).build()

    # Conversation handler for text-based multi-step flows only
    conv_handler = ConversationHandler(
        entry_points=[
            CommandHandler("wake", wake_command),
            CommandHandler("sleep", sleep_command),
        ],
        states={
            WAITING_FOR_WAKE_TIME: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, receive_wake_time)
            ],
            WAITING_FOR_SLEEP_TIME: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, receive_sleep_time)
            ],
        },
        fallbacks=[CommandHandler("cancel", cancel)],
    )

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("help", help_command))
    app.add_handler(CommandHandler("now", now_command))
    app.add_handler(CommandHandler("info", info_command))
    app.add_handler(CallbackQueryHandler(button_handler))
    app.add_handler(conv_handler)
    # Catch-all for free-text (outside conversation)
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, message_router))

    logger.info("Bot is running…")
    app.run_polling(allowed_updates=Update.ALL_TYPES)


if __name__ == "__main__":
    main()
