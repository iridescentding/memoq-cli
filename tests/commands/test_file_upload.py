# -*- coding: utf-8 -*-
"""
Tests for file upload CLI argument handling.
"""

from unittest.mock import patch

from click.testing import CliRunner

from memoq_cli.commands.file import file


class TestFileUploadCommand:
    """Test file upload command options."""

    @patch("memoq_cli.commands.file.FileManager")
    def test_upload_passes_external_document_id_for_file(self, MockFileManager, tmp_path):
        upload_path = tmp_path / "jaytest1.txt"
        upload_path.write_text("高蛋白拿铁pro", encoding="utf-8")
        mock_fm = MockFileManager.return_value
        mock_fm.upload_file.return_value = {
            "file_name": "jaytest1.txt",
            "file_guid": "file-guid-123",
        }

        runner = CliRunner()
        result = runner.invoke(
            file,
            [
                "upload",
                "project-guid-123",
                "-p",
                str(upload_path),
                "-l",
                "eng",
                "--external-document-id",
                "jaytest1-external-id",
            ],
            obj={"verbose": False},
        )

        assert result.exit_code == 0, result.output
        mock_fm.upload_file.assert_called_once_with(
            str(upload_path),
            "project-guid-123",
            ["eng"],
            external_document_id="jaytest1-external-id",
        )
