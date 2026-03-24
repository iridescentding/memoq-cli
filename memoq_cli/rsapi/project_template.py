# -*- coding: utf-8 -*-
"""
memoQ CLI - Project Template Manager
"""

from typing import List, Dict, Any

from .client import RSAPIClient
from ..utils import get_logger


class ProjectTemplateClient(RSAPIClient):
    """memoQ Project Template Client"""

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.logger = get_logger("rsapi.project_template")

    def list_templates(self) -> List[Dict[str, Any]]:
        """List all project templates"""
        return self.get("projecttemplates")

    def get_template(self, template_guid: str) -> Dict[str, Any]:
        """Get specific project template details by GUID"""
        return self.get(f"projecttemplates/{template_guid}")

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
            name = template.get("Name", "N/A")
            if len(name) > 38:
                name = name[:35] + "..."

            guid = template.get("Guid", "N/A")
            source = template.get("SourceLanguageCode", "N/A")

            targets = template.get("TargetLanguageCodes", [])
            target_str = ", ".join(targets[:3])
            if len(targets) > 3:
                target_str += f" (+{len(targets)-3})"

            print(f"{i:<4} {name:<40} {guid:<38} {source:<10} {target_str:<20}")

        print(f"{'='*120}\n")

    def print_template_details(self, template: Dict[str, Any]):
        """Print detailed project template information"""
        print(f"\n{'='*80}")
        print(f"Project Template Details")
        print(f"{'='*80}")

        print(f"\nName: {template.get('Name', 'N/A')}")
        print(f"GUID: {template.get('Guid', 'N/A')}")
        print(f"Source Language: {template.get('SourceLanguageCode', 'N/A')}")

        targets = template.get("TargetLanguageCodes", [])
        if targets:
            print(f"Target Languages: {', '.join(targets)}")

        # Translation Memories
        tms = template.get("TranslationMemories", [])
        if tms:
            print(f"\nTranslation Memories ({len(tms)}):")
            for tm in tms:
                print(f"  - {tm.get('Name', 'N/A')} ({tm.get('Guid', 'N/A')})")

        # Term Bases
        tbs = template.get("TermBases", [])
        if tbs:
            print(f"\nTerm Bases ({len(tbs)}):")
            for tb in tbs:
                print(f"  - {tb.get('Name', 'N/A')} ({tb.get('Guid', 'N/A')})")

        # Workflow Steps
        steps = template.get("WorkflowSteps", [])
        if steps:
            print(f"\nWorkflow Steps ({len(steps)}):")
            for step in steps:
                print(f"  {step.get('Order', '?')}. {step.get('Name', 'N/A')}")

        print(f"\n{'='*80}\n")
