from __future__ import annotations

from unittest.mock import patch

import pytest

from cacheio import config, CacheFactory, Adapter, AsyncAdapter

CACHE = "cacheio._cache_factory.SyncCache"
REDIS_CACHE = "cacheio._cache_factory.SyncRedisCache"
ASYNC_CACHE = "cacheio._cache_factory.AsyncCache"


class TestCacheFactory:
    """Test suite for the CacheFactory class."""

    def test_memory_cache_creates_adapter_with_default_ttl_and_threshold(self):
        """
        Tests memory_cache creates Adapter with default TTL and threshold from config.
        """
        with patch(CACHE) as mock_cache_class:
            config.default_ttl = 300
            config.default_threshold = 500
            adapter = CacheFactory.memory_cache()

            assert isinstance(adapter, Adapter)
            mock_cache_class.assert_called_once_with(500, 300)

    def test_memory_cache_creates_adapter_with_custom_ttl(self):
        """
        Tests memory_cache uses provided custom TTL.
        """
        with patch(CACHE) as mock_cache_class:
            config.default_threshold = 500
            custom_ttl = 600
            adapter = CacheFactory.memory_cache(ttl=custom_ttl)

            assert isinstance(adapter, Adapter)
            mock_cache_class.assert_called_once_with(500, custom_ttl)

    def test_memory_cache_creates_adapter_with_custom_threshold(self):
        """
        Tests memory_cache uses provided custom threshold.
        """
        with patch(CACHE) as mock_cache_class:
            config.default_ttl = 300
            custom_threshold = 1000
            adapter = CacheFactory.memory_cache(threshold=custom_threshold)

            assert isinstance(adapter, Adapter)
            mock_cache_class.assert_called_once_with(custom_threshold, 300)

    def test_memory_cache_raises_importerror_if_cachelib_not_installed(self):
        """
        Tests memory_cache raises ImportError if cachelib not loaded.
        """
        with patch("cacheio._cache_factory.CACHELIB_LOADED", False), patch(CACHE, None):
            with pytest.raises(
                ImportError,
                match="The 'cachelib' library is not installed.",
            ):
                CacheFactory.memory_cache()

    def test_redis_cache_creates_adapter_with_defaults(self):
        """
        Tests redis_cache creates Adapter with default params from config.
        """
        with patch(REDIS_CACHE) as mock_redis_cache_class:
            config.default_ttl = 300
            adapter = CacheFactory.redis_cache()

            assert isinstance(adapter, Adapter)
            mock_redis_cache_class.assert_called_once_with(
                host="localhost",
                port=6379,
                password=None,
                db=0,
                default_timeout=300,
                key_prefix=None,
            )

    def test_redis_cache_creates_adapter_with_custom_params(self):
        """
        Tests redis_cache creates Adapter with custom parameters.
        """
        with patch(REDIS_CACHE) as mock_redis_cache_class:
            adapter = CacheFactory.redis_cache(
                ttl=900,
                host="redis.local",
                port=6380,
                password="secret",
                db=2,
                namespace="prefix",
                extra_arg="foo",
            )

            assert isinstance(adapter, Adapter)
            mock_redis_cache_class.assert_called_once_with(
                host="redis.local",
                port=6380,
                password="secret",
                db=2,
                default_timeout=900,
                key_prefix="prefix",
                extra_arg="foo",
            )

    @pytest.mark.asyncio
    async def test_async_memory_cache_creates_async_adapter_with_default_ttl(self):
        """
        Tests async_memory_cache creates AsyncAdapter with default TTL from config.
        """
        with patch(ASYNC_CACHE) as mock_async_cache_class:
            config.default_ttl = 300
            adapter = CacheFactory.async_memory_cache()

            assert isinstance(adapter, AsyncAdapter)
            mock_async_cache_class.assert_called_once_with(
                mock_async_cache_class.MEMORY, ttl=300
            )

    @pytest.mark.asyncio
    async def test_async_memory_cache_creates_async_adapter_with_custom_ttl(self):
        """
        Tests async_memory_cache uses provided custom TTL.
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
        Tests async_memory_cache forwards custom kwargs to aiocache.Cache.
        """
        with patch(ASYNC_CACHE) as mock_async_cache_class:
            config.default_ttl = 300
            custom_kwargs = {"key": "value"}
            adapter = CacheFactory.async_memory_cache(**custom_kwargs)

            assert isinstance(adapter, AsyncAdapter)
            mock_async_cache_class.assert_called_once_with(
                mock_async_cache_class.MEMORY, ttl=300, **custom_kwargs
            )

    @pytest.mark.asyncio
    async def test_async_memory_cache_raises_importerror_if_aiocache_not_installed(
        self,
    ):
        """
        Tests async_memory_cache raises ImportError if aiocache not loaded.
        """
        with patch("cacheio._cache_factory.AIOCACHE_LOADED", False), patch(
            ASYNC_CACHE, None
        ):
            with pytest.raises(
                ImportError,
                match="The 'aiocache' library is not installed.",
            ):
                CacheFactory.async_memory_cache()

    @pytest.mark.asyncio
    async def test_async_redis_cache_creates_adapter_with_defaults(self):
        """
        Tests async_redis_cache creates AsyncAdapter with default params from config.
        """
        with patch(ASYNC_CACHE) as mock_async_cache_class:
            config.default_ttl = 300
            adapter = CacheFactory.async_redis_cache()

            assert isinstance(adapter, AsyncAdapter)
            mock_async_cache_class.assert_called_once_with(
                mock_async_cache_class.REDIS,
                endpoint="localhost",
                port=6379,
                password=None,
                db=0,
                timeout=300,
                namespace=None,
            )

    @pytest.mark.asyncio
    async def test_async_redis_cache_creates_adapter_with_custom_params(self):
        """
        Tests async_redis_cache creates AsyncAdapter with custom parameters including
        callable namespace.
        """
        with patch(ASYNC_CACHE) as mock_async_cache_class:
            # Namespace as string
            adapter = CacheFactory.async_redis_cache(
                ttl=900,
                host="redis.local",
                port=6380,
                password="secret",
                db=2,
                namespace="prefix",
                extra_arg="foo",
            )
            assert isinstance(adapter, AsyncAdapter)
            mock_async_cache_class.assert_called_with(
                mock_async_cache_class.REDIS,
                endpoint="redis.local",
                port=6380,
                password="secret",
                db=2,
                timeout=900,
                namespace="prefix",
                extra_arg="foo",
            )

            # Namespace as callable
            mock_async_cache_class.reset_mock()

            def namespace_callable():
                return "callable_prefix"

            adapter = CacheFactory.async_redis_cache(
                namespace=namespace_callable,
            )
            assert isinstance(adapter, AsyncAdapter)
            mock_async_cache_class.assert_called_with(
                mock_async_cache_class.REDIS,
                endpoint="localhost",
                port=6379,
                password=None,
                db=0,
                timeout=300,
                namespace="callable_prefix",
            )
