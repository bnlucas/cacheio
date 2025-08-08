from __future__ import annotations

import pytest
from unittest.mock import AsyncMock, MagicMock

from cacheio import async_cached, async_memoized, AsyncAdapter


class TestAsyncCacheDecorators:
    """Test suite for the async_cached decorator and async_memoized decorator."""

    @pytest.fixture
    def mock_adapter(self):
        """Provides a mock AsyncAdapter instance with a mocked get_or_set method."""
        mock_adapter = MagicMock(spec=AsyncAdapter)
        mock_adapter.get_or_set = AsyncMock()
        return mock_adapter

    class MyAsyncClass:
        """Dummy class to test async_cached and async_memoized decorators."""

        def __init__(self, cache_adapter):
            self._cache = cache_adapter
            self._custom_cache = cache_adapter

        @async_cached(ttl=60)
        async def my_async_method(self, a, b):
            return a + b

        @async_cached()
        async def my_method_without_ttl(self, x):
            return x * 2

        @async_cached(ttl=5, cache_attr="_custom_cache")
        async def my_custom_cache_method(self, val):
            return val

        @async_memoized(key_fn=lambda self, x: f"key_{x}", ttl=120)
        async def my_async_memoized(self, x):
            return x * 10

        @async_cached()
        async def method_raises(self, a):
            raise ValueError("Oops!")

    @pytest.mark.asyncio
    async def test_async_cached_calls_get_or_set_correctly(self, mock_adapter):
        instance = self.MyAsyncClass(mock_adapter)

        async def side_effect(key, fn, ttl=None):
            return await fn()

        mock_adapter.get_or_set.side_effect = side_effect

        result = await instance.my_async_method(1, 2)

        assert result == 3

        mock_adapter.get_or_set.assert_awaited_once()
        key_arg, fn_arg = mock_adapter.get_or_set.call_args[0][:2]
        ttl_arg = mock_adapter.get_or_set.call_args[1].get("ttl")

        assert (
            key_arg == f"{instance.my_async_method.__module__}"
            f".{instance.my_async_method.__qualname__}"
        )
        assert callable(fn_arg)
        assert ttl_arg == 60

    @pytest.mark.asyncio
    async def test_async_cached_returns_cached_value(self, mock_adapter):
        instance = self.MyAsyncClass(mock_adapter)
        cached_value = "cached result"

        mock_adapter.get_or_set.return_value = cached_value

        result = await instance.my_async_method(5, 10)

        assert result == cached_value
        mock_adapter.get_or_set.assert_awaited_once()

    @pytest.mark.asyncio
    async def test_async_cached_propagates_exceptions(self, mock_adapter):
        instance = self.MyAsyncClass(mock_adapter)

        async def raise_exc():
            raise ValueError("Test error")

        async def side_effect(key, fn, ttl=None):
            return await raise_exc()

        mock_adapter.get_or_set.side_effect = side_effect

        with pytest.raises(ValueError, match="Test error"):
            await instance.my_async_method(1, 2)

    @pytest.mark.asyncio
    async def test_async_cached_with_custom_cache_attr(self, mock_adapter):
        instance = self.MyAsyncClass(mock_adapter)

        await instance.my_custom_cache_method("abc")

        mock_adapter.get_or_set.assert_awaited_once()
        key_arg = mock_adapter.get_or_set.call_args[0][0]
        assert (
            key_arg == f"{instance.my_custom_cache_method.__module__}"
            f".{instance.my_custom_cache_method.__qualname__}"
        )

    @pytest.mark.asyncio
    async def test_async_cached_without_ttl_works(self, mock_adapter):
        instance = self.MyAsyncClass(mock_adapter)

        await instance.my_method_without_ttl(3)

        mock_adapter.get_or_set.assert_awaited_once()
        ttl_arg = mock_adapter.get_or_set.call_args[1].get("ttl")
        assert ttl_arg is None

    @pytest.mark.asyncio
    async def test_async_memoized_calls_get_or_set_with_key_fn(self, mock_adapter):
        instance = self.MyAsyncClass(mock_adapter)

        async def fake_fn():
            return 100

        async def side_effect(key, fn, ttl=None):
            return await fake_fn()

        mock_adapter.get_or_set.side_effect = side_effect
        result = await instance.my_async_memoized(7)

        assert result == 100
        mock_adapter.get_or_set.assert_awaited_once()

        key_arg = mock_adapter.get_or_set.call_args[0][0]
        expected_key = "key_7"
        assert key_arg == expected_key

        ttl_arg = mock_adapter.get_or_set.call_args[1].get("ttl")
        assert ttl_arg == 120

    @pytest.mark.asyncio
    async def test_async_cached_raises_on_standalone_function(self):
        with pytest.raises(TypeError, match="async_cache.*only.*methods.*class"):

            @async_cached()
            async def standalone():
                return 123

    @pytest.mark.asyncio
    async def test_async_cached_raises_if_not_method(self):
        # Trying to decorate a staticmethod or classmethod without self should raise
        with pytest.raises(TypeError, match="async_cache.*only.*methods.*class"):

            class C:
                @staticmethod
                @async_cached()
                async def foo():
                    return 1

            await C.foo()
