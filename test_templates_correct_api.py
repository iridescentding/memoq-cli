#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Test Project Templates using correct Light Resource Service API
Based on official memoQ documentation:
https://docs.memoq.com/current/api-docs/wsapi/api/lightresourceservice/
"""

from zeep import Client
from zeep.transports import Transport
from zeep.helpers import serialize_object
from requests import Session
from memoq_cli.wsapi.client import APIKeyPlugin
import json


def main():
    wsdl_url = f"{SERVER_URL}/memoqservices/resource?wsdl"

    print(f"\n{'='*100}")
    print(f"Testing Light Resource Service API - Project Templates")
    print(f"Using official memoQ API: ListResources(ResourceType, LightResourceListFilter)")
    print(f"{'='*100}\n")

    session = Session()
    session.verify = False
    session.trust_env = False

    transport = Transport(session=session, timeout=30)
    plugins = [APIKeyPlugin(API_KEY)]

    try:
        client = Client(wsdl_url, transport=transport, plugins=plugins)

        # Step 1: Discover available ResourceType enum values
        print("Step 1: Discovering ResourceType enum values...\n")

        # Get the ResourceType type from the WSDL
        resource_type_enum = None
        for type_obj in client.wsdl.types.types:
            type_name = str(type_obj)
            if 'ResourceType' in type_name:
                resource_type_enum = type_obj
                print(f"Found ResourceType: {type_obj}")
                break

        # Try to call ListResources to see all resources first
        print("\n\nStep 2: Calling ListResources() to see all available resources...")
        print("(This might show what types are available on the server)\n")

        # Try without parameters first to see what happens
        try:
            all_resources = client.service.ListResources()
            print(f"✅ ListResources() returned {len(all_resources) if all_resources else 0} resources")

            if all_resources and len(all_resources) > 0:
                # Group by Type
                types_found = {}
                for res in all_resources:
                    res_type = res.Type if hasattr(res, 'Type') else 'Unknown'
                    if res_type not in types_found:
                        types_found[res_type] = []
                    types_found[res_type].append(res)

                print(f"\nResource types found on server:")
                for res_type, items in sorted(types_found.items()):
                    print(f"  - {res_type}: {len(items)} items")

        except TypeError as e:
            print(f"ListResources() requires parameters: {e}")

        # Step 3: Try to get ResourceType factory to create enum values
        print("\n\nStep 3: Attempting to list ProjectTemplate resources...\n")

        # Try different approaches to specify ResourceType
        approaches = [
            ("String 'ProjectTemplate'", 'ProjectTemplate'),
            ("Try without resourceType param", None),
        ]

        for approach_name, resource_type_value in approaches:
            try:
                print(f"Trying: {approach_name}")

                if resource_type_value is None:
                    # Call with just filter parameter
                    templates = client.service.ListResources(None)
                else:
                    # Call with resource type
                    templates = client.service.ListResources(resource_type_value, None)

                templates_data = serialize_object(templates)

                if templates_data:
                    print(f"  ✅ SUCCESS! Found {len(templates_data)} items")

                    # Filter for templates
                    project_templates = [t for t in templates_data
                                       if 'template' in str(t.get('Type', '')).lower() or
                                          'template' in str(t.get('FriendlyName', '')).lower()]

                    if project_templates:
                        print(f"  ✅ Found {len(project_templates)} project templates!\n")
                        print(f"  {'Name':<60} {'GUID':<36}")
                        print(f"  {'-'*96}")
                        for i, template in enumerate(project_templates[:20], 1):
                            name = template.get('FriendlyName', 'N/A')
                            if len(name) > 58:
                                name = name[:55] + "..."
                            guid = template.get('Guid', 'N/A')
                            print(f"  {name:<60} {guid:<36}")

                        if len(project_templates) > 20:
                            print(f"\n  ... and {len(project_templates) - 20} more templates")

                        return  # Success, exit
                    else:
                        print(f"  ⚠️  No templates found in {len(templates_data)} resources")
                else:
                    print(f"  ❌ Returned 0 items")

            except Exception as e:
                error_msg = str(e)[:150]
                print(f"  ❌ Failed: {error_msg}")

            print()

        print(f"\n{'='*100}")
        print("Unable to retrieve project templates")
        print(f"{'='*100}")
        print("\nPossible reasons:")
        print("1. Server might not have ProjectTemplate enum value available")
        print("2. Templates might require different authentication (user login vs API key)")
        print("3. Templates might only be accessible via UI Resource Console")
        print("4. Server version might not support template API access")

    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    import urllib3
    urllib3.disable_warnings()
    main()
