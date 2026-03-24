from __future__ import annotations

from collections import defaultdict

from redis import Redis


class RefreshSessionStore:
    def set_token_hash(self, session_id: str, token_hash: str, ttl_seconds: int) -> None:
        raise NotImplementedError

    def get_token_hash(self, session_id: str) -> str | None:
        raise NotImplementedError

    def delete_session(self, session_id: str) -> None:
        raise NotImplementedError


class RedisRefreshSessionStore(RefreshSessionStore):
    def __init__(self, redis_url: str, prefix: str) -> None:
        self.client = Redis.from_url(redis_url, decode_responses=True)
        self.prefix = prefix

    def _key(self, session_id: str) -> str:
        return f"{self.prefix}:{session_id}"

    def set_token_hash(self, session_id: str, token_hash: str, ttl_seconds: int) -> None:
        self.client.set(self._key(session_id), token_hash, ex=ttl_seconds)

    def get_token_hash(self, session_id: str) -> str | None:
        return self.client.get(self._key(session_id))

    def delete_session(self, session_id: str) -> None:
        self.client.delete(self._key(session_id))


class MemoryRefreshSessionStore(RefreshSessionStore):
    def __init__(self) -> None:
        self._store: dict[str, str] = defaultdict(str)

    def set_token_hash(self, session_id: str, token_hash: str, ttl_seconds: int) -> None:
        del ttl_seconds
        self._store[session_id] = token_hash

    def get_token_hash(self, session_id: str) -> str | None:
        value = self._store.get(session_id)
        return value or None

    def delete_session(self, session_id: str) -> None:
        self._store.pop(session_id, None)


def create_refresh_session_store(redis_url: str, prefix: str) -> RefreshSessionStore:
    if redis_url.startswith("memory://"):
        return MemoryRefreshSessionStore()

    return RedisRefreshSessionStore(redis_url, prefix)
