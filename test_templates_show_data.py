#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Show the actual data returned for ProjectTemplate resources
"""

from zeep import Client
from zeep.transports import Transport
from zeep.helpers import serialize_object
from requests import Session
from memoq_cli.wsapi.client import APIKeyPlugin
import json


def main():
    """Test and show ProjectTemplate data"""
    SERVER_URL = "https://memoq.datalsp.com:8081"
    API_KEY = "lNWFkQ2VJm2AlfDCpEuUdduVMLO5GsGrzx8VBchJ"

    wsdl_url = f"{SERVER_URL}/memoqservices/resource?wsdl"

    print(f"\n{'='*100}")
    print(f"Retrieving Project Templates from memoQ Server")
    print(f"{'='*100}\n")

    session = Session()
    session.verify = False
    session.trust_env = False

    transport = Transport(session=session, timeout=30)
    plugins = [APIKeyPlugin(API_KEY)]

    try:
        client = Client(wsdl_url, transport=transport, plugins=plugins)

        print("Calling: ListResources('ProjectTemplate', None)\n")

        # Call with 'ProjectTemplate' string
        templates = client.service.ListResources('ProjectTemplate', None)
        templates_data = serialize_object(templates)

        print(f"✅ Found {len(templates_data)} project templates!\n")

        # Show structure of first item
        if templates_data and len(templates_data) > 0:
            print("First item structure:")
            print(json.dumps(templates_data[0], indent=2, default=str))
            print("\n" + "="*100 + "\n")

        # Display all templates
        print(f"{'#':<4} {'Name':<60} {'GUID':<36}")
        print("="*100)

        for i, template in enumerate(templates_data, 1):
            name = template.get('FriendlyName', 'N/A')
            if len(name) > 58:
                name = name[:55] + "..."

            guid = template.get('Guid', 'N/A')

            print(f"{i:<4} {name:<60} {guid:<36}")

        print("="*100)

        # Test GetResourceInfo with first template
        if templates_data:
            print(f"\n\nTesting GetResourceInfo for first template...")
            first_guid = templates_data[0].get('Guid')
            print(f"GUID: {first_guid}\n")

            # Call GetResourceInfo(ResourceType, Guid)
            template_info = client.service.GetResourceInfo('ProjectTemplate', first_guid)
            info_data = serialize_object(template_info)

            print("Detailed template information:")
            print(json.dumps(info_data, indent=2, default=str))

        print(f"\n\n{'='*100}")
        print("✅ Successfully retrieved project templates!")
        print(f"{'='*100}\n")

    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    import urllib3
    urllib3.disable_warnings()
    main()
