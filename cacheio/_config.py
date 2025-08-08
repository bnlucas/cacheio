"""
A global configuration object for the caching library.

This module allows users to modify default settings, such as the time-to-live
(TTL) for cached items, in a centralized manner.
"""

from __future__ import annotations

from typing import Callable, Literal, TypeVar, cast, overload


T = TypeVar("T")
IntLiteral = Literal["default_ttl", "default_threshold"]


class Config:
    """A simple configuration object to store global settings for the caching library.

    :ivar default_ttl: The default time-to-live in seconds for cache entries if no
                       specific TTL is provided.
    :vartype default_ttl: int
    :ivar default_threshold: The default entries threshold the cache backend holds.
    :vartype default_threshold: int
    """

    __slots__ = (
        "default_ttl",
        "default_threshold",
    )

    def __init__(self) -> None:
        self.default_ttl: int = 300
        self.default_threshold: int = 500

    @overload
    def get(self, attr: IntLiteral, override: int | None = None) -> int: ...

    @overload
    def get(self, attr: str, override: T | None = None) -> T: ...

    def get(self, attr: str, override: T | None = None) -> T:
        """
        Retrieve a configuration attribute value.

        :param attr: The name of the attribute to retrieve.
        :type attr: str
        :param override: The default value to return if the attribute does not exist.
        :type override: T
        :return: The attribute value or the provided default.
        :rtype: T
        :raises AttributeError: If the attribute does not exist
        """
        if not hasattr(self, attr):
            raise AttributeError(f"Unknown configuration attribute: '{attr}'")

        if override is not None:
            return cast(T, override)

        value = getattr(self, attr)
        return cast(T, value)


config = Config()


def configure(
    fn: Callable[[Config], None],
) -> None:
    """
    Passes the global configuration object to a function for modification.

    :param fn: A function that takes a Config object as its single argument.
    :type fn: Callable[[Config], None]
    """
    if not callable(fn):
        raise TypeError("The 'fn' argument must be a callable.")

    fn(config)


__all__ = (
    "config",
    "configure",
)
