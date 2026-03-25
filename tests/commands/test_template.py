# -*- coding: utf-8 -*-
"""
Tests for template CLI commands
"""

import pytest
from unittest.mock import patch, Mock
from click.testing import CliRunner
from memoq_cli.commands.template import template


class TestTemplateListFilter:
    """Test that template list passes filters to WSAPI (server-side)"""

    @patch('memoq_cli.commands.template.ProjectTemplateManager')
    def test_filter_flag_passes_name_filter_to_wsapi(self, MockManager):
        """--filter should pass name_filter to list_templates for server-side filtering"""
        mock_manager = MockManager.return_value
        mock_manager.list_templates.return_value = [
            {"Guid": "t-1", "Name": "Game Template", "SourceLangCode": "en-US"}
        ]

        runner = CliRunner()
        result = runner.invoke(template, ["list", "--filter", "Game"], obj={"verbose": False})

        mock_manager.list_templates.assert_called_once_with(name_filter="Game")

    @patch('memoq_cli.commands.template.ProjectTemplateManager')
    def test_lang_flag_passes_language_filter_to_wsapi(self, MockManager):
        """--lang should pass language_filter to list_templates"""
        mock_manager = MockManager.return_value
        mock_manager.list_templates.return_value = []

        runner = CliRunner()
        result = runner.invoke(template, ["list", "--lang", "de-DE"], obj={"verbose": False})

        mock_manager.list_templates.assert_called_once_with(name_filter=None, language_filter="de-DE")

    @patch('memoq_cli.commands.template.ProjectTemplateManager')
    def test_both_filter_and_lang_flags(self, MockManager):
        """Both --filter and --lang should be passed to list_templates"""
        mock_manager = MockManager.return_value
        mock_manager.list_templates.return_value = []

        runner = CliRunner()
        result = runner.invoke(
            template, ["list", "--filter", "Game", "--lang", "en-US"],
            obj={"verbose": False}
        )

        mock_manager.list_templates.assert_called_once_with(
            name_filter="Game", language_filter="en-US"
        )

    @patch('memoq_cli.commands.template.ProjectTemplateManager')
    def test_no_filter_passes_no_filter_args(self, MockManager):
        """No flags should call list_templates without filter args"""
        mock_manager = MockManager.return_value
        mock_manager.list_templates.return_value = []

        runner = CliRunner()
        result = runner.invoke(template, ["list"], obj={"verbose": False})

        mock_manager.list_templates.assert_called_once_with(name_filter=None)
