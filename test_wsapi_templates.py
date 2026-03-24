#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Test WSAPI Project Template functionality with real server
"""

from memoq_cli.wsapi.project_template import ProjectTemplateManager


def main():
    """Test project template functionality"""

    # Configuration
    SERVER_URL = "https://memoq.datalsp.com"
    PORT = 8081
    API_KEY = "lNWFkQ2VJm2AlfDCpEuUdduVMLO5GsGrzx8VBchJ"

    print("\n" + "="*80)
    print("memoQ WSAPI Project Template Test")
    print("="*80)

    # Create manager
    manager = ProjectTemplateManager(
        host=SERVER_URL,
        port=PORT,
        api_key=API_KEY,
        verify_ssl=False
    )

    try:
        # Test list_templates
        print("\n1. Testing list_templates()...")
        templates = manager.list_templates()
        print(f"✅ Found {len(templates)} project templates")

        # Display template list
        if templates:
            print("\n2. Displaying template list...")
            manager.print_template_list(templates)

            # Test get_template with first template
            print("\n3. Testing get_template() with first template...")
            first_template_guid = templates[0].get("Guid")
            print(f"   Fetching template: {first_template_guid}")

            template_details = manager.get_template(first_template_guid)
            print("✅ Successfully retrieved template details")

            # Display detailed info
            print("\n4. Displaying template details...")
            manager.print_template_details(template_details)
        else:
            print("\n⚠️  No templates available on this server")

        print("\n" + "="*80)
        print("✅ All tests passed successfully!")
        print("="*80 + "\n")

    except Exception as e:
        print(f"\n❌ Error occurred: {e}")
        import traceback
        traceback.print_exc()
        print("\n" + "="*80)
        print("❌ Tests failed")
        print("="*80 + "\n")

    finally:
        manager.close()


if __name__ == "__main__":
    import urllib3
    urllib3.disable_warnings()
    main()
