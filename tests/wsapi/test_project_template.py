# -*- coding: utf-8 -*-
"""
Tests for WSAPI Project Template Manager
"""

import pytest
from unittest.mock import Mock, MagicMock
from memoq_cli.wsapi.project_template import ProjectTemplateManager


class TestProjectTemplateManager:
    """Test WSAPI ProjectTemplateManager"""

    def test_list_templates_returns_project_templates(self):
        """Test that list_templates calls ListResources with 'ProjectTemplate' type"""
        # Arrange
        manager = ProjectTemplateManager(
            host="https://memoq.test.com",
            port=8081,
            api_key="test_key"
        )

        # Mock the Resource service client
        mock_resource_service = Mock()
        mock_templates = [
            {
                "Guid": "template-1",
                "Name": "Template 1",
                "SourceLangCode": "en-US",
                "TargetLangCodes": {"string": ["de-DE"]}
            },
            {
                "Guid": "template-2",
                "Name": "Template 2",
                "SourceLangCode": "de-DE",
                "TargetLangCodes": {"string": ["en-US", "fr-FR"]}
            }
        ]
        mock_resource_service.ListResources.return_value = mock_templates

        # Mock get_client to return our mock service
        manager.get_client = Mock(return_value=MagicMock(service=mock_resource_service))

        # Act
        templates = manager.list_templates()

        # Assert
        # Verify ListResources was called with 'ProjectTemplate' type
        mock_resource_service.ListResources.assert_called_once_with('ProjectTemplate', None)

        # Verify results
        assert len(templates) == 2
        assert templates[0]["Name"] == "Template 1"
        assert templates[1]["Name"] == "Template 2"
