#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Test script for Project Template functionality
Tests against real memoQ server
"""

from memoq_cli.rsapi.project_template import ProjectTemplateClient


def main():
    """Test project template functionality"""

    print("\n" + "="*80)
    print("memoQ Project Template Test")
    print("="*80)

    # Create client
    client = ProjectTemplateClient(
        host=SERVER_URL,
        port=PORT,
        verify_ssl=False
    )

    try:
        # Test authentication with username/password
        print("\n1. Testing authentication with username/password...")
        client.authenticate_with_password(USERNAME, PASSWORD)
        print("✅ Authentication successful")

        # Test list_templates
        print("\n2. Testing list_templates()...")
        templates = client.list_templates()
        print(f"✅ Found {len(templates)} project templates")

        # Display template list
        print("\n3. Displaying template list...")
        client.print_template_list(templates)

        # Test get_template with first template (if available)
        if templates:
            print("\n4. Testing get_template() with first template...")
            first_template_guid = templates[0].get("Guid")
            print(f"   Fetching template: {first_template_guid}")

            template_details = client.get_template(first_template_guid)
            print("✅ Successfully retrieved template details")

            # Display detailed info
            print("\n5. Displaying template details...")
            client.print_template_details(template_details)
        else:
            print("\n⚠️  No templates available to test get_template()")

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
        client.close()


if __name__ == "__main__":
    main()
