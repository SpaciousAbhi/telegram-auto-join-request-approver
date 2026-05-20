from __future__ import annotations

import asyncio
import logging
from typing import Any, Awaitable, Callable

from aiogram import Bot, Dispatcher
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode
from aiogram.fsm.storage.memory import MemoryStorage
from aiogram.types import BotCommand, TelegramObject
from aiogram import BaseMiddleware

from app.config import get_settings
from app.db import Database
from app.routers import bulk, chat_events, chats, owner, settings, start
from app.services.bulk import BulkApprovalService


class DependencyMiddleware(BaseMiddleware):
    def __init__(self, **deps: Any):
        self.deps = deps

    async def __call__(
        self,
        handler: Callable[[TelegramObject, dict[str, Any]], Awaitable[Any]],
        event: TelegramObject,
        data: dict[str, Any],
    ) -> Any:
        data.update(self.deps)
        return await handler(event, data)


async def main() -> None:
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s: %(message)s")
    config = get_settings()
    db = Database(config.mongo_db_uri)
    await db.setup()
    bulk_service = BulkApprovalService(db)
    bot = Bot(config.bot_token, default=DefaultBotProperties(parse_mode=ParseMode.HTML))
    dp = Dispatcher(storage=MemoryStorage())
    dp.update.middleware(DependencyMiddleware(db=db, owner_id=config.owner_id, bulk_service=bulk_service))
    dp.include_router(start.router)
    dp.include_router(settings.router)
    dp.include_router(chats.router)
    dp.include_router(bulk.router)
    dp.include_router(owner.router)
    dp.include_router(chat_events.router)
    await bot.set_my_commands(
        [
            BotCommand(command="start", description="Open main menu"),
            BotCommand(command="owner", description="Owner control panel"),
        ]
    )
    await bot.delete_webhook(drop_pending_updates=False)
    await dp.start_polling(bot, allowed_updates=dp.resolve_used_update_types())


if __name__ == "__main__":
    asyncio.run(main())
