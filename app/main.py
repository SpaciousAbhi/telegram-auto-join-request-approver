from __future__ import annotations

import asyncio
import logging
from typing import Any, Awaitable, Callable

from aiogram import Bot, Dispatcher
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode
from aiogram.fsm.storage.memory import MemoryStorage
from aiogram.types import BotCommand, ChatAdministratorRights, TelegramObject
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
    default_rights = ChatAdministratorRights(
        is_anonymous=False,
        can_manage_chat=True,
        can_delete_messages=False,
        can_manage_video_chats=False,
        can_restrict_members=False,
        can_promote_members=False,
        can_change_info=False,
        can_invite_users=True,
        can_post_stories=False,
        can_edit_stories=False,
        can_delete_stories=False,
        can_post_messages=False,
        can_edit_messages=False,
        can_pin_messages=False,
        can_manage_topics=False,
    )
    try:
        await bot.set_my_default_administrator_rights(default_rights, for_channels=True)
        await bot.set_my_default_administrator_rights(default_rights, for_channels=False)
    except Exception as exc:
        await db.log_event("startup_warning", "Could not set default admin rights", {"error": str(exc)}, "warning")
    await bot.set_my_commands(
        [
            BotCommand(command="start", description="Open main menu"),
            BotCommand(command="owner", description="Owner control panel"),
        ]
    )
    await bot.delete_webhook(drop_pending_updates=False)
    allowed_updates = set(dp.resolve_used_update_types())
    allowed_updates.update({"chat_join_request", "my_chat_member", "callback_query", "message"})
    await db.log_event("startup", "Bot worker started", {"allowed_updates": sorted(allowed_updates)})
    await dp.start_polling(bot, allowed_updates=sorted(allowed_updates))


if __name__ == "__main__":
    asyncio.run(main())
