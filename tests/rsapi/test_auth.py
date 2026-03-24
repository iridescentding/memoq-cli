# -*- coding: utf-8 -*-
"""
Tests for RSAPI Authentication
"""

import pytest
from unittest.mock import Mock, patch
from memoq_cli.rsapi.client import RSAPIClient


class TestRSAPIAuthentication:
    """Test RSAPI authentication methods"""

    def test_authenticate_with_username_password(self):
        """Test authentication with username and password"""
        # Arrange
        client = RSAPIClient(
            host="https://memoq.test.com",
            port=8082,
            verify_ssl=False
        )

        mock_response = Mock()
        mock_response.json.return_value = {"AccessToken": "test-token-123"}
        mock_response.raise_for_status = Mock()

        with patch.object(client.session, 'post', return_value=mock_response) as mock_post:
            # Act
            token = client.authenticate_with_password("testuser", "testpass")

            # Assert
            mock_post.assert_called_once()
            call_args = mock_post.call_args
            assert call_args[0][0].endswith("/auth/login")

            # Check payload
            payload = call_args[1]['json']
            assert payload['username'] == "testuser"
            assert payload['password'] == "testpass"
            assert payload['LoginMode'] == 0

            assert token == "test-token-123"
            assert client._access_token == "test-token-123"
