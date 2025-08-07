from __future__ import annotations

import pytest

from unittest.mock import AsyncMock, MagicMock

from cacheio import async_cached, AsyncAdapter
from cacheio._async_adapter import invoke_cache_adapter


class TestAsyncCached:
    """Test suite for the async_cached decorator and related functions."""

    @pytest.fixture
    def mock_adapter(self):
        """Provides a mock AsyncAdapter instance with a mocked memoize method."""
        mock_adapter = MagicMock(spec=AsyncAdapter)
        mock_adapter.memoize = AsyncMock()

        return mock_adapter

    class MyAsyncClass:
        """A dummy class to test the async_cached decorator on its methods."""

        def __init__(self, cache_adapter):
            self._cache = cache_adapter

        @async_cached(key_fn=lambda _, a, b: f"key_{a}_{b}", ttl=60)
        async def my_async_method(self, a, b):
            return a + b

        @async_cached(key_fn=lambda _, a, b: f"key_{a}_{b}", ttl=60)
        async def my_method_with_exception(self, a, b):
            raise ValueError("Something went wrong!")

        @async_cached(key_fn=lambda _, x: f"key_{x}", cache_attr="_my_custom_cache")
        async def my_custom_cache_method(self, x):
            return x

    @pytest.mark.asyncio
    async def test_async_cached_decorator_calls_memoize_correctly(self, mock_adapter):
        """
        Verifies that the decorated method's wrapper function correctly uses
        the adapter's async memoize method.
        """
        instance = self.MyAsyncClass(mock_adapter)
        await instance.my_async_method(5, 10)

        mock_adapter.memoize.assert_awaited_once()
        key, fn = mock_adapter.memoize.call_args[0]
        kwargs = mock_adapter.memoize.call_args[1]

        assert key == "key_5_10"
        assert await fn() == 15
        assert kwargs["ttl"] == 60

    @pytest.mark.asyncio
    async def test_async_cached_decorator_propagates_exceptions(self, mock_adapter):
        """
        Tests that an exception raised by the decorated method is correctly propagated.
        """
        instance = self.MyAsyncClass(mock_adapter)

        async def memoize_side_effect(key, fn, ttl):
            return await fn()

        mock_adapter.memoize.side_effect = memoize_side_effect

        with pytest.raises(ValueError, match="Something went wrong!"):
            await instance.my_method_with_exception(5, 10)

        mock_adapter.memoize.assert_awaited_once()

    @pytest.mark.asyncio
    async def test_async_cached_decorator_with_custom_cache_attr(self, mock_adapter):
        """
        Tests that the decorator works correctly with a custom cache attribute name.
        """
        instance = self.MyAsyncClass(mock_adapter)
        setattr(instance, "_my_custom_cache", mock_adapter)

        await instance.my_custom_cache_method(42)

        mock_adapter.memoize.assert_awaited_once()
        key, fn = mock_adapter.memoize.call_args[0]
        assert key == "key_42"
        assert await fn() == 42

    @pytest.mark.asyncio
    async def test_invoke_cache_adapter_raises_if_cache_attr_missing(self):
        """
        Tests that invoke_cache_adapter raises an AttributeError if the cache attribute
        is missing from the instance.
        """

        class NoCacheClass:
            pass

        no_cache_instance = NoCacheClass()

        with pytest.raises(
            AttributeError,
            match="The provided cache attribute `_cache` does not exist.",
        ):

            def key_fn(x):
                return str(x)

            async def fn(self, x):
                return x

            await invoke_cache_adapter(
                self=no_cache_instance,
                key_fn=key_fn,
                cache_attr="_cache",
                fn=fn,
                args=(10,),
                kwargs={},
                ttl=None,
            )

    @pytest.mark.asyncio
    async def test_async_cached_decorator_on_standalone_function_raises_error(self):
        """
        Tests that using the async_cached decorator on a non-method function
        raises an informative TypeError.
        """
        with pytest.raises(
            TypeError,
            match=r"async_cached.*only.*methods.*class",
        ):

            @async_cached(key_fn=lambda _: "key")
            async def standalone_function():
                return 42

    @pytest.mark.asyncio
    async def test_async_cached_decorator_returns_cached_value(self, mock_adapter):
        """
        Verifies that the decorated method returns the value provided by the cache
        adapter. This simulates a cache hit scenario.
        """
        cached_value = "I am a cached value."
        mock_adapter.memoize.return_value = cached_value

        instance = self.MyAsyncClass(mock_adapter)
        result = await instance.my_async_method(1, 2)

        assert result == cached_value
        mock_adapter.memoize.assert_awaited_once_with(
            "key_1_2", mock_adapter.memoize.call_args[0][1], ttl=60
        )
