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

        try:
            # 创建过滤器 - 使用完整命名空间
            # 可用字段: Client, Domain, LastChangedBefore, NameOrDescription,
            #          Project, SourceLanguageCode, Subject, TargetLanguageCode, TimeClosed
            filter_type = client.get_type("{http://kilgray.com/memoqservices/2007}ServerProjectListFilter")

            filter_kwargs = {}
            if filter_text:
                filter_kwargs["NameOrDescription"] = filter_text

            project_filter = filter_type(**filter_kwargs) if filter_kwargs else None

            # API key is automatically added by APIKeyPlugin
            result = client.service.ListProjects(
                filter=project_filter
            )
            self.log_soap_debug("ListProjects")

            projects = serialize_object(result) or []

            return projects

        except Fault as e:
            self.logger.error(f"列出项目失败: {e}")
            raise

    def get_project_info(self, project_guid: str) -> Dict[str, Any]:
        """获取项目详细信息"""
        client = self.get_client("ServerProject")

        try:
            result = client.service.GetProject(
                spGuid=project_guid  # API uses spGuid, not serverProjectGuid
            )
            self.log_soap_debug("GetProject")
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

        try:
            result = client.service.ListProjectTranslationDocuments(
                serverProjectGuid=project_guid
            )
            self.log_soap_debug("ListProjectTranslationDocuments")

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

        try:
            result = client.service.GetProjectStatistics(
                serverProjectGuid=project_guid
            )
            self.log_soap_debug("GetProjectStatistics")
            return serialize_object(result) or {}

        except Fault as e:
            self.logger.error(f"获取项目统计失败: {e}")
            raise

    def list_users(self, active_only: bool = True) -> List[Dict[str, Any]]:
        """列出所有用户"""
        client = self.get_client("Security")

        try:
            result = client.service.ListUsers()
            self.log_soap_debug("ListUsers")
            users = serialize_object(result) or []

            if active_only:
                users = [u for u in users if not u.get("IsDisabled", False)]

            return users

        except Fault as e:
            self.logger.error(f"列出用户失败: {e}")
            raise

    def set_project_translation_document_user_assignments(
        self,
        project_guid: str,
        document_guid: str,
        user_guid: str,
        role: int,
        deadline: Optional[str] = None,
    ) -> None:
        """
        设置翻译文档用户分配

        Args:
            project_guid: 项目 GUID
            document_guid: 文档 GUID
            user_guid: 用户 GUID
            role: 角色 (0=Translator, 1=Reviewer1, 2=Reviewer2)
            deadline: 可选的截止日期
        """
        client = self.get_client("ServerProject")

        try:
            # 外层类型: 每个文档的用户角色分配
            doc_assignment_type = client.get_type(
                "{http://kilgray.com/memoqservices/2007}"
                "ServerProjectTranslationDocumentUserAssignments"
            )

            # 内层类型: 单个用户-角色分配
            role_assignment_type = client.get_type(
                "{http://kilgray.com/memoqservices/2007}"
                "TranslationDocumentUserRoleAssignment"
            )

            role_kwargs = {
                "UserGuid": user_guid,
                "DocumentAssignmentRole": role,
            }
            if deadline:
                role_kwargs["DeadLine"] = deadline

            role_assignment = role_assignment_type(**role_kwargs)

            doc_assignment = doc_assignment_type(
                DocumentGuid=document_guid,
                UserRoleAssignments=[role_assignment]
            )

            client.service.SetProjectTranslationDocumentUserAssignments(
                serverProjectGuid=project_guid,
                assignments=[doc_assignment]
            )
            self.log_soap_debug("SetProjectTranslationDocumentUserAssignments")

        except Fault as e:
            self.logger.error(f"设置文档用户分配失败: {e}")
            raise

    def set_project_users(
        self,
        project_guid: str,
        user_infos: List[Dict[str, Any]],
    ) -> None:
        """设置项目用户"""
        client = self.get_client("ServerProject")

        try:
            user_info_type = client.get_type(
                "{http://kilgray.com/memoqservices/2007}"
                "ServerProjectUserInfo"
            )

            user_info_objects = []
            for info in user_infos:
                user_info_objects.append(user_info_type(**info))

            client.service.SetProjectUsers(
                serverProjectGuid=project_guid,
                userInfos=user_info_objects
            )
            self.log_soap_debug("SetProjectUsers")

        except Fault as e:
            self.logger.error(f"设置项目用户失败: {e}")
            raise
