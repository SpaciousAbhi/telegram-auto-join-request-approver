from __future__ import annotations

import asyncio
from dataclasses import dataclass
from typing import Any

from aiogram import Bot
from aiogram.exceptions import TelegramBadRequest, TelegramForbiddenError, TelegramRetryAfter

from app.constants import REQUIRED_ADMIN_RIGHTS


async def safe_answer(callback: Any, text: str | None = None, show_alert: bool = False) -> None:
    try:
        await callback.answer(text or "", show_alert=show_alert)
    except TelegramBadRequest as exc:
        if "query is too old" not in str(exc).lower() and "query id is invalid" not in str(exc).lower():
            raise


async def safe_edit(message: Any, text: str, reply_markup: Any = None) -> None:
    try:
        await message.edit_text(text, reply_markup=reply_markup, disable_web_page_preview=True)
    except TelegramBadRequest as exc:
        if "message is not modified" not in str(exc).lower():
            await message.answer(text, reply_markup=reply_markup, disable_web_page_preview=True)


def member_status_value(member: Any) -> str:
    status = getattr(member, "status", "")
    return getattr(status, "value", status)


def is_joined_member(member: Any) -> bool:
    status = member_status_value(member)
    if status in {"creator", "administrator", "member"}:
        return True
    if status == "restricted" and bool(getattr(member, "is_member", False)):
        return True
    return False


async def approve_join_request(bot: Bot, chat_id: int, user_id: int) -> tuple[bool, str | None]:
    while True:
        try:
            await bot.approve_chat_join_request(chat_id=chat_id, user_id=user_id)
            return True, None
        except TelegramRetryAfter as exc:
            await asyncio.sleep(exc.retry_after + 1)
        except (TelegramBadRequest, TelegramForbiddenError) as exc:
            err_msg = str(exc)
            if "user_already_participant" in err_msg.lower():
                return True, None
            return False, err_msg


@dataclass
class PermissionReport:
    is_admin: bool
    ok: bool
    missing: list[str]
    status: str


async def inspect_bot_permissions(bot: Bot, chat_id: int, bot_id: int) -> PermissionReport:
    try:
        member = await bot.get_chat_member(chat_id=chat_id, user_id=bot_id)
    except (TelegramBadRequest, TelegramForbiddenError) as exc:
        return PermissionReport(False, False, REQUIRED_ADMIN_RIGHTS, str(exc))

    status = member_status_value(member)
    is_admin = status in {"administrator", "creator"}
    missing = []
    for right in REQUIRED_ADMIN_RIGHTS:
        if not getattr(member, right, False):
            missing.append(right)
    return PermissionReport(is_admin, is_admin and not missing, missing, status)


async def can_approve_in_chat(bot: Bot, chat_id: int) -> tuple[bool, str | None]:
    me = await bot.get_me()
    report = await inspect_bot_permissions(bot, chat_id, me.id)
    if not report.is_admin:
        return False, "Bot is not admin in this chat."
    if report.missing:
        return False, "Missing permissions: " + ", ".join(report.missing)
    return True, None


async def force_target_completed(bot: Bot, db: Any, user_id: int, target: dict) -> tuple[bool, str | None]:
    if target.get("mode") == "request" and await db.has_join_request_mark(user_id, target["chat_id"]):
        return True, None
    try:
        member = await bot.get_chat_member(chat_id=target["chat_id"], user_id=user_id)
        if is_joined_member(member):
            return True, None
        return False, None
    except (TelegramBadRequest, TelegramForbiddenError) as exc:
        return False, str(exc)
