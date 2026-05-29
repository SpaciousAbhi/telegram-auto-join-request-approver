from __future__ import annotations

import re
from dataclasses import dataclass
from datetime import UTC, datetime, timedelta
from typing import Any
from urllib.parse import quote_plus

from aiogram import Bot
from aiogram.exceptions import TelegramRetryAfter
from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup

from app.i18n import t
from app.services.telegram import approve_join_request, can_approve_in_chat


APPROVAL_RETRY_STATUSES = {
    "pending",
    "awaiting_verification",
    "verification_dm_failed",
    "approval_retry",
    "permission_error",
    "failed",
}
VERIFICATION_RETRY_STATUSES = {"pending", "verification_dm_failed"}
OPEN_CHANNEL_BUTTON = "Open the Channel"


@dataclass
class ApprovalRunResult:
    status: str
    ok: bool
    error: str | None = None
    retryable: bool = False


def utcnow() -> datetime:
    return datetime.now(UTC)


def _retry_after_seconds(error: str | None) -> int | None:
    if not error:
        return None
    match = re.search(r"retry_after=(\d+)", error)
    if match:
        return int(match.group(1)) + 1
    return None


def retry_delay_for(item: dict[str, Any], error: str | None = None, permission: bool = False) -> timedelta:
    retry_after = _retry_after_seconds(error)
    if retry_after is not None:
        return timedelta(seconds=max(1, retry_after))
    attempts = int(item.get("approval_attempts") or 0)
    if permission:
        return timedelta(minutes=5)
    if attempts <= 1:
        return timedelta(seconds=15)
    if attempts == 2:
        return timedelta(minutes=1)
    if attempts == 3:
        return timedelta(minutes=3)
    if attempts == 4:
        return timedelta(minutes=10)
    return timedelta(minutes=30)


def is_terminal_approval_error(error: str | None) -> bool:
    if not error:
        return False
    lowered = error.lower()
    terminal_tokens = (
        "hide_requester_missing",
        "requester_missing",
        "participant_join_request_missing",
        "join request not found",
        "request not found",
        "user_id_invalid",
        "user not found",
    )
    return any(token in lowered for token in terminal_tokens)


def is_permission_error(error: str | None) -> bool:
    if not error:
        return False
    lowered = error.lower()
    permission_tokens = (
        "chat_admin_required",
        "not enough rights",
        "have no rights",
        "need administrator",
        "bot is not admin",
        "bot is not a member",
        "missing permissions",
    )
    return any(token in lowered for token in permission_tokens)


def _chat_url_from_username(username: str | None) -> str | None:
    if not username:
        return None
    return f"https://t.me/{quote_plus(username.lstrip('@'))}"


async def open_channel_link(bot: Bot, db: Any, item: dict[str, Any]) -> tuple[str | None, str | None]:
    chat_id = int(item["chat_id"])
    user_id = int(item["user_id"])
    chat = await db.chat(chat_id) or {}
    username_link = _chat_url_from_username(chat.get("username") or item.get("chat_username"))
    if username_link:
        return username_link, None
    try:
        invite = await bot.create_chat_invite_link(
            chat_id=chat_id,
            name=f"Open Channel {user_id}",
        )
        return invite.invite_link, None
    except Exception as exc:
        create_error = str(exc)
    try:
        exported = await bot.export_chat_invite_link(chat_id=chat_id)
        return exported, create_error
    except Exception as exc:
        fallback = item.get("open_channel_link") or chat.get("invite_link") or item.get("invite_link")
        if fallback:
            return fallback, f"{create_error}; export failed: {exc}"
        return None, f"{create_error}; export failed: {exc}"


async def approval_notification_markup(bot: Bot, db: Any, item: dict[str, Any]) -> tuple[InlineKeyboardMarkup | None, str | None, str | None]:
    link, error = await open_channel_link(bot, db, item)
    if not link:
        return None, None, error
    markup = InlineKeyboardMarkup(inline_keyboard=[[InlineKeyboardButton(text=OPEN_CHANNEL_BUTTON, url=link)]])
    return markup, link, error


def _notification_target(item: dict[str, Any]) -> int:
    return int(item.get("user_chat_id") or item["user_id"])


def _notification_retry_at(item: dict[str, Any], error: str | None) -> datetime | None:
    lowered = (error or "").lower()
    if "bot was blocked" in lowered or "user is deactivated" in lowered or "chat not found" in lowered:
        return None
    attempts = int(item.get("notify_attempts") or 0)
    delay = timedelta(minutes=1 if attempts <= 1 else 5 if attempts <= 3 else 30)
    return utcnow() + delay


