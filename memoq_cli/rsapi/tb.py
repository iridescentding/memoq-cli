# -*- coding: utf-8 -*-
"""
memoQ CLI - TB (Terminology Base) Manager
"""

from typing import List, Dict, Any, Optional

from .client import RSAPIClient
from ..utils import get_logger


class TBManager(RSAPIClient):
    """memoQ Terminology Base Manager"""

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.logger = get_logger("rsapi.tb")
    
    def list_tbs(
        self,
        filter_text: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """列出所有 TB"""
        tbs = self.get("tbs")
        
        if filter_text:
            filter_text = filter_text.lower()
            tbs = [
                tb for tb in tbs
                if filter_text in tb.get("FriendlyName", "").lower()
                or filter_text in tb.get("TBGuid", "").lower()
            ]
        
        return tbs
    
    def get_tb_info(self, tb_guid: str) -> Dict[str, Any]:
        """获取 TB 详细信息"""
        return self.get(f"tbs/{tb_guid}")
    
    def create_tb(
        self,
        name: str,
        languages: List[str],
        description: str = ""
    ) -> Dict[str, Any]:
        """创建新 TB"""
        payload = {
            "FriendlyName": name,
            "Languages": languages,
            "Description": description
        }
        
        result = self.post("tbs", payload)
        self.logger.info(f"TB 创建成功: {name}")
        return result
    
    def delete_tb(self, tb_guid: str) -> bool:
        """删除 TB"""
        result = self.delete(f"tbs/{tb_guid}")
        self.logger.info(f"TB 已删除: {tb_guid}")
        return result
    
    def add_entry(
        self,
        tb_guid: str,
        terms: Dict[str, str],
        definition: str = "",
        domain: str = ""
    ) -> Dict[str, Any]:
        """添加术语条目"""
        payload = {
            "Terms": [
                {"LangCode": lang, "Term": term}
                for lang, term in terms.items()
            ],
            "Definition": definition,
            "Domain": domain
        }
        
        result = self.post(f"tbs/{tb_guid}/entries", payload)
        self.logger.info(f"术语条目已添加")
        return result
    
    def search_tb(
        self,
        tb_guid: str,
        search_text: str,
        source_lang: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """搜索术语"""
        params = {"q": search_text}
        if source_lang:
            params["sourceLang"] = source_lang
        
        return self.get(f"tbs/{tb_guid}/entries", params)
    
    def import_csv(
        self,
        tb_guid: str,
        csv_path: str,
        wait_for_completion: bool = True
    ) -> Dict[str, Any]:
        """
        Import terms from CSV file.

        Args:
            tb_guid: Target TB GUID
            csv_path: Path to CSV file
            wait_for_completion: Whether to wait for import to complete

        Returns:
            Import result or task info
        """
        result = self.upload_file(f"tbs/{tb_guid}/import", csv_path)
        self.logger.info("CSV import task started")

        if wait_for_completion and "TaskId" in result:
            result = self.wait_for_task(result["TaskId"])

        return result

    def export_csv(
        self,
        tb_guid: str,
        output_path: str
    ) -> str:
        """
        Export TB as CSV file.

        Args:
            tb_guid: TB GUID to export
            output_path: Path to save CSV file

        Returns:
            Output file path
        """
        result = self.post(f"tbs/{tb_guid}/export")

        if "TaskId" in result:
            task_result = self.wait_for_task(result["TaskId"])

            if "DownloadUrl" in task_result:
                self.download_to_file(task_result["DownloadUrl"], output_path)
                self.logger.info(f"CSV exported to: {output_path}")
                return output_path

        return result
