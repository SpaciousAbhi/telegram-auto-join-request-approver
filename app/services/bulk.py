from __future__ import annotations

import asyncio
from typing import Any

from aiogram import Bot

from app.services.formatters import bulk_status
from app.keyboards import bulk_control_keyboard
from app.services.telegram import approve_join_request, can_approve_in_chat


class BulkApprovalService:
    def __init__(self, db: Any):
        self.db = db
        self._tasks: dict[str, asyncio.Task] = {}

    async def start(self, bot: Bot, owner_id: int, chat_id: int, message: Any, speed_per_minute: int) -> dict:
        pending = await self.db.bulk_pending_for_chat(chat_id)
        job = await self.db.create_bulk_job(owner_id, chat_id, len(pending))
        await self.db.log_event("bulk_start", "Bulk approval started", {"owner_id": owner_id, "chat_id": chat_id, "total": len(pending)})
        task = asyncio.create_task(self._run(bot, job, pending, message, speed_per_minute))
        self._tasks[str(job["_id"])] = task
        return job

    async def _run(self, bot: Bot, job: dict, pending: list[dict], message: Any, speed_per_minute: int) -> None:
        interval = 60 / max(1, speed_per_minute)
        approved = failed = skipped = 0
        can_approve, permission_error = await can_approve_in_chat(bot, job["chat_id"])
        if not can_approve:
            job = await self.db.update_bulk_job(job["_id"], status="failed", failed=len(pending), last_error=permission_error)
            await self.db.log_event("bulk_error", "Bulk approval permission failed", {"chat_id": job["chat_id"], "error": permission_error}, "error")
            try:
                await message.edit_text(bulk_status(job), reply_markup=bulk_control_keyboard(str(job["_id"])))
            except Exception:
                pass
            return
        for idx, item in enumerate(pending, start=1):
            current = await self.db.db.bulk_jobs.find_one({"_id": job["_id"]})
            if not current or current.get("status") == "stopped":
                await self.db.update_bulk_job(job["_id"], status="stopped")
                return
            while current.get("status") == "paused":
                await asyncio.sleep(2)
                current = await self.db.db.bulk_jobs.find_one({"_id": job["_id"]})
            if item.get("status") not in {"pending", "verification_dm_failed"}:
                skipped += 1
                await self.db.mark_request(item["chat_id"], item["user_id"], "skipped", "Request is no longer pending in local queue.")
                job = await self.db.update_bulk_job(job["_id"], approved=approved, failed=failed, skipped=skipped)
                continue
            ok, error = await approve_join_request(bot, item["chat_id"], item["user_id"])
            if ok:
                approved += 1
                await self.db.mark_request(item["chat_id"], item["user_id"], "approved")
                await self.db.record_approval(item["chat_id"], True)
            else:
                failed += 1
                await self.db.mark_request(item["chat_id"], item["user_id"], "failed", error)
                await self.db.record_approval(item["chat_id"], False)
            job = await self.db.update_bulk_job(job["_id"], approved=approved, failed=failed, skipped=skipped)
            if idx == 1 or idx % 25 == 0 or idx == len(pending):
                try:
                    await message.edit_text(bulk_status(job), reply_markup=bulk_control_keyboard(str(job["_id"])))
                except Exception:
                    pass
            await asyncio.sleep(interval)
        job = await self.db.update_bulk_job(job["_id"], status="completed", approved=approved, failed=failed, skipped=skipped)
        await self.db.log_event(
            "bulk_completed",
            "Bulk approval completed",
            {"chat_id": job["chat_id"], "approved": approved, "failed": failed, "skipped": skipped},
            "info" if failed == 0 else "warning",
        )
        try:
            await message.edit_text(bulk_status(job), reply_markup=bulk_control_keyboard(str(job["_id"])))
        except Exception:
            pass