async def send_acceptance_notification(bot: Bot, db: Any, item: dict[str, Any], source: str, lang: str = "en") -> bool:
    user_doc = await db.user(item["user_id"]) if hasattr(db, "user") else None
    if not isinstance(user_doc, dict):
        user_doc = {}
    lang = (user_doc or {}).get("language") or lang
    markup, link, link_error = await approval_notification_markup(bot, db, item)
    if not markup:
        retry_at = _notification_retry_at(item, link_error)
        await db.mark_notification(item["chat_id"], item["user_id"], "retry" if retry_at else "failed", link_error, retry_at)
        await db.log_event(
            "acceptance_notification_error",
            "Open Channel link could not be created",
            {"chat_id": item["chat_id"], "user_id": item["user_id"], "error": link_error, "source": source},
            "warning" if retry_at else "error",
        )
        return False
    try:
        await bot.send_message(_notification_target(item), t(lang, "verified"), reply_markup=markup)
        await db.mark_notification(item["chat_id"], item["user_id"], "sent", link=link)
        severity = "warning" if link_error else "info"
        await db.log_event(
            "acceptance_notification_sent",
            "Acceptance notification sent with Open Channel button",
            {"chat_id": item["chat_id"], "user_id": item["user_id"], "source": source, "link_warning": link_error},
            severity,
        )
        return True
    except TelegramRetryAfter as exc:
        retry_at = utcnow() + timedelta(seconds=exc.retry_after + 1)
        error = f"TelegramRetryAfter: retry_after={exc.retry_after}"
    except Exception as exc:
        error = str(exc)
        retry_at = _notification_retry_at(item, error)
    status = "retry" if retry_at else "failed"
    await db.mark_notification(item["chat_id"], item["user_id"], status, error, retry_at, link=link)
    await db.log_event(
        "acceptance_notification_error",
        "Acceptance notification could not be delivered",
        {"chat_id": item["chat_id"], "user_id": item["user_id"], "error": error, "source": source},
        "warning" if retry_at else "error",
    )
    return False


async def retry_acceptance_notifications(bot: Bot, db: Any, limit: int = 100) -> None:
    for item in await db.due_notification_requests(limit=limit):
        await send_acceptance_notification(bot, db, item, "notification_retry")


async def approve_stored_request(
    bot: Bot,
    db: Any,
    item: dict[str, Any],
    source: str,
    notify_user: bool = True,
    claim: bool = True,
    permission_cache: dict[int, tuple[bool, str | None]] | None = None,
) -> ApprovalRunResult:
    chat_id = int(item["chat_id"])
    user_id = int(item["user_id"])
    if claim:
        claimed = await db.claim_request_for_approval(chat_id, user_id)
        if not claimed:
            return ApprovalRunResult("locked", False, "Request is locked by another worker.", True)
        item = claimed

    connected_chat = await db.chat(chat_id)
    if connected_chat and connected_chat.get("removed_by_owner"):
        error = "Connected chat was deactivated by owner."
        await db.mark_request(chat_id, user_id, "chat_deactivated_by_owner", error)
        await db.log_event(
            "approval_skipped",
            "Approval skipped because chat is deactivated",
            {"chat_id": chat_id, "user_id": user_id, "source": source, "error": error},
            "warning",
        )
        return ApprovalRunResult("chat_deactivated_by_owner", False, error, False)

    if permission_cache is not None and chat_id in permission_cache:
        can_approve, permission_error = permission_cache[chat_id]
    else:
        can_approve, permission_error = await can_approve_in_chat(bot, chat_id)
        if permission_cache is not None:
            permission_cache[chat_id] = (can_approve, permission_error)
    if not can_approve:
        retry_at = utcnow() + retry_delay_for(item, permission_error, permission=True)
        await db.schedule_request_retry(chat_id, user_id, "permission_error", permission_error, retry_at)
        if connected_chat and is_permission_error(permission_error):
            await db.mark_chat_inactive(chat_id, permission_error or "Missing approve permission")
        await db.log_event(
            "approval_retry_scheduled",
            "Approval delayed until bot permissions are fixed",
            {"chat_id": chat_id, "user_id": user_id, "retry_at": retry_at.isoformat(), "source": source, "error": permission_error},
            "error",
        )
        return ApprovalRunResult("permission_error", False, permission_error, True)

    ok, error = await approve_join_request(bot, chat_id, user_id)
    if ok:
        await db.mark_request(chat_id, user_id, "approved")
        await db.record_approval(chat_id, True)
        await db.log_event(
            "approval",
            "Join request approved",
            {"chat_id": chat_id, "user_id": user_id, "source": source},
            "info",
        )
        if notify_user:
            await send_acceptance_notification(bot, db, item, source)
        return ApprovalRunResult("approved", True)

    if is_terminal_approval_error(error):
        await db.mark_request(chat_id, user_id, "skipped", error)
        await db.record_approval(chat_id, False)
        await db.log_event(
            "approval_terminal",
            "Join request could not be approved because Telegram no longer exposes it",
            {"chat_id": chat_id, "user_id": user_id, "source": source, "error": error},
            "warning",
        )
        return ApprovalRunResult("skipped", False, error, False)

    retry_at = utcnow() + retry_delay_for(item, error, permission=is_permission_error(error))
    retry_status = "permission_error" if is_permission_error(error) else "approval_retry"
    await db.schedule_request_retry(chat_id, user_id, retry_status, error, retry_at)
    await db.log_event(
        "approval_retry_scheduled",
        "Join request approval failed and will be retried",
        {"chat_id": chat_id, "user_id": user_id, "retry_at": retry_at.isoformat(), "source": source, "error": error},
        "warning",
    )
    return ApprovalRunResult(retry_status, False, error, True)
