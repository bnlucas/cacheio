import importlib
from unittest.mock import patch


def test_cachelib_import_failure():
    """Test that `Cache` is None when cachelib is not available."""
    module_to_test = "cacheio._cache_factory"

    with patch.dict("sys.modules", {"cachelib": None}):
        reloaded_module = importlib.reload(importlib.import_module(module_to_test))
        assert reloaded_module.Cache is None


def test_aiocache_import_failure():
    """Test that `AsyncCache` is None when aiocache is not available."""
    module_to_test = "cacheio._cache_factory"

    with patch.dict("sys.modules", {"aiocache": None}):
        reloaded_module = importlib.reload(importlib.import_module(module_to_test))
        assert reloaded_module.AsyncCache is None
