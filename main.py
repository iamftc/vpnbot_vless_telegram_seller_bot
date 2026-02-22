"""
Точка входа приложения
"""
import asyncio
import logging
import sys
from pathlib import Path

from aiogram import Bot, Dispatcher
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode
from aiogram.webhook.aiohttp_server import SimpleRequestHandler, setup_application

from bot.config import settings
from bot.db.database import db
from bot.vpn.xui_api import xui
from bot.payments.cryptobot import crypto_bot
from bot.middlewares.auth_middleware import AuthMiddleware, MaintenanceMiddleware
from bot.tasks.subscription_checker import check_expiring_subscriptions
from bot.tasks.payment_checker import check_crypto_payments

# Импорт роутеров
from bot.handlers.common.start import router as start_router
# from bot.handlers.user import ... (другие роутеры)

# Настройка логирования
logging.basicConfig(
    level=settings.LOG_LEVEL,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(settings.LOG_FILE),
        logging.StreamHandler(sys.stdout)
    ]
)

logger = logging.getLogger(__name__)


async def on_startup(bot: Bot):
    """Инициализация при запуске"""
    logger.info("🚀 Бот запускается...")
    
    # Подключение к БД
    await db.connect()
    await db.create_tables()
    
    # Инициализация 3x-ui
    api_success = await xui.init(
        settings.XUI_BASE_URL,
        settings.XUI_USERNAME,
        settings.XUI_PASSWORD,
        settings.DEFAULT_SUB_DOMAIN
    )
    
    if api_success:
        logger.info("✅ 3x-ui API инициализировано")
    else:
        logger.warning("⚠️ 3x-ui API не удалось инициализировать")
    
    # Настройка webhook (если URL указан)
    if settings.BOT_WEBHOOK_URL:
        await bot.set_webhook(
            settings.BOT_WEBHOOK_URL,
            secret_token=settings.BOT_WEBHOOK_SECRET
        )
        logger.info(f"🔗 Webhook установлен: {settings.BOT_WEBHOOK_URL}")
    else:
        await bot.delete_webhook()
        logger.info("🔗 Webhook удалён (polling mode)")
    
    # Запуск фоновых задач
    asyncio.create_task(check_expiring_subscriptions(bot))
    asyncio.create_task(check_crypto_payments(bot))
    
    logger.info("✅ Бот готов к работе")


async def on_shutdown(bot: Bot):
    """Очистка при остановке"""
    logger.info("🛑 Бот останавливается...")
    
    await xui.close()
    await crypto_bot.close()
    await db.disconnect()
    
    if settings.BOT_WEBHOOK_URL:
        await bot.delete_webhook()
    
    logger.info("✅ Бот остановлен")


def create_dispatcher() -> Dispatcher:
    """Создание диспетчера с middleware"""
    dp = Dispatcher()
    
    # Middleware
    dp.message.middleware(AuthMiddleware())
    dp.message.middleware(MaintenanceMiddleware())
    dp.callback_query.middleware(AuthMiddleware())
    dp.callback_query.middleware(MaintenanceMiddleware())
    
    # Регистрация роутеров
    dp.include_router(start_router)
    # dp.include_router(other_routers...)
    
    return dp


async def main():
    """Основная функция"""
    bot = Bot(
        token=settings.BOT_TOKEN,
        default=DefaultBotProperties(parse_mode=ParseMode.MARKDOWN)
    )
    
    dp = create_dispatcher()
    
    # Регистрация хендлеров жизненного цикла
    dp.startup.register(on_startup)
    dp.shutdown.register(on_shutdown)
    
    try:
        if settings.BOT_WEBHOOK_URL:
            # Webhook mode
            from aiohttp import web
            
            app = web.Application()
            webhook_requests_handler = SimpleRequestHandler(
                dispatcher=dp,
                bot=bot,
                secret_token=settings.BOT_WEBHOOK_SECRET
            )
            webhook_requests_handler.register(app, path="/webhook")
            
            setup_application(app, dp, bot=bot)
            
            runner = web.AppRunner(app)
            await runner.setup()
            site = web.TCPSite(runner, "0.0.0.0", 8080)
            await site.start()
            
            logger.info("🌐 Сервер запущен на порту 8080")
            
            # Держим приложение запущенным
            while True:
                await asyncio.sleep(3600)
        else:
            # Polling mode
            await dp.start_polling(bot)
    
    except KeyboardInterrupt:
        logger.info("👋 Получен сигнал остановки")
    finally:
        await bot.session.close()


if __name__ == "__main__":
    asyncio.run(main())