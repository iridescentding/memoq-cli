# -*- coding: utf-8 -*-
"""
Tests for project creation CLI commands.
"""

from types import SimpleNamespace
from unittest.mock import patch
from click.testing import CliRunner

from memoq_cli.commands.project import project


class TestProjectCreateCommands:
    """Test project creation command argument handling."""

    @patch("memoq_cli.commands.project.ProjectManager")
    def test_createfromtemplate_passes_template_payload(self, MockProjectManager):
        mock_pm = MockProjectManager.return_value
        mock_pm.create_project_from_template.return_value = {
            "ProjectGuid": "project-guid-123"
        }

        runner = CliRunner()
        result = runner.invoke(
            project,
            [
                "createfromtemplate", "template-guid-123",
                "--creator-user", "user-guid-123",
                "--name", "Template Project",
                "--source-lang", "eng",
                "--target-lang", "de-DE,zho-CN",
                "--client", "ACME",
                "--yes",
                "--json",
            ],
            obj={"verbose": False},
        )

        assert result.exit_code == 0, result.output
        mock_pm.create_project_from_template.assert_called_once_with(
            template_guid="template-guid-123",
            creator_user="user-guid-123",
            name="Template Project",
            source_language_code="eng",
            target_language_codes=["de-DE", "zho-CN"],
            description=None,
            client_attr="ACME",
            domain=None,
            project_attr=None,
            subject=None,
            project_creation_aspects=None,
        )
        assert "project-guid-123" in result.output

    @patch("memoq_cli.commands.project.ProjectManager")
    def test_new_passes_create_project_payload(self, MockProjectManager):
        mock_pm = MockProjectManager.return_value
        mock_pm.create_project.return_value = "project-guid-456"

        runner = CliRunner()
        result = runner.invoke(
            project,
            [
                "new",
                "--name", "New Project",
                "--creator-user", "user-guid-456",
                "--source-lang", "eng",
                "--target-lang", "de-DE",
                "--target-lang", "zho-CN",
                "--desc", "Created by tests",
                "--callback-url", "http://localhost:8088/memoq-callback.asmx",
                "--download-preview",
                "--record-version-history",
                "--yes",
                "--json",
            ],
            obj={"verbose": False},
        )

        assert result.exit_code == 0, result.output
        mock_pm.create_project.assert_called_once()
        kwargs = mock_pm.create_project.call_args.kwargs
        assert kwargs["name"] == "New Project"
        assert kwargs["creator_user"] == "user-guid-456"
        assert kwargs["source_language_code"] == "eng"
        assert kwargs["target_language_codes"] == ["de-DE", "zho-CN"]
        assert kwargs["description"] == "Created by tests"
        assert kwargs["deadline"] is not None
        assert kwargs["callback_url"] == "http://localhost:8088/memoq-callback.asmx"
        assert kwargs["download_preview2"] is True
        assert kwargs["download_skeleton2"] is False
        assert kwargs["record_version_history"] is True
        assert "project-guid-456" in result.output

    @patch("memoq_cli.commands.project.ProjectManager")
    def test_new_defaults_creator_user_from_config_username(self, MockProjectManager):
        mock_pm = MockProjectManager.return_value
        mock_pm.list_users.return_value = [
            {
                "UserGuid": "resolved-user-guid",
                "UserName": "jaytestnew",
                "FullName": "Jay Test",
            }
        ]
        mock_pm.create_project.return_value = "project-guid-789"

        runner = CliRunner()
        result = runner.invoke(
            project,
            [
                "new",
                "--name", "New Project",
                "--source-lang", "zho-CN",
                "--target-lang", "eng-US",
                "--yes",
                "--json",
            ],
            obj={
                "verbose": False,
                "config": SimpleNamespace(username="jaytestnew"),
            },
        )

        assert result.exit_code == 0, result.output
        mock_pm.list_users.assert_called_once_with(active_only=True)
        kwargs = mock_pm.create_project.call_args.kwargs
        assert kwargs["creator_user"] == "resolved-user-guid"

    @patch("memoq_cli.commands.project.ProjectManager")
    def test_createfromtemplate_defaults_creator_user_from_config_username(
        self, MockProjectManager
    ):
        mock_pm = MockProjectManager.return_value
        mock_pm.list_users.return_value = [
            {
                "UserGuid": "resolved-user-guid",
                "UserName": "jaytestnew",
                "FullName": "Jay Test",
            }
        ]
        mock_pm.create_project_from_template.return_value = {
            "ProjectGuid": "project-guid-999"
        }

        runner = CliRunner()
        result = runner.invoke(
            project,
            [
                "createfromtemplate",
                "template-guid-999",
                "--name", "Template Project",
                "--yes",
                "--json",
            ],
            obj={
                "verbose": False,
                "config": SimpleNamespace(username="jaytestnew"),
            },
        )

        assert result.exit_code == 0, result.output
        mock_pm.list_users.assert_called_once_with(active_only=True)
        kwargs = mock_pm.create_project_from_template.call_args.kwargs
        assert kwargs["creator_user"] == "resolved-user-guid"
