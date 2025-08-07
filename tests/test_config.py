from __future__ import annotations

import pytest

from cacheio import config, configure
from cacheio._config import Config


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
        # Save original values to restore after test
        original_ttl = config.default_ttl
        original_threshold = config.default_threshold

        def set_custom_values(cfg: Config):
            cfg.default_ttl = 600
            cfg.default_threshold = 1000

        configure(set_custom_values)

        assert config.default_ttl == 600
        assert config.default_threshold == 1000

        # Restore original values
        config.default_ttl = original_ttl
        config.default_threshold = original_threshold

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
        original_ttl = config.default_ttl
        original_threshold = config.default_threshold

        new_config = Config()
        new_config.default_ttl = 900
        new_config.default_threshold = 1500

        def apply_new_config(cfg: Config):
            cfg.default_ttl = new_config.default_ttl
            cfg.default_threshold = new_config.default_threshold

        configure(apply_new_config)

        assert config.default_ttl == 900
        assert config.default_threshold == 1500

        # Restore original values
        config.default_ttl = original_ttl
        config.default_threshold = original_threshold

    def test_configure_modifies_a_single_config_value(self):
        """
        Tests that the configure function can successfully modify a single
        setting on the global config object without affecting others.
        """
        original_ttl = config.default_ttl
        original_threshold = config.default_threshold

        def set_custom_ttl(cfg: Config):
            cfg.default_ttl = 999

        configure(set_custom_ttl)

        assert config.default_ttl == 999
        assert config.default_threshold == original_threshold

        # Restore original values
        config.default_ttl = original_ttl
        config.default_threshold = original_threshold
