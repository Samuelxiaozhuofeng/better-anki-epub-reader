from __future__ import annotations

import asyncio
import time
from typing import Dict, Optional

from aqt.qt import QThread, pyqtSignal

from ..utils.ai_client import AIClient
from ..utils.lookup_json import (
    LookupResult,
    build_json_repair_prompt,
    parse_lookup_result,
)


class LookupThread(QThread):
    partial = pyqtSignal(int, str)  # request_id, accumulated_text
    finished = pyqtSignal(int, object, str)  # request_id, result, raw_text
    failed = pyqtSignal(int, str)  # request_id, error_message
    cancelled = pyqtSignal(int)  # request_id

    def __init__(
        self,
        *,
        request_id: int,
        ai_client: AIClient,
        prompt: str,
        enabled_optional_fields: Dict[str, bool],
        max_basic_meanings: int = 3,
        repair_attempts: int = 1,
        parent=None,
    ):
        super().__init__(parent)
        self._request_id = request_id
        self._ai_client = ai_client
        self._prompt = prompt
        self._enabled_optional_fields = enabled_optional_fields
        self._max_basic_meanings = max_basic_meanings
        self._repair_attempts = max(0, int(repair_attempts))

        self._cancelled = False
        self._loop: Optional[asyncio.AbstractEventLoop] = None
        self._main_task: Optional[asyncio.Task] = None

    def cancel(self) -> None:
        self._cancelled = True
        loop = self._loop
        task = self._main_task
        if loop and task:
            try:
                loop.call_soon_threadsafe(task.cancel)
            except Exception:
                pass

    def _is_cancelled(self) -> bool:
        return self._cancelled

    def run(self) -> None:
        self._loop = asyncio.new_event_loop()
        asyncio.set_event_loop(self._loop)
        try:
            self._main_task = self._loop.create_task(self._run_async())
            self._loop.run_until_complete(self._main_task)
        except asyncio.CancelledError:
            self.cancelled.emit(self._request_id)
        except Exception as exc:
            self.failed.emit(self._request_id, str(exc))
        finally:
            try:
                pending = asyncio.all_tasks(loop=self._loop)
                for t in pending:
                    t.cancel()
                if pending:
                    self._loop.run_until_complete(asyncio.gather(*pending, return_exceptions=True))
            except Exception:
                pass
            try:
                self._loop.close()
            except Exception:
                pass
            self._loop = None
            self._main_task = None

    async def _run_async(self) -> None:
        raw = ""
        last_emit = 0.0

        async for delta in self._ai_client.explain_stream(self._prompt, cancel_cb=self._is_cancelled):
            if self._cancelled:
                raise asyncio.CancelledError()
            raw += delta

            now = time.monotonic()
            if now - last_emit >= 0.05:
                last_emit = now
                self.partial.emit(self._request_id, raw)

        if self._cancelled:
            raise asyncio.CancelledError()

        self.partial.emit(self._request_id, raw)

        try:
            result = parse_lookup_result(raw, max_basic_meanings=self._max_basic_meanings)
            self.finished.emit(self._request_id, result, raw)
            return
        except Exception:
            pass

        invalid_output = raw
        for _ in range(self._repair_attempts):
            if self._cancelled:
                raise asyncio.CancelledError()

            repair_prompt = build_json_repair_prompt(invalid_output=invalid_output)
            repaired = await self._ai_client.explain(repair_prompt)
            if repaired.error:
                raise Exception(repaired.error)
            invalid_output = repaired.explanation
            try:
                result = parse_lookup_result(invalid_output, max_basic_meanings=self._max_basic_meanings)
                self.finished.emit(self._request_id, result, raw)
                return
            except Exception:
                continue

        raise Exception("模型输出无法解析为 JSON（已尝试修复/重试）")
