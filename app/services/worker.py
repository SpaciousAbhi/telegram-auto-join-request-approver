from __future__ import annotations

import asyncio
import logging
from datetime import timedelta

from aiogram import Bot

from app.db import Database
from app.keyboards import robot_keyboard
from app.services.approval import (
    APPROVAL_RETRY_STATUSES,
    VERIFICATION_RETRY_STATUSES,
    approve_stored_request,
    retry_acceptance_notifications,
    utcnow,
)
from app.ui import render_verification_request_text

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
    await retry_acceptance_notifications(bot, db)

    if not verification_enabled:
        items = await db.due_approval_requests(APPROVAL_RETRY_STATUSES, limit=200)

        if items:
            logger.info("Background worker: found %s requests due for approval.", len(items))

        permission_cache: dict[int, tuple[bool, str | None]] = {}
        for item in items:
            try:
                await approve_stored_request(
                    bot,
                    db,
                    item,
                    "background_worker",
                    notify_user=True,
                    permission_cache=permission_cache,
                )
                await asyncio.sleep(0.2)
            except Exception as exc:
                logger.error(f"Error processing background request {item.get('user_id')} for chat {item.get('chat_id')}: {exc}", exc_info=True)
                await db.log_event(
                    "background_worker_error",
                    "Background approval loop failed for one request",
                    {"chat_id": item.get("chat_id"), "user_id": item.get("user_id"), "error": str(exc)},
                    "error",
                )

    else:
        # 1. Process requests due for verification DM (VERIFICATION_RETRY_STATUSES = {"pending", "verification_dm_failed"})
        items_to_verify = await db.due_approval_requests(VERIFICATION_RETRY_STATUSES, limit=100)

        if items_to_verify:
            logger.info("Background worker: found %s requests due for verification DM.", len(items_to_verify))

        me = await bot.get_me()

        for item in items_to_verify:
            try:
                chat_id = item["chat_id"]
                user_id = item["user_id"]
                chat_title = item.get("chat_title") or f"Chat {chat_id}"
                user_chat_id = item.get("user_chat_id")
                claimed = await db.claim_request_for_approval(chat_id, user_id)
                if not claimed:
                    continue
                item = claimed

                connected_chat = await db.chat(chat_id)
                if connected_chat and connected_chat.get("removed_by_owner"):
                    await db.mark_request(chat_id, user_id, "chat_deactivated_by_owner")
                    continue

                payload = f"verify_{chat_id}_{user_id}"
                text = render_verification_request_text(chat_title)
                lang = ((await db.user(user_id)) or {}).get("language") or "en"
                try:
                    await bot.send_message(user_chat_id or user_id, text, reply_markup=robot_keyboard(me.username, payload, lang))
                    await db.mark_request(chat_id, user_id, "awaiting_verification")
                    await db.log_event(
                        "background_verification_sent",
                        f"Background verification sent: {chat_title}",
                        {"chat_id": chat_id, "user_id": user_id}
                    )
                except Exception as exc:
                    # Fallback to immediate approval if DM fails to send in background
                    await db.log_event(
                        "background_verification_dm_failed_fallback",
                        f"Background verification DM failed, approving directly: {chat_title}",
                        {"chat_id": chat_id, "user_id": user_id, "error": str(exc)},
                        "warning",
                    )
                    await approve_stored_request(
                        bot,
                        db,
                        item,
                        "background_worker_verification_fallback",
                        notify_user=True,
                        claim=False,  # Already claimed!
                    )
                await asyncio.sleep(0.5)
            except Exception as exc:
                logger.error(f"Error sending verification DM to {item.get('user_id')} for chat {item.get('chat_id')}: {exc}", exc_info=True)
                await db.log_event(
                    "background_worker_error",
                    "Background verification loop failed for one request",
                    {"chat_id": item.get("chat_id"), "user_id": item.get("user_id"), "error": str(exc)},
                    "error",
                )

        # 2. Process timed-out awaiting_verification requests (older than 5 minutes)
        five_minutes_ago = utcnow() - timedelta(minutes=5)
        timed_out_query = {
            "status": "awaiting_verification",
            "updated_at": {"$lte": five_minutes_ago},
            "$or": [
                {"approval_locked_until": {"$exists": False}},
                {"approval_locked_until": None},
                {"approval_locked_until": {"$lte": utcnow()}},
            ]
        }
        timed_out_items = await db.db.pending_requests.find(timed_out_query).to_list(length=100)

        if timed_out_items:
            logger.info("Background worker: found %s timed-out awaiting_verification requests to auto-approve.", len(timed_out_items))

        for item in timed_out_items:
            try:
                await approve_stored_request(
                    bot,
                    db,
                    item,
                    "background_worker_verification_timeout",
                    notify_user=True,
                    claim=True,
                )
                await asyncio.sleep(0.2)
            except Exception as exc:
                logger.error(f"Error auto-approving timed out request {item.get('user_id')} for chat {item.get('chat_id')}: {exc}", exc_info=True)
                await db.log_event(
                    "background_worker_error",
                    "Background timeout approval loop failed for one request",
                    {"chat_id": item.get("chat_id"), "user_id": item.get("user_id"), "error": str(exc)},
                    "error",
                )

        # 3. Process requests in {"approval_retry", "permission_error", "failed"} that are due for retry
        retry_items = await db.due_approval_requests({"approval_retry", "permission_error", "failed"}, limit=100)

        if retry_items:
            logger.info("Background worker: found %s requests due for approval retry.", len(retry_items))

        permission_cache: dict[int, tuple[bool, str | None]] = {}
        for item in retry_items:
            try:
                await approve_stored_request(
                    bot,
                    db,
                    item,
                    "background_worker_retry",
                    notify_user=True,
                    claim=True,
                    permission_cache=permission_cache,
                )
                await asyncio.sleep(0.2)
            except Exception as exc:
                logger.error(f"Error retrying background approval for request {item.get('user_id')} for chat {item.get('chat_id')}: {exc}", exc_info=True)
                await db.log_event(
                    "background_worker_error",
                    "Background approval retry loop failed for one request",
                    {"chat_id": item.get("chat_id"), "user_id": item.get("user_id"), "error": str(exc)},
                    "error",
                )
