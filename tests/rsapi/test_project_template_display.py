# -*- coding: utf-8 -*-
"""
Tests for Project Template Display Utilities
"""

import pytest
from io import StringIO
import sys
from unittest.mock import Mock
from memoq_cli.rsapi.project_template import ProjectTemplateClient


class TestProjectTemplateDisplay:
    """Test project template display utilities"""

    def test_print_template_list_displays_templates(self, capsys):
        """Test that print_template_list displays templates in table format"""
        # Arrange
        client = ProjectTemplateClient(
            host="https://memoq.test.com",
            port=8082,
            api_key="test_key"
        )

        templates = [
            {
                "Guid": "guid-1",
                "Name": "Template One",
                "SourceLanguageCode": "en-US",
                "TargetLanguageCodes": ["de-DE", "fr-FR"]
            },
            {
                "Guid": "guid-2",
                "Name": "Template Two",
                "SourceLanguageCode": "en-US",
                "TargetLanguageCodes": ["ja-JP"]
            }
        ]

        # Act
        client.print_template_list(templates)
        captured = capsys.readouterr()

        # Assert
        assert "Template One" in captured.out
        assert "Template Two" in captured.out
        assert "guid-1" in captured.out
        assert "guid-2" in captured.out
        assert "en-US" in captured.out

    def test_print_template_details_displays_full_info(self, capsys):
        """Test that print_template_details displays detailed template information"""
        # Arrange
        client = ProjectTemplateClient(
            host="https://memoq.test.com",
            port=8082,
            api_key="test_key"
        )

        template = {
            "Guid": "template-guid-123",
            "Name": "Detailed Template",
            "SourceLanguageCode": "en-US",
            "TargetLanguageCodes": ["de-DE", "fr-FR", "ja-JP"],
            "TranslationMemories": [
                {"Name": "TM1", "Guid": "tm-guid-1"},
                {"Name": "TM2", "Guid": "tm-guid-2"}
            ],
            "TermBases": [
                {"Name": "TB1", "Guid": "tb-guid-1"}
            ],
            "WorkflowSteps": [
                {"Name": "Translation", "Order": 1},
                {"Name": "Review", "Order": 2}
            ]
        }

        # Act
        client.print_template_details(template)
        captured = capsys.readouterr()

        # Assert
        assert "Detailed Template" in captured.out
        assert "template-guid-123" in captured.out
        assert "en-US" in captured.out
        assert "de-DE" in captured.out
        assert "TM1" in captured.out
        assert "TB1" in captured.out
        assert "Translation" in captured.out
        assert "Review" in captured.out
