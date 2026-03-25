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

    def test_list_templates_with_name_filter(self):
        """Test that list_templates passes NameOrDescription filter to WSAPI"""
        manager = ProjectTemplateManager(
            host="https://memoq.test.com",
            port=8081,
            api_key="test_key"
        )

        mock_resource_service = Mock()
        mock_resource_service.ListResources.return_value = [
            {"Guid": "t-1", "Name": "Game Template", "SourceLangCode": "en-US"}
        ]

        mock_client = MagicMock()
        mock_client.service = mock_resource_service
        # Mock get_type to return a callable that creates filter objects
        mock_filter_type = Mock()
        mock_filter_instance = Mock()
        mock_filter_type.return_value = mock_filter_instance
        mock_client.get_type.return_value = mock_filter_type

        manager.get_client = Mock(return_value=mock_client)

        templates = manager.list_templates(name_filter="Game")

        # Should have created a LightResourceListFilter
        mock_client.get_type.assert_called_once_with('{http://kilgray.com/memoqservices/2007}LightResourceListFilter')
        mock_filter_type.assert_called_once_with(NameOrDescription='Game')
        # Should pass filter to ListResources
        mock_resource_service.ListResources.assert_called_once_with(
            'ProjectTemplate', mock_filter_instance
        )
        assert len(templates) == 1

    def test_list_templates_with_language_filter(self):
        """Test that list_templates passes LanguageCode filter to WSAPI"""
        manager = ProjectTemplateManager(
            host="https://memoq.test.com",
            port=8081,
            api_key="test_key"
        )

        mock_resource_service = Mock()
        mock_resource_service.ListResources.return_value = [
            {"Guid": "t-1", "Name": "Template DE", "SourceLangCode": "de-DE"}
        ]

        mock_client = MagicMock()
        mock_client.service = mock_resource_service
        mock_filter_type = Mock()
        mock_filter_instance = Mock()
        mock_filter_type.return_value = mock_filter_instance
        mock_client.get_type.return_value = mock_filter_type

        manager.get_client = Mock(return_value=mock_client)

        templates = manager.list_templates(language_filter="de-DE")

        mock_client.get_type.assert_called_once_with('{http://kilgray.com/memoqservices/2007}LightResourceListFilter')
        mock_filter_type.assert_called_once_with(LanguageCode='de-DE')
        mock_resource_service.ListResources.assert_called_once_with(
            'ProjectTemplate', mock_filter_instance
        )

    def test_list_templates_with_both_filters(self):
        """Test that list_templates passes both filter fields"""
        manager = ProjectTemplateManager(
            host="https://memoq.test.com",
            port=8081,
            api_key="test_key"
        )

        mock_resource_service = Mock()
        mock_resource_service.ListResources.return_value = []

        mock_client = MagicMock()
        mock_client.service = mock_resource_service
        mock_filter_type = Mock()
        mock_filter_instance = Mock()
        mock_filter_type.return_value = mock_filter_instance
        mock_client.get_type.return_value = mock_filter_type

        manager.get_client = Mock(return_value=mock_client)

        templates = manager.list_templates(name_filter="Game", language_filter="en-US")

        mock_filter_type.assert_called_once_with(
            NameOrDescription='Game', LanguageCode='en-US'
        )
        mock_resource_service.ListResources.assert_called_once_with(
            'ProjectTemplate', mock_filter_instance
        )

    def test_list_templates_no_filter_passes_none(self):
        """Test that list_templates without filters still passes None (backward compat)"""
        manager = ProjectTemplateManager(
            host="https://memoq.test.com",
            port=8081,
            api_key="test_key"
        )

        mock_resource_service = Mock()
        mock_resource_service.ListResources.return_value = []
        manager.get_client = Mock(return_value=MagicMock(service=mock_resource_service))

        manager.list_templates()

        mock_resource_service.ListResources.assert_called_once_with('ProjectTemplate', None)
