from typing import Optional, List
import asyncio

class Homepage:
    def __init__(self, username: str):
        self._username = username
        self._posts = []
        self._update_queue: Optional[asyncio.Queue] = None
        self._btnPressed = False  # Initialize the new attribute
        self._sessionId = ''

    @property
    def username(self) -> str:
        return self._username

    @property
    def posts(self) -> List[str]:
        return self._posts

    @property
    def btnPressed(self) -> bool:
        return self._btnPressed

    @btnPressed.setter
    def btnPressed(self, value: bool) -> None:
        self._btnPressed = value

    @property
    def sessionId(self) -> str:
        return self._sessionId

    @sessionId.setter
    def sessionId(self, value: str) -> None:
        if self._sessionId == '':
            self._sessionId = value

    def add_post(self, content: str) -> None:
        """Simple method to add a post to the list"""
        self._posts.append(content)

    async def queue_update(self, update_data: dict) -> None:
        """Generic method to queue any SSE update"""
        if self._update_queue is not None:
            await self._update_queue.put(update_data)