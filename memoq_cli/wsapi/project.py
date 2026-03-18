# -*- coding: utf-8 -*-
"""
memoQ CLI - 项目管理模块
"""

from datetime import datetime
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
        deadline: datetime,
    ) -> None:
        """
        增量设置翻译文档用户分配（read-modify-write）

        仅修改指定文档的指定角色，保留其他文档和角色的现有分配。

        Args:
            project_guid: 项目 GUID
            document_guid: 文档 GUID
            user_guid: 用户 GUID
            role: 角色 (0=Translator, 1=Reviewer1, 2=Reviewer2)
            deadline: 截止日期 (必填，DateTime 非空类型)
        """
        client = self.get_client("ServerProject")

        try:
            ns = "{http://kilgray.com/memoqservices/2007}"

            doc_assignment_type = client.get_type(
                ns + "ServerProjectTranslationDocumentUserAssignments"
            )
            role_assignment_type = client.get_type(
                ns + "TranslationDocumentUserRoleAssignment"
            )
            array_role_type = client.get_type(
                ns + "ArrayOfTranslationDocumentUserRoleAssignment"
            )
            array_doc_type = client.get_type(
                ns + "ArrayOfServerProjectTranslationDocumentUserAssignments"
            )

            # Step 1: 读取现有所有文档分配
            existing = self.list_translation_document_assignments(project_guid)

            # Step 2: 构建完整的分配列表
            doc_assignments = []
            target_doc_found = False

            for doc_assign in existing:
                existing_doc_guid = str(doc_assign.get("DocumentGuid", ""))
                assignments_data = doc_assign.get("Assignments") or {}
                if isinstance(assignments_data, dict):
                    assign_list = assignments_data.get(
                        "TranslationDocumentDetailedAssignmentInfo"
                    ) or []
                else:
                    assign_list = assignments_data

                role_objs = []

                if existing_doc_guid == str(document_guid):
                    # 目标文档：保留其他角色，替换目标角色
                    target_doc_found = True
                    target_role_replaced = False

                    for info in assign_list:
                        existing_role = info.get("RoleId", -1)
                        if existing_role == role:
                            # 替换为新分配
                            target_role_replaced = True
                            role_objs.append(role_assignment_type(
                                UserGuid=user_guid,
                                DocumentAssignmentRole=role,
                                DeadLine=deadline,
                            ))
                        else:
                            # 保留原有分配
                            user_info = info.get("User", {})
                            role_objs.append(role_assignment_type(
                                UserGuid=str(user_info.get("AssigneeGuid", "")),
                                DocumentAssignmentRole=existing_role,
                                DeadLine=info.get("Deadline"),
                            ))

                    if not target_role_replaced:
                        # 新增角色
                        role_objs.append(role_assignment_type(
                            UserGuid=user_guid,
                            DocumentAssignmentRole=role,
                            DeadLine=deadline,
                        ))
                else:
                    # 非目标文档：原样保留
                    for info in assign_list:
                        user_info = info.get("User", {})
                        role_objs.append(role_assignment_type(
                            UserGuid=str(user_info.get("AssigneeGuid", "")),
                            DocumentAssignmentRole=info.get("RoleId", 0),
                            DeadLine=info.get("Deadline"),
                        ))

                if role_objs:
                    doc_assignments.append(doc_assignment_type(
                        DocumentGuid=existing_doc_guid,
                        UserRoleAssignments=array_role_type(
                            TranslationDocumentUserRoleAssignment=role_objs
                        ),
                    ))

            if not target_doc_found:
                # 目标文档之前没有任何分配，新建
                doc_assignments.append(doc_assignment_type(
                    DocumentGuid=document_guid,
                    UserRoleAssignments=array_role_type(
                        TranslationDocumentUserRoleAssignment=[
                            role_assignment_type(
                                UserGuid=user_guid,
                                DocumentAssignmentRole=role,
                                DeadLine=deadline,
                            )
                        ]
                    ),
                ))

            # Step 3: 写入完整列表
            assignments_array = array_doc_type(
                ServerProjectTranslationDocumentUserAssignments=doc_assignments
            )

            client.service.SetProjectTranslationDocumentUserAssignments(
                serverProjectGuid=project_guid,
                assignments=assignments_array,
            )
            self.log_soap_debug("SetProjectTranslationDocumentUserAssignments")

        except Fault as e:
            self.logger.error(f"设置文档用户分配失败: {e}")
            raise

    def list_translation_document_assignments(
        self,
        project_guid: str,
        document_guids: Optional[List[str]] = None,
    ) -> List[Dict[str, Any]]:
        """
        列出项目中翻译文档的分配情况

        Args:
            project_guid: 项目 GUID
            document_guids: 可选的文档 GUID 列表，为 None 则列出所有文档
        """
        client = self.get_client("ServerProject")

        try:
            options_type = client.get_type(
                "{http://kilgray.com/memoqservices/2007}"
                "ListTranslationDocumentAssignmentsOptions"
            )

            options_kwargs = {}
            if document_guids:
                options_kwargs["DocumentGuids"] = document_guids

            options = options_type(**options_kwargs)

            result = client.service.ListTranslationDocumentAssignments(
                serverProjectGuid=project_guid,
                options=options,
            )
            self.log_soap_debug("ListTranslationDocumentAssignments")
            return serialize_object(result) or []

        except Fault as e:
            self.logger.error(f"列出文档分配失败: {e}")
            raise

    def list_project_users(
        self,
        project_guid: str,
    ) -> List[Dict[str, Any]]:
        """列出项目中的用户"""
        client = self.get_client("ServerProject")

        try:
            result = client.service.ListProjectUsers(
                serverProjectGuid=project_guid
            )
            self.log_soap_debug("ListProjectUsers")
            return serialize_object(result) or []

        except Fault as e:
            self.logger.error(f"列出项目用户失败: {e}")
            raise

    def set_project_users(
        self,
        project_guid: str,
        user_infos: List[Dict[str, Any]],
    ) -> None:
        """
        增量设置项目用户（read-modify-write）

        保留现有项目用户，仅添加或更新指定的用户。
        """
        client = self.get_client("ServerProject")

        try:
            ns = "{http://kilgray.com/memoqservices/2007}"

            user_info_type = client.get_type(ns + "ServerProjectUserInfo")
            roles_type = client.get_type(
                "{http://schemas.datacontract.org/2004/07/MemoQServices}"
                "ServerProjectRoles"
            )
            array_type = client.get_type(ns + "ArrayOfServerProjectUserInfo")

            # Step 1: 读取现有项目用户
            existing_users = self.list_project_users(project_guid)

            # 构建 GUID -> 用户信息 的映射
            user_map = {}
            for eu in existing_users:
                user_data = eu.get("User", {})
                guid = str(user_data.get("UserGuid", ""))
                roles = eu.get("ProjectRoles", {})
                user_map[guid] = {
                    "UserGuid": guid,
                    "ProjectRoles": {
                        "ProjectManager": roles.get("ProjectManager", False),
                        "Terminologist": roles.get("Terminologist", False),
                    },
                    "PermForLicense": eu.get("PermForLicense", True),
                }

            # Step 2: 合并新用户（添加或更新）
            for info in user_infos:
                guid = str(info["UserGuid"])
                project_roles = info.get("ProjectRoles", {})
                if not isinstance(project_roles, dict):
                    project_roles = {"ProjectManager": False, "Terminologist": False}
                user_map[guid] = {
                    "UserGuid": guid,
                    "ProjectRoles": project_roles,
                    "PermForLicense": info.get("PermForLicense", True),
                }

            # Step 3: 构建完整列表并写入
            user_info_objects = []
            for data in user_map.values():
                roles_obj = roles_type(**data["ProjectRoles"])
                user_info_objects.append(user_info_type(
                    UserGuid=data["UserGuid"],
                    ProjectRoles=roles_obj,
                    PermForLicense=data["PermForLicense"],
                ))

            users_array = array_type(ServerProjectUserInfo=user_info_objects)

            client.service.SetProjectUsers(
                serverProjectGuid=project_guid,
                userInfos=users_array,
            )
            self.log_soap_debug("SetProjectUsers")

        except Fault as e:
            self.logger.error(f"设置项目用户失败: {e}")
            raise
