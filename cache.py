import time
from typing import Any


class TTLCache:
    """Cache simples em memória com expiração por tempo."""

    def __init__(self, ttl_seconds: int = 3600):
        self.ttl = ttl_seconds
        self._data: dict[Any, tuple[float, Any]] = {}

    def get(self, key):
        item = self._data.get(key)
        if item is None:
            return None
        expires_at, value = item
        if time.monotonic() > expires_at:
            del self._data[key]
            return None
        return value

    def set(self, key, value):
        self._data[key] = (time.monotonic() + self.ttl, value)

    def clear(self):
        self._data.clear()
