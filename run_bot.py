import asyncio
import logging
from backend.bot import dp, bot

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def main():
    logger.info("Starting isolated bot...")
    try:
        await dp.start_polling(bot, skip_updates=True)
    except Exception as e:
        logger.error(f"Bot failed: {e}")
    finally:
        await bot.session.close()

if __name__ == "__main__":
    asyncio.run(main())
