from __future__ import annotations

import functools
import inspect

from typing import Callable, Concatenate, ParamSpec, TypeVar, TYPE_CHECKING

from ._types import T, R, SyncMethod, SyncDecorator


if TYPE_CHECKING:
    from cachelib import BaseCache
    from .protocols import AdapterProtocol

    TBackend = TypeVar("TBackend", bound=BaseCache)

P = ParamSpec("P")


class Adapter:
    """
    A concrete cache adapter for synchronous caching backends, such as `cachelib`.

    This adapter provides a high-level, synchronous interface for common caching
    operations, allowing for memoization and data retrieval using an underlying
    synchronous cache backend.
    """

    __slots__ = ("_backend",)

    def __init__(
        self,
        backend: TBackend,
    ) -> None:
        self._backend = backend

    def has(
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
        return self._backend.has(key)

    def get(
        self,
        key: str,
    ) -> R | None:
        """
        Retrieves a value from the synchronous cache by its key.

        :param key: The key associated with the value.
        :type key: str
        :return: The cached value, or ``None`` if the key is not found.
        :rtype: R | None
        """
        return self._backend.get(key)

    def set(
        self,
        key: str,
        value: R,
        *,
        ttl: int | None = None,
    ) -> bool:
        """
        Stores a value in the synchronous cache with an optional time-to-live (TTL).

        :param key: The key to store the value under.
        :type key: str
        :param value: The value to be cached.
        :type value: Any
        :param ttl: The time-to-live for the cache entry in seconds.
        :type ttl: int | None
        """

        return self._backend.set(key, value, timeout=ttl)

    def memoize(
        self,
        key: str,
        fn: Callable[[], R],
        *,
        ttl: int | None = None,
    ) -> R | None:
        """
        Executes a synchronous callable and caches its result.

        If the key exists in the cache, the cached value is returned. Otherwise,
        the callable ``fn`` is executed, its result is cached, and then returned.

        :param key: The cache key for the result of the callable.
        :type key: str
        :param fn: The callable to execute if the key is not in the cache.
                   It must be a no-argument callable that returns a value of type R.
        :type fn: Callable[[], R]
        :param ttl: The time-to-live for the cache entry in seconds.
        :type ttl: int | None
        :return: The result of the callable or the cached value.
        :rtype: R | None
        """
        if self._backend.has(key):
            return self._backend.get(key)

        value = fn()
        self._backend.set(key, value, timeout=ttl)

        return value

    def delete(
        self,
        key: str,
    ) -> bool:
        """
        Deletes a key from the synchronous cache.

        :param key: The key to delete.
        :type key: str
        """
        return self._backend.delete(key)

    def clear(
        self,
    ) -> bool:
        """
        Clears all items from the cache.

        :return: ``True`` if the cache was successfully cleared, ``False`` otherwise.
        :rtype: bool
        """
        return self._backend.clear()


def invoke_cache_adapter(
    self: T,
    key_fn: Callable[Concatenate[T, P], str],
    cache_attr: str,
    fn: SyncMethod[T, P, R],
    args: tuple,
    kwargs: dict,
    *,
    ttl: int | None = None,
) -> R | None:
    """
    Invokes a synchronous function and caches its result using a cache adapter.

    This helper function contains the core logic for the :py:func:`cached` decorator,
    handling the retrieval of the cache adapter, key generation, and memoization.

    :param self: The instance of the class the decorated method belongs to.
    :type self: T
    :param cache_attr: The name of the attribute on ``self`` that holds the cache
                       adapter.
    :type cache_attr: str
    :param key_fn: A function that generates a cache key from the decorated
                   function's arguments.
    :type key_fn: KeyCallable[P]
    :param fn: The decorated function to be executed.
    :type fn: SyncMethod[T, P, R]
    :param args: The positional arguments passed to the decorated function.
    :type args: P.args
    :param kwargs: The keyword arguments passed to the decorated function.
    :type kwargs: P.kwargs
    :param ttl: The time-to-live for the cached item in seconds.
    :type ttl: int | None
    :return: The result of the function or the cached value.
    :rtype: R | None
    """
    if not hasattr(self, cache_attr):
        raise AttributeError(
            f"The provided cache attribute `{cache_attr}` does not exist."
        )

    adapter: AdapterProtocol = getattr(self, cache_attr)

    def result_fn() -> R | None:
        return fn(self, *args, **kwargs)

    key = key_fn(self, *args, **kwargs)
    return adapter.memoize(key, result_fn, ttl=ttl)


def cached(
    key_fn: Callable[Concatenate[T, P], str],
    *,
    cache_attr: str = "_cache",
    ttl: int | None = None,
) -> SyncDecorator[T, P, R]:
    """
    A decorator for memoizing a synchronous function's result using an
    synchronous cache adapter.

    The decorator generates a cache key using ``key_fn`` and delegates caching
    logic to a synchronous cache adapter found on the decorated object.

    :param key_fn: A function that generates a cache key from the decorated
                   function's arguments.
    :type key_fn: KeyCallable[P]
    :param cache_attr: The name of the attribute on ``self`` that holds the cache
                       adapter.
    :type cache_attr: str
    :param ttl: The time-to-live for the cached item in seconds.
    :type ttl: int | None
    :return: The decorated function (wrapper).
    :rtype: SyncMethod[T, P, R | None]
    """

    def decorator(
        fn: SyncMethod[T, P, R],
    ) -> SyncMethod[T, P, R | None]:
        argspec = inspect.getfullargspec(fn)

        if not argspec.args or argspec.args[0] != "self":
            raise TypeError(
                "The 'cached' decorator can only be used on methods of a class."
            )

        @functools.wraps(fn)
        def wrapper(
            self: T,
            *args: P.args,
            **kwargs: P.kwargs,
        ) -> R | None:
            """
            The wrapper function that executes the caching logic before
            calling the original decorated function.
            """
            return invoke_cache_adapter(
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
    "Adapter",
    "cached",
)
