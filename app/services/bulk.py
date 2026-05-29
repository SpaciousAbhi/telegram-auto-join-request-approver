from __future__ import annotations

import asyncio
from typing import Any

from aiogram import Bot

from app.services.formatters import bulk_status
from app.keyboards import bulk_control_keyboard
from app.services.approval import approve_stored_request


class BulkProgressUpdater:
    def __init__(self, bot: Bot, db: Any, job_id: Any, progress_chat_id: int | None = None, progress_message_id: int | None = None, message_obj: Any = None):
        self.bot = bot
        self.db = db
        self.job_id = job_id
        self.progress_chat_id = progress_chat_id
        self.progress_message_id = progress_message_id
        self.message_obj = message_obj

    async def update(self, job: dict) -> None:
        if self.message_obj:
            try:
                await self.message_obj.edit_text(bulk_status(job), reply_markup=bulk_control_keyboard(str(job["_id"])))
            except Exception:
                pass
        elif self.progress_chat_id and self.progress_message_id:
            try:
                await self.bot.edit_message_text(
                    chat_id=self.progress_chat_id,
                    message_id=self.progress_message_id,
                    text=bulk_status(job),
                    reply_markup=bulk_control_keyboard(str(job["_id"]))
                )
            except Exception:
                pass


class BulkApprovalService:
    def __init__(self, db: Any):
        self.db = db
        self._tasks: dict[str, asyncio.Task] = {}

    async def start(self, bot: Bot, owner_id: int, chat_id: int, progress_chat_id: int, progress_message_id: int, speed_per_minute: int) -> dict:
        pending = await self.db.bulk_pending_for_chat(chat_id)
        job = await self.db.create_bulk_job(
            owner_id, chat_id, len(pending), progress_chat_id, progress_message_id
        )
        await self.db.log_event("bulk_start", "Bulk approval started", {"owner_id": owner_id, "chat_id": chat_id, "total": len(pending)})
        updater = BulkProgressUpdater(bot, self.db, job["_id"], progress_chat_id, progress_message_id)
        task = asyncio.create_task(self._run(bot, job, pending, updater, speed_per_minute))
        self._tasks[str(job["_id"])] = task
        return job

    async def resume_job(self, bot: Bot, job: dict, speed_per_minute: int) -> None:
        job_id_str = str(job["_id"])
        if job_id_str in self._tasks and not self._tasks[job_id_str].done():
            return  # already running
        pending = await self.db.bulk_pending_for_chat(job["chat_id"])
        await self.db.log_event("bulk_resume", "Bulk approval resumed after restart", {"chat_id": job["chat_id"], "total": len(pending)})
        updater = BulkProgressUpdater(bot, self.db, job["_id"], job.get("progress_chat_id"), job.get("progress_message_id"))
        task = asyncio.create_task(self._run(bot, job, pending, updater, speed_per_minute, is_resume=True))
        self._tasks[job_id_str] = task

    async def resume_all_jobs(self, bot: Bot) -> None:
        settings = await self.db.settings()
        speed = int(settings.get("approval_speed_per_minute", 600))
        running_jobs = await self.db.db.bulk_jobs.find({"status": "running"}).to_list(length=None)
        for job in running_jobs:
            await self.resume_job(bot, job, speed)

    async def _run(self, bot: Bot, job: dict, pending: list[dict], updater: BulkProgressUpdater, speed_per_minute: int, is_resume: bool = False) -> None:
        interval = 60 / max(1, speed_per_minute)
        approved = job.get("approved", 0) if is_resume else 0
        failed = job.get("failed", 0) if is_resume else 0
        skipped = job.get("skipped", 0) if is_resume else 0
        permission_cache: dict[int, tuple[bool, str | None]] = {}
        for idx, item in enumerate(pending, start=1):
            current = await self.db.db.bulk_jobs.find_one({"_id": job["_id"]})
            if not current or current.get("status") == "stopped":
                await self.db.update_bulk_job(job["_id"], status="stopped")
                return
            while current.get("status") == "paused":
                await asyncio.sleep(2)
                current = await self.db.db.bulk_jobs.find_one({"_id": job["_id"]})
            if item.get("status") not in {"pending", "verification_dm_failed", "approval_retry", "permission_error", "failed"}:
                skipped += 1
                await self.db.mark_request(item["chat_id"], item["user_id"], "skipped", "Request is no longer pending in local queue.")
                job = await self.db.update_bulk_job(job["_id"], approved=approved, failed=failed, skipped=skipped)
                continue
            result = await approve_stored_request(
                bot,
                self.db,
                item,
                "bulk_job",
                notify_user=True,
                permission_cache=permission_cache,
            )
            if result.ok:
                approved += 1
            elif result.status in {"skipped", "chat_deactivated_by_owner"}:
                skipped += 1
            else:
                failed += 1
            job = await self.db.update_bulk_job(job["_id"], approved=approved, failed=failed, skipped=skipped)
            if idx == 1 or idx % 25 == 0 or idx == len(pending):
                await updater.update(job)
            await asyncio.sleep(interval)
        job = await self.db.update_bulk_job(job["_id"], status="completed", approved=approved, failed=failed, skipped=skipped)
        await self.db.log_event(
            "bulk_completed",
            "Bulk approval completed",
            {"chat_id": job["chat_id"], "approved": approved, "failed": failed, "skipped": skipped},
            "info" if failed == 0 else "warning",
        )
        await updater.update(job)
