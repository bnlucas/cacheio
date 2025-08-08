from __future__ import annotations

import pytest

from cacheio import config, configure
from cacheio._config import Config


@pytest.fixture(autouse=True)
def reset_config_defaults():
    # Reset config to default values before and after each test
    original_ttl = config.default_ttl
    original_threshold = config.default_threshold
    yield
    config.default_ttl = original_ttl
    config.default_threshold = original_threshold


class TestConfig:
    """Test suite for the Config class and the global config object."""

    def test_config_initialization(self):
        """
        Verifies that the Config object is initialized with the correct
        default values.
        """
        assert config.default_ttl == 300
        assert config.default_threshold == 500

    def test_configure_modifies_all_config_values(self):
        """
        Tests that the configure function can successfully modify multiple
        settings on the global config object.
        """

        def set_custom_values(cfg: Config):
            cfg.default_ttl = 600
            cfg.default_threshold = 1000

        configure(set_custom_values)

        assert config.default_ttl == 600
        assert config.default_threshold == 1000

    def test_configure_raises_typeerror_with_non_callable(self):
        """
        Tests that the configure function raises a TypeError if a non-callable
        object is provided.
        """
        with pytest.raises(TypeError, match="The 'fn' argument must be a callable."):
            # Attempt to configure with an integer, which is not callable.
            configure(123)

    def test_configure_modifies_config_with_new_config_instance(self):
        """
        Tests that the configure function can successfully be used to apply a new
        Config object.
        """
        new_config = Config()
        new_config.default_ttl = 900
        new_config.default_threshold = 1500

        def apply_new_config(cfg: Config):
            cfg.default_ttl = new_config.default_ttl
            cfg.default_threshold = new_config.default_threshold

        configure(apply_new_config)

        assert config.default_ttl == 900
        assert config.default_threshold == 1500

    def test_configure_modifies_a_single_config_value(self):
        """
        Tests that the configure function can successfully modify a single
        setting on the global config object without affecting others.
        """

        def set_custom_ttl(cfg: Config):
            cfg.default_ttl = 999

        configure(set_custom_ttl)

        assert config.default_ttl == 999
        assert config.default_threshold == 500

    def test_get_returns_override_value_if_provided(self):
        """
        Tests that Config.get returns the override value if it is provided,
        ignoring the stored attribute value.
        """
        # Ensure default values
        config.default_ttl = 300

        # Override takes precedence
        assert config.get("default_ttl", override=123) == 123

    def test_get_returns_attribute_value_if_no_override(self):
        """
        Tests that Config.get returns the stored attribute value if no override is
        provided.
        """
        config.default_threshold = 999
        assert config.get("default_threshold") == 999

    def test_get_raises_attribute_error_for_unknown_attr(self):
        """
        Tests that Config.get raises AttributeError when an unknown attribute is
        requested.
        """
        with pytest.raises(
            AttributeError, match="Unknown configuration attribute: 'unknown'"
        ):
            config.get("unknown")
