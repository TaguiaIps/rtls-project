from __future__ import annotations

from datetime import datetime, timedelta, timezone

from redis import Redis


def utc_now() -> datetime:
    return datetime.now(timezone.utc)


class MessageDedupeStore:
    def claim_message(self, gateway_identifier: str, message_id: str, ttl_seconds: int) -> bool:
        raise NotImplementedError


class RedisMessageDedupeStore(MessageDedupeStore):
    def __init__(self, redis_url: str, prefix: str) -> None:
        self.client = Redis.from_url(redis_url, decode_responses=True)
        self.prefix = prefix

    def _key(self, gateway_identifier: str, message_id: str) -> str:
        return f"{self.prefix}:{gateway_identifier}:{message_id}"

    def claim_message(self, gateway_identifier: str, message_id: str, ttl_seconds: int) -> bool:
        claimed = self.client.set(
            self._key(gateway_identifier, message_id),
            "1",
            ex=ttl_seconds,
            nx=True,
        )
        return bool(claimed)


class MemoryMessageDedupeStore(MessageDedupeStore):
    def __init__(self) -> None:
        self._store: dict[str, datetime] = {}

    def claim_message(self, gateway_identifier: str, message_id: str, ttl_seconds: int) -> bool:
        key = f"{gateway_identifier}:{message_id}"
        now = utc_now()
        expires_at = self._store.get(key)
        if expires_at is not None and expires_at > now:
            return False

        self._store[key] = now + timedelta(seconds=ttl_seconds)
        expired_keys = [candidate for candidate, expiry in self._store.items() if expiry <= now]
        for expired_key in expired_keys:
            self._store.pop(expired_key, None)
        return True


def create_message_dedupe_store(redis_url: str, prefix: str) -> MessageDedupeStore:
    if redis_url.startswith("memory://"):
        return MemoryMessageDedupeStore()

    return RedisMessageDedupeStore(redis_url, prefix)
