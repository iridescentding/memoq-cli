#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Test Light Resource Service API for Project Templates
Based on memoQ API documentation
"""

from zeep import Client
from zeep.transports import Transport
from zeep.helpers import serialize_object
from requests import Session
from memoq_cli.wsapi.client import APIKeyPlugin
import json


def main():

    wsdl_url = f"{SERVER_URL}/memoqservices/resource?wsdl"

    print(f"\n{'='*80}")
    print(f"Testing Light Resource Service API - Project Templates")
    print(f"Server: {SERVER_URL}")
    print(f"{'='*80}\n")

    session = Session()
    session.verify = False
    session.trust_env = False

    transport = Transport(session=session, timeout=30)
    plugins = [APIKeyPlugin(API_KEY)]

    try:
        client = Client(wsdl_url, transport=transport, plugins=plugins)

        # According to documentation:
        # ResourceType.ProjectTemplate = 16
        # Method: ListResources(ResourceType resourceType, LightResourceListFilter filter)

        print("1. Calling ListResources with ResourceType.ProjectTemplate (16)...")

        # Create filter (optional, can be None)
        # Filter has: LanguageCode, NameOrDescription
        filter_obj = None  # Try without filter first

        # Call ListResources with ProjectTemplate type (value = 16)
        resources = client.service.ListResources(16, filter_obj)

        # Convert to Python dict
        resources_data = serialize_object(resources)

        if not resources_data:
            print("❌ No project templates found")
            return

        print(f"✅ Found {len(resources_data)} project templates!\n")

        # Display templates
        print(f"{'='*120}")
        print(f"{'#':<4} {'Name':<50} {'GUID':<38} {'Type':<15}")
        print(f"{'='*120}")

        for i, template in enumerate(resources_data[:20], 1):  # Show first 20
            name = template.get('FriendlyName', 'N/A')
            if len(name) > 48:
                name = name[:45] + "..."

            guid = template.get('Guid', 'N/A')
            res_type = template.get('Type', 'N/A')

            print(f"{i:<4} {name:<50} {guid:<38} {res_type:<15}")

        if len(resources_data) > 20:
            print(f"\n... and {len(resources_data) - 20} more templates")

        print(f"{'='*120}\n")

        # Test GetResourceInfo with first template
        if resources_data:
            first_guid = resources_data[0].get('Guid')
            print(f"\n2. Testing GetResourceInfo for first template...")
            print(f"   GUID: {first_guid}\n")

            resource_info = client.service.GetResourceInfo(first_guid)
            info_data = serialize_object(resource_info)

            print(f"Template Details:")
            print(f"  Name: {info_data.get('FriendlyName', 'N/A')}")
            print(f"  GUID: {info_data.get('Guid', 'N/A')}")
            print(f"  Type: {info_data.get('Type', 'N/A')}")
            print(f"  Description: {info_data.get('Description', 'N/A')[:100]}")

        # Test with filter
        print(f"\n\n3. Testing with filter (name contains 'Game')...")

        # Create filter object
        filter_type = client.get_type('ns0:LightResourceListFilter')
        filter_with_name = filter_type(NameOrDescription='Game')

        filtered_resources = client.service.ListResources(16, filter_with_name)
        filtered_data = serialize_object(filtered_resources)

        if filtered_data:
            print(f"✅ Found {len(filtered_data)} templates matching 'Game':\n")
            for template in filtered_data[:10]:
                print(f"  - {template.get('FriendlyName', 'N/A')}")
        else:
            print("No templates found matching filter")

        print(f"\n{'='*80}")
        print("✅ Light Resource API test completed successfully!")
        print(f"{'='*80}\n")

    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    import urllib3
    urllib3.disable_warnings()
    main()
