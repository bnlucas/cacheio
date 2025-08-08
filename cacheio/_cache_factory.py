from __future__ import annotations

from typing import Any, Callable

try:
    from cachelib import SimpleCache as SyncCache, RedisCache as SyncRedisCache

    CACHELIB_LOADED = True
except ImportError:
    CACHELIB_LOADED = False
    SyncCache = None
    SyncRedisCache = None

try:
    from aiocache import Cache as AsyncCache

    AIOCACHE_LOADED = True
except ImportError:
    AIOCACHE_LOADED = False
    AsyncCache = None

from ._config import config
from ._async_adapter import AsyncAdapter
from ._adapter import Adapter


def ensure_cachelib() -> None:
    """
    Raise ImportError if `cachelib` is not installed.

    This helper function ensures that the synchronous caching
    dependencies are available before attempting to use them.

    :raises ImportError: If `cachelib` is not installed.
    """
    if not CACHELIB_LOADED:
        raise ImportError(
            "The 'cachelib' library is not installed. Please install "
            "'cacheio[sync]' to use synchronous caching."
        )


def ensure_aiocache() -> None:
    """
    Raise ImportError if `aiocache` is not installed.

    This helper function ensures that the asynchronous caching
    dependencies are available before attempting to use them.

    :raises ImportError: If `aiocache` is not installed.
    """
    if not AIOCACHE_LOADED:
        raise ImportError(
            "The 'aiocache' library is not installed. Please install "
            "'cacheio[async]' to use asynchronous caching."
        )


class CacheFactory:
    """
    Factory class for creating synchronous and asynchronous cache adapters.

    Provides static methods to create configured cache instances
    backed by either memory or Redis, using `cachelib` and `aiocache`.
    """

    @staticmethod
    def memory_cache(
        *,
        ttl: int | None = None,
        threshold: int | None = None,
    ) -> Adapter:
        """
        Create a synchronous in-memory cache Adapter.

        Constructs a `cachelib.SimpleCache` instance with the specified
        parameters, wrapped in an `Adapter`.
        The `ttl` and `threshold` parameters default to global values
        from `config` if not provided.

        :param ttl: Time-to-live for cache entries in seconds.
                    If None, defaults to `config.default_ttl`.
        :type ttl: int | None
        :param threshold: Maximum number of items before cache pruning.
                          If None, defaults to `config.default_threshold`.
        :type threshold: int | None
        :return: A configured synchronous cache Adapter instance.
        :rtype: Adapter
        """
        ensure_cachelib()

        ttl = config.get("default_ttl", ttl)
        threshold = config.get("default_threshold", threshold)

        return Adapter(SyncCache(threshold, ttl))

    @staticmethod
    def redis_cache(
        *,
        ttl: int | None = None,
        host: Any = "localhost",
        port: int = 6379,
        password: str | None = None,
        db: int = 0,
        namespace: str | Callable[[], str] | None = None,
        **kwargs: Any,
    ) -> Adapter:
        """
        Create a synchronous Redis cache Adapter.

        Constructs a `cachelib.RedisCache` instance with the provided
        parameters, wrapped in an `Adapter`. The `ttl` parameter defaults
        to the global value from `config` if not provided.

        :param ttl: Time-to-live for cache entries in seconds.
                    This value is mapped to `default_timeout` for the `cachelib`
                    backend. If None, defaults to `config.default_ttl`.
        :type ttl: int | None
        :param host: Redis server hostname or IP. Defaults to "localhost".
        :type host: Any
        :param port: Redis server port. Defaults to 6379.
        :type port: int
        :param password: Password for Redis authentication.
        :type password: str | None
        :param db: Redis database index. Defaults to 0.
        :type db: int
        :param namespace: Cache key prefix as string or callable returning a string.
                          This value is mapped to `key_prefix` for the `cachelib`
                          backend. If callable, it is not invoked automatically here.
        :type namespace: str | Callable[[], str] | None
        :param kwargs: Additional keyword arguments forwarded to `redis.Redis`.
        :type kwargs: Any
        :return: A configured synchronous Redis cache Adapter instance.
        :rtype: Adapter
        """
        ensure_cachelib()

        ttl = config.get("default_ttl", ttl)

        return Adapter(
            SyncRedisCache(
                host=host,
                port=port,
                password=password,
                db=db,
                default_timeout=ttl,
                key_prefix=namespace,
                **kwargs,
            )
        )

    @staticmethod
    def async_memory_cache(
        *,
        ttl: int | None = None,
        **kwargs: Any,
    ) -> AsyncAdapter:
        """
        Create an asynchronous in-memory cache AsyncAdapter.

        Constructs an `aiocache.Cache` instance using the in-memory
        backend, wrapped in an `AsyncAdapter`.
        The `ttl` parameter defaults to the global value from `config`
        if not provided.

        :param ttl: Time-to-live for cache entries in seconds.
                    If None, defaults to `config.default_ttl`.
        :type ttl: int | None
        :param kwargs: Additional keyword arguments forwarded to `aiocache.Cache`.
        :type kwargs: Any
        :return: A configured asynchronous in-memory cache AsyncAdapter instance.
        :rtype: AsyncAdapter
        """
        ensure_aiocache()

        ttl = config.get("default_ttl", ttl)

        return AsyncAdapter(AsyncCache(AsyncCache.MEMORY, ttl=ttl, **kwargs))

    @staticmethod
    def async_redis_cache(
        *,
        ttl: int | None = None,
        host: Any = "localhost",
        port: int = 6379,
        password: str | None = None,
        db: int = 0,
        namespace: str | Callable[[], str] | None = None,
        **kwargs: Any,
    ) -> AsyncAdapter:
        """
        Create an asynchronous Redis cache AsyncAdapter.

        Constructs an `aiocache.RedisCache` instance with the specified
        parameters, wrapped in an `AsyncAdapter`. The `ttl` parameter defaults
        to the global value from `config` if not provided.

        If `namespace` is a callable, it is invoked before being passed
        to the cache backend.

        :param ttl: Time-to-live for cache entries in seconds.
                    This value is mapped to `timeout` for the `aiocache` backend.
                    If None, defaults to `config.default_ttl`.
        :type ttl: int | None
        :param host: Redis server hostname or IP. This value is mapped to `endpoint`
                     for the `aiocache` backend. Defaults to "localhost".
        :type host: Any
        :param port: Redis server port. Defaults to 6379.
        :type port: int
        :param password: Password for Redis authentication.
        :type password: str | None
        :param db: Redis database index. Defaults to 0.
        :type db: int
        :param namespace: Cache key prefix as string or callable returning a string.
                          If callable, it is invoked to get the prefix.
        :type namespace: str | Callable[[], str] | None
        :param kwargs: Additional keyword arguments forwarded to `aiocache.RedisCache`.
        :type kwargs: Any
        :return: A configured asynchronous Redis cache AsyncAdapter instance.
        :rtype: AsyncAdapter
        """
        ensure_aiocache()

        ttl = config.get("default_ttl", ttl)

        if callable(namespace):
            namespace = namespace()

        return AsyncAdapter(
            AsyncCache(
                AsyncCache.REDIS,
                endpoint=host,
                port=port,
                password=password,
                db=db,
                timeout=ttl,
                namespace=namespace,
                **kwargs,
            )
        )


__all__ = ("CacheFactory",)
