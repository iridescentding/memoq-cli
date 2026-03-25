# -*- coding: utf-8 -*-
"""
Integration test: Upload testfilter.xml -> ImportNewAndPublish -> ListResources verify

This test hits the real memoQ server. Run with:
    uv run python -m pytest tests/integration/test_import_filter.py -v -s
"""

import os
import pytest
from datetime import datetime
from zeep.helpers import serialize_object

from memoq_cli.wsapi.client import WSAPIClient
from memoq_cli.wsapi.file_manager import FileManager


# Skip if no config.json (CI environment)
pytestmark = pytest.mark.skipif(
    not os.path.exists("config.json"),
    reason="No config.json found, skip integration test"
)

RESOURCE_NS = "http://kilgray.com/memoqservices/2007"


class TestImportFilterResource:
    """Integration test: import a FilterConfig resource to memoQ server"""

    def setup_method(self):
        self.timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        self.resource_name = f"testimportfilterbyclaude_{self.timestamp}"
        self.created_guid = None

    def test_upload_and_import_filter(self):
        """Full flow: upload file -> ImportNewAndPublish -> ListResources verify"""
        filter_file = os.path.join(os.path.dirname(__file__), "..", "..", "testfilter.xml")
        filter_file = os.path.abspath(filter_file)
        assert os.path.exists(filter_file), f"testfilter.xml not found at {filter_file}"

        # Step 1: Upload file
        fm = FileManager()
        file_guid = fm.upload_file_chunked(filter_file, "testfilter.xml")
        assert file_guid is not None, "File upload failed"
        print(f"\n  Step 1 OK: File uploaded, fileGuid = {file_guid}")

        # Step 2: ImportNewAndPublish
        resource_client = fm.get_client("Resource")

        # Create LightResourceInfo
        resource_info_type = resource_client.get_type(
            f'{{{RESOURCE_NS}}}LightResourceInfo'
        )
        resource_info = resource_info_type(
            Name=self.resource_name,
            Description=f"Test filter imported by Claude at {self.timestamp}",
            Readonly=False,
        )

        new_guid = resource_client.service.ImportNewAndPublish(
            resourceType='FilterConfigs',
            fileGuid=file_guid,
            resourceInfo=resource_info,
        )
        assert new_guid is not None, "ImportNewAndPublish returned None"
        self.created_guid = str(new_guid)
        print(f"  Step 2 OK: Filter created, GUID = {self.created_guid}")

        # Step 3: ListResources to verify
        filter_type = resource_client.get_type(
            f'{{{RESOURCE_NS}}}LightResourceListFilter'
        )
        list_filter = filter_type(NameOrDescription=self.resource_name)
        resources = resource_client.service.ListResources('FilterConfigs', list_filter)
        resources_data = serialize_object(resources)

        assert resources_data is not None, "ListResources returned None"
        assert len(resources_data) >= 1, f"Expected at least 1 result, got {len(resources_data)}"

        found = any(
            r.get("Name") == self.resource_name or r.get("FriendlyName") == self.resource_name
            for r in resources_data
        )
        assert found, f"Filter '{self.resource_name}' not found in ListResources results"
        print(f"  Step 3 OK: Filter verified in ListResources ({len(resources_data)} results)")
        print(f"\n  SUCCESS: Filter '{self.resource_name}' created with GUID {self.created_guid}")
