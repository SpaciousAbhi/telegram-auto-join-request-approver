from types import SimpleNamespace
from unittest.mock import AsyncMock, MagicMock

import pytest
from aiogram.exceptions import TelegramRetryAfter

from app.services.approval import approval_notification_markup, approve_stored_request


@pytest.mark.asyncio
async def test_approval_retry_after_is_persisted_for_restart_resume():
    bot = AsyncMock()
    bot.get_me = AsyncMock(return_value=MagicMock(id=1))
    bot.get_chat_member = AsyncMock(return_value=MagicMock(status="administrator", can_invite_users=True))
    bot.approve_chat_join_request = AsyncMock(
        side_effect=TelegramRetryAfter(method=None, message="Too many requests", retry_after=7)
    )

    item = {
        "chat_id": -100123,
        "user_id": 456,
        "status": "pending",
        "approval_attempts": 1,
    }
    db = AsyncMock()
    db.claim_request_for_approval = AsyncMock(return_value=item)
    db.chat = AsyncMock(return_value={"chat_id": -100123, "active": True})

    result = await approve_stored_request(bot, db, item, "test", notify_user=False)

    assert not result.ok
    assert result.retryable
    db.schedule_request_retry.assert_called_once()
    _, _, status, error, retry_at = db.schedule_request_retry.call_args.args
    assert status == "approval_retry"
    assert "retry_after=7" in error
    assert retry_at is not None
    db.mark_request.assert_not_called()


@pytest.mark.asyncio
async def test_open_channel_button_uses_fresh_non_expiring_invite_for_private_chat():
    bot = AsyncMock()
    bot.create_chat_invite_link = AsyncMock(return_value=SimpleNamespace(invite_link="https://t.me/+fresh-private-link"))
    db = AsyncMock()
    db.chat = AsyncMock(return_value={"chat_id": -100123, "title": "Private Channel", "username": None})
    item = {"chat_id": -100123, "user_id": 456}

    markup, link, error = await approval_notification_markup(bot, db, item)

    assert error is None
    assert link == "https://t.me/+fresh-private-link"
    button = markup.inline_keyboard[0][0]
    assert button.text == "Open the Channel"
    assert button.url == "https://t.me/+fresh-private-link"
    bot.create_chat_invite_link.assert_awaited_once()
