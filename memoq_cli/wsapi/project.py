# -*- coding: utf-8 -*-
"""
memoQ CLI - 项目管理模块
"""

from typing import List, Dict, Any, Optional
from zeep.exceptions import Fault
from zeep.helpers import serialize_object

from .client import WSAPIClient
from ..utils import get_logger


class ProjectManager(WSAPIClient):
    """memoQ 项目管理"""
    
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.logger = get_logger("wsapi.project")
    
    def list_projects(
        self,
        filter_text: Optional[str] = None,
        include_archived: bool = False
    ) -> List[Dict[str, Any]]:
        """列出所有项目"""
        client = self.get_client("ServerProject")
        header = self._get_auth_header()
        
        try:
            # 创建过滤器
            filter_type = client.get_type("ns0:ServerProjectListFilter")
            project_filter = filter_type(
                IncludeArchived=include_archived
            )
            
            result = client.service.ListProjects(
                _soapheaders=[header],
                filter=project_filter
            )
            
            projects = serialize_object(result) or []
            
            # 文本过滤
            if filter_text:
                filter_text = filter_text.lower()
                projects = [
                    p for p in projects
                    if filter_text in p.get("Name", "").lower()
                    or filter_text in p.get("ServerProjectGuid", "").lower()
                ]
            
            return projects
            
        except Fault as e:
            self.logger.error(f"列出项目失败: {e}")
            raise
    
    def get_project_info(self, project_guid: str) -> Dict[str, Any]:
        """获取项目详细信息"""
        client = self.get_client("ServerProject")
        header = self._get_auth_header()
        
        try:
            result = client.service.GetProject(
                _soapheaders=[header],
                serverProjectGuid=project_guid
            )
            return serialize_object(result) or {}
            
        except Fault as e:
            self.logger.error(f"获取项目信息失败: {e}")
            raise
    
    def list_project_documents(
        self,
        project_guid: str,
        include_deleted: bool = False
    ) -> List[Dict[str, Any]]:
        """列出项目中的所有文档"""
        client = self.get_client("ServerProject")
        header = self._get_auth_header()
        
        try:
            result = client.service.ListProjectTranslationDocuments(
                _soapheaders=[header],
                serverProjectGuid=project_guid
            )
            
            documents = serialize_object(result) or []
            
            if not include_deleted:
                documents = [
                    d for d in documents
                    if not d.get("IsDeleted", False)
                ]
            
            return documents
            
        except Fault as e:
            self.logger.error(f"列出项目文档失败: {e}")
            raise
    
    def get_document_status(self, project_guid: str) -> List[Dict[str, Any]]:
        """获取项目文档状态统计"""
        documents = self.list_project_documents(project_guid)
        
        status_map = {
            0: "TranslationInProgress",
            1: "TranslationFinished",
            2: "Review1InProgress",
            3: "Review1Finished",
            4: "Review2InProgress",
            5: "Review2Finished",
            6: "ProofreadingInProgress",
            7: "ProofreadingFinished",
        }
        
        for doc in documents:
            status_id = doc.get("DocumentStatus", 0)
            doc["StatusName"] = status_map.get(status_id, f"Unknown({status_id})")
        
        return documents
    
    def get_project_statistics(self, project_guid: str) -> Dict[str, Any]:
        """获取项目统计信息"""
        client = self.get_client("ServerProject")
        header = self._get_auth_header()
        
        try:
            result = client.service.GetProjectStatistics(
                _soapheaders=[header],
                serverProjectGuid=project_guid
            )
            return serialize_object(result) or {}
            
        except Fault as e:
            self.logger.error(f"获取项目统计失败: {e}")
            raise
