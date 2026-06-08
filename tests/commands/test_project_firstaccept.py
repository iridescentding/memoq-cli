# -*- coding: utf-8 -*-
"""
Tests for project document FirstAccept CLI commands.
"""

import json
from datetime import datetime
from unittest.mock import patch

from click.testing import CliRunner

from memoq_cli.commands.project import project


PROJECT_USERS = [
    {"User": {"UserGuid": "user-guid-1", "FullName": "User One"}},
    {"User": {"UserGuid": "user-guid-2", "FullName": "User Two"}},
]


class TestProjectDocsFirstAcceptCommand:
    """Test FirstAccept assignment command argument handling."""

    @patch("memoq_cli.commands.project.ProjectManager")
    def test_firstaccept_noninteractive_passes_payload(self, MockProjectManager):
        mock_pm = MockProjectManager.return_value
        mock_pm.list_project_users.return_value = PROJECT_USERS
        mock_pm.set_translation_document_first_accept_assignments.return_value = [
            {"DocumentGuid": "doc-guid-1", "ErrorCode": None}
        ]

        runner = CliRunner()
        result = runner.invoke(
            project,
            [
                "docs",
                "project-guid-123",
                "firstaccept",
                "--doc",
                "doc-guid-1",
                "--user",
                "user-guid-1",
                "--user",
                "user-guid-2",
                "--role",
                "translator",
                "--deadline",
                "2026-06-22",
                "--first-accept-deadline",
                "2026-06-10",
                "--yes",
                "--json",
            ],
            obj={"verbose": False},
        )

        assert result.exit_code == 0, result.output
        mock_pm.list_project_users.assert_called_once_with("project-guid-123")
        mock_pm.set_translation_document_first_accept_assignments.assert_called_once_with(
            project_guid="project-guid-123",
            document_guids=["doc-guid-1"],
            user_guids=["user-guid-1", "user-guid-2"],
            role=0,
            deadline=datetime(2026, 6, 22),
            first_accept_deadline=datetime(2026, 6, 10),
            throw_fault=True,
        )
        data = json.loads(result.output)
        assert data[0]["DocumentGuid"] == "doc-guid-1"

    @patch("memoq_cli.commands.project.ProjectManager")
    def test_firstaccept_requires_at_least_two_users(self, MockProjectManager):
        mock_pm = MockProjectManager.return_value

        runner = CliRunner()
        result = runner.invoke(
            project,
            [
                "docs",
                "project-guid-123",
                "firstaccept",
                "--doc",
                "doc-guid-1",
                "--user",
                "user-guid-1",
                "--role",
                "translator",
                "--deadline",
                "2026-06-22",
                "--first-accept-deadline",
                "2026-06-10",
                "--yes",
            ],
            obj={"verbose": False},
        )

        assert result.exit_code != 0
        assert "At least two --user values are required" in result.output
        mock_pm.set_translation_document_first_accept_assignments.assert_not_called()

    @patch("memoq_cli.commands.project.ProjectManager")
    def test_firstaccept_rejects_users_missing_from_project(
        self, MockProjectManager
    ):
        mock_pm = MockProjectManager.return_value
        mock_pm.list_project_users.return_value = PROJECT_USERS

        runner = CliRunner()
        result = runner.invoke(
            project,
            [
                "docs",
                "project-guid-123",
                "firstaccept",
                "--doc",
                "doc-guid-1",
                "--user",
                "user-guid-1",
                "--user",
                "missing-user-guid",
                "--role",
                "translator",
                "--deadline",
                "2026-06-22",
                "--first-accept-deadline",
                "2026-06-10",
                "--yes",
            ],
            obj={"verbose": False},
        )

        assert result.exit_code != 0
        assert "not project members" in result.output
        mock_pm.set_translation_document_first_accept_assignments.assert_not_called()

    @patch("memoq_cli.commands.project.ProjectManager")
    def test_firstaccept_pretty_output_contains_summary(self, MockProjectManager):
        mock_pm = MockProjectManager.return_value
        mock_pm.list_project_users.return_value = PROJECT_USERS
        mock_pm.set_translation_document_first_accept_assignments.return_value = [
            {"DocumentGuid": "doc-guid-1", "ErrorCode": None}
        ]

        runner = CliRunner()
        result = runner.invoke(
            project,
            [
                "docs",
                "project-guid-123",
                "firstaccept",
                "--doc",
                "doc-guid-1",
                "--user",
                "user-guid-1",
                "--user",
                "user-guid-2",
                "--role",
                "reviewer1",
                "--deadline",
                "2026-06-22",
                "--first-accept-deadline",
                "2026-06-10",
                "--yes",
            ],
            obj={"verbose": False},
        )

        assert result.exit_code == 0, result.output
        assert "FirstAccept assignment summary" in result.output
        assert "Reviewer1" in result.output
        assert "doc-guid-1" in result.output

    @patch("memoq_cli.commands.project.ProjectManager")
    def test_detailed_output_shows_firstaccept_assignment(self, MockProjectManager):
        mock_pm = MockProjectManager.return_value
        mock_pm.list_project_translation_documents2.return_value = [
            {
                "DocumentName": "Document 1",
                "DocumentGuid": "doc-guid-1",
                "DocumentStatus": "TranslationInProgress",
                "TargetLangCode": "de-DE",
                "UserAssignments": {
                    "TranslationDocumentDetailedAssignmentInfo": [
                        {
                            "AssignmentType": "FirstAccept",
                            "RoleId": 0,
                            "Deadline": datetime(2026, 6, 22),
                            "FirstAcceptDeadline": datetime(2026, 6, 10),
                            "Status": "Pending",
                            "Users": {
                                "TranslationDocumentFirstAcceptUserInfo": [
                                    {"AssigneeName": "User One"},
                                    {"AssigneeName": "User Two"},
                                ]
                            },
                        }
                    ]
                },
            }
        ]

        runner = CliRunner()
        result = runner.invoke(
            project,
            ["docs", "project-guid-123", "detailed"],
            obj={"verbose": False},
        )

        assert result.exit_code == 0, result.output
        assert "FirstAccept [Pending]" in result.output
        assert "User One, User Two" in result.output
        assert "first accept: 2026-06-10 00:00" in result.output
        assert "deadline: 2026-06-22 00:00" in result.output

    @patch("memoq_cli.commands.project.ProjectManager")
    def test_userassign_output_shows_firstaccept_assignment(self, MockProjectManager):
        mock_pm = MockProjectManager.return_value
        mock_pm.list_project_documents.return_value = [
            {"DocumentName": "Document 1", "DocumentGuid": "doc-guid-1"}
        ]
        mock_pm.list_translation_document_assignments.return_value = [
            {
                "DocumentGuid": "doc-guid-1",
                "Assignments": {
                    "TranslationDocumentDetailedAssignmentInfo": [
                        {
                            "AssignmentType": "FirstAccept",
                            "RoleId": 0,
                            "Deadline": datetime(2026, 6, 22),
                            "FirstAcceptDeadline": datetime(2026, 6, 10),
                            "Status": "Pending",
                            "Users": {
                                "TranslationDocumentFirstAcceptUserInfo": [
                                    {"AssigneeName": "User One"},
                                    {"AssigneeName": "User Two"},
                                ]
                            },
                        }
                    ]
                },
            }
        ]

        runner = CliRunner()
        result = runner.invoke(
            project,
            ["docs", "project-guid-123", "userassign"],
            obj={"verbose": False},
        )

        assert result.exit_code == 0, result.output
        assert "FirstAccept [Pending]" in result.output
        assert "User One, User Two" in result.output
        assert "first accept: 2026-06-10 00:00" in result.output
        assert "2026-06-22 00:00" in result.output
