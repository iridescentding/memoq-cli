# -*- coding: utf-8 -*-
"""
Tests for WSAPI file import payloads.
"""

from unittest.mock import Mock, MagicMock

from memoq_cli.wsapi.file_manager import FileManager


class TestFileImportPayloads:
    """Test FileManager import option payloads."""

    def _mock_client(self):
        client = MagicMock()

        def get_type(type_name):
            if type_name.endswith("ArrayOfImportTranslationDocumentOptions"):
                return lambda items: {"items": items}
            return lambda **kwargs: {"type": type_name, "kwargs": kwargs}

        client.get_type.side_effect = get_type
        return client

    def test_import_document_passes_external_document_id(self):
        manager = FileManager(
            host="https://memoq.test.com",
            port=8081,
            api_key="test_key",
        )
        client = self._mock_client()
        client.service.ImportTranslationDocumentsWithOptions.return_value = [
            {"DocumentGuid": "doc-guid-123"}
        ]
        manager.get_client = Mock(return_value=client)

        manager.import_document_to_project(
            file_guid="file-guid-123",
            project_guid="project-guid-123",
            target_languages=["eng"],
            external_document_id="jaytest1-external-id",
        )

        options_array = client.service.ImportTranslationDocumentsWithOptions.call_args.kwargs[
            "importDocOptions"
        ]
        import_options = options_array["items"][0]
        assert import_options["kwargs"]["ExternalDocumentId"] == "jaytest1-external-id"
