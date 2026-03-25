#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Test the actual server to see project templates
Using the working WSAPI Resource service approach
"""

from memoq_cli.wsapi.project_template import ProjectTemplateManager


def main():
    """Test with real server"""

    print("\n" + "="*100)
    print("Testing Project Templates on Real Server")
    print("Server: https://memoq.datalsp.com:8081")
    print("="*100)

    manager = ProjectTemplateManager(
        host=SERVER_URL,
        port=PORT,
        api_key=API_KEY,
        verify_ssl=False
    )

    try:
        print("\nCalling Resource.ListResources()...")

        # Get the Resource service client
        client = manager.get_client("Resource")

        # Call ListResources to get ALL resources
        all_resources = client.service.ListResources()

        print(f"Total resources returned: {len(all_resources) if all_resources else 0}")

        if not all_resources:
            print("\n❌ No resources found at all!")
            return

        # Group by Type
        by_type = {}
        for resource in all_resources:
            res_type = resource['Type'] if isinstance(resource, dict) else getattr(resource, 'Type', 'Unknown')
            if res_type not in by_type:
                by_type[res_type] = []
            by_type[res_type].append(resource)

        print(f"\nResource types found:")
        for res_type, items in sorted(by_type.items()):
            marker = " ⭐" if 'template' in str(res_type).lower() or 'project' in str(res_type).lower() else ""
            print(f"  {res_type}: {len(items)} items{marker}")

        # Show project templates
        template_types = [k for k in by_type.keys() if 'template' in str(k).lower()]

        if template_types:
            for template_type in template_types:
                templates = by_type[template_type]
                print(f"\n\n{'='*100}")
                print(f"Templates of type '{template_type}': {len(templates)}")
                print(f"{'='*100}\n")

                print(f"{'#':<4} {'Name':<60} {'GUID':<36}")
                print("-"*100)

                for i, template in enumerate(templates[:30], 1):
                    if isinstance(template, dict):
                        name = template.get('FriendlyName', 'N/A')
                        guid = template.get('Guid', 'N/A')
                    else:
                        name = getattr(template, 'FriendlyName', 'N/A')
                        guid = getattr(template, 'Guid', 'N/A')

                    if len(name) > 58:
                        name = name[:55] + "..."

                    print(f"{i:<4} {name:<60} {guid:<36}")

                if len(templates) > 30:
                    print(f"\n... and {len(templates) - 30} more")
        else:
            print("\n⚠️ No template types found in resources")
            print("\nAll available types:")
            for res_type in sorted(by_type.keys()):
                print(f"  - {res_type}")

        print(f"\n{'='*100}\n")

    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()

    finally:
        manager.close()


if __name__ == "__main__":
    import urllib3
    urllib3.disable_warnings()
    main()
