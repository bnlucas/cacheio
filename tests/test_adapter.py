from __future__ import annotations

import pytest
from unittest.mock import MagicMock

from cacheio import Adapter


class TestAdapter:
    """Comprehensive test suite for the Adapter class methods."""

    @pytest.fixture
    def mock_backend(self):
        """Provides a mock backend for the Adapter."""
        backend = MagicMock()
        backend.has = MagicMock(return_value=False)
        return backend

    @pytest.fixture
    def adapter(self, mock_backend):
        """Provides a real Adapter instance with a mock backend."""
        return Adapter(mock_backend)

    # Core method tests

    def test_get_calls_backend_get(self, adapter, mock_backend):
        adapter.get("test_key")
        mock_backend.get.assert_called_once_with("test_key")

    def test_set_calls_backend_set(self, adapter, mock_backend):
        adapter.set("test_key", "test_value", ttl=300)
        mock_backend.set.assert_called_once_with("test_key", "test_value", timeout=300)

    def test_delete_calls_backend_delete(self, adapter, mock_backend):
        adapter.delete("test_key")
        mock_backend.delete.assert_called_once_with("test_key")

    def test_clear_calls_backend_clear(self, adapter, mock_backend):
        mock_backend.clear.return_value = True
        result = adapter.clear()
        assert result is True
        mock_backend.clear.assert_called_once()

    def test_get_or_set_cache_hit_does_not_call_fn(self, adapter, mock_backend):
        mock_backend.has.return_value = True
        mock_backend.get.return_value = "cached_value"
        mock_fn = MagicMock(return_value="new_value")

        result = adapter.get_or_set("test_key", mock_fn)

        assert result == "cached_value"
        mock_backend.has.assert_called_once_with("test_key")
        mock_backend.get.assert_called_once_with("test_key")
        mock_fn.assert_not_called()
        mock_backend.set.assert_not_called()

    def test_get_or_set_cache_miss_calls_fn_and_sets_value(self, adapter, mock_backend):
        mock_backend.has.return_value = False
        mock_fn = MagicMock(return_value="new_value")

        result = adapter.get_or_set("test_key", mock_fn, ttl=60)

        assert result == "new_value"
        mock_backend.has.assert_called_once_with("test_key")
        mock_fn.assert_called_once()
        mock_backend.get.assert_not_called()
        mock_backend.set.assert_called_once_with("test_key", "new_value", timeout=60)

    def test_get_or_set_caches_none_value(self, adapter, mock_backend):
        mock_backend.has.return_value = False
        mock_fn = MagicMock(return_value=None)

        result1 = adapter.get_or_set("test_key", mock_fn)

        assert result1 is None
        mock_backend.has.assert_called_once_with("test_key")
        mock_fn.assert_called_once()
        mock_backend.set.assert_called_once_with("test_key", None, timeout=None)

        mock_backend.has.reset_mock()
        mock_backend.get.reset_mock()
        mock_fn.reset_mock()
        mock_backend.set.reset_mock()

        mock_backend.has.return_value = True
        mock_backend.get.return_value = None

        result2 = adapter.get_or_set("test_key", mock_fn)

        assert result2 is None
        mock_backend.has.assert_called_once_with("test_key")
        mock_backend.get.assert_called_once_with("test_key")
        mock_fn.assert_not_called()
        mock_backend.set.assert_not_called()

    def test_get_or_set_propagates_exceptions(self, adapter, mock_backend):
        mock_backend.has.return_value = False
        mock_fn = MagicMock(side_effect=ValueError("Test exception"))

        with pytest.raises(ValueError, match="Test exception"):
            adapter.get_or_set("test_key", mock_fn)

        mock_backend.has.assert_called_once_with("test_key")
        mock_fn.assert_called_once()
        mock_backend.set.assert_not_called()

    def test_get_or_set_on_cache_miss_without_ttl(self, adapter, mock_backend):
        mock_backend.has.return_value = False
        mock_fn = MagicMock(return_value="new_value")

        result = adapter.get_or_set("test_key", mock_fn)

        assert result == "new_value"
        mock_backend.has.assert_called_once_with("test_key")
        mock_fn.assert_called_once()
        mock_backend.set.assert_called_once_with("test_key", "new_value", timeout=None)

    def test_has_calls_backend_has(self, adapter, mock_backend):
        mock_backend.has.return_value = True
        result = adapter.has("test_key")

        assert result is True
        mock_backend.has.assert_called_once_with("test_key")

        mock_backend.has.reset_mock()
        mock_backend.has.return_value = False
        result = adapter.has("another_key")

        assert result is False
        mock_backend.has.assert_called_once_with("another_key")

    # Bulk method tests

    def test_get_many_and_multi_get(self, adapter, mock_backend):
        mock_backend.get_many.return_value = ["val1", None, "val3"]

        keys = ["key1", "key2", "key3"]

        result1 = adapter.get_many(*keys)
        result2 = adapter.multi_get(*keys)

        assert result1 == ["val1", None, "val3"]
        assert result2 == ["val1", None, "val3"]

        mock_backend.get_many.assert_called_with(*keys)

    def test_set_many_and_multi_set(self, adapter, mock_backend):
        mapping = {"key1": "val1", "key2": "val2"}

        adapter.set_many(mapping, ttl=120)
        adapter.multi_set(mapping, ttl=120)

        mock_backend.set_many.assert_called_with(mapping, timeout=120)
        assert mock_backend.set_many.call_count == 2

    def test_delete_many_and_multi_delete(self, adapter, mock_backend):
        keys = ["key1", "key2"]

        adapter.delete_many(*keys)
        adapter.multi_delete(*keys)

        mock_backend.delete_many.assert_called_with(*keys)
        assert mock_backend.delete_many.call_count == 2

    def test_add_returns_true_on_success(self, adapter, mock_backend):
        mock_backend.add.return_value = True

        result = adapter.add("key", "value", ttl=30)
        assert result is True
        mock_backend.add.assert_called_once_with("key", "value", timeout=30)

    def test_increment_and_decrement(self, adapter, mock_backend):
        mock_backend.inc.return_value = 5
        mock_backend.dec.return_value = 3

        inc_result = adapter.increment("counter", amount=2)
        dec_result = adapter.decrement("counter", amount=1)

        assert inc_result == 5
        assert dec_result == 3

        mock_backend.inc.assert_called_once_with("counter", 2)
        mock_backend.dec.assert_called_once_with("counter", 1)
