# -*- coding: utf-8 -*-
"""
Tests for Project Template Client
"""

import pytest
from unittest.mock import Mock, patch
from memoq_cli.rsapi.project_template import ProjectTemplateClient


class TestProjectTemplateClient:
    """Test ProjectTemplateClient"""

    def test_list_templates_calls_correct_endpoint(self):
        """Test that list_templates calls the projecttemplates endpoint"""
        # Arrange
        client = ProjectTemplateClient(
            host="https://memoq.test.com",
            port=8082,
            api_key="test_key",
            verify_ssl=False
        )

        # Mock the get method
        mock_response = [
            {
                "Guid": "template-guid-1",
                "Name": "Test Template 1",
                "SourceLanguageCode": "en-US",
                "TargetLanguageCodes": ["de-DE", "fr-FR"]
            },
            {
                "Guid": "template-guid-2",
                "Name": "Test Template 2",
                "SourceLanguageCode": "en-US",
                "TargetLanguageCodes": ["ja-JP"]
            }
        ]
        client.get = Mock(return_value=mock_response)

        # Act
        result = client.list_templates()

        # Assert
        client.get.assert_called_once_with("projecttemplates")
        assert len(result) == 2
        assert result[0]["Name"] == "Test Template 1"
        assert result[1]["Guid"] == "template-guid-2"

    def test_list_templates_returns_list(self):
        """Test that list_templates returns a list"""
        # Arrange
        client = ProjectTemplateClient(
            host="https://memoq.test.com",
            port=8082,
            api_key="test_key"
        )
        client.get = Mock(return_value=[])

        # Act
        result = client.list_templates()

        # Assert
        assert isinstance(result, list)

    def test_get_template_calls_correct_endpoint(self):
        """Test that get_template calls the projecttemplates/{guid} endpoint"""
        # Arrange
        client = ProjectTemplateClient(
            host="https://memoq.test.com",
            port=8082,
            api_key="test_key"
        )

        mock_template = {
            "Guid": "template-guid-123",
            "Name": "Test Template",
            "SourceLanguageCode": "en-US",
            "TargetLanguageCodes": ["de-DE", "fr-FR"],
            "TranslationMemories": [{"Name": "TM1", "Guid": "tm-guid-1"}],
            "TermBases": [{"Name": "TB1", "Guid": "tb-guid-1"}],
            "WorkflowSteps": [{"Name": "Translation", "Order": 1}]
        }
        client.get = Mock(return_value=mock_template)

        # Act
        result = client.get_template("template-guid-123")

        # Assert
        client.get.assert_called_once_with("projecttemplates/template-guid-123")
        assert result["Guid"] == "template-guid-123"
        assert result["Name"] == "Test Template"
        assert len(result["TranslationMemories"]) == 1
        assert len(result["TermBases"]) == 1
