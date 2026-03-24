#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Test different service endpoints to find Light Resource Service
"""

from zeep import Client
from zeep.transports import Transport
from requests import Session
from memoq_cli.wsapi.client import APIKeyPlugin


def test_endpoint(wsdl_url, api_key):
    """Test a WSDL endpoint"""
    print(f"\nTesting: {wsdl_url}")
    print("-" * 80)

    session = Session()
    session.verify = False
    session.trust_env = False

    transport = Transport(session=session, timeout=30)
    plugins = [APIKeyPlugin(api_key)]

    try:
        client = Client(wsdl_url, transport=transport, plugins=plugins)

        print("✅ WSDL loaded successfully!")

        # List operations
        print("\nAvailable operations:")
        for service in client.wsdl.services.values():
            for port in service.ports.values():
                operations = sorted(port.binding._operations.keys())
                for op in operations[:10]:  # Show first 10
                    print(f"  - {op}")
                if len(operations) > 10:
                    print(f"  ... and {len(operations) - 10} more")

        return client

    except Exception as e:
        print(f"❌ Failed: {str(e)[:100]}")
        return None


def main():
    """Test different service endpoints"""
    SERVER_URL = "https://memoq.datalsp.com:8081"
    API_KEY = "lNWFkQ2VJm2AlfDCpEuUdduVMLO5GsGrzx8VBchJ"

    print("\n" + "="*80)
    print("Searching for Light Resource Service Endpoint")
    print("="*80)

    # Try different possible endpoints
    endpoints_to_try = [
        f"{SERVER_URL}/memoqservices/resource?wsdl",  # Standard Resource service
        f"{SERVER_URL}/memoqservices/lightresource?wsdl",  # Light Resource service
        f"{SERVER_URL}/memoqservices/lightresources?wsdl",  # Plural
        f"{SERVER_URL}/memoqlightresourceservice?wsdl",  # Different format
        f"{SERVER_URL}/memoqservices/LightResourceService?wsdl",  # Capitalized
    ]

    working_clients = {}

    for endpoint in endpoints_to_try:
        client = test_endpoint(endpoint, API_KEY)
        if client:
            working_clients[endpoint] = client

    if not working_clients:
        print("\n\n❌ No working endpoints found!")
        return

    print(f"\n\n{'='*80}")
    print(f"Found {len(working_clients)} working endpoint(s)")
    print("="*80)

    # Try calling ListResources on each working endpoint
    for endpoint, client in working_clients.items():
        print(f"\n\nTesting endpoint: {endpoint}")
        print("-" * 80)

        try:
            # Try ListResources with no parameters
            print("Calling ListResources()...")
            result = client.service.ListResources()
            print(f"✅ Success! Returned {len(result) if result else 0} items")

            if result and len(result) > 0:
                print(f"\nFirst item type: {type(result[0])}")
                if hasattr(result[0], 'Type'):
                    print(f"First item resource Type: {result[0].Type}")
                if hasattr(result[0], 'FriendlyName'):
                    print(f"First item name: {result[0].FriendlyName}")

        except TypeError as e:
            # Method requires parameters
            print(f"⚠️  Method requires parameters: {str(e)[:100]}")

            # Try to get the method signature
            try:
                operation = None
                for service in client.wsdl.services.values():
                    for port in service.ports.values():
                        if 'ListResources' in port.binding._operations:
                            operation = port.binding._operations['ListResources']
                            break

                if operation:
                    print(f"\nMethod signature:")
                    print(f"  Input: {operation.input}")

            except:
                pass

        except Exception as e:
            print(f"❌ Error calling ListResources: {str(e)[:150]}")


if __name__ == "__main__":
    import urllib3
    urllib3.disable_warnings()
    main()
