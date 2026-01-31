import os
import asyncio
import logging
from telegram import Bot
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes
from dotenv import load_dotenv

# Load env vars
load_dotenv()

TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")
ENABLED = os.getenv("TELEGRAM_ENABLED", "false").lower() == "true"

logger = logging.getLogger("TelegramBridge")

class TelegramBridge:
    def __init__(self):
        self.enabled = ENABLED
        if self.enabled and TOKEN:
            self.bot = Bot(token=TOKEN)
        else:
            self.bot = None
            if self.enabled:
                logger.warning("⚠️ Telegram enabled but TOKEN is missing!")

    async def send_message_async(self, text: str):
        if not self.enabled or not self.bot or not CHAT_ID:
            logger.debug("Telegram bridge disabled or not configured.")
            return
        
        try:
            await self.bot.send_message(chat_id=CHAT_ID, text=text)
            logger.info("📩 Message sent to Telegram.")
        except Exception as e:
            logger.error(f"❌ Failed to send Telegram message: {e}")

    def send_message(self, text: str):
        """Synchronous wrapper for async send_message"""
        if not self.enabled: return
        try:
            loop = asyncio.get_event_loop()
            if loop.is_running():
                # In a running loop (like FastAPI), we need to create a task
                asyncio.create_task(self.send_message_async(text))
            else:
                loop.run_until_complete(self.send_message_async(text))
        except Exception as e:
            # Fallback for when loop is not established
            asyncio.run(self.send_message_async(text))

# Singleton
_bridge = None
def get_telegram_bridge():
    global _bridge
    if _bridge is None:
        _bridge = TelegramBridge()
    return _bridge

async def start_handler(update, context):
    await update.message.reply_text(f"🤖 Ziva Orchestrator Online.\nNode: {os.getenv('NODE_ID')}\nRole: {os.getenv('NODE_ROLE')}")

async def status_handler(update, context):
    # This would ideally call the Overseer
    await update.message.reply_text("📊 Status request received. Analyzing vitals...")

def run_bot():
    """Starts the persistent bot listener"""
    if not ENABLED or not TOKEN:
        print("Telegram bot listener disabled.")
        return

    app = ApplicationBuilder().token(TOKEN).build()
    app.add_handler(CommandHandler("start", start_handler))
    app.add_handler(CommandHandler("status", status_handler))
    
    print("🚀 Telegram Bot Listener started...")
    app.run_polling()

if __name__ == "__main__":
    run_bot()
