import os
import logging
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, ContextTypes, filters
from anthropic import Anthropic

TELEGRAM_TOKEN = os.environ.get("TELEGRAM_BOT_TOKEN")
ANTHROPIC_API_KEY = os.environ.get("ANTHROPIC_API_KEY")

SYSTEM_PROMPT = """You are an auto-reply assistant for Colonel, who runs "Major Metrics" \
(a data analytics venture) and also handles borehole/drilling-related inquiries in Isiolo, Kenya. \
You are replying to someone who just messaged Colonel on Telegram while he's unavailable.

Rules:
- Keep replies short (2-4 sentences), warm, and professional.
- If the message is a business inquiry (data analytics, pricing, drilling/borehole services), \
acknowledge it, show interest, and say Colonel will follow up personally soon.
- If it's a casual/personal message, reply briefly and naturally, and mention Colonel will \
respond himself soon.
- Never invent prices, specific dates, or commitments Colonel hasn't given you.
- Always make clear (briefly, without being robotic) that this is an automatic reply.
- Reply in the same language the person used (English or Swahili)."""

WELCOME_MESSAGE = "👋 Welcome! You've reached Colonel's auto-reply assistant. I'll respond right away — Colonel will follow up personally soon."
MAX_HISTORY_MESSAGES = 6

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)
client = Anthropic(api_key=ANTHROPIC_API_KEY)
conversation_history = {}

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(WELCOME_MESSAGE)

async def ai_reply(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    text = update.message.text
    history = conversation_history.get(user.id, [])
    history.append({"role": "user", "content": text})
    history = history[-MAX_HISTORY_MESSAGES:]
    try:
        response = client.messages.create(
            model="claude-sonnet-4-6",
            max_tokens=300,
            system=SYSTEM_PROMPT,
            messages=history,
        )
        reply_text = response.content[0].text
    except Exception as e:
        logger.error(f"Claude API error: {e}")
        reply_text = "Thanks for your message! Small technical hiccup — Colonel will get back to you personally soon."
    history.append({"role": "assistant", "content": reply_text})
    conversation_history[user.id] = history
    await update.message.reply_text(reply_text)

def main():
    app = ApplicationBuilder().token(TELEGRAM_TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, ai_reply))
    print("Bot running...")
    app.run_polling()

if __name__ == "__main__":
    main()
