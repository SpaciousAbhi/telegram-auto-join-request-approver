from __future__ import annotations

from datetime import UTC, datetime, timedelta
from typing import Any

from motor.motor_asyncio import AsyncIOMotorClient, AsyncIOMotorDatabase
from pymongo import ASCENDING, DESCENDING, ReturnDocument

from app.constants import DEFAULT_SETTINGS


def now() -> datetime:
    return datetime.now(UTC)


class Database:
    def __init__(self, uri: str):
        self.client = AsyncIOMotorClient(uri)
        self.db: AsyncIOMotorDatabase = self.client.get_default_database(default="auto_join_request_bot")

    async def setup(self) -> None:
        await self.db.users.create_index([("user_id", ASCENDING)], unique=True)
        await self.db.connected_chats.create_index([("chat_id", ASCENDING)], unique=True)
        await self.db.connected_chats.create_index([("owner_id", ASCENDING)])
        await self.db.pending_requests.create_index([("chat_id", ASCENDING), ("user_id", ASCENDING)], unique=True)
        await self.db.force_chats.create_index([("chat_id", ASCENDING)], unique=True)
        await self.db.subscriber_trick_chats.create_index([("chat_id", ASCENDING)], unique=True)
        await self.db.join_request_marks.create_index([("user_id", ASCENDING), ("chat_id", ASCENDING)], unique=True)
        await self.db.bulk_jobs.create_index([("owner_id", ASCENDING), ("created_at", DESCENDING)])
        await self.db.broadcast_jobs.create_index([("created_at", DESCENDING)])
        await self.db.settings.update_one({"_id": "runtime"}, {"$setOnInsert": DEFAULT_SETTINGS}, upsert=True)

    async def settings(self) -> dict[str, Any]:
        doc = await self.db.settings.find_one({"_id": "runtime"}) or {}
        merged = {**DEFAULT_SETTINGS, **doc}
        merged.pop("_id", None)
        return merged

    async def set_setting(self, key: str, value: Any) -> None:
        await self.db.settings.update_one({"_id": "runtime"}, {"$set": {key: value}}, upsert=True)

    async def upsert_user(self, user: Any, language: str | None = None, verified: bool | None = None) -> None:
        data = {
            "user_id": user.id,
            "first_name": user.first_name,
            "last_name": user.last_name,
            "username": user.username,
            "is_bot": user.is_bot,
            "updated_at": now(),
        }
        if language:
            data["language"] = language
        if verified is not None:
            data["verified"] = verified
            if verified:
                data["verified_at"] = now()
        await self.db.users.update_one(
            {"user_id": user.id},
            {"$set": data, "$setOnInsert": {"created_at": now(), "banned": False}},
            upsert=True,
        )

    async def user(self, user_id: int) -> dict[str, Any] | None:
        return await self.db.users.find_one({"user_id": user_id})

    async def set_language(self, user_id: int, language: str) -> None:
        await self.db.users.update_one({"user_id": user_id}, {"$set": {"language": language, "updated_at": now()}}, upsert=True)

    async def upsert_connected_chat(self, data: dict[str, Any]) -> None:
        payload = {**data, "updated_at": now(), "active": data.get("active", True)}
        await self.db.connected_chats.update_one(
            {"chat_id": data["chat_id"]},
            {"$set": payload, "$setOnInsert": {"created_at": now(), "total_approved": 0, "failed_approvals": 0}},
            upsert=True,
        )

    async def chats_for_owner(self, owner_id: int) -> list[dict[str, Any]]:
        return await self.db.connected_chats.find({"owner_id": owner_id}).sort("updated_at", DESCENDING).to_list(length=200)

    async def chat(self, chat_id: int) -> dict[str, Any] | None:
        return await self.db.connected_chats.find_one({"chat_id": chat_id})

    async def mark_chat_inactive(self, chat_id: int, reason: str) -> None:
        await self.db.connected_chats.update_one({"chat_id": chat_id}, {"$set": {"active": False, "last_error": reason, "updated_at": now()}})

    async def add_pending_request(self, chat: Any, user: Any, invite_link: str | None = None) -> None:
        await self.db.pending_requests.update_one(
            {"chat_id": chat.id, "user_id": user.id},
            {
                "$set": {
                    "chat_id": chat.id,
                    "chat_title": chat.title,
                    "user_id": user.id,
                    "first_name": user.first_name,
                    "username": user.username,
                    "invite_link": invite_link,
                    "status": "pending",
                    "updated_at": now(),
                },
                "$setOnInsert": {"created_at": now()},
            },
            upsert=True,
        )

    async def mark_request(self, chat_id: int, user_id: int, status: str, error: str | None = None) -> None:
        update = {"status": status, "updated_at": now()}
        if error:
            update["error"] = error
        await self.db.pending_requests.update_one({"chat_id": chat_id, "user_id": user_id}, {"$set": update})

    async def pending_for_chat(self, chat_id: int, limit: int = 5000) -> list[dict[str, Any]]:
        return await self.db.pending_requests.find({"chat_id": chat_id, "status": "pending"}).sort("created_at", ASCENDING).to_list(length=limit)

    async def active_pending_for_user(self, chat_id: int, user_id: int) -> dict[str, Any] | None:
        return await self.db.pending_requests.find_one(
            {"chat_id": chat_id, "user_id": user_id, "status": {"$in": ["pending", "awaiting_verification", "verification_dm_failed"]}}
        )

    async def bulk_pending_for_chat(self, chat_id: int, limit: int = 5000) -> list[dict[str, Any]]:
        return await self.db.pending_requests.find(
            {"chat_id": chat_id, "status": {"$in": ["pending", "verification_dm_failed"]}}
        ).sort("created_at", ASCENDING).to_list(length=limit)

    async def record_approval(self, chat_id: int, success: bool) -> None:
        field = "total_approved" if success else "failed_approvals"
        await self.db.connected_chats.update_one({"chat_id": chat_id}, {"$inc": {field: 1}, "$set": {"updated_at": now()}})

    async def add_force_chat(self, data: dict[str, Any]) -> None:
        await self.db.force_chats.update_one(
            {"chat_id": data["chat_id"]},
            {"$set": {**data, "updated_at": now()}, "$setOnInsert": {"created_at": now(), "active": True}},
            upsert=True,
        )

    async def force_chats(self) -> list[dict[str, Any]]:
        return await self.db.force_chats.find({"active": True}).sort("created_at", ASCENDING).to_list(length=None)

    async def remove_force_chat(self, chat_id: int) -> None:
        await self.db.force_chats.update_one({"chat_id": chat_id}, {"$set": {"active": False, "updated_at": now()}})

    async def add_subscriber_trick_chat(self, data: dict[str, Any]) -> None:
        await self.db.subscriber_trick_chats.update_one(
            {"chat_id": data["chat_id"]},
            {"$set": {**data, "updated_at": now(), "active": True}, "$setOnInsert": {"created_at": now()}},
            upsert=True,
        )

    async def subscriber_trick_chats(self) -> list[dict[str, Any]]:
        return await self.db.subscriber_trick_chats.find({"active": True}).sort("created_at", ASCENDING).to_list(length=None)

    async def remove_subscriber_trick_chat(self, chat_id: int) -> None:
        await self.db.subscriber_trick_chats.update_one({"chat_id": chat_id}, {"$set": {"active": False, "updated_at": now()}})

    async def mark_join_request_sent(self, user_id: int, chat_id: int) -> None:
        await self.db.join_request_marks.update_one(
            {"user_id": user_id, "chat_id": chat_id},
            {"$set": {"requested_at": now()}},
            upsert=True,
        )

    async def has_join_request_mark(self, user_id: int, chat_id: int) -> bool:
        return bool(await self.db.join_request_marks.find_one({"user_id": user_id, "chat_id": chat_id}))

    async def create_bulk_job(self, owner_id: int, chat_id: int, total: int) -> dict[str, Any]:
        doc = {
            "owner_id": owner_id,
            "chat_id": chat_id,
            "total": total,
            "approved": 0,
            "failed": 0,
            "skipped": 0,
            "status": "running",
            "created_at": now(),
            "updated_at": now(),
        }
        result = await self.db.bulk_jobs.insert_one(doc)
        doc["_id"] = result.inserted_id
        return doc

    async def update_bulk_job(self, job_id: Any, **fields: Any) -> dict[str, Any] | None:
        fields["updated_at"] = now()
        return await self.db.bulk_jobs.find_one_and_update({"_id": job_id}, {"$set": fields}, return_document=ReturnDocument.AFTER)

    async def owner_stats(self) -> dict[str, int]:
        today = now() - timedelta(hours=24)
        return {
            "users": await self.db.users.count_documents({}),
            "registered": await self.db.users.count_documents({"banned": {"$ne": True}}),
            "verified": await self.db.users.count_documents({"verified": True}),
            "connected_chats": await self.db.connected_chats.count_documents({}),
            "active_chats": await self.db.connected_chats.count_documents({"active": True}),
            "force_chats": await self.db.force_chats.count_documents({"active": True}),
            "subscriber_trick_chats": await self.db.subscriber_trick_chats.count_documents({"active": True}),
            "active_bulk_jobs": await self.db.bulk_jobs.count_documents({"status": {"$in": ["running", "paused"]}}),
            "today_approvals": await self.db.pending_requests.count_documents({"status": "approved", "updated_at": {"$gte": today}}),
            "failed_jobs": await self.db.bulk_jobs.count_documents({"failed": {"$gt": 0}}),
        }
