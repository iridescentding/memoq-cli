# -*- coding: utf-8 -*-
"""
Tests for Config
"""

import pytest
from memoq_cli.config import Config


class TestConfigDefaults:
    """Test config default values"""

    def test_rsapi_port_defaults_to_8082_not_443(self):
        """Test that RSAPI port defaults to 8082, not 443"""
        # Arrange: Create config with no config file (uses defaults)
        config = Config()
        config._config = {"server": {}}  # Empty server config, should use defaults

        # Act
        port = config.rsapi_port

        # Assert
        assert port == 8082, f"Expected default RSAPI port to be 8082, but got {port}"
