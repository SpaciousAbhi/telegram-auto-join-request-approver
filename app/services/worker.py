from __future__ import annotations

import asyncio
import logging
from datetime import UTC, datetime, timedelta

from aiogram import Bot

from app.db import Database
from app.keyboards import robot_keyboard
from app.services.telegram import approve_join_request, can_approve_in_chat

logger = logging.getLogger(__name__)


async def worker_loop(bot: Bot, db: Database) -> None:
    logger.info("Background worker loop started.")
    # Wait a bit after startup to avoid overlapping with initial resume tasks
    await asyncio.sleep(10)
    while True:
        try:
            await process_pending_requests(bot, db)
        except Exception as exc:
            logger.error(f"Error in background worker process_pending_requests: {exc}", exc_info=True)
        await asyncio.sleep(30)


async def process_pending_requests(bot: Bot, db: Database) -> None:
    settings = await db.settings()
    verification_enabled = bool(settings.get("verification_enabled", False))
    now_utc = datetime.now(UTC)

    if not verification_enabled:
        # 1. Verification is DISABLED:
        # We find any requests with status "pending", "awaiting_verification", "verification_dm_failed".
        # We also find requests with status "failed" or "permission_error" updated more than 5 minutes ago to retry them.
        five_minutes_ago = now_utc - timedelta(minutes=5)
        query = {
            "$or": [
                {"status": {"$in": ["pending", "awaiting_verification", "verification_dm_failed"]}},
                {"status": {"$in": ["failed", "permission_error"]}, "updated_at": {"$lt": five_minutes_ago}}
            ]
        }
        cursor = db.db.pending_requests.find(query)
        items = await cursor.to_list(length=100)  # batch of 100 per cycle

        if items:
            logger.info(f"Background worker: found {len(items)} requests to approve immediately.")

        for item in items:
            try:
                chat_id = item["chat_id"]
                user_id = item["user_id"]
                
                connected_chat = await db.chat(chat_id)
                if connected_chat and connected_chat.get("removed_by_owner"):
                    await db.mark_request(chat_id, user_id, "chat_deactivated_by_owner")
                    continue

                can_approve, permission_error = await can_approve_in_chat(bot, chat_id)
                if not can_approve:
                    await db.mark_request(chat_id, user_id, "permission_error", permission_error)
                    continue

                ok, error = await approve_join_request(bot, chat_id, user_id)
                await db.mark_request(chat_id, user_id, "approved" if ok else "failed", error)
                await db.record_approval(chat_id, ok)
                await db.log_event(
                    "background_approval",
                    f"Background {'Approved' if ok else 'Approval failed'}: {item.get('chat_title') or chat_id}",
                    {"chat_id": chat_id, "user_id": user_id, "error": error},
                    "info" if ok else "error",
                )
                await asyncio.sleep(0.2)
            except Exception as exc:
                logger.error(f"Error processing background request {item.get('user_id')} for chat {item.get('chat_id')}: {exc}", exc_info=True)

    else:
        # 2. Verification is ENABLED:
        # - Any requests with status "pending": try to send verification DM.
        # - Any requests with status "verification_dm_failed" updated more than 10 minutes ago: retry sending DM.
        pending_query = {"status": "pending"}
        pending_items = await db.db.pending_requests.find(pending_query).to_list(length=50)

        ten_minutes_ago = now_utc - timedelta(minutes=10)
        dm_failed_query = {"status": "verification_dm_failed", "updated_at": {"$lt": ten_minutes_ago}}
        failed_items = await db.db.pending_requests.find(dm_failed_query).to_list(length=50)

        items_to_verify = []
        for item in pending_items:
            items_to_verify.append((item, False))
        for item in failed_items:
            items_to_verify.append((item, True))

        if items_to_verify:
            logger.info(f"Background worker: found {len(items_to_verify)} requests to send verification DMs.")

        me = await bot.get_me()

        for item, is_retry in items_to_verify:
            try:
                chat_id = item["chat_id"]
                user_id = item["user_id"]
                chat_title = item.get("chat_title") or f"Chat {chat_id}"
                user_chat_id = item.get("user_chat_id")

                connected_chat = await db.chat(chat_id)
                if connected_chat and connected_chat.get("removed_by_owner"):
                    await db.mark_request(chat_id, user_id, "chat_deactivated_by_owner")
                    continue

                payload = f"verify_{chat_id}_{user_id}"
                text = (
                    f"𝗛𝗲𝗹𝗹𝗼, 𝘆𝗼𝘂 𝗿𝗲𝗾𝘂𝗲𝘀𝘁𝗲𝗱 𝘁𝗼 𝗷𝗼𝗶𝗻 {chat_title}. "
                    "𝗣𝗹𝗲𝗮𝘀𝗲 𝗽𝗿𝗼𝘃𝗲 𝘆𝗼𝘂 𝗮𝗿𝗲 𝗻𝗼𝘁 𝗮 𝗿𝗼𝗯𝗼𝘁 𝘁𝗼 𝗴𝗲𝘁 𝗮𝗰𝗰𝗲𝘀𝘀."
                )
                try:
                    await bot.send_message(user_chat_id or user_id, text, reply_markup=robot_keyboard(me.username, payload))
                    await db.mark_request(chat_id, user_id, "awaiting_verification")
                    await db.log_event(
                        "background_verification_sent",
                        f"Background verification sent ({'retry' if is_retry else 'new'}): {chat_title}",
                        {"chat_id": chat_id, "user_id": user_id}
                    )
                except Exception as exc:
                    await db.mark_request(chat_id, user_id, "verification_dm_failed", str(exc))
                    if not is_retry:
                        await db.log_event(
                            "background_verification_error",
                            f"Background verification DM failed: {chat_title}",
                            {"chat_id": chat_id, "user_id": user_id, "error": str(exc)},
                            "error"
                        )
                await asyncio.sleep(0.5)
            except Exception as exc:
                logger.error(f"Error sending verification DM to {item.get('user_id')} for chat {item.get('chat_id')}: {exc}", exc_info=True)
