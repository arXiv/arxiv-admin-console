from typing import Dict, Optional, Any
import asyncio
from datetime import datetime
from dataclasses import dataclass

class UserSession:
    user_locks: Dict[str, asyncio.Lock]  # A dictionary to store locks for individual users
    user_cookies: Dict[str, Any]          # Simulated storage of cookiess per user
    cookies_expiration: Dict[str, datetime]  # Simulated storage of cookies expiry times per user

    def __init__(self):
        self.global_lock = asyncio.Lock()
        self.user_locks = {}
        self.user_cookies = {}
        self.cookies_expiration = {}

    async def lock(self, user_id: str) -> None:
        user_lock = self.user_locks.get(user_id)
        while user_lock is None:
            await self.global_lock.acquire()
            user_lock = self.user_locks.get(user_id)
            if user_lock is None:
                user_lock = asyncio.Lock()
                self.user_locks[user_id] = user_lock
            self.global_lock.release()

        await user_lock.acquire()

    def unlock(self, user_id: str) -> None:
        user_lock = self.user_locks.get(user_id)
        if user_lock is None:
            return
        user_lock.release()

    async def set_user_cookies_with_lock(self, user_id: str, cookies: Any) -> None:
        await self.lock(user_id)
        self.user_cookies[user_id] = cookies
        self.unlock(user_id)

    def set_user_cookies(self, user_id: str, cookies: Any) -> None:
        self.user_cookies[user_id] = cookies

    def get_user_cookies(self, user_id: str) -> Optional[Any]:
        return self.user_cookies.get(user_id)

@dataclass
class TapirSessionData:
    session_id: str
    user_id: str
    client_ip: str
    session_created: datetime
    session_exp: datetime
    privilege: str

