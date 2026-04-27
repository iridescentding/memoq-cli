# -*- coding: utf-8 -*-
"""
Tests for WSAPI project creation payloads.
"""

from unittest.mock import Mock, MagicMock

from memoq_cli.wsapi.project import ProjectManager


class TestProjectCreationPayloads:
    """Test ProjectManager project creation wrappers."""

    def _mock_client(self):
        client = MagicMock()

        def get_type(type_name):
            if type_name.endswith("ArrayOfstring"):
                return lambda string: {"string": string}
            return lambda **kwargs: {"type": type_name, "kwargs": kwargs}

        client.get_type.side_effect = get_type
        return client

    def test_create_project_from_template_builds_expected_payload(self):
        manager = ProjectManager(
            host="https://memoq.test.com",
            port=8081,
            api_key="test_key",
        )
        client = self._mock_client()
        client.service.CreateProjectFromTemplate.return_value = {
            "ProjectGuid": "project-guid-123"
        }
        manager.get_client = Mock(return_value=client)

        result = manager.create_project_from_template(
            template_guid="template-guid-123",
            creator_user="user-guid-123",
            name="Template Project",
            target_language_codes=["de-DE", "zho-CN"],
        )

        client.service.CreateProjectFromTemplate.assert_called_once()
        payload = client.service.CreateProjectFromTemplate.call_args.kwargs["createInfo"]
        assert payload["kwargs"]["TemplateGuid"] == "template-guid-123"
        assert payload["kwargs"]["CreatorUser"] == "user-guid-123"
        assert payload["kwargs"]["Name"] == "Template Project"
        assert payload["kwargs"]["TargetLanguageCodes"] == {
            "string": ["de-DE", "zho-CN"]
        }
        assert result["ProjectGuid"] == "project-guid-123"

    def test_create_project_builds_desktop_docs_payload(self):
        manager = ProjectManager(
            host="https://memoq.test.com",
            port=8081,
            api_key="test_key",
        )
        client = self._mock_client()
        client.service.CreateProject2.return_value = "project-guid-456"
        manager.get_client = Mock(return_value=client)

        result = manager.create_project(
            name="New Project",
            creator_user="user-guid-456",
            source_language_code="eng",
            target_language_codes=["de-DE"],
            callback_url="http://localhost:8088/memoq-callback.asmx",
            download_preview2=True,
        )

        client.service.CreateProject2.assert_called_once()
        payload = client.service.CreateProject2.call_args.kwargs["spInfo"]
        assert payload["kwargs"]["Name"] == "New Project"
        assert payload["kwargs"]["CreatorUser"] == "user-guid-456"
        assert payload["kwargs"]["SourceLanguageCode"] == "eng"
        assert payload["kwargs"]["TargetLanguageCodes"] == {"string": ["de-DE"]}
        assert payload["kwargs"]["Deadline"] is not None
        assert (
            payload["kwargs"]["CallbackWebServiceUrl"]
            == "http://localhost:8088/memoq-callback.asmx"
        )
        assert payload["kwargs"]["DownloadPreview2"] is True
        assert payload["kwargs"]["AllowPackageCreation"] is False
        assert result == "project-guid-456"
