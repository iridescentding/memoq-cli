# -*- coding: utf-8 -*-
"""
memoQ CLI - File Manager Module

Handles file upload/download operations via WSAPI.
"""

import os
import tempfile
import zipfile
from pathlib import Path
from typing import List, Dict, Any, Optional
from zeep.exceptions import Fault
from zeep.helpers import serialize_object

from .client import WSAPIClient
from ..utils import get_logger, get_files_from_directory, filter_files


class FileManager(WSAPIClient):
    """memoQ File Manager for upload/download operations"""

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.logger = get_logger("wsapi.file")

    def upload_file(
        self,
        file_path: str,
        project_guid: str,
        target_languages: Optional[List[str]] = None
    ) -> Dict[str, Any]:
        """
        Upload a single file to a project.

        Args:
            file_path: Path to the file
            project_guid: Target project GUID
            target_languages: Optional list of target language codes

        Returns:
            Upload result information
        """
        if not os.path.exists(file_path):
            raise FileNotFoundError(f"File not found: {file_path}")

        client = self.get_client("FileManager")
        header = self._get_auth_header()

        file_name = os.path.basename(file_path)
        self.logger.info(f"Uploading file: {file_name}")

        with open(file_path, "rb") as f:
            file_data = f.read()

        try:
            # Create import options
            import_options_type = client.get_type("ns0:ImportDocumentOptions")
            import_options = import_options_type(
                TargetLangCodes=target_languages or []
            )

            result = client.service.ImportDocument(
                _soapheaders=[header],
                serverProjectGuid=project_guid,
                fileName=file_name,
                fileContent=file_data,
                importOptions=import_options
            )

            return serialize_object(result) or {"status": "success", "file": file_name}

        except Fault as e:
            self.logger.error(f"Upload failed: {e}")
            raise

    def upload_zip(
        self,
        zip_path: str,
        project_guid: str,
        preserve_structure: bool = True,
        target_languages: Optional[List[str]] = None
    ) -> Dict[str, Any]:
        """
        Upload a ZIP archive to a project.

        Args:
            zip_path: Path to the ZIP file
            project_guid: Target project GUID
            preserve_structure: Whether to preserve directory structure
            target_languages: Optional list of target language codes

        Returns:
            Upload result information
        """
        if not os.path.exists(zip_path):
            raise FileNotFoundError(f"ZIP file not found: {zip_path}")

        client = self.get_client("FileManager")
        header = self._get_auth_header()

        self.logger.info(f"Uploading ZIP: {zip_path}")

        with open(zip_path, "rb") as f:
            zip_data = f.read()

        try:
            import_options_type = client.get_type("ns0:ImportDocumentOptions")
            import_options = import_options_type(
                TargetLangCodes=target_languages or [],
                PreserveDirectoryStructure=preserve_structure
            )

            result = client.service.ImportDocumentFromZip(
                _soapheaders=[header],
                serverProjectGuid=project_guid,
                zipContent=zip_data,
                importOptions=import_options
            )

            return serialize_object(result) or {"status": "success"}

        except Fault as e:
            self.logger.error(f"ZIP upload failed: {e}")
            raise

    def upload_directory(
        self,
        directory: str,
        project_guid: str,
        target_languages: Optional[List[str]] = None,
        filter_system_files: bool = True
    ) -> Dict[str, Any]:
        """
        Upload all files from a directory to a project.

        Creates a temporary ZIP and uploads it.

        Args:
            directory: Path to the directory
            project_guid: Target project GUID
            target_languages: Optional list of target language codes
            filter_system_files: Whether to filter out system files

        Returns:
            Upload result information
        """
        if not os.path.isdir(directory):
            raise NotADirectoryError(f"Directory not found: {directory}")

        # Get files from directory
        files = get_files_from_directory(
            directory,
            recursive=True,
            filter_system=filter_system_files
        )

        if not files:
            raise ValueError(f"No files found in directory: {directory}")

        self.logger.info(f"Creating ZIP from {len(files)} files in {directory}")

        # Create temporary ZIP
        with tempfile.NamedTemporaryFile(suffix=".zip", delete=False) as tmp:
            tmp_path = tmp.name

        try:
            with zipfile.ZipFile(tmp_path, "w", zipfile.ZIP_DEFLATED) as zf:
                base_dir = Path(directory)
                for file_path in files:
                    arcname = Path(file_path).relative_to(base_dir)
                    zf.write(file_path, arcname)

            # Upload the ZIP
            result = self.upload_zip(
                tmp_path,
                project_guid,
                preserve_structure=True,
                target_languages=target_languages
            )

            result["files_count"] = len(files)
            return result

        finally:
            # Clean up temp file
            if os.path.exists(tmp_path):
                os.remove(tmp_path)

    def download_document(
        self,
        project_guid: str,
        document_guid: str,
        output_path: str,
        export_format: str = "target"
    ) -> str:
        """
        Download a document from a project.

        Args:
            project_guid: Project GUID
            document_guid: Document GUID
            output_path: Output file path
            export_format: Export format ("target" or "xliff")

        Returns:
            Path to the downloaded file
        """
        client = self.get_client("FileManager")
        header = self._get_auth_header()

        self.logger.info(f"Downloading document: {document_guid}")

        try:
            if export_format == "xliff":
                result = client.service.ExportDocumentAsXliff(
                    _soapheaders=[header],
                    serverProjectGuid=project_guid,
                    documentGuid=document_guid
                )
            else:
                result = client.service.ExportTranslatedDocument(
                    _soapheaders=[header],
                    serverProjectGuid=project_guid,
                    documentGuid=document_guid
                )

            # Write file content
            os.makedirs(os.path.dirname(output_path), exist_ok=True)
            with open(output_path, "wb") as f:
                f.write(result)

            self.logger.info(f"Downloaded to: {output_path}")
            return output_path

        except Fault as e:
            self.logger.error(f"Download failed: {e}")
            raise

    def download_all_documents(
        self,
        project_guid: str,
        output_dir: str,
        export_format: str = "target"
    ) -> List[str]:
        """
        Download all documents from a project.

        Args:
            project_guid: Project GUID
            output_dir: Output directory
            export_format: Export format ("target" or "xliff")

        Returns:
            List of downloaded file paths
        """
        from .project import ProjectManager

        pm = ProjectManager()
        documents = pm.list_project_documents(project_guid)

        if not documents:
            self.logger.warning("No documents found in project")
            return []

        os.makedirs(output_dir, exist_ok=True)
        downloaded = []

        for doc in documents:
            doc_guid = doc.get("DocumentGuid", "")
            doc_name = doc.get("DocumentName", f"document_{doc_guid}")

            ext = ".xliff" if export_format == "xliff" else ""
            output_path = os.path.join(output_dir, f"{doc_name}{ext}")

            try:
                self.download_document(
                    project_guid, doc_guid, output_path, export_format
                )
                downloaded.append(output_path)
            except Exception as e:
                self.logger.error(f"Failed to download {doc_name}: {e}")

        return downloaded

    def import_xliff(
        self,
        xliff_path: str,
        project_guid: str,
        document_guid: str,
        confirm_level: str = "Confirmed"
    ) -> Dict[str, Any]:
        """
        Import XLIFF to update a document.

        Args:
            xliff_path: Path to XLIFF file
            project_guid: Project GUID
            document_guid: Document GUID to update
            confirm_level: Confirmation level

        Returns:
            Import result
        """
        if not os.path.exists(xliff_path):
            raise FileNotFoundError(f"XLIFF file not found: {xliff_path}")

        client = self.get_client("FileManager")
        header = self._get_auth_header()

        self.logger.info(f"Importing XLIFF: {xliff_path}")

        with open(xliff_path, "rb") as f:
            xliff_data = f.read()

        try:
            result = client.service.ImportXliffDocument(
                _soapheaders=[header],
                serverProjectGuid=project_guid,
                documentGuid=document_guid,
                xliffContent=xliff_data,
                confirmationLevel=confirm_level
            )

            return serialize_object(result) or {"status": "success"}

        except Fault as e:
            self.logger.error(f"XLIFF import failed: {e}")
            raise
