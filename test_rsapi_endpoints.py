#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Test different RSAPI endpoints to find project templates
"""

from memoq_cli.rsapi.client import RSAPIClient


def test_endpoint(client, endpoint):
    """Test an endpoint and print results"""
    try:
        print(f"Testing: {endpoint}")
        result = client.get(endpoint)
        print(f"  ✅ Success! Found {len(result) if isinstance(result, list) else 'data'}")
        if isinstance(result, list) and len(result) > 0:
            print(f"  First item keys: {list(result[0].keys())[:5]}")
        return True
    except Exception as e:
        print(f"  ❌ Failed: {str(e)[:80]}")
        return False


def main():
    """Main function"""
    SERVER_URL = "https://memoq.datalsp.com"
    PORT = 8082
    USERNAME = "wsapi"
    PASSWORD = "Datalsp2026@"

    print("\n" + "="*80)
    print("Testing RSAPI Endpoints for Project Templates")
    print("="*80 + "\n")

    client = RSAPIClient(
        host=SERVER_URL,
        port=PORT,
        verify_ssl=False
    )

    # Authenticate
    print("Authenticating...")
    client.authenticate_with_password(USERNAME, PASSWORD)
    print("✅ Authenticated\n")

    # Test various endpoints
    endpoints_to_test = [
        "projecttemplates",
        "project-templates",
        "templates",
        "resources/projecttemplates",
        "resources/templates",
        "resources",  # List all resources
        "serverprojecttemplates",
        "server-project-templates",
    ]

    successful = []
    for endpoint in endpoints_to_test:
        if test_endpoint(client, endpoint):
            successful.append(endpoint)
        print()

    if successful:
        print(f"\n{'='*80}")
        print(f"Successful endpoints:")
        for ep in successful:
            print(f"  - {ep}")
        print(f"{'='*80}\n")
    else:
        print(f"\n{'='*80}")
        print("No successful endpoints found")
        print("Project templates might not be available via Light Resources API")
        print("They may only be accessible via WSAPI")
        print(f"{'='*80}\n")

    client.close()


if __name__ == "__main__":
    import urllib3
    urllib3.disable_warnings()
    main()
