from __future__ import annotations

import pytest

from unittest.mock import AsyncMock

from cacheio import AsyncAdapter


class TestAsyncAdapter:
    """Test suite for the AsyncAdapter class methods."""

    @pytest.fixture
    def mock_backend(self):
        """Provides an async mock backend for the AsyncAdapter."""
        backend = AsyncMock()
        backend.exists = AsyncMock(return_value=False)

        return backend

    @pytest.fixture
    def adapter(self, mock_backend):
        """Provides a real AsyncAdapter instance with a mock backend."""
        return AsyncAdapter(mock_backend)

    @pytest.mark.asyncio
    async def test_init_sets_backend_correctly(self, mock_backend):
        """Verifies that __init__ sets the internal _backend attribute."""
        adapter_instance = AsyncAdapter(mock_backend)
        assert adapter_instance._backend == mock_backend

    @pytest.mark.asyncio
    async def test_has_calls_backend_exists(self, adapter, mock_backend):
        """Verifies that the has method awaits the backend's exists method."""
        await adapter.has("test_key")
        mock_backend.exists.assert_awaited_once_with("test_key")

    @pytest.mark.asyncio
    async def test_get_calls_backend_get(self, adapter, mock_backend):
        """Verifies that the get method awaits the backend's get method."""
        await adapter.get("test_key")
        mock_backend.get.assert_awaited_once_with("test_key")

    @pytest.mark.asyncio
    async def test_set_calls_backend_set(self, adapter, mock_backend):
        """Verifies that the set method awaits the backend's set method."""
        await adapter.set("test_key", "test_value", ttl=60)
        mock_backend.set.assert_awaited_once_with("test_key", "test_value", ttl=60)

    @pytest.mark.asyncio
    async def test_delete_calls_backend_delete(self, adapter, mock_backend):
        """
        Verifies that the delete method awaits the backend's delete method and
        normalizes the result.
        """
        mock_backend.delete.return_value = 1
        result = await adapter.delete("test_key")

        assert result is True
        mock_backend.delete.assert_awaited_once_with("test_key")

    @pytest.mark.asyncio
    async def test_clear_calls_backend_clear(self, adapter, mock_backend):
        """
        Tests that the Adapter's clear method calls the backend's clear method and
        returns its result.
        """
        mock_backend.clear.return_value = True
        result = await adapter.clear()

        assert result is True
        mock_backend.clear.assert_awaited_once()

    @pytest.mark.asyncio
    async def test_memoize_on_cache_hit_does_not_call_fn(self, adapter, mock_backend):
        """
        Tests that memoize returns the cached value on a cache hit without executing
        the provided function.
        """
        # A cache hit means the key exists
        mock_backend.exists.return_value = True
        mock_backend.get.return_value = "cached_value"
        mock_fn = AsyncMock(return_value="new_value")

        result = await adapter.memoize("test_key", mock_fn)

        assert result == "cached_value"

        mock_backend.exists.assert_awaited_once_with("test_key")
        mock_backend.get.assert_awaited_once_with("test_key")
        mock_fn.assert_not_awaited()
        mock_backend.set.assert_not_awaited()

    @pytest.mark.asyncio
    async def test_memoize_on_cache_miss_calls_fn_and_sets_value(
        self, adapter, mock_backend
    ):
        """
        Tests that memoize executes the function on a cache miss and caches the result.
        """
        # A cache miss means the key does not exist
        mock_backend.exists.return_value = False
        mock_fn = AsyncMock(return_value="new_value")

        result = await adapter.memoize("test_key", mock_fn, ttl=60)

        assert result == "new_value"

        mock_backend.exists.assert_awaited_once_with("test_key")
        mock_fn.assert_awaited_once()
        mock_backend.get.assert_not_awaited()
        mock_backend.set.assert_awaited_once_with("test_key", "new_value", ttl=60)

    @pytest.mark.asyncio
    async def test_memoize_caches_none_value(self, adapter, mock_backend):
        """
        Tests that memoize correctly caches and returns a None value.
        """
        # A cache miss means the key does not exist
        mock_backend.exists.return_value = False
        mock_fn = AsyncMock(return_value=None)

        # First call: cache miss, fn is executed
        result1 = await adapter.memoize("test_key", mock_fn)

        assert result1 is None
        mock_backend.exists.assert_awaited_once_with("test_key")
        mock_fn.assert_awaited_once()
        mock_backend.set.assert_awaited_once_with("test_key", None, ttl=None)

        # Reset mocks for the second call
        mock_backend.exists.reset_mock()
        mock_backend.get.reset_mock()
        mock_fn.reset_mock()
        mock_backend.set.reset_mock()

        # Second call: cache hit, fn is not executed
        mock_backend.exists.return_value = True
        mock_backend.get.return_value = None

        result2 = await adapter.memoize("test_key", mock_fn)

        assert result2 is None

        mock_backend.exists.assert_awaited_once_with("test_key")
        mock_backend.get.assert_awaited_once_with("test_key")
        mock_fn.assert_not_awaited()
        mock_backend.set.assert_not_awaited()

    @pytest.mark.asyncio
    async def test_memoize_propagates_exceptions(self, adapter, mock_backend):
        """
        Tests that memoize does not catch exceptions raised by the provided function.
        """
        # A cache miss means the key does not exist
        mock_backend.exists.return_value = False
        mock_fn = AsyncMock(side_effect=ValueError("Test exception"))

        with pytest.raises(ValueError, match="Test exception"):
            await adapter.memoize("test_key", mock_fn)

        mock_backend.exists.assert_awaited_once_with("test_key")
        mock_fn.assert_awaited_once()
        mock_backend.set.assert_not_awaited()

    @pytest.mark.asyncio
    async def test_memoize_on_cache_miss_without_ttl(self, adapter, mock_backend):
        """
        Tests that memoize works correctly when ttl is not provided.
        """
        # A cache miss means the key does not exist
        mock_backend.exists.return_value = False
        mock_fn = AsyncMock(return_value="new_value")

        result = await adapter.memoize("test_key", mock_fn)

        assert result == "new_value"

        mock_backend.exists.assert_awaited_once_with("test_key")
        mock_fn.assert_awaited_once()
        mock_backend.set.assert_awaited_once_with("test_key", "new_value", ttl=None)
