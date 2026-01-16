# -*- coding: utf-8 -*-
"""
memoQ CLI - TM (Translation Memory) Manager
"""

from typing import List, Dict, Any, Optional

from .client import RSAPIClient
from ..utils import get_logger


class TMManager(RSAPIClient):
    """memoQ Translation Memory Manager"""

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.logger = get_logger("rsapi.tm")
    
    def list_tms(
        self,
        filter_text: Optional[str] = None,
        source_lang: Optional[str] = None,
        target_lang: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """列出所有 TM"""
        tms = self.get("tms")
        
        # 过滤
        if filter_text:
            filter_text = filter_text.lower()
            tms = [
                tm for tm in tms
                if filter_text in tm.get("FriendlyName", "").lower()
                or filter_text in tm.get("TMGuid", "").lower()
            ]
        
        if source_lang:
            tms = [
                tm for tm in tms
                if tm.get("SourceLangCode", "").lower() == source_lang.lower()
            ]
        
        if target_lang:
            tms = [
                tm for tm in tms
                if tm.get("TargetLangCode", "").lower() == target_lang.lower()
            ]
        
        return tms
    
    def get_tm_info(self, tm_guid: str) -> Dict[str, Any]:
        """获取 TM 详细信息"""
        return self.get(f"tms/{tm_guid}")
    
    def create_tm(
        self,
        name: str,
        source_lang: str,
        target_lang: str,
        description: str = ""
    ) -> Dict[str, Any]:
        """创建新 TM"""
        payload = {
            "FriendlyName": name,
            "SourceLangCode": source_lang,
            "TargetLangCode": target_lang,
            "Description": description
        }
        
        result = self.post("tms", payload)
        self.logger.info(f"TM 创建成功: {name}")
        return result
    
    def delete_tm(self, tm_guid: str) -> bool:
        """删除 TM"""
        result = self.delete(f"tms/{tm_guid}")
        self.logger.info(f"TM 已删除: {tm_guid}")
        return result
    
    def import_tmx(
        self,
        tm_guid: str,
        tmx_path: str,
        wait_for_completion: bool = True
    ) -> Dict[str, Any]:
        """
        Import TMX file into TM.

        Args:
            tm_guid: Target TM GUID
            tmx_path: Path to TMX file
            wait_for_completion: Whether to wait for import to complete

        Returns:
            Import result or task info
        """
        result = self.upload_file(f"tms/{tm_guid}/import", tmx_path)
        self.logger.info("TMX import task started")

        if wait_for_completion and "TaskId" in result:
            result = self.wait_for_task(result["TaskId"])

        return result

    def export_tmx(
        self,
        tm_guid: str,
        output_path: str,
        wait_for_completion: bool = True
    ) -> str:
        """
        Export TM as TMX file.

        Args:
            tm_guid: TM GUID to export
            output_path: Path to save TMX file
            wait_for_completion: Whether to wait for export to complete

        Returns:
            Output file path
        """
        result = self.post(f"tms/{tm_guid}/export")

        if wait_for_completion and "TaskId" in result:
            task_result = self.wait_for_task(result["TaskId"])

            if "DownloadUrl" in task_result:
                self.download_to_file(task_result["DownloadUrl"], output_path)
                self.logger.info(f"TMX exported to: {output_path}")
                return output_path

        return result

    def search_tm(
        self,
        tm_guid: str,
        source_text: str,
        match_threshold: int = 75
    ) -> List[Dict[str, Any]]:
        """
        Search TM for matching entries.

        Args:
            tm_guid: TM GUID to search
            source_text: Source text to search for
            match_threshold: Minimum match percentage (0-100)

        Returns:
            List of matching entries
        """
        payload = {
            "SourceText": source_text,
            "MatchThreshold": match_threshold
        }

        return self.post(f"tms/{tm_guid}/search", payload)
