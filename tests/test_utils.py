from __future__ import annotations

import pytest

from cacheio._utils import ensure_decorated_class_method, ensure_cache_adapter


class TestEnsureDecoratedClassMethod:
    def test_valid_method_passes(self):
        class Foo:
            def method(self):
                pass

        # Should not raise
        ensure_decorated_class_method(Foo.method, "test_decorator")

    def test_valid_async_method_passes(self):
        class Foo:
            async def method(self):
                pass

        # Should not raise
        ensure_decorated_class_method(Foo.method, "test_decorator")

    def test_function_without_self_raises(self):
        def not_a_method():
            pass

        with pytest.raises(TypeError) as excinfo:
            ensure_decorated_class_method(not_a_method, "test_decorator")

        assert "test_decorator" in str(excinfo.value)
        assert "methods of a class" in str(excinfo.value)

    def test_method_with_wrong_first_arg_raises(self):
        def func(wrong):
            pass

        with pytest.raises(TypeError) as excinfo:
            ensure_decorated_class_method(func, "my_decorator")

        assert "my_decorator" in str(excinfo.value)
        assert "methods of a class" in str(excinfo.value)


class TestEnsureCacheAdapter:
    class Dummy:
        pass

    def test_object_with_cache_attr_passes(self):
        obj = self.Dummy()
        setattr(obj, "_cache", object())

        # Should not raise
        ensure_cache_adapter(obj, "_cache")

    def test_object_without_cache_attr_raises(self):
        obj = self.Dummy()

        with pytest.raises(AttributeError) as excinfo:
            ensure_cache_adapter(obj, "_cache")

        assert "_cache" in str(excinfo.value)
        assert "does not exist" in str(excinfo.value)
