from __future__ import annotations

import functools
import inspect

from typing import Awaitable, Callable, Concatenate, ParamSpec, TypeVar, TYPE_CHECKING

from ._types import T, R, AsyncMethod, AsyncDecorator


if TYPE_CHECKING:
    from aiocache import BaseCache
    from .protocols import AsyncAdapterProtocol

    TBackend = TypeVar("TBackend", bound=BaseCache)


P = ParamSpec("P")


class AsyncAdapter:
    """
    A concrete cache adapter for asynchronous caching backends, such as `aiocache`.

    This adapter provides a high-level, asynchronous interface for common caching
    operations, allowing for memoization and data retrieval using an underlying
    asynchronous cache backend.
    """

    __slots__ = ("_backend",)

    def __init__(
        self,
        backend: TBackend,
    ) -> None:
        self._backend = backend

    async def has(
        self,
        key: str,
    ) -> bool:
        """
        Checks for the existence of a key in the cache.

        :param key: The key associated with the value.
        :type key: str
        :return: ``True`` if the key exists, ``False`` otherwise.
        :rtype: bool
        """
        return await self._backend.exists(key)

    async def get(
        self,
        key: str,
    ) -> R | None:
        """
        Retrieves a value from the asynchronous cache by its key.

        :param key: The key associated with the value.
        :type key: str
        :return: The cached value, or ``None`` if the key is not found.
        :rtype: R | None
        """
        return await self._backend.get(key)

    async def set(
        self,
        key: str,
        value: R,
        *,
        ttl: int | None = None,
    ) -> None:
        """
        Stores a value in the asynchronous cache with an optional time-to-live (TTL).

        :param key: The key to store the value under.
        :type key: str
        :param value: The value to be cached.
        :type value: Any
        :param ttl: The time-to-live for the cache entry in seconds.
        :type ttl: int | None
        :return: An awaitable that returns nothing.
        :rtype: Awaitable[None]
        """
        return await self._backend.set(key, value, ttl=ttl)

    async def memoize(
        self,
        key: str,
        fn: Callable[[], Awaitable[R]],
        *,
        ttl: int | None = None,
    ) -> R | None:
        """
        Executes an asynchronous callable and caches its result.

        If the key exists in the cache, the cached value is returned. Otherwise,
        the callable ``fn`` is executed, its result is cached, and then returned.

        :param key: The cache key for the result of the callable.
        :type key: str
        :param fn: The callable to execute if the key is not in the cache.
                   It must be a no-argument callable that returns an awaitable.
        :type fn: Callable[[], Awaitable[R]]
        :param ttl: The time-to-live for the cache entry in seconds.
        :type ttl: int | None
        :return: The result of the callable or the cached value.
        :rtype: R | None
        """
        if await self._backend.exists(key):
            return await self._backend.get(key)

        value = await fn()
        await self._backend.set(key, value, ttl=ttl)

        return value

    async def delete(
        self,
        key: str,
    ) -> bool:
        """
        Deletes a key from the asynchronous cache.

        This method normalizes the backend's return value (0 or 1) to a boolean.

        :param key: The key to delete.
        :type key: str
        :return: ``True`` if the key was deleted, ``False`` otherwise.
        :rtype: bool
        """
        return await self._backend.delete(key) == 1

    async def clear(
        self,
    ) -> bool:
        """
        Clears all items from the cache.

        :return: ``True`` if the cache was successfully cleared, ``False`` otherwise.
        :rtype: bool
        """
        return await self._backend.clear()


async def invoke_cache_adapter(
    self: T,
    key_fn: Callable[Concatenate[T, P], str],
    cache_attr: str,
    fn: AsyncMethod[T, P, R],
    args: tuple,
    kwargs: dict,
    *,
    ttl: int | None = None,
) -> R | None:
    """
    Invokes an asynchronous function and caches its result using a cache adapter.

    This helper function contains the core logic for the :py:func:`async_cached`
    decorator, handling the retrieval of the async cache adapter, key generation,
    and memoization.

    :param self: The instance of the class the decorated method belongs to.
    :type self: T
    :param cache_attr: The name of the attribute on ``self`` that holds the cache
                       adapter.
    :type cache_attr: str
    :param key_fn: A function that generates a cache key from the decorated
                   function's arguments.
    :type key_fn: KeyCallable[P]
    :param fn: The decorated async function to be executed.
    :type fn: AsyncMethod[T, P, R]
    :param args: The positional arguments passed to the decorated function.
    :type args: P.args
    :param kwargs: The keyword arguments passed to the decorated function.
    :type kwargs: P.kwargs
    :param ttl: The time-to-live for the cached item in seconds.
    :type ttl: int | None
    :return: The result of the async function or the cached value.
    :rtype: R | None
    """
    if not hasattr(self, cache_attr):
        raise AttributeError(
            f"The provided cache attribute `{cache_attr}` does not exist."
        )

    adapter: AsyncAdapterProtocol = getattr(self, cache_attr)

    async def result_fn() -> R | None:
        return await fn(self, *args, **kwargs)

    key = key_fn(self, *args, **kwargs)
    return await adapter.memoize(key, result_fn, ttl=ttl)


def async_cached(
    key_fn: Callable[Concatenate[T, P], str],
    *,
    cache_attr: str = "_cache",
    ttl: int | None = None,
) -> AsyncDecorator[T, P, R]:
    """
    A decorator for memoizing an asynchronous function's result using an
    asynchronous cache adapter.

    The decorator generates a cache key using ``key_fn`` and delegates caching
    logic to an asynchronous cache adapter found on the decorated object.

    :param key_fn: A function that generates a cache key from the decorated
                   function's arguments.
    :type key_fn: KeyCallable[P]
    :param cache_attr: The name of the attribute on ``self`` that holds the cache
                       adapter.
    :type cache_attr: str
    :param ttl: The time-to-live for the cached item in seconds.
    :type ttl: int | None
    :return: The decorated async function (wrapper).
    :rtype: AsyncMethod[T, P, R | None]
    """

    def decorator(
        fn: AsyncMethod[T, P, R],
    ) -> AsyncMethod[T, P, R | None]:
        argspec = inspect.getfullargspec(fn)

        if not argspec.args or argspec.args[0] != "self":
            raise TypeError(
                "The 'async_cached' decorator can only be used on methods of a class."
            )

        @functools.wraps(fn)
        async def wrapper(
            self: T,
            *args: P.args,
            **kwargs: P.kwargs,
        ) -> R | None:
            """
            The wrapper function that executes the caching logic before
            calling the original decorated function.
            """
            return await invoke_cache_adapter(
                self,
                key_fn,
                cache_attr,
                fn,
                args,
                kwargs,
                ttl=ttl,
            )

        return wrapper

    return decorator


__all__ = (
    "AsyncAdapter",
    "async_cached",
)
