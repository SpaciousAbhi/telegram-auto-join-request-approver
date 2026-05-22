from __future__ import annotations

import asyncio
from typing import Any
from datetime import datetime

from aiogram import Bot
from pymongo import UpdateOne

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
        task = asyncio.create_task(self._run(bot, job, pending, message, speed_per_minute))
        self._tasks[str(job["_id"])] = task
        return job

    async def _run(self, bot: Bot, job: dict, pending: list[dict], message: Any, speed_per_minute: int) -> None:
        chunk_size = max(1, speed_per_minute // 60)
        interval = chunk_size * 60 / max(1, speed_per_minute)
        approved = failed = skipped = 0
        last_update_time = 0.0

        can_approve, permission_error = await can_approve_in_chat(bot, job["chat_id"])
        if not can_approve:
            job = await self.db.update_bulk_job(job["_id"], status="failed", failed=len(pending), last_error=permission_error)
            try:
                await message.edit_text(bulk_status(job), reply_markup=bulk_control_keyboard(str(job["_id"])))
            except Exception:
                pass
            return

        async def _update_status(force: bool = False):
            nonlocal last_update_time, job
            current_time = datetime.now().timestamp()
            if force or current_time - last_update_time >= 3.0:
                job = await self.db.update_bulk_job(job["_id"], approved=approved, failed=failed, skipped=skipped)
                try:
                    await message.edit_text(bulk_status(job), reply_markup=bulk_control_keyboard(str(job["_id"])))
                except Exception:
                    pass
                last_update_time = datetime.now().timestamp()

        async def process_batch(batch: list[dict]):
            nonlocal approved, failed, skipped
            tasks = []
            for item in batch:
                if item.get("status") not in {"pending", "verification_dm_failed"}:
                    skipped += 1
                    tasks.append(asyncio.create_task(self._mark_skipped(item)))
                else:
                    tasks.append(asyncio.create_task(self._process_single(bot, item)))
            results = await asyncio.gather(*tasks, return_exceptions=True)

            updates = []
            batch_approved = 0
            batch_failed = 0
            for i, result in enumerate(results):
                item = batch[i]
                if isinstance(result, tuple):
                    ok, error = result
                    status = "approved" if ok else "failed"
                    if ok:
                        batch_approved += 1
                    else:
                        batch_failed += 1
                elif isinstance(result, str) and result == "skipped":
                    status = "skipped"
                    error = "Request is no longer pending in local queue."
                else:
                    continue

                update_doc = {"status": status, "updated_at": datetime.now()}
                if not isinstance(result, str) and not ok:
                    update_doc["error"] = error
                elif isinstance(result, str):
                    update_doc["error"] = error

                updates.append(UpdateOne(
                    {"chat_id": item["chat_id"], "user_id": item["user_id"]},
                    {"$set": update_doc}
                ))

            if updates:
                await self.db.db.pending_requests.bulk_write(updates, ordered=False)

            approved += batch_approved
            failed += batch_failed
            await self.db.record_approvals(job["chat_id"], batch_approved, batch_failed)

        for i in range(0, len(pending), chunk_size):
            current = await self.db.db.bulk_jobs.find_one({"_id": job["_id"]})
            if not current or current.get("status") == "stopped":
                await self.db.update_bulk_job(job["_id"], status="stopped", approved=approved, failed=failed, skipped=skipped)
                return
            while current.get("status") == "paused":
                await asyncio.sleep(2)
                current = await self.db.db.bulk_jobs.find_one({"_id": job["_id"]})

            batch = pending[i:i + chunk_size]
            await process_batch(batch)
            await _update_status()
            await asyncio.sleep(interval)

        job = await self.db.update_bulk_job(job["_id"], status="completed", approved=approved, failed=failed, skipped=skipped)
        await _update_status(force=True)

    async def _process_single(self, bot: Bot, item: dict) -> tuple[bool, str | None]:
        ok, error = await approve_join_request(bot, item["chat_id"], item["user_id"])
        return ok, error

    async def _mark_skipped(self, item: dict) -> str:
        return "skipped"
