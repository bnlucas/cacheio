from __future__ import annotations

import threading
from unittest.mock import MagicMock

import pytest

from cacheio import cached, Adapter
from cacheio._adapter import invoke_cache_adapter


class TestCached:
    """Test suite for the cached decorator and related functions."""

    @pytest.fixture
    def mock_adapter(self):
        """Provides a mock Adapter instance with a mocked memoize method."""
        mock_adapter = MagicMock(spec=Adapter)
        mock_adapter.memoize = MagicMock()

        return mock_adapter

    def test_cached_decorator_calls_memoize_correctly(self, mock_adapter):
        """
        Verifies that the decorated method's wrapper function correctly uses the
        adapter's memoize method.
        """

        class MyClass:
            def __init__(self, cache_adapter):
                self._cache = cache_adapter

            @cached(lambda _, a, b: f"key_{a}_{b}", ttl=60)
            def my_method(self, a, b):
                return a + b

        instance = MyClass(mock_adapter)
        instance.my_method(5, 10)

        mock_adapter.memoize.assert_called_once()
        key, fn = mock_adapter.memoize.call_args[0]
        kwargs = mock_adapter.memoize.call_args[1]

        assert key == "key_5_10"
        assert fn() == 15
        assert kwargs["ttl"] == 60

    def test_cached_decorator_propagates_exceptions(self, mock_adapter):
        """
        Tests that an exception raised by the decorated method is correctly propagated.
        """

        class MyClass:
            def __init__(self, cache_adapter):
                self._cache = cache_adapter

            @cached(lambda _, a, b: f"key_{a}_{b}", ttl=60)
            def my_method_with_exception(self, a, b):
                raise ValueError("Something went wrong!")

        instance = MyClass(mock_adapter)
        mock_adapter.memoize.side_effect = lambda key, fn, ttl: fn()

        with pytest.raises(ValueError, match="Something went wrong!"):
            instance.my_method_with_exception(5, 10)

        mock_adapter.memoize.assert_called_once()

    def test_cached_decorator_with_custom_cache_attr(self, mock_adapter):
        """
        Tests that the decorator works correctly with a custom cache attribute name.
        """

        class MyClass:
            def __init__(self, cache_adapter):
                self._my_custom_cache = cache_adapter

            @cached(lambda _, a: f"key_{a}", cache_attr="_my_custom_cache")
            def my_method(self, a):
                return a

        instance = MyClass(mock_adapter)
        instance.my_method(42)

        mock_adapter.memoize.assert_called_once()
        key, fn = mock_adapter.memoize.call_args[0]
        assert key == "key_42"
        assert fn() == 42

    def test_invoke_cache_adapter_raises_if_cache_attr_missing(self):
        """
        Tests that invoke_cache_adapter raises an AttributeError if the cache attribute
        is missing from the instance.
        """

        class NoCacheClass:
            pass

        no_cache_instance = NoCacheClass()

        with pytest.raises(
            AttributeError,
            match="The provided cache attribute `_cache` does not exist.",
        ):

            def key_fn(x):
                return str(x)

            def fn(self, x):
                return x

            invoke_cache_adapter(
                self=no_cache_instance,
                key_fn=key_fn,
                cache_attr="_cache",
                fn=fn,
                args=(10,),
                kwargs={},
                ttl=None,
            )

    def test_cached_decorator_on_standalone_function_raises_error(self):
        """
        Tests that using the cached decorator on a non-method function raises an
        informative TypeError.
        """

        with pytest.raises(
            TypeError,
            match="The 'cached' decorator can only be used on methods of a class.",
        ):

            @cached(lambda _: "key")
            def standalone_function():
                return 42

            # The error will be raised when the function is called
            standalone_function()

    def test_cached_decorator_is_thread_safe(self, mock_adapter):
        """
        Tests that the cached decorator handles concurrent calls from multiple threads
        correctly. This test verifies that a decorated function's logic is only
        executed once for a cache miss, even with multiple threads trying to access it
        at the same time.
        """
        slow_fn_mock = MagicMock(return_value="result")

        def memoize_side_effect(key, fn, ttl):
            if mock_adapter.memoize.call_count == 1:
                result = fn()
                return result
            else:
                return "cached_result"

        mock_adapter.memoize.side_effect = memoize_side_effect

        class MyClass:
            def __init__(self, cache_adapter):
                self._cache = cache_adapter
                self.lock = threading.Lock()

            @cached(lambda _: "key")
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

        assert mock_adapter.memoize.call_count == 5
        assert slow_fn_mock.call_count == 1
