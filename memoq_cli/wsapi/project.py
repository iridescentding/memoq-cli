# -*- coding: utf-8 -*-
"""
memoQ CLI - 项目管理模块
"""

from datetime import datetime, timedelta
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

    def _array_of_string(self, client, values: Optional[List[str]]):
        """Build the SOAP ArrayOfstring wrapper memoQ expects for string arrays."""
        if not values:
            return None
        array_type = client.get_type(
            "{http://schemas.microsoft.com/2003/10/Serialization/Arrays}"
            "ArrayOfstring"
        )
        return array_type(string=list(values))

    def create_project_from_template(
        self,
        template_guid: str,
        creator_user: str,
        name: Optional[str] = None,
        source_language_code: Optional[str] = None,
        target_language_codes: Optional[List[str]] = None,
        description: Optional[str] = None,
        client_attr: Optional[str] = None,
        domain: Optional[str] = None,
        project_attr: Optional[str] = None,
        subject: Optional[str] = None,
        project_creation_aspects: Optional[List[str]] = None,
    ) -> Dict[str, Any]:
        """Create a server project from a project template."""
        client = self.get_client("ServerProject")

        try:
            ns = "{http://kilgray.com/memoqservices/2007}"
            create_info_type = client.get_type(ns + "TemplateBasedProjectCreateInfo")

            kwargs = {
                "TemplateGuid": template_guid,
                "CreatorUser": creator_user,
            }
            optional_values = {
                "Name": name,
                "SourceLanguageCode": source_language_code,
                "Description": description,
                "Client": client_attr,
                "Domain": domain,
                "Project": project_attr,
                "Subject": subject,
            }
            kwargs.update({
                key: value for key, value in optional_values.items()
                if value is not None
            })

            target_langs = self._array_of_string(client, target_language_codes)
            if target_langs is not None:
                kwargs["TargetLanguageCodes"] = target_langs

            aspects = self._array_of_string(client, project_creation_aspects)
            if aspects is not None:
                kwargs["ProjectCreationAspects"] = aspects

            create_info = create_info_type(**kwargs)
            result = client.service.CreateProjectFromTemplate(
                createInfo=create_info
            )
            self.log_soap_debug("CreateProjectFromTemplate")
            return serialize_object(result) or {}

        except Fault as e:
            self.logger.error(f"通过模板创建项目失败: {e}")
            raise

    def create_project(
        self,
        name: str,
        creator_user: str,
        source_language_code: str,
        target_language_codes: List[str],
        description: Optional[str] = None,
        client_attr: Optional[str] = None,
        domain: Optional[str] = None,
        project_attr: Optional[str] = None,
        subject: Optional[str] = None,
        deadline: Optional[datetime] = None,
        callback_url: Optional[str] = None,
        allow_overlapping_workflow: bool = False,
        allow_package_creation: bool = False,
        download_preview2: bool = False,
        download_skeleton2: bool = False,
        enable_communication: bool = False,
        omit_hits_with_no_target_term: bool = False,
        prevent_delivery_on_qa_error: bool = False,
        record_version_history: bool = False,
        strict_sublang_matching: bool = False,
        strict_sublang_matching_livedocs: bool = False,
        strict_sublang_matching_tm: bool = False,
        checkout_is_disabled: bool = False,
        create_offline_tm_tb_copies: bool = False,
        download_preview: bool = False,
        download_skeleton: bool = False,
        enable_bilingual_export_in_local_copy: bool = False,
        enable_split_join: bool = False,
        enable_web_trans: bool = False,
    ) -> str:
        """Create a new Desktop Docs server project via CreateProject2."""
        client = self.get_client("ServerProject")

        try:
            if deadline is None:
                deadline = (
                    datetime.now() + timedelta(days=14)
                ).replace(hour=9, minute=0, second=0, microsecond=0)

            ns = "{http://kilgray.com/memoqservices/2007}"
            create_info_type = client.get_type(ns + "ServerProjectDesktopDocsCreateInfo")

            kwargs = {
                "Name": name,
                "CreatorUser": creator_user,
                "SourceLanguageCode": source_language_code,
                "TargetLanguageCodes": self._array_of_string(
                    client, target_language_codes
                ),
                "AllowOverlappingWorkflow": allow_overlapping_workflow,
                "AllowPackageCreation": allow_package_creation,
                "DownloadPreview2": download_preview2,
                "DownloadSkeleton2": download_skeleton2,
                "EnableCommunication": enable_communication,
                "OmitHitsWithNoTargetTerm": omit_hits_with_no_target_term,
                "PreventDeliveryOnQAError": prevent_delivery_on_qa_error,
                "RecordVersionHistory": record_version_history,
                "StrictSubLangMatching": strict_sublang_matching,
                "StrictSubLangMatchingLiveDocs": strict_sublang_matching_livedocs,
                "StrictSubLangMatchingTM": strict_sublang_matching_tm,
                "CheckoutIsDisabled": checkout_is_disabled,
                "CreateOfflineTMTBCopies": create_offline_tm_tb_copies,
                "DownloadPreview": download_preview,
                "DownloadSkeleton": download_skeleton,
                "EnableBilingualExportInLocalCopy": (
                    enable_bilingual_export_in_local_copy
                ),
                "EnableSplitJoin": enable_split_join,
                "EnableWebTrans": enable_web_trans,
            }
            optional_values = {
                "Description": description,
                "Client": client_attr,
                "Domain": domain,
                "Project": project_attr,
                "Subject": subject,
                "Deadline": deadline,
                "CallbackWebServiceUrl": callback_url,
            }
            kwargs.update({
                key: value for key, value in optional_values.items()
                if value is not None
            })

            create_info = create_info_type(**kwargs)
            result = client.service.CreateProject2(spInfo=create_info)
            self.log_soap_debug("CreateProject2")
            return str(result)

        except Fault as e:
            self.logger.error(f"创建项目失败: {e}")
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

    # -- Statistics (async task-based) ----------------------------------

    def _build_statistics_options(self, sp_client):
        """构造一个默认 StatisticsOptions / Build default StatisticsOptions."""
        ns = "{http://kilgray.com/memoqservices/2007}"
        options_type = sp_client.get_type(ns + "StatisticsOptions")
        return options_type(
            Algorithm="MemoQ",
            Analysis_Homogenity=False,
            Analysis_ProjectTMs=True,
            Analyzis_DetailsByTM=False,
            DisableCrossFileRepetition=False,
            IncludeLockedRows=True,
            RepetitionPreferenceOver100=False,
            ShowCounts=True,
            ShowCounts_IncludeTargetCount=False,
            ShowCounts_IncludeWhitespacesInCharCount=False,
            ShowCounts_StatusReport=True,
            ShowResultsPerFile=True,
            TagCharWeight=0.0,
            TagWordWeight=0.0,
        )

    def _wait_for_task(self, task_id: str, poll_interval: float = 2.0,
                       timeout: float = 600.0) -> Dict[str, Any]:
        """轮询任务直到完成, 返回 TaskResult / Poll a task until done, return result."""
        import time
        tasks = self.get_client("Tasks")
        start = time.time()
        last_status = None
        while True:
            info = tasks.service.GetTaskStatus(taskId=task_id)
            self.log_soap_debug("GetTaskStatus")
            info_dict = serialize_object(info) or {}
            status = info_dict.get("Status")
            last_status = status
            if status == "Completed":
                break
            if status in ("Failed", "Cancelled", "InvalidTask"):
                raise RuntimeError(
                    f"Statistics task {task_id} ended with status {status}"
                )
            if time.time() - start > timeout:
                raise TimeoutError(
                    f"Statistics task {task_id} timed out after {timeout:.0f}s "
                    f"(last status: {last_status})"
                )
            time.sleep(poll_interval)

        result = tasks.service.GetTaskResult(taskId=task_id)
        self.log_soap_debug("GetTaskResult")
        return serialize_object(result) or {}

    def get_project_statistics(
        self,
        project_guid: str,
        target_lang_codes: Optional[List[str]] = None,
        result_format: str = "CSV_MemoQ",
    ) -> Dict[str, Any]:
        """
        获取项目统计信息 (异步, 使用 StartStatisticsOnProjectTask2)
        Get project-level statistics via async task.

        Args:
            project_guid: 项目 GUID
            target_lang_codes: 可选, 指定目标语言 / Optional target language filter
            result_format: StatisticsResultFormat 枚举值 / enum string
        """
        sp = self.get_client("ServerProject")

        try:
            ns = "{http://kilgray.com/memoqservices/2007}"
            req_type = sp.get_type(ns + "CreateStatisticsOnProjectRequest")
            array_str = sp.get_type(
                "{http://schemas.microsoft.com/2003/10/Serialization/Arrays}"
                "ArrayOfstring"
            )

            req_kwargs = {
                "ProjectGuid": project_guid,
                "Options": self._build_statistics_options(sp),
                "ResultFormat": result_format,
            }
            if target_lang_codes:
                req_kwargs["TargetLangCodes"] = array_str(string=target_lang_codes)

            request = req_type(**req_kwargs)

            task_info = sp.service.StartStatisticsOnProjectTask2(request=request)
            self.log_soap_debug("StartStatisticsOnProjectTask2")
            task_id = (serialize_object(task_info) or {}).get("TaskId")
            if not task_id:
                raise RuntimeError("StartStatisticsOnProjectTask2 returned no TaskId")
            self.logger.info(f"统计任务已启动 / stats task started: {task_id}")

            return self._wait_for_task(str(task_id))

        except Fault as e:
            self.logger.error(f"获取项目统计失败: {e}")
            raise

    def get_document_statistics(
        self,
        project_guid: str,
        document_guids: List[str],
        result_format: str = "CSV_MemoQ",
    ) -> Dict[str, Any]:
        """
        获取指定文档的统计信息 (异步, StartStatisticsOnTranslationDocumentsTask2)
        Get document-level statistics via async task.
        """
        sp = self.get_client("ServerProject")

        try:
            ns = "{http://kilgray.com/memoqservices/2007}"
            req_type = sp.get_type(ns + "CreateStatisticsOnDocumentsRequest")
            array_guid = sp.get_type(
                "{http://schemas.microsoft.com/2003/10/Serialization/Arrays}"
                "ArrayOfguid"
            )

            request = req_type(
                ProjectGuid=project_guid,
                Options=self._build_statistics_options(sp),
                ResultFormat=result_format,
                DocumentOrSliceGuids=array_guid(guid=document_guids),
            )

            task_info = sp.service.StartStatisticsOnTranslationDocumentsTask2(
                request=request
            )
            self.log_soap_debug("StartStatisticsOnTranslationDocumentsTask2")
            task_id = (serialize_object(task_info) or {}).get("TaskId")
            if not task_id:
                raise RuntimeError(
                    "StartStatisticsOnTranslationDocumentsTask2 returned no TaskId"
                )
            self.logger.info(f"文档统计任务已启动 / docs stats task started: {task_id}")

            return self._wait_for_task(str(task_id))

        except Fault as e:
            self.logger.error(f"获取文档统计失败: {e}")
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

    def list_project_translation_documents2(
        self,
        project_guid: str,
        fill_in_assignment_info: bool = True,
    ) -> List[Dict[str, Any]]:
        """
        列出项目翻译文档的详细信息（使用 ListProjectTranslationDocuments2）

        Args:
            project_guid: 项目 GUID
            fill_in_assignment_info: 是否填充分配信息（False 性能更好）
        """
        client = self.get_client("ServerProject")

        try:
            options_type = client.get_type(
                "{http://kilgray.com/memoqservices/2007}"
                "ListServerProjectTranslationDocument2Options"
            )
            options = options_type(
                FillInAssignmentInformation=fill_in_assignment_info,
            )

            result = client.service.ListProjectTranslationDocuments2(
                serverProjectGuid=project_guid,
                options=options,
            )
            self.log_soap_debug("ListProjectTranslationDocuments2")
            return serialize_object(result) or []

        except Fault as e:
            self.logger.error(f"列出项目文档详情失败: {e}")
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

    def update_project(
        self,
        project_guid: str,
        description: Optional[str] = None,
        deadline: Optional[datetime] = None,
        client: Optional[str] = None,
        domain: Optional[str] = None,
        project_attr: Optional[str] = None,
        subject: Optional[str] = None,
        callback_url: Optional[str] = None,
        source_editing_turned_off: Optional[bool] = None,
    ) -> None:
        """
        Update server project header information.

        Uses WSAPI UpdateProject(ServerProjectUpdateInfo).
        All fields except project_guid are optional; null means no change.
        """
        ws_client = self.get_client("ServerProject")

        try:
            ns = "{http://kilgray.com/memoqservices/2007}"
            update_info_type = ws_client.get_type(ns + "ServerProjectUpdateInfo")

            kwargs = {"ServerProjectGuid": project_guid}

            if description is not None:
                kwargs["Description"] = description
            if deadline is not None:
                kwargs["Deadline"] = deadline
            if client is not None:
                kwargs["Client"] = client
            if domain is not None:
                kwargs["Domain"] = domain
            if project_attr is not None:
                kwargs["Project"] = project_attr
            if subject is not None:
                kwargs["Subject"] = subject
            if callback_url is not None:
                kwargs["CallbackWebServiceUrl"] = callback_url
            if source_editing_turned_off is not None:
                kwargs["SourceEditingTurnedOff"] = source_editing_turned_off

            update_info = update_info_type(**kwargs)

            ws_client.service.UpdateProject(spInfo=update_info)
            self.log_soap_debug("UpdateProject")
            self.logger.info(f"项目已更新: {project_guid}")

        except Fault as e:
            self.logger.error(f"更新项目失败: {e}")
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
