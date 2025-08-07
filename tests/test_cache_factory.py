from __future__ import annotations

from unittest.mock import patch

import pytest

from cacheio import config, CacheFactory, Adapter, AsyncAdapter

CACHE = "cacheio._cache_factory.Cache"
ASYNC_CACHE = "cacheio._cache_factory.AsyncCache"


class TestCacheFactory:
    """Test suite for the CacheFactory class."""

    def test_memory_cache_creates_adapter_with_default_ttl(self):
        """
        Tests that memory_cache creates a synchronous Adapter with the default TTL
        from the global config.
        """
        with patch(CACHE) as mock_cache_class:
            config.default_ttl = 300
            adapter = CacheFactory.memory_cache()

            assert isinstance(adapter, Adapter)

            mock_cache_class.assert_called_once_with(500, config.default_ttl)

    def test_memory_cache_creates_adapter_with_custom_ttl(self):
        """
        Tests that memory_cache uses a provided custom TTL.
        """
        with patch(CACHE) as mock_cache_class:
            custom_ttl = 600
            adapter = CacheFactory.memory_cache(ttl=custom_ttl)

            assert isinstance(adapter, Adapter)

            mock_cache_class.assert_called_once_with(500, custom_ttl)

    def test_memory_cache_creates_adapter_with_custom_threshold(self):
        """
        Tests that memory_cache uses a provided custom threshold.
        """
        with patch(CACHE) as mock_cache_class:
            custom_threshold = 1000
            adapter = CacheFactory.memory_cache(threshold=custom_threshold)

            assert isinstance(adapter, Adapter)

            mock_cache_class.assert_called_once_with(
                custom_threshold, config.default_ttl
            )

    def test_memory_cache_raises_importerror_if_cachelib_is_not_installed(self):
        """
        Tests that memory_cache raises ImportError if cachelib is missing.
        """
        with patch(CACHE, None):
            with pytest.raises(
                ImportError, match="The 'cachelib' library is not installed."
            ):
                CacheFactory.memory_cache()

    @pytest.mark.asyncio
    async def test_async_memory_cache_creates_async_adapter_with_default_ttl(self):
        """
        Tests that async_memory_cache creates an asynchronous Adapter with the default
        TTL from the global config.
        """
        with patch(ASYNC_CACHE) as mock_async_cache_class:
            config.default_ttl = 300
            adapter = CacheFactory.async_memory_cache()

            assert isinstance(adapter, AsyncAdapter)

            mock_async_cache_class.assert_called_once_with(
                mock_async_cache_class.MEMORY, ttl=config.default_ttl
            )

    @pytest.mark.asyncio
    async def test_async_memory_cache_creates_async_adapter_with_custom_ttl(self):
        """
        Tests that async_memory_cache uses a provided custom TTL.
        """
        with patch(ASYNC_CACHE) as mock_async_cache_class:
            custom_ttl = 900
            adapter = CacheFactory.async_memory_cache(ttl=custom_ttl)
            assert isinstance(adapter, AsyncAdapter)
            mock_async_cache_class.assert_called_once_with(
                mock_async_cache_class.MEMORY, ttl=custom_ttl
            )

    @pytest.mark.asyncio
    async def test_async_memory_cache_creates_adapter_with_custom_kwargs(self):
        """
        Tests that async_memory_cache forwards custom keyword arguments to the
        aiocache constructor.
        """
        with patch(ASYNC_CACHE) as mock_async_cache_class:
            config.default_ttl = 300
            custom_kwargs = {"key": "value"}
            adapter = CacheFactory.async_memory_cache(**custom_kwargs)

            assert isinstance(adapter, AsyncAdapter)

            mock_async_cache_class.assert_called_once_with(
                mock_async_cache_class.MEMORY, ttl=config.default_ttl, **custom_kwargs
            )

    @pytest.mark.asyncio
    async def test_async_memory_cache_raises_importerror_if_aiocache_is_not_installed(
        self,
    ):
        """
        Tests that async_memory_cache raises ImportError if aiocache is missing.
        """
        with patch(ASYNC_CACHE, None):
            with pytest.raises(
                ImportError, match="The 'aiocache' library is not installed."
            ):
                CacheFactory.async_memory_cache()
