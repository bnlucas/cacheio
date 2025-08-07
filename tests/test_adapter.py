# In tests/test_adapter.py

from __future__ import annotations

import pytest

from unittest.mock import MagicMock

from cacheio import Adapter


class TestAdapter:
    """Test suite for the Adapter class methods."""

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

    def test_get_calls_backend_get(self, adapter, mock_backend):
        """Verifies that the Adapter's get method calls the backend's get method."""
        adapter.get("test_key")
        mock_backend.get.assert_called_once_with("test_key")

    def test_set_calls_backend_set(self, adapter, mock_backend):
        """Verifies that the Adapter's set method calls the backend's set method."""
        adapter.set("test_key", "test_value", ttl=300)
        mock_backend.set.assert_called_once_with("test_key", "test_value", timeout=300)

    def test_delete_calls_backend_delete(self, adapter, mock_backend):
        """
        Verifies that the Adapter's delete method calls the backend's delete method.
        """
        adapter.delete("test_key")
        mock_backend.delete.assert_called_once_with("test_key")

    def test_clear_calls_backend_clear(self, adapter, mock_backend):
        """
        Tests that the Adapter's clear method calls the backend's clear method and
        returns its result.
        """
        mock_backend.clear.return_value = True
        result = adapter.clear()

        assert result is True
        mock_backend.clear.assert_called_once()

    def test_memoize_on_cache_hit_does_not_call_fn(self, adapter, mock_backend):
        """
        Tests that memoize returns the cached value on a cache hit without executing
        the provided function.
        """
        mock_backend.has.return_value = True
        mock_backend.get.return_value = "cached_value"
        mock_fn = MagicMock(return_value="new_value")

        result = adapter.memoize("test_key", mock_fn)

        assert result == "cached_value"

        mock_backend.has.assert_called_once_with("test_key")
        mock_backend.get.assert_called_once_with("test_key")
        mock_fn.assert_not_called()
        mock_backend.set.assert_not_called()

    def test_memoize_on_cache_miss_calls_fn_and_sets_value(self, adapter, mock_backend):
        """
        Tests that memoize executes the function on a cache miss and caches the result.
        """
        mock_backend.has.return_value = False
        mock_fn = MagicMock(return_value="new_value")

        result = adapter.memoize("test_key", mock_fn, ttl=60)

        assert result == "new_value"

        mock_backend.has.assert_called_once_with("test_key")
        mock_fn.assert_called_once()
        mock_backend.get.assert_not_called()
        mock_backend.set.assert_called_once_with("test_key", "new_value", timeout=60)

    def test_memoize_caches_none_value(self, adapter, mock_backend):
        """
        Tests that memoize correctly caches and returns a None value.
        """
        mock_backend.has.return_value = False
        mock_fn = MagicMock(return_value=None)

        result1 = adapter.memoize("test_key", mock_fn)

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

        result2 = adapter.memoize("test_key", mock_fn)

        assert result2 is None

        mock_backend.has.assert_called_once_with("test_key")
        mock_backend.get.assert_called_once_with("test_key")
        mock_fn.assert_not_called()
        mock_backend.set.assert_not_called()

    def test_memoize_propagates_exceptions(self, adapter, mock_backend):
        """
        Tests that memoize does not catch exceptions raised by the provided function.
        """
        mock_backend.has.return_value = False
        mock_fn = MagicMock(side_effect=ValueError("Test exception"))

        with pytest.raises(ValueError, match="Test exception"):
            adapter.memoize("test_key", mock_fn)

        mock_backend.has.assert_called_once_with("test_key")
        mock_fn.assert_called_once()
        mock_backend.set.assert_not_called()

    def test_memoize_on_cache_miss_without_ttl(self, adapter, mock_backend):
        """
        Tests that memoize works correctly when ttl is not provided.
        """
        mock_backend.has.return_value = False
        mock_fn = MagicMock(return_value="new_value")

        result = adapter.memoize("test_key", mock_fn)

        assert result == "new_value"

        mock_backend.has.assert_called_once_with("test_key")
        mock_fn.assert_called_once()
        mock_backend.set.assert_called_once_with("test_key", "new_value", timeout=None)

    def test_has_calls_backend_has(self, adapter, mock_backend):
        """Verifies that the Adapter's has method calls the backend's has method."""
        mock_backend.has.return_value = True
        result = adapter.has("test_key")

        assert result is True
        mock_backend.has.assert_called_once_with("test_key")

        mock_backend.has.reset_mock()
        mock_backend.has.return_value = False
        result = adapter.has("another_key")

        assert result is False
        mock_backend.has.assert_called_once_with("another_key")
