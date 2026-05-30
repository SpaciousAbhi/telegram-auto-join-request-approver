import pytest
from unittest.mock import AsyncMock, MagicMock
from bson import ObjectId
from app.services.bulk import BulkProgressUpdater
from app.services.worker import process_pending_requests

@pytest.mark.asyncio
async def test_bulk_progress_updater_with_message():
    message_obj = AsyncMock()
    updater = BulkProgressUpdater(bot=None, db=None, job_id="job123", message_obj=message_obj)
    job = {"_id": "job123", "total": 10, "approved": 2, "failed": 1, "skipped": 0, "status": "running"}
    await updater.update(job)
    assert message_obj.edit_text.called

@pytest.mark.asyncio
async def test_bulk_progress_updater_with_ids():
    bot = AsyncMock()
    updater = BulkProgressUpdater(bot=bot, db=None, job_id="job123", progress_chat_id=111, progress_message_id=222)
    job = {"_id": "job123", "total": 10, "approved": 2, "failed": 1, "skipped": 0, "status": "running"}
    await updater.update(job)
    assert bot.edit_message_text.called

@pytest.mark.asyncio
async def test_process_pending_requests_verification_disabled():
    bot = AsyncMock()
    bot.get_me = AsyncMock(return_value=MagicMock(id=1, username="test_bot"))
    bot.get_chat_member = AsyncMock(return_value=MagicMock(status="administrator", can_invite_users=True))
    bot.approve_chat_join_request = AsyncMock(return_value=True)

    db = AsyncMock()
    db.settings = AsyncMock(return_value={"verification_enabled": False})
    db.chat = AsyncMock(return_value={"active": True})
    db.due_notification_requests = AsyncMock(return_value=[])
    item = {
        "chat_id": 123,
        "user_id": 456,
        "chat_title": "Test Chat",
        "status": "pending",
        "approval_attempts": 0,
        "user_chat_id": 456,
    }
    db.due_approval_requests = AsyncMock(return_value=[item])
    db.claim_request_for_approval = AsyncMock(return_value={**item, "approval_attempts": 1})

    invite = MagicMock()
    invite.invite_link = "https://t.me/+fresh"
    bot.create_chat_invite_link = AsyncMock(return_value=invite)

    await process_pending_requests(bot, db)
    
    assert db.mark_request.called
    db.mark_request.assert_called_with(123, 456, "approved")


@pytest.mark.asyncio
async def test_process_pending_requests_verification_dm_fails_fallback():
    bot = AsyncMock()
    bot.get_me = AsyncMock(return_value=MagicMock(id=1, username="test_bot"))
    bot.get_chat_member = AsyncMock(return_value=MagicMock(status="administrator", can_invite_users=True))
    bot.approve_chat_join_request = AsyncMock(return_value=True)
    # Simulate DM failure
    bot.send_message = AsyncMock(side_effect=Exception("Blocked by user"))

    db = AsyncMock()
    db.settings = AsyncMock(return_value={"verification_enabled": True})
    db.chat = AsyncMock(return_value={"active": True})
    db.due_notification_requests = AsyncMock(return_value=[])
    
    item = {
        "chat_id": 123,
        "user_id": 456,
        "chat_title": "Test Chat",
        "status": "pending",
        "approval_attempts": 0,
        "user_chat_id": 456,
    }
    db.due_approval_requests = AsyncMock(return_value=[item])
    db.claim_request_for_approval = AsyncMock(return_value={**item, "approval_attempts": 1})
    
    # We mock find on db.db.pending_requests (for the timed-out query) to return empty list
    mock_cursor = AsyncMock()
    mock_cursor.to_list = AsyncMock(return_value=[])
    db.db.pending_requests.find = MagicMock(return_value=mock_cursor)

    invite = MagicMock()
    invite.invite_link = "https://t.me/+fresh"
    bot.create_chat_invite_link = AsyncMock(return_value=invite)

    await process_pending_requests(bot, db)
    
    # Verification fails, so it should fall back to immediate approval
    assert bot.approve_chat_join_request.called
    db.mark_request.assert_called_with(123, 456, "approved")


@pytest.mark.asyncio
async def test_process_pending_requests_awaiting_verification_timeout():
    bot = AsyncMock()
    bot.get_me = AsyncMock(return_value=MagicMock(id=1, username="test_bot"))
    bot.get_chat_member = AsyncMock(return_value=MagicMock(status="administrator", can_invite_users=True))
    bot.approve_chat_join_request = AsyncMock(return_value=True)

    db = AsyncMock()
    db.settings = AsyncMock(return_value={"verification_enabled": True})
    db.chat = AsyncMock(return_value={"active": True})
    db.due_notification_requests = AsyncMock(return_value=[])
    db.due_approval_requests = AsyncMock(return_value=[])
    
    item = {
        "chat_id": 123,
        "user_id": 456,
        "chat_title": "Test Chat",
        "status": "awaiting_verification",
        "approval_attempts": 0,
        "user_chat_id": 456,
    }
    db.claim_request_for_approval = AsyncMock(return_value={**item, "approval_attempts": 1})
    
    mock_cursor = AsyncMock()
    mock_cursor.to_list = AsyncMock(return_value=[item])
    db.db.pending_requests.find = MagicMock(return_value=mock_cursor)

    invite = MagicMock()
    invite.invite_link = "https://t.me/+fresh"
    bot.create_chat_invite_link = AsyncMock(return_value=invite)

    await process_pending_requests(bot, db)
    
    assert bot.approve_chat_join_request.called
    db.mark_request.assert_called_with(123, 456, "approved")
