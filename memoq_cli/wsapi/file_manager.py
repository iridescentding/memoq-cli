# -*- coding: utf-8 -*-
"""
memoQ CLI - File Manager Module

Handles file upload/download operations via WSAPI.
Uses chunked upload for reliable file transfer.
"""

import os
import tempfile
import zipfile
from pathlib import Path
from typing import List, Dict, Any, Optional
from zeep.exceptions import Fault
from zeep.helpers import serialize_object

from .client import WSAPIClient
from ..utils import get_logger, is_system_file


class FileManager(WSAPIClient):
    """memoQ File Manager for upload/download operations"""

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.logger = get_logger("wsapi.file")

    def upload_file_chunked(
        self,
        file_path: str,
        file_name: Optional[str] = None,
        chunk_size: int = 1024 * 1024
    ) -> Optional[str]:
        """
        Upload file using chunked upload to FileManager service.

        Args:
            file_path: Path to the file
            file_name: Optional file name (defaults to basename)
            chunk_size: Chunk size in bytes (default 1MB)

        Returns:
            Upload session ID (file GUID) on success, None on failure
        """
        if not os.path.exists(file_path):
            raise FileNotFoundError(f"File not found: {file_path}")

        client = self.get_client("FileManager")
        file_name = file_name or os.path.basename(file_path)

        try:
            # Check if it's a ZIP file
            is_zip = file_name.lower().endswith('.zip')

            # 1. Begin chunked upload session
            self.logger.debug(f"Starting upload session: {file_name}, isZipped={is_zip}")
            upload_session_id = client.service.BeginChunkedFileUpload(
                fileName=file_name,
                isZipped=is_zip
            )
            self.logger.debug(f"Upload session ID: {upload_session_id}")

            # 2. Upload file in chunks
            with open(file_path, 'rb') as f:
                chunk_index = 0
                while True:
                    chunk = f.read(chunk_size)
                    if not chunk:
                        break

                    client.service.AddNextFileChunk(
                        fileIdAndSessionId=upload_session_id,
                        fileData=chunk
                    )
                    chunk_index += 1

            # 3. End upload session
            client.service.EndChunkedFileUpload(upload_session_id)
            self.logger.info(f"Upload complete: {file_name} ({chunk_index} chunks)")
            return str(upload_session_id)

        except Fault as e:
            self.logger.error(f"SOAP Fault during upload: {e}")
            return None
        except Exception as e:
            self.logger.error(f"Upload failed: {e}")
            return None

    def import_document_to_project(
        self,
        file_guid: str,
        project_guid: str,
        target_languages: List[str],
        import_path: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Import an uploaded file into a project.

        Args:
            file_guid: File GUID from upload
            project_guid: Target project GUID
            target_languages: List of target language codes
            import_path: Optional path within project

        Returns:
            Import result
        """
        # Clear cached clients and create fresh session to avoid stale connections
        # This is important after large file uploads
        self._clients.clear()
        self._session.close()
        from requests import Session
        self._session = Session()
        self._session.verify = self._verify_ssl
        self._session.trust_env = False  # Bypass proxy

        client = self.get_client("ServerProject")

        try:
            # Get types
            ImportOptionsType = client.get_type(
                '{http://kilgray.com/memoqservices/2007}ImportTranslationDocumentOptions'
            )
            ArrayImportOptionsType = client.get_type(
                '{http://kilgray.com/memoqservices/2007}ArrayOfImportTranslationDocumentOptions'
            )

            # Build import options
            kwargs = {
                'FileGuid': file_guid,
                'TargetLangCodes': {'string': list(target_languages)},
            }
            if import_path:
                kwargs['PathToSetAsImportPath'] = import_path

            item = ImportOptionsType(**kwargs)
            import_options_array = ArrayImportOptionsType([item])

            # Call import
            results = client.service.ImportTranslationDocumentsWithOptions(
                serverProjectGuid=project_guid,
                importDocOptions=import_options_array
            )

            if results:
                result = results[0]
                result_dict = serialize_object(result) or {}

                # Check for errors
                if hasattr(result, 'ErrorMessage') and result.ErrorMessage:
                    self.logger.error(f"Import error: {result.ErrorMessage}")
                    result_dict['error'] = result.ErrorMessage
                else:
                    self.logger.info(f"Document imported successfully")

                return result_dict

            return {"status": "no_result"}

        except Fault as e:
            self.logger.error(f"Import failed: {e}")
            raise

    def upload_file(
        self,
        file_path: str,
        project_guid: str,
        target_languages: Optional[List[str]] = None
    ) -> Dict[str, Any]:
        """
        Upload a single file to a project (chunked upload + import).

        Args:
            file_path: Path to the file
            project_guid: Target project GUID
            target_languages: Optional list of target language codes

        Returns:
            Upload result information
        """
        if not os.path.exists(file_path):
            raise FileNotFoundError(f"File not found: {file_path}")

        file_name = os.path.basename(file_path)
        self.logger.info(f"Uploading file: {file_name}")

        # Step 1: Upload file to FileManager
        file_guid = self.upload_file_chunked(file_path, file_name)
        if not file_guid:
            raise RuntimeError(f"Failed to upload file: {file_name}")

        # Step 2: Import into project
        target_langs = target_languages or ['eng']
        result = self.import_document_to_project(
            file_guid=file_guid,
            project_guid=project_guid,
            target_languages=target_langs
        )

        result['file_name'] = file_name
        result['file_guid'] = file_guid
        return result

    def download_file_chunked(
        self,
        file_guid: str,
        output_path: str,
        chunk_size: int = 1024 * 1024
    ) -> str:
        """
        Download file using chunked download from FileManager service.

        Args:
            file_guid: File GUID to download
            output_path: Output file path
            chunk_size: Chunk size in bytes (default 1MB)

        Returns:
            Path to the downloaded file
        """
        client = self.get_client("FileManager")

        try:
            # 1. Begin chunked download session
            self.logger.debug(f"Starting download session: {file_guid}")
            download_info = client.service.BeginChunkedFileDownload(
                fileGuid=file_guid,
                zip=False
            )

            # Extract session ID from response
            session_id = download_info.BeginChunkedFileDownloadResult
            file_name = download_info.fileName
            file_size = download_info.fileSize
            self.logger.debug(f"Download session: {session_id}, file: {file_name}, size: {file_size}")

            # 2. Download file in chunks
            os.makedirs(os.path.dirname(output_path) or '.', exist_ok=True)
            with open(output_path, 'wb') as f:
                chunk_index = 0
                while True:
                    chunk = client.service.GetNextFileChunk(
                        sessionId=session_id,
                        byteCount=chunk_size
                    )

                    if not chunk:
                        break

                    f.write(chunk)
                    chunk_index += 1

            # 3. End download session
            client.service.EndChunkedFileDownload(sessionId=session_id)
            self.logger.info(f"Download complete: {output_path} ({chunk_index} chunks)")
            return output_path

        except Fault as e:
            self.logger.error(f"SOAP Fault during download: {e}")
            raise
        except Exception as e:
            self.logger.error(f"Download failed: {e}")
            raise

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
        client = self.get_client("ServerProject")

        self.logger.info(f"Downloading document: {document_guid}")

        try:
            if export_format == "xliff":
                # Export as XLIFF bilingual
                result = client.service.ExportTranslationDocumentAsXliffBilingual(
                    serverProjectGuid=project_guid,
                    docGuid=document_guid  # API uses docGuid
                )
            else:
                # Export translated document
                result = client.service.ExportTranslationDocument(
                    serverProjectGuid=project_guid,
                    docGuid=document_guid  # API uses docGuid
                )

            # Result contains FileGuid - use chunked download
            if result and hasattr(result, 'FileGuid') and result.FileGuid:
                return self.download_file_chunked(
                    str(result.FileGuid),
                    output_path
                )
            else:
                error_msg = getattr(result, 'MainMessage', 'Unknown error')
                raise RuntimeError(f"Export failed: {error_msg}")

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
        project_guid: str
    ) -> Dict[str, Any]:
        """
        Import XLIFF/mqxliff to update a document.

        Uses UpdateTranslationDocumentFromBilingual for mqxliff files.

        Args:
            xliff_path: Path to XLIFF/mqxliff file
            project_guid: Project GUID

        Returns:
            Import result
        """
        if not os.path.exists(xliff_path):
            raise FileNotFoundError(f"XLIFF file not found: {xliff_path}")

        self.logger.info(f"Importing XLIFF: {xliff_path}")

        # Step 1: Upload the XLIFF file
        file_name = os.path.basename(xliff_path)
        file_guid = self.upload_file_chunked(xliff_path, file_name)
        if not file_guid:
            raise RuntimeError(f"Failed to upload XLIFF: {file_name}")

        # Step 2: Update document from bilingual
        client = self.get_client("ServerProject")

        try:
            # docFormat enum values: MBD, XLIFF, TwoColumnRTF, TableDOCX
            # MQXLIFF files use 'XLIFF' format
            result = client.service.UpdateTranslationDocumentFromBilingual(
                serverProjectGuid=project_guid,
                fileGuid=file_guid,
                docFormat='XLIFF'
            )

            result_dict = serialize_object(result) or {}
            self.logger.info(f"XLIFF import complete")
            return result_dict

        except Fault as e:
            self.logger.error(f"XLIFF import failed: {e}")
            raise
