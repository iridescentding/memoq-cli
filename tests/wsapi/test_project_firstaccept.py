# -*- coding: utf-8 -*-
"""
Tests for WSAPI FirstAccept document assignment payloads.
"""

from datetime import datetime
from unittest.mock import MagicMock, Mock

from memoq_cli.wsapi.project import ProjectManager


class TestProjectFirstAcceptAssignments:
    """Test ProjectManager advanced document assignment wrappers."""

    def _mock_client(self):
        client = MagicMock()

        def get_type(type_name):
            if type_name.endswith("ArrayOfguid"):
                return lambda guid: {"type": type_name, "guid": guid}
            if type_name.endswith("ArrayOfTranslationDocumentAssignmentInfo"):
                return lambda TranslationDocumentAssignmentInfo: {
                    "type": type_name,
                    "TranslationDocumentAssignmentInfo": (
                        TranslationDocumentAssignmentInfo
                    ),
                }
            if type_name.endswith("ArrayOfTranslationDocumentAssignments"):
                return lambda TranslationDocumentAssignments: {
                    "type": type_name,
                    "TranslationDocumentAssignments": TranslationDocumentAssignments,
                }
            return lambda **kwargs: {"type": type_name, "kwargs": kwargs}

        client.get_type.side_effect = get_type
        return client

    def test_first_accept_assignment_builds_set_translation_payload(self):
        manager = ProjectManager(
            host="https://memoq.test.com",
            port=8081,
            api_key="test_key",
        )
        client = self._mock_client()
        client.service.SetTranslationDocumentAssignments.return_value = [
            {"DocumentGuid": "doc-guid-1", "ErrorCode": None},
            {"DocumentGuid": "doc-guid-2", "ErrorCode": None},
        ]
        manager.get_client = Mock(return_value=client)

        deadline = datetime(2026, 6, 22)
        first_accept_deadline = datetime(2026, 6, 10)

        result = manager.set_translation_document_first_accept_assignments(
            project_guid="project-guid-123",
            document_guids=["doc-guid-1", "doc-guid-2"],
            user_guids=["user-guid-1", "user-guid-2"],
            role=0,
            deadline=deadline,
            first_accept_deadline=first_accept_deadline,
        )

        client.service.SetTranslationDocumentAssignments.assert_called_once()
        client.service.SetProjectTranslationDocumentUserAssignments.assert_not_called()
        call_kwargs = client.service.SetTranslationDocumentAssignments.call_args.kwargs
        assert call_kwargs["serverProjectGuid"] == "project-guid-123"

        options = call_kwargs["options"]
        assert options["kwargs"]["ThrowFault"] is True

        doc_array = options["kwargs"]["DocumentAssignments"]
        doc_assignments = doc_array["TranslationDocumentAssignments"]
        assert len(doc_assignments) == 2
        assert doc_assignments[0]["kwargs"]["DocumentGuid"] == "doc-guid-1"
        assert doc_assignments[1]["kwargs"]["DocumentGuid"] == "doc-guid-2"

        first_doc_assignment_array = doc_assignments[0]["kwargs"]["Assignments"]
        first_doc_assignment = first_doc_assignment_array[
            "TranslationDocumentAssignmentInfo"
        ][0]
        assert first_doc_assignment["kwargs"]["AssignmentType"] == "FirstAccept"
        assert first_doc_assignment["kwargs"]["RoleId"] == 0
        assert first_doc_assignment["kwargs"]["Deadline"] == deadline
        assert first_doc_assignment["kwargs"]["FirstAcceptDeadline"] == (
            first_accept_deadline
        )
        assert first_doc_assignment["kwargs"]["UserGuids"] == {
            "type": "{http://schemas.microsoft.com/2003/10/Serialization/Arrays}"
            "ArrayOfguid",
            "guid": ["user-guid-1", "user-guid-2"],
        }
        assert result[0]["DocumentGuid"] == "doc-guid-1"
