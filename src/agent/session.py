import asyncio
import time

from langchain_core.messages import BaseMessage

SESSION_TTL = 30 * 60


class SessionStore:
    def __init__(self):
        self._sessions: dict[str, dict] = {}
        self._cleanup_task: asyncio.Task | None = None

    def start_cleanup(self):
        if self._cleanup_task is None or self._cleanup_task.done():
            self._cleanup_task = asyncio.create_task(self._cleanup_loop())

    async def _cleanup_loop(self):
        while True:
            await asyncio.sleep(60)
            self._evict_expired()

    def _evict_expired(self):
        now = time.time()
        expired = [
            sid for sid, data in self._sessions.items()
            if now - data["last_active"] > SESSION_TTL
        ]
        for sid in expired:
            del self._sessions[sid]

    def get_history(self, session_id: str) -> list[BaseMessage]:
        if session_id not in self._sessions:
            return []
        self._sessions[session_id]["last_active"] = time.time()
        return self._sessions[session_id]["messages"]

    def update_history(self, session_id: str, messages: list[BaseMessage]):
        self._sessions[session_id] = {
            "messages": messages,
            "last_active": time.time(),
        }


session_store = SessionStore()
