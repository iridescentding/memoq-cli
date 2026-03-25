#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Test if Light Resources are accessible via RSAPI (HTTP/REST)
"""

from memoq_cli.rsapi.client import RSAPIClient


def test_endpoint(client, endpoint):
    """Test an endpoint"""
    try:
        print(f"Testing: GET {endpoint}")
        result = client.get(endpoint)
        print(f"  ✅ Success! Type: {type(result)}")
        if isinstance(result, list):
            print(f"  Found {len(result)} items")
            if len(result) > 0:
                print(f"  First item keys: {list(result[0].keys())[:10]}")
        return result
    except Exception as e:
        error_str = str(e)[:100]
        print(f"  ❌ Failed: {error_str}")
        return None


def main():
    print("\n" + "="*80)
    print("Testing RSAPI for Light Resources / Project Templates")
    print("="*80 + "\n")

    client = RSAPIClient(
        host=SERVER_URL,
        port=PORT,
        verify_ssl=False
    )

    try:
        # Authenticate
        print("1. Authenticating with username/password...")
        client.authenticate_with_password(USERNAME, PASSWORD)
        print("   ✅ Authenticated\n")

        # Try different endpoints that might exist
        print("2. Testing various endpoints:\n")

        endpoints = [
            "resources",
            "lightresources",
            "light-resources",
            "resources/projecttemplates",
            "resources/project-templates",
            "projecttemplates",
            "project-templates",
            "templates/project",
            "server-project-templates",
        ]

        successful = []
        for endpoint in endpoints:
            result = test_endpoint(client, endpoint)
            if result is not None:
                successful.append((endpoint, result))
            print()

        if successful:
            print(f"\n{'='*80}")
            print(f"✅ Found {len(successful)} working endpoint(s)!")
            print("="*80 + "\n")

            for endpoint, result in successful:
                print(f"\nEndpoint: {endpoint}")
                print("-" * 80)
                if isinstance(result, list) and len(result) > 0:
                    print(f"Sample items:")
                    for i, item in enumerate(result[:3], 1):
                        name = item.get('Name') or item.get('FriendlyName') or item.get('name', 'N/A')
                        guid = item.get('Guid') or item.get('guid') or item.get('id', 'N/A')
                        print(f"  {i}. {name} ({guid})")
        else:
            print(f"\n{'='*80}")
            print("❌ No working REST/RSAPI endpoints found for templates")
            print("="*80)
            print("\nTemplates might only be accessible via:")
            print("  1. memoQ UI Resource Console")
            print("  2. A specific WSAPI service we haven't found yet")
            print("  3. Might require admin/special permissions")

    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()

    finally:
        client.close()


if __name__ == "__main__":
    import urllib3
    urllib3.disable_warnings()
    main()
