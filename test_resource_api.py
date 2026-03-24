#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Test Resource API to find project templates
"""

from zeep import Client
from zeep.transports import Transport
from zeep.helpers import serialize_object
from requests import Session
from memoq_cli.wsapi.client import APIKeyPlugin
import json


def main():
    """Main function"""
    SERVER_URL = "https://memoq.datalsp.com:8081"
    API_KEY = "lNWFkQ2VJm2AlfDCpEuUdduVMLO5GsGrzx8VBchJ"

    wsdl_url = f"{SERVER_URL}/memoqservices/resource?wsdl"

    print(f"\n{'='*80}")
    print(f"Testing Resource API")
    print(f"{'='*80}\n")

    session = Session()
    session.verify = False
    session.trust_env = False

    transport = Transport(session=session, timeout=30)
    plugins = [APIKeyPlugin(API_KEY)]

    try:
        client = Client(wsdl_url, transport=transport, plugins=plugins)

        # List all resources
        print("Calling ListResources()...")
        resources = client.service.ListResources()

        # Convert to Python dict for easier inspection
        resources_data = serialize_object(resources)

        print(f"\nFound {len(resources_data) if resources_data else 0} resources")

        # Group by resource type
        by_type = {}
        if resources_data:
            for resource in resources_data:
                res_type = resource.get('Type', 'Unknown')
                if res_type not in by_type:
                    by_type[res_type] = []
                by_type[res_type].append(resource)

        print(f"\nResource types found:")
        for res_type, items in sorted(by_type.items()):
            print(f"  - {res_type}: {len(items)} items")

        # Show project templates if found
        if 'ServerProjectTemplate' in by_type or 'ProjectTemplate' in by_type:
            template_key = 'ServerProjectTemplate' if 'ServerProjectTemplate' in by_type else 'ProjectTemplate'
            print(f"\n{'='*80}")
            print(f"Project Templates ({len(by_type[template_key])} found):")
            print(f"{'='*80}\n")

            for i, template in enumerate(by_type[template_key][:5], 1):  # Show first 5
                print(f"{i}. {template.get('FriendlyName', 'N/A')}")
                print(f"   GUID: {template.get('Guid', 'N/A')}")
                print(f"   Source: {template.get('SourceLangCode', 'N/A')}")
                print(f"   Targets: {template.get('TargetLangCodes', 'N/A')}")
                print()

        # Try GetResourceInfo for first template
        if 'ServerProjectTemplate' in by_type and by_type['ServerProjectTemplate']:
            first_template_guid = by_type['ServerProjectTemplate'][0].get('Guid')
            print(f"\n{'='*80}")
            print(f"Getting detailed info for first template...")
            print(f"{'='*80}\n")

            detail = client.service.GetResourceInfo(first_template_guid)
            detail_data = serialize_object(detail)
            print(json.dumps(detail_data, indent=2, default=str))

    except Exception as e:
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    import urllib3
    urllib3.disable_warnings()
    main()
