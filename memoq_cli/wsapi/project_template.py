# -*- coding: utf-8 -*-
"""
memoQ CLI - WSAPI Project Template Manager
"""

from typing import List, Dict, Any
from zeep.helpers import serialize_object

from .client import WSAPIClient
from ..utils import get_logger


class ProjectTemplateManager(WSAPIClient):
    """memoQ WSAPI Project Template Manager"""

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.logger = get_logger("wsapi.project_template")

    def list_templates(self) -> List[Dict[str, Any]]:
        """
        List all project templates

        Uses Light Resource Service API:
        ListResources(ResourceType.ProjectTemplate, filter)

        Returns:
            List of project template dictionaries
        """
        client = self.get_client("Resource")

        # Call ListResources with 'ProjectTemplate' resource type
        # According to memoQ documentation:
        # https://docs.memoq.com/current/api-docs/wsapi/api/lightresourceservice/
        templates = client.service.ListResources('ProjectTemplate', None)

        # Convert to Python dict
        templates_data = serialize_object(templates)

        if not templates_data:
            return []

        return templates_data

    def get_template(self, template_guid: str) -> Dict[str, Any]:
        """
        Get detailed information about a specific project template

        Uses Light Resource Service API:
        GetResourceInfo(ResourceType.ProjectTemplate, guid)

        Args:
            template_guid: Template GUID

        Returns:
            Template details dictionary
        """
        client = self.get_client("Resource")

        # Call GetResourceInfo with ResourceType and GUID
        # According to memoQ documentation:
        # GetResourceInfo(ResourceType resourceType, Guid resourceGuid)
        resource_info = client.service.GetResourceInfo('ProjectTemplate', template_guid)

        # Convert to Python dict
        template_data = serialize_object(resource_info)

        return template_data

    def print_template_list(self, templates: List[Dict[str, Any]]):
        """Print project templates in table format"""
        if not templates:
            print("No project templates found.")
            return

        print(f"\n{'='*120}")
        print(f"Project Templates ({len(templates)} total)")
        print(f"{'='*120}")
        print(f"{'#':<4} {'Name':<40} {'GUID':<38} {'Source':<10} {'Targets':<20}")
        print(f"{'-'*120}")

        for i, template in enumerate(templates, 1):
            # Use "Name" key (not "FriendlyName") for Light Resource API
            name = template.get("Name", template.get("FriendlyName", "N/A"))
            if len(name) > 38:
                name = name[:35] + "..."

            guid = template.get("Guid", "N/A")
            source = template.get("SourceLangCode", "N/A")

            # TargetLangCodes is an object with "string" array
            targets = template.get("TargetLangCodes", {})
            if isinstance(targets, dict):
                target_list = targets.get("string", [])
            elif isinstance(targets, list):
                target_list = targets
            else:
                target_list = []

            if target_list:
                target_str = ", ".join(target_list[:3])
                if len(target_list) > 3:
                    target_str += f" (+{len(target_list)-3})"
            else:
                target_str = "N/A"

            print(f"{i:<4} {name:<40} {guid:<38} {source:<10} {target_str:<20}")

        print(f"{'='*120}\n")

    def print_template_details(self, template: Dict[str, Any]):
        """Print detailed project template information"""
        print(f"\n{'='*80}")
        print(f"Project Template Details")
        print(f"{'='*80}")

        # Use "Name" key (not "FriendlyName") for Light Resource API
        name = template.get("Name", template.get("FriendlyName", "N/A"))
        print(f"\nName: {name}")
        print(f"GUID: {template.get('Guid', 'N/A')}")
        print(f"Description: {template.get('Description', 'N/A')}")
        print(f"Source Language: {template.get('SourceLangCode', 'N/A')}")
        print(f"Read-only: {template.get('Readonly', False)}")
        print(f"Is Default: {template.get('IsDefault', False)}")

        # TargetLangCodes is an object with "string" array
        targets = template.get("TargetLangCodes", {})
        if isinstance(targets, dict):
            target_list = targets.get("string", [])
        elif isinstance(targets, list):
            target_list = targets
        else:
            target_list = []

        if target_list:
            print(f"Target Languages: {', '.join(target_list)}")

        print(f"\n{'='*80}\n")
