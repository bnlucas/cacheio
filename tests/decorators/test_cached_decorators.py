from __future__ import annotations

import threading
from unittest.mock import MagicMock

import pytest

from cacheio import cached, memoized, Adapter


class TestCachedDecorators:
    """Test suite for the cached and memoized decorators and related functions."""

    @pytest.fixture
    def mock_adapter(self):
        mock_adapter = MagicMock(spec=Adapter)
        mock_adapter.get_or_set = MagicMock()
        return mock_adapter

    def test_cached_decorator_calls_get_or_set_correctly(self, mock_adapter):
        class MyClass:
            def __init__(self, cache_adapter):
                self._cache = cache_adapter

            @cached(ttl=60)
            def my_method(self, a, b):
                return a + b

        instance = MyClass(mock_adapter)
        mock_adapter.get_or_set.side_effect = lambda key, fn, ttl=None: fn()

        result = instance.my_method(5, 10)

        mock_adapter.get_or_set.assert_called_once()
        key, fn = mock_adapter.get_or_set.call_args[0][:2]
        kwargs = mock_adapter.get_or_set.call_args[1]

        # Key is full qualified name of my_method
        assert key == f"{MyClass.my_method.__module__}.{MyClass.my_method.__qualname__}"
        assert fn() == 15
        assert kwargs["ttl"] == 60
        assert result == 15

    def test_memoized_decorator_calls_get_or_set_with_key_fn(self, mock_adapter):
        class MyClass:
            def __init__(self, cache_adapter):
                self._cache = cache_adapter

            @memoized(lambda self, x: f"key_{x}", ttl=30)
            def my_memoized_method(self, x):
                return x * 10

        instance = MyClass(mock_adapter)
        mock_adapter.get_or_set.side_effect = lambda key, fn, ttl=None: fn()

        result = instance.my_memoized_method(7)

        mock_adapter.get_or_set.assert_called_once()
        key, fn = mock_adapter.get_or_set.call_args[0][:2]
        kwargs = mock_adapter.get_or_set.call_args[1]

        assert key == "key_7"
        assert fn() == 70
        assert kwargs["ttl"] == 30
        assert result == 70

    def test_cached_decorator_propagates_exceptions(self, mock_adapter):
        class MyClass:
            def __init__(self, cache_adapter):
                self._cache = cache_adapter

            @cached(ttl=60)
            def my_method_with_exception(self, a, b):
                raise ValueError("Something went wrong!")

        instance = MyClass(mock_adapter)

        def raise_exc():
            raise ValueError("Something went wrong!")

        mock_adapter.get_or_set.side_effect = lambda key, fn, ttl=None: raise_exc()

        with pytest.raises(ValueError, match="Something went wrong!"):
            instance.my_method_with_exception(5, 10)

        mock_adapter.get_or_set.assert_called_once()

    def test_memoized_decorator_propagates_exceptions(self, mock_adapter):
        class MyClass:
            def __init__(self, cache_adapter):
                self._cache = cache_adapter

            @memoized(lambda self, x: f"key_{x}", ttl=30)
            def my_memoized_method_with_exception(self, x):
                raise RuntimeError("Oops!")

        instance = MyClass(mock_adapter)

        def raise_exc():
            raise RuntimeError("Oops!")

        mock_adapter.get_or_set.side_effect = lambda key, fn, ttl=None: raise_exc()

        with pytest.raises(RuntimeError, match="Oops!"):
            instance.my_memoized_method_with_exception(5)

        mock_adapter.get_or_set.assert_called_once()

    def test_cached_decorator_with_custom_cache_attr(self, mock_adapter):
        class MyClass:
            def __init__(self, cache_adapter):
                self._my_custom_cache = cache_adapter

            @cached(cache_attr="_my_custom_cache", ttl=50)
            def my_method(self, a):
                return a

        instance = MyClass(mock_adapter)
        mock_adapter.get_or_set.side_effect = lambda key, fn, ttl=None: fn()

        result = instance.my_method(42)

        mock_adapter.get_or_set.assert_called_once()
        key, fn = mock_adapter.get_or_set.call_args[0][:2]
        assert key == f"{MyClass.my_method.__module__}.{MyClass.my_method.__qualname__}"
        assert fn() == 42
        assert result == 42

    def test_memoized_decorator_with_custom_cache_attr(self, mock_adapter):
        class MyClass:
            def __init__(self, cache_adapter):
                self._my_cache = cache_adapter

            @memoized(lambda self, x: f"key_{x}", cache_attr="_my_cache", ttl=20)
            def my_method(self, x):
                return x

        instance = MyClass(mock_adapter)
        mock_adapter.get_or_set.side_effect = lambda key, fn, ttl=None: fn()

        result = instance.my_method(99)

        mock_adapter.get_or_set.assert_called_once()
        key, fn = mock_adapter.get_or_set.call_args[0][:2]
        assert key == "key_99"
        assert fn() == 99
        assert result == 99

    def test_cached_decorator_on_standalone_function_raises_error(self):
        with pytest.raises(
            TypeError,
            match="The 'cached' decorator can only be used on methods of a class.",
        ):

            @cached()
            def standalone_function():
                return 42

            standalone_function()

    def test_memoized_decorator_on_standalone_function_raises_error(self):
        with pytest.raises(
            TypeError,
            match="The 'memoized' decorator can only be used on methods of a class.",
        ):

            @memoized(lambda *args: "key")
            def standalone_function():
                return 42

            standalone_function()

    def test_cached_decorator_is_thread_safe(self, mock_adapter):
        slow_fn_mock = MagicMock(return_value="result")

        def get_or_set_side_effect(key, fn, ttl=None):
            if mock_adapter.get_or_set.call_count == 1:
                return fn()
            else:
                return "cached_result"

        mock_adapter.get_or_set.side_effect = get_or_set_side_effect

        class MyClass:
            def __init__(self, cache_adapter):
                self._cache = cache_adapter
                self.lock = threading.Lock()

            @cached()
            def my_method(self):
                with self.lock:
                    return slow_fn_mock()

        instance = MyClass(mock_adapter)

        threads = []
        for _ in range(5):
            thread = threading.Thread(target=instance.my_method)
            threads.append(thread)

        for thread in threads:
            thread.start()

        for thread in threads:
            thread.join()

        assert mock_adapter.get_or_set.call_count == 5
        assert slow_fn_mock.call_count == 1
