from __future__ import annotations

import pytest
from unittest.mock import AsyncMock

from cacheio import AsyncAdapter


class TestAsyncAdapter:
    """Comprehensive test suite for the AsyncAdapter class methods."""

    @pytest.fixture
    def mock_backend(self):
        backend = AsyncMock()
        backend.exists = AsyncMock(return_value=False)
        return backend

    @pytest.fixture
    def adapter(self, mock_backend):
        return AsyncAdapter(mock_backend)

    @pytest.mark.asyncio
    async def test_init_sets_backend_correctly(self, mock_backend):
        adapter_instance = AsyncAdapter(mock_backend)
        assert adapter_instance._backend == mock_backend

    @pytest.mark.asyncio
    async def test_has_calls_backend_exists(self, adapter, mock_backend):
        await adapter.has("test_key")
        mock_backend.exists.assert_awaited_once_with("test_key")

    @pytest.mark.asyncio
    async def test_get_calls_backend_get(self, adapter, mock_backend):
        await adapter.get("test_key")
        mock_backend.get.assert_awaited_once_with("test_key")

    @pytest.mark.asyncio
    async def test_get_many_and_multi_get(self, adapter, mock_backend):
        mock_backend.multi_get.return_value = ["val1", None, "val3"]

        keys = ["key1", "key2", "key3"]

        result1 = await adapter.get_many(*keys)
        result2 = await adapter.multi_get(*keys)

        assert result1 == ["val1", None, "val3"]
        assert result2 == ["val1", None, "val3"]

        mock_backend.multi_get.assert_called_with(keys)

    @pytest.mark.asyncio
    async def test_set_calls_backend_set(self, adapter, mock_backend):
        await adapter.set("test_key", "test_value", ttl=60)
        mock_backend.set.assert_awaited_once_with("test_key", "test_value", ttl=60)

    @pytest.mark.asyncio
    async def test_set_many_and_multi_set(self, adapter, mock_backend):
        mapping = {"key1": "val1", "key2": "val2"}

        await adapter.set_many(mapping, ttl=120)
        await adapter.multi_set(mapping, ttl=120)

        mock_backend.multi_set.assert_called_with(mapping, ttl=120)
        assert mock_backend.multi_set.call_count == 2

    @pytest.mark.asyncio
    async def test_add_returns_true_on_success(self, adapter, mock_backend):
        mock_backend.add.return_value = True

        result = await adapter.add("key", "value", ttl=30)
        assert result is True
        mock_backend.add.assert_awaited_once_with("key", "value", ttl=30)

    @pytest.mark.asyncio
    async def test_get_or_set_cache_hit_does_not_call_fn(self, adapter, mock_backend):
        mock_backend.exists.return_value = True
        mock_backend.get.return_value = "cached_value"
        mock_fn = AsyncMock(return_value="new_value")

        result = await adapter.get_or_set("test_key", mock_fn)

        assert result == "cached_value"

        mock_backend.exists.assert_awaited_once_with("test_key")
        mock_backend.get.assert_awaited_once_with("test_key")
        mock_fn.assert_not_awaited()
        mock_backend.set.assert_not_awaited()

    @pytest.mark.asyncio
    async def test_get_or_set_cache_miss_calls_fn_and_sets_value(
        self, adapter, mock_backend
    ):
        mock_backend.exists.return_value = False
        mock_fn = AsyncMock(return_value="new_value")

        result = await adapter.get_or_set("test_key", mock_fn, ttl=60)

        assert result == "new_value"

        mock_backend.exists.assert_awaited_once_with("test_key")
        mock_fn.assert_awaited_once()
        mock_backend.get.assert_not_awaited()
        mock_backend.set.assert_awaited_once_with("test_key", "new_value", ttl=60)

    @pytest.mark.asyncio
    async def test_get_or_set_caches_none_value(self, adapter, mock_backend):
        mock_backend.exists.return_value = False
        mock_fn = AsyncMock(return_value=None)

        result1 = await adapter.get_or_set("test_key", mock_fn)
        assert result1 is None

        mock_backend.exists.assert_awaited_once_with("test_key")
        mock_fn.assert_awaited_once()
        mock_backend.set.assert_awaited_once_with("test_key", None, ttl=None)

        mock_backend.exists.reset_mock()
        mock_backend.get.reset_mock()
        mock_fn.reset_mock()
        mock_backend.set.reset_mock()

        mock_backend.exists.return_value = True
        mock_backend.get.return_value = None

        result2 = await adapter.get_or_set("test_key", mock_fn)
        assert result2 is None

        mock_backend.exists.assert_awaited_once_with("test_key")
        mock_backend.get.assert_awaited_once_with("test_key")
        mock_fn.assert_not_awaited()
        mock_backend.set.assert_not_awaited()

    @pytest.mark.asyncio
    async def test_get_or_set_propagates_exceptions(self, adapter, mock_backend):
        mock_backend.exists.return_value = False
        mock_fn = AsyncMock(side_effect=ValueError("Test exception"))

        with pytest.raises(ValueError, match="Test exception"):
            await adapter.get_or_set("test_key", mock_fn)

        mock_backend.exists.assert_awaited_once_with("test_key")
        mock_fn.assert_awaited_once()
        mock_backend.set.assert_not_awaited()

    @pytest.mark.asyncio
    async def test_get_or_set_on_cache_miss_without_ttl(self, adapter, mock_backend):
        mock_backend.exists.return_value = False
        mock_fn = AsyncMock(return_value="new_value")

        result = await adapter.get_or_set("test_key", mock_fn)

        assert result == "new_value"

        mock_backend.exists.assert_awaited_once_with("test_key")
        mock_fn.assert_awaited_once()
        mock_backend.set.assert_awaited_once_with("test_key", "new_value", ttl=None)

    @pytest.mark.asyncio
    async def test_delete_calls_backend_delete_and_normalizes(
        self, adapter, mock_backend
    ):
        mock_backend.delete.return_value = 1
        result = await adapter.delete("test_key")

        assert result is True
        mock_backend.delete.assert_awaited_once_with("test_key")

    @pytest.mark.asyncio
    async def test_delete_many_and_multi_delete(self, adapter, mock_backend):
        keys = ["key1", "key2"]

        await adapter.delete_many(*keys)
        await adapter.multi_delete(*keys)

        mock_backend.delete.assert_any_await("key1")
        mock_backend.delete.assert_any_await("key2")
        # Called twice for each key because both methods iterate keys independently
        assert mock_backend.delete.await_count == len(keys) * 2

    @pytest.mark.asyncio
    async def test_increment_and_decrement(self, adapter, mock_backend):
        mock_backend.increment.return_value = 5

        inc_result = await adapter.increment("counter", amount=2)
        dec_result = await adapter.decrement("counter", amount=1)

        assert inc_result == 5
        assert dec_result == 5  # decrement calls increment with negative amount

        mock_backend.increment.assert_any_await("counter", 2)
        mock_backend.increment.assert_any_await("counter", -1)

    @pytest.mark.asyncio
    async def test_clear_calls_backend_clear(self, adapter, mock_backend):
        mock_backend.clear.return_value = True
        result = await adapter.clear()

        assert result is True
        mock_backend.clear.assert_awaited_once()
