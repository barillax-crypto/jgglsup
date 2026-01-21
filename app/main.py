"""Main bot entry point."""

import asyncio
import logging
from aiogram import Bot, Dispatcher
from aiogram.fsm.storage.memory import MemoryStorage

from app.config import Config
from app.handlers import router

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)


async def main() -> None:
    """Run the bot."""
    # Validate config
    Config.validate()
    Config.ensure_dirs()

    logger.info("Starting crypto exchange onboarding bot...")
    logger.info(f"Chat model: {Config.OR_CHAT_MODEL}")
    logger.info(f"Embed model: {Config.OR_EMBED_MODEL}")
    logger.info(f"Vector store: {Config.CHROMA_PERSIST_DIR}")
    logger.info(f"Docs directory: {Config.DOCS_DIR}")

    # Initialize bot
    bot = Bot(token=Config.TELEGRAM_BOT_TOKEN)
    storage = MemoryStorage()
    dp = Dispatcher(storage=storage)

    # Register handlers
    dp.include_router(router)

    logger.info("Bot started. Polling for messages...")

    try:
        await dp.start_polling(bot)
    except Exception as e:
        logger.error(f"Bot error: {e}")
    finally:
        await bot.session.close()


if __name__ == "__main__":
    asyncio.run(main())
