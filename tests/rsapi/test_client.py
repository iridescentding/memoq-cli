# -*- coding: utf-8 -*-
"""
Tests for RSAPI Client
"""

import pytest
from memoq_cli.rsapi.client import RSAPIClient


class TestRSAPIClientPort:
    """Test RSAPI client port configuration"""

    def test_uses_default_port_8082_from_config(self):
        """Test that RSAPIClient uses port 8082 by default from config"""
        # Arrange & Act
        client = RSAPIClient(
            host="https://memoq.datalsp.com",
            verify_ssl=False
        )

        # Assert
        # The base_url should contain port 8082
        assert ":8082/" in client.base_url
        assert client.base_url == "https://memoq.datalsp.com:8082/memoqserverhttpapi/v1"

    def test_uses_explicit_port_when_provided(self):
        """Test that RSAPIClient uses explicit port when provided"""
        # Arrange & Act
        client = RSAPIClient(
            host="https://memoq.datalsp.com",
            port=9999,
            verify_ssl=False
        )

        # Assert
        assert ":9999/" in client.base_url

    def test_constructs_correct_auth_url(self):
        """Test that authentication URL is constructed correctly with port 8082"""
        # Arrange
        client = RSAPIClient(
            host="https://memoq.datalsp.com",
            verify_ssl=False
        )

        # Act
        auth_url = client._get_url("auth/login")

        # Assert
        assert auth_url == "https://memoq.datalsp.com:8082/memoqserverhttpapi/v1/auth/login"
