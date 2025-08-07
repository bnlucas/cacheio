from __future__ import annotations

from typing import Any, Callable, Protocol

from cacheio._types import R


class AdapterProtocol(Protocol):
    """
    Protocol for synchronous cache adapters.

    This protocol provides a uniform interface for synchronous caching backends,
    including methods for getting, setting, memoizing, and deleting keys.
    """

    def has(
        self,
        key: str,
    ) -> bool:
        """
        Checks for the existence of a key in the cache.

        This method is an efficient, atomic way to determine if a key exists
        without retrieving its value.

        :param key: The key associated with the value.
        :type key: str
        :return: ``True`` if the key exists, ``False`` otherwise.
        :rtype: bool
        """
        ...

    def get(
        self,
        key: str,
    ) -> R | None:
        """
        Retrieves a value from the cache by its key.

        :param key: The key associated with the value.
        :type key: str
        :return: The cached value, or ``None`` if the key is not found.
        :rtype: R | None
        """
        ...

    def set(
        self,
        key: str,
        value: Any,
        *,
        ttl: int | None = None,
    ) -> None:
        """
        Stores a value in the cache with an optional time-to-live (TTL).

        :param key: The key to store the value under.
        :type key: str
        :param value: The value to be cached.
        :type value: Any
        :param ttl: The time-to-live for the cache entry in seconds.
        :type ttl: int | None
        """
        ...

    def memoize(
        self,
        key: str,
        fn: Callable[[], R],
        *,
        ttl: int | None = None,
    ) -> R | None:
        """
        Executes a callable and caches its result.

        If the key exists in the cache, the cached value is returned. Otherwise,
        the callable ``fn`` is executed, its result is cached, and then returned.

        :param key: The cache key for the result of the callable.
        :type key: str
        :param fn: The callable to execute if the key is not in the cache.
                   It must be a no-argument callable.
        :type fn: Callable[[], R]
        :param ttl: The time-to-live for the cache entry in seconds.
        :type ttl: int | None
        :return: The result of the callable or the cached value.
        :rtype: R | None
        """
        ...

    def delete(
        self,
        key: str,
    ) -> None:
        """
        Deletes a key from the cache.

        :param key: The key to delete.
        :type key: str
        """
        ...

    def clear(
        self,
    ) -> bool:
        """
        Clears all items from the cache.

        :return: ``True`` if the cache was successfully cleared, ``False`` otherwise.
        :rtype: bool
        """
        ...


__all__ = ("AdapterProtocol",)
