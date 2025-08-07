from __future__ import annotations

import pytest

from unittest.mock import patch, MagicMock, AsyncMock

from cacheio import AsyncAdapter, async_cached
from cacheio.mixins import AsyncCacheable


class TestAsyncCacheableIntegration:
    """Test suite for the AsyncCacheable mixin's integration behavior."""

    @patch("cacheio._cache_factory.CacheFactory.async_memory_cache")
    @pytest.mark.asyncio
    async def test_init_calls_super_init(self, mock_factory):
        """Tests that the mixin's __init__ calls the parent's __init__."""
        mock_adapter = MagicMock(spec=AsyncAdapter)
        mock_factory.return_value = mock_adapter

        class MockParent:
            def __init__(self, *args, **kwargs):
                self.init_called = True

        class MyClass(AsyncCacheable, MockParent):
            pass

        instance = MyClass()

        assert instance.init_called is True
        assert instance._cache is mock_adapter

    @patch("cacheio._cache_factory.CacheFactory.async_memory_cache")
    @pytest.mark.asyncio
    async def test_decorated_method_uses_mixin_cache(self, mock_factory):
        """
        Tests that a decorated async method can successfully use the mixin's cache.
        """
        mock_adapter = MagicMock(spec=AsyncAdapter)
        mock_factory.return_value = mock_adapter

        class MyClass(AsyncCacheable):
            @async_cached(key_fn=lambda _, x: f"key_{x}")
            async def my_async_method(self, x):
                return x * 2

        instance = MyClass()
        await instance.my_async_method(5)

        mock_adapter.memoize.assert_awaited_once()
        key, fn = mock_adapter.memoize.call_args[0]

        assert key == "key_5"
        assert await fn() == 10

    @patch("cacheio._cache_factory.CacheFactory.async_memory_cache")
    @pytest.mark.asyncio
    async def test_complex_inheritance_hierarchy(self, mock_factory):
        """
        Tests that the mixin works correctly with a more complex class hierarchy,
        ensuring the Method Resolution Order is not broken.
        """
        mock_factory.return_value = MagicMock(spec=AsyncAdapter)

        class Grandparent:
            def __init__(self, *args, **kwargs):
                self.grandparent_init_called = True
                super().__init__(*args, **kwargs)

        class Parent(Grandparent):
            def __init__(self, *args, **kwargs):
                self.parent_init_called = True
                super().__init__(*args, **kwargs)

        class MyClass(AsyncCacheable, Parent):
            def __init__(self, *args, **kwargs):
                self.my_class_init_called = True
                super().__init__(*args, **kwargs)

        instance = MyClass()

        assert instance.my_class_init_called is True
        assert instance.parent_init_called is True
        assert instance.grandparent_init_called is True
        assert hasattr(instance, "_cache")

    @patch("cacheio._cache_factory.CacheFactory.async_memory_cache")
    @pytest.mark.asyncio
    async def test_decorated_method_with_custom_cache_attr(self, mock_default_factory):
        """
        Tests that a decorated method can use a custom cache attribute,
        bypassing the default cache provided by the mixin.
        """
        # A mock for the custom cache attribute.
        mock_custom_adapter = MagicMock(spec=AsyncAdapter)
        mock_custom_adapter.memoize = AsyncMock()

        # The mixin will still try to create a default cache, but it won't be used.
        mock_default_factory.return_value = MagicMock(spec=AsyncAdapter)

        class MyClass(AsyncCacheable):
            def __init__(self):
                super().__init__()
                # Manually set the custom cache attribute.
                self._my_other_cache = mock_custom_adapter

            @async_cached(key_fn=lambda _, x: f"key_{x}", cache_attr="_my_other_cache")
            async def my_async_method(self, x):
                return x * 3

        instance = MyClass()
        await instance.my_async_method(10)

        # Assert that the custom cache's memoize method was called, not the default one.
        mock_custom_adapter.memoize.assert_awaited_once()
        mock_default_factory.return_value.memoize.assert_not_awaited()

        key, fn = mock_custom_adapter.memoize.call_args[0]
        assert key == "key_10"
        assert await fn() == 30
