# -*- coding: utf-8 -*-
"""
Tests for resource CLI commands
"""

import pytest
from unittest.mock import patch, Mock, MagicMock
from click.testing import CliRunner
from memoq_cli.commands.resource import resource


RESOURCE_NS = "{http://kilgray.com/memoqservices/2007}"


class TestResourceImportNewFilter:
    """Test memoq resource importnewfilter command"""

    @patch('memoq_cli.commands.resource.FileManager')
    @patch('memoq_cli.commands.resource.WSAPIClient')
    def test_uploads_file_and_calls_import(self, MockWSAPI, MockFM):
        """importnewfilter should upload file then call ImportNewAndPublish"""
        mock_fm = MockFM.return_value
        mock_fm.upload_file_chunked.return_value = "file-guid-123"

        mock_client = MagicMock()
        mock_resource_info_type = Mock()
        mock_resource_info_instance = Mock()
        mock_resource_info_type.return_value = mock_resource_info_instance
        mock_client.get_type.return_value = mock_resource_info_type
        mock_client.service.ImportNewAndPublish.return_value = "new-guid-456"
        MockWSAPI.return_value.get_client.return_value = mock_client

        runner = CliRunner()
        result = runner.invoke(
            resource,
            ["importnewfilter", "/path/to/test.xml", "--name", "MyFilter"],
            obj={"verbose": False},
        )

        assert result.exit_code == 0, result.output
        mock_fm.upload_file_chunked.assert_called_once_with("/path/to/test.xml")
        mock_client.service.ImportNewAndPublish.assert_called_once_with(
            resourceType="FilterConfigs",
            fileGuid="file-guid-123",
            resourceInfo=mock_resource_info_instance,
        )
        assert "new-guid-456" in result.output

    @patch('memoq_cli.commands.resource.FileManager')
    @patch('memoq_cli.commands.resource.WSAPIClient')
    def test_auto_generates_name_with_timestamp(self, MockWSAPI, MockFM):
        """importnewfilter without --name should generate timestamped name"""
        mock_fm = MockFM.return_value
        mock_fm.upload_file_chunked.return_value = "file-guid-123"

        mock_client = MagicMock()
        mock_resource_info_type = Mock()
        mock_resource_info_instance = Mock()
        mock_resource_info_type.return_value = mock_resource_info_instance
        mock_client.get_type.return_value = mock_resource_info_type
        mock_client.service.ImportNewAndPublish.return_value = "new-guid-789"
        MockWSAPI.return_value.get_client.return_value = mock_client

        runner = CliRunner()
        result = runner.invoke(
            resource,
            ["importnewfilter", "/path/to/test.xml"],
            obj={"verbose": False},
        )

        assert result.exit_code == 0, result.output
        # Name should be auto-generated from filename + timestamp
        call_kwargs = mock_resource_info_type.call_args
        name = call_kwargs.kwargs.get("Name", "") or call_kwargs[1].get("Name", "")
        assert "test" in name.lower()

    @patch('memoq_cli.commands.resource.FileManager')
    def test_fails_when_upload_returns_none(self, MockFM):
        """importnewfilter should report error when upload fails"""
        mock_fm = MockFM.return_value
        mock_fm.upload_file_chunked.return_value = None

        runner = CliRunner()
        result = runner.invoke(
            resource,
            ["importnewfilter", "/path/to/test.xml"],
            obj={"verbose": False},
        )

        assert result.exit_code != 0 or "error" in result.output.lower() or "fail" in result.output.lower()


class TestResourceListAll:
    """Test memoq resource listall command"""

    @patch('memoq_cli.commands.resource.WSAPIClient')
    def test_lists_resources_for_all_types(self, MockWSAPI):
        """listall should call ListResources for each supported resource type"""
        mock_client = MagicMock()
        mock_client.service.ListResources.return_value = [
            {"Guid": "g1", "Name": "Resource1"},
        ]
        MockWSAPI.return_value.get_client.return_value = mock_client

        runner = CliRunner()
        result = runner.invoke(resource, ["listall"], obj={"verbose": False})

        assert result.exit_code == 0, result.output
        # Should have called ListResources multiple times (once per type)
        assert mock_client.service.ListResources.call_count > 1
        # Output should contain resource type names
        assert "FilterConfigs" in result.output
        assert "ProjectTemplate" in result.output

    @patch('memoq_cli.commands.resource.WSAPIClient')
    def test_listall_with_type_filter(self, MockWSAPI):
        """listall --type should only list that specific resource type"""
        mock_client = MagicMock()
        mock_client.service.ListResources.return_value = [
            {"Guid": "g1", "Name": "Filter1"},
        ]
        MockWSAPI.return_value.get_client.return_value = mock_client

        runner = CliRunner()
        result = runner.invoke(
            resource, ["listall", "--type", "FilterConfigs"],
            obj={"verbose": False},
        )

        assert result.exit_code == 0, result.output
        mock_client.service.ListResources.assert_called_once()
        assert "FilterConfigs" in result.output

    @patch('memoq_cli.commands.resource.WSAPIClient')
    def test_listall_handles_api_errors_gracefully(self, MockWSAPI):
        """listall should skip types that error and continue"""
        mock_client = MagicMock()

        def side_effect(resource_type, filter_obj):
            if resource_type == "FilterConfigs":
                return [{"Guid": "g1", "Name": "Filter1"}]
            raise Exception("deserialization error")

        mock_client.service.ListResources.side_effect = side_effect
        MockWSAPI.return_value.get_client.return_value = mock_client

        runner = CliRunner()
        result = runner.invoke(resource, ["listall"], obj={"verbose": False})

        assert result.exit_code == 0, result.output
        assert "FilterConfigs" in result.output
