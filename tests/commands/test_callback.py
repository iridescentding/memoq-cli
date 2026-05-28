# -*- coding: utf-8 -*-
"""
Tests for memoQ callback CLI commands.
"""

from unittest.mock import patch

from click.testing import CliRunner

from memoq_cli import config as config_module
from memoq_cli.cli import cli
from memoq_cli.commands.callback import callback


PROJECT_GUID = "c25f0cdb-4242-f111-966c-a38328e9a256"


class TestCallbackCommands:
    """Test callback command argument handling."""

    @patch("memoq_cli.commands.callback.ProjectManager")
    def test_configure_builds_callback_url_and_updates_project(self, MockProjectManager):
        mock_pm = MockProjectManager.return_value

        runner = CliRunner()
        result = runner.invoke(
            callback,
            [
                "configure",
                PROJECT_GUID,
                "--base-url",
                "https://callback.example.com/",
            ],
            obj={"verbose": False},
        )

        assert result.exit_code == 0, result.output
        mock_pm.update_project.assert_called_once_with(
            PROJECT_GUID,
            callback_url="https://callback.example.com/memoq-callback.asmx",
        )
        assert "https://callback.example.com/memoq-callback.asmx" in result.output

    @patch("memoq_cli.commands.callback.ProjectManager")
    def test_configure_accepts_full_callback_url(self, MockProjectManager):
        mock_pm = MockProjectManager.return_value

        runner = CliRunner()
        result = runner.invoke(
            callback,
            [
                "configure",
                PROJECT_GUID,
                "--callback-url",
                "https://callback.example.com/memoq-callback.asmx",
            ],
            obj={"verbose": False},
        )

        assert result.exit_code == 0, result.output
        mock_pm.update_project.assert_called_once_with(
            PROJECT_GUID,
            callback_url="https://callback.example.com/memoq-callback.asmx",
        )

    def test_configure_requires_one_url_source(self):
        runner = CliRunner()

        result = runner.invoke(
            callback,
            [
                "configure",
                PROJECT_GUID,
                "--base-url",
                "https://callback.example.com/",
                "--callback-url",
                "https://callback.example.com/memoq-callback.asmx",
            ],
            obj={"verbose": False},
        )

        assert result.exit_code != 0
        assert "Pass exactly one of --base-url or --callback-url" in result.output

    def test_callback_serve_help_does_not_require_config(self, tmp_path, monkeypatch):
        monkeypatch.setattr(
            config_module,
            "CONFIG_SEARCH_PATHS",
            [tmp_path / "config.json"],
        )
        config_module.reset_config()

        runner = CliRunner()
        result = runner.invoke(cli, ["callback", "serve", "--help"])

        assert result.exit_code == 0, result.output
        assert "Run a local memoQ SOAP callback endpoint." in result.output
