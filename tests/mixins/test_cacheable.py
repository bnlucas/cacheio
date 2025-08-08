from __future__ import annotations

from unittest.mock import patch, MagicMock

from cacheio import Adapter, memoized
from cacheio.mixins import Cacheable


class TestCacheableIntegration:
    """Test suite for the Cacheable mixin's integration behavior."""

    @patch("cacheio._cache_factory.CacheFactory.memory_cache")
    def test_init_calls_super_init(self, mock_factory):
        """Tests that the mixin's __init__ calls the parent's __init__."""
        mock_adapter = MagicMock(spec=Adapter)
        mock_factory.return_value = mock_adapter

        class MockParent:
            def __init__(self, *args, **kwargs):
                self.init_called = True

        class MyClass(Cacheable, MockParent):
            pass

        instance = MyClass()

        assert instance.init_called is True
        assert instance._cache is mock_adapter

    @patch("cacheio._cache_factory.CacheFactory.memory_cache")
    def test_decorated_method_uses_mixin_cache(self, mock_factory):
        """Tests that a decorated method can successfully use the mixin's cache."""
        mock_adapter = MagicMock(spec=Adapter)
        mock_adapter.get_or_set = MagicMock()
        mock_factory.return_value = mock_adapter

        class MyClass(Cacheable):
            @memoized(key_fn=lambda self, x: f"key_{x}")
            def my_method(self, x):
                return x * 2

        instance = MyClass()
        instance.my_method(5)

        mock_adapter.get_or_set.assert_called_once()
        key, fn = mock_adapter.get_or_set.call_args[0]

        assert key == "key_5"
        assert fn() == 10

    @patch("cacheio._cache_factory.CacheFactory.memory_cache")
    def test_complex_inheritance_hierarchy(self, mock_factory):
        """
        Tests that the mixin works correctly with a more complex class hierarchy,
        ensuring the Method Resolution Order is not broken.
        """
        mock_factory.return_value = MagicMock(spec=Adapter)

        class Grandparent:
            def __init__(self, *args, **kwargs):
                self.grandparent_init_called = True
                super().__init__(*args, **kwargs)

        class Parent(Grandparent):
            def __init__(self, *args, **kwargs):
                self.parent_init_called = True
                super().__init__(*args, **kwargs)

        class MyClass(Cacheable, Parent):
            def __init__(self, *args, **kwargs):
                self.my_class_init_called = True
                super().__init__(*args, **kwargs)

        instance = MyClass()

        assert instance.my_class_init_called is True
        assert instance.parent_init_called is True
        assert instance.grandparent_init_called is True
        assert hasattr(instance, "_cache")

    @patch("cacheio._cache_factory.CacheFactory.memory_cache")
    def test_decorated_method_with_custom_cache_attr(self, mock_default_factory):
        """
        Tests that a decorated method can use a custom cache attribute,
        bypassing the default cache provided by the mixin.
        """
        # A mock for the custom cache attribute.
        mock_custom_adapter = MagicMock(spec=Adapter)
        mock_custom_adapter.get_or_set = MagicMock()

        # The mixin will still try to create a default cache, but it won't be used.
        mock_default_factory.return_value = MagicMock(spec=Adapter)

        class MyClass(Cacheable):
            def __init__(self):
                super().__init__()
                # Manually set the custom cache attribute.
                self._my_other_cache = mock_custom_adapter

            @memoized(key_fn=lambda self, x: f"key_{x}", cache_attr="_my_other_cache")
            def my_method(self, x):
                return x * 3

        instance = MyClass()
        instance.my_method(10)

        mock_custom_adapter.get_or_set.assert_called_once()
        mock_default_factory.return_value.get_or_set.assert_not_called()

        key, fn = mock_custom_adapter.get_or_set.call_args[0]
        assert key == "key_10"
        assert fn() == 30
