"""
Application entry point.
Handles startup, shutdown, background tasks, and graceful cleanup.
"""
from __future__ import annotations

import asyncio
import logging
import signal
import sys
from typing import Set

from aiogram import Bot, Dispatcher
from aiogram.fsm.storage.redis import RedisStorage

from bot.config.settings import get_settings
from bot.db.engine import init_db, close_db
from bot.cache.redis_client import get_redis, close_redis
from bot.handlers import register_all_routers
from bot.middlewares.rate_limit import RateLimitMiddleware
from bot.middlewares.auth import AuthMiddleware
from bot.middlewares.anti_abuse import AntiAbuseMiddleware
from bot.tasks.expiry_checker import (
    check_expiring_subscriptions,
    cleanup_expired_clients,
)
from bot.tasks.payment_poller import check_crypto_payments
from bot.tasks.health import start_health_server
from bot.vpn.xui_client import XUIClient

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)-7s | %(name)s | %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
logger = logging.getLogger(__name__)

settings = get_settings()
background_tasks: Set[asyncio.Task] = set()


async def on_startup(bot: Bot, xui: XUIClient) -> None:
    """Initialize all services on startup."""
    # Database
    await init_db()
    logger.info("✅ Database initialized")

    # Redis
    redis = await get_redis()
    await redis.ping()
    logger.info("✅ Redis connected")

    # 3x-ui Panel
    if settings.xui_base_url:
        success = await xui.init(
            settings.xui_base_url,
            settings.xui_username,
            settings.xui_password.get_secret_value(),
            settings.subscription_domain,
        )
        if success:
            logger.info("✅ 3x-ui panel connected")
        else:
            logger.warning("⚠️ 3x-ui panel connection failed")

    # Health endpoint
    await start_health_server()

    # Background tasks
    tasks = [
        check_expiring_subscriptions(bot),
        check_crypto_payments(bot, xui),
        cleanup_expired_clients(bot),
    ]
    for coro in tasks:
        task = asyncio.create_task(coro)
        background_tasks.add(task)
        task.add_done_callback(background_tasks.discard)

    logger.info("🚀 Bot started with %d background tasks", len(tasks))


async def on_shutdown(xui: XUIClient) -> None:
    """Graceful shutdown."""
    logger.info("🛑 Shutting down...")

    # Cancel background tasks
    for task in background_tasks:
        task.cancel()
    if background_tasks:
        await asyncio.gather(*background_tasks, return_exceptions=True)

    # Close connections
    await xui.close()
    await close_redis()
    await close_db()
    logger.info("✅ Cleanup complete")


async def main() -> None:
    # FSM storage via Redis
    storage = RedisStorage.from_url(settings.redis_url)

    bot = Bot(token=settings.bot_token.get_secret_value())
    dp = Dispatcher(storage=storage)
    xui = XUIClient()

    # Register middleware stack (order matters)
    dp.message.middleware(AntiAbuseMiddleware())
    dp.message.middleware(RateLimitMiddleware())
    dp.message.middleware(AuthMiddleware())
    dp.callback_query.middleware(RateLimitMiddleware())
    dp.callback_query.middleware(AuthMiddleware())

    # Register handlers
    register_all_routers(dp)

    # Lifecycle
    await on_startup(bot, xui)

    try:
        if settings.webhook_url:
            # Webhook mode for production
            from aiogram.webhook.aiohttp_server import (
                SimpleRequestHandler,
                setup_application,
            )
            from aiohttp import web

            await bot.set_webhook(
                settings.webhook_url,
                secret_token=settings.webhook_secret.get_secret_value(),
            )
            app = web.Application()
            handler = SimpleRequestHandler(
                dispatcher=dp,
                bot=bot,
                secret_token=settings.webhook_secret.get_secret_value(),
            )
            handler.register(app, path="/webhook")
            setup_application(app, dp)

            runner = web.AppRunner(app)
            await runner.setup()
            site = web.TCPSite(runner, "0.0.0.0", 8443)
            await site.start()
            logger.info("🌐 Webhook mode on port 8443")
            await asyncio.Event().wait()
        else:
            # Polling mode for development
            logger.info("🔄 Polling mode")
            await dp.start_polling(bot)
    finally:
        await on_shutdown(xui)
        await bot.session.close()


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except (KeyboardInterrupt, SystemExit):
        logger.info("Bot stopped")
