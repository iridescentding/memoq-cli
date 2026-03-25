#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Explore CreateProjectFromTemplate operation
"""

from zeep import Client
from zeep.transports import Transport
from requests import Session
from memoq_cli.wsapi.client import APIKeyPlugin


def main():
    """Main function"""

    wsdl_url = f"{SERVER_URL}/memoqservices/serverproject?wsdl"

    print(f"\n{'='*80}")
    print(f"Exploring CreateProjectFromTemplate Operation")
    print(f"{'='*80}\n")

    session = Session()
    session.verify = False
    session.trust_env = False

    transport = Transport(session=session, timeout=30)
    plugins = [APIKeyPlugin(API_KEY)]

    try:
        client = Client(wsdl_url, transport=transport, plugins=plugins)

        # Get the operation
        operation = client.service._binding._operations['CreateProjectFromTemplate']

        print("Operation: CreateProjectFromTemplate")
        print(f"\nInput: {operation.input.body.type}")
        print(f"Output: {operation.output.body.type}")

        # Get the input type details
        input_type = operation.input.body.type
        print(f"\nInput parameters:")
        for element in input_type.elements:
            name, el_type = element
            print(f"  - {name}: {el_type.type if hasattr(el_type, 'type') else el_type}")

        # Check if there's a method to list templates
        print(f"\n\nSearching for 'List' operations with 'Template' in name...")
        for op_name in sorted(client.service._binding._operations.keys()):
            if 'list' in op_name.lower() and 'template' in op_name.lower():
                print(f"  ⭐ Found: {op_name}")

        print(f"\n\nSearching for 'Get' operations with 'Template' in name...")
        for op_name in sorted(client.service._binding._operations.keys()):
            if 'get' in op_name.lower() and 'template' in op_name.lower():
                print(f"  ⭐ Found: {op_name}")

    except Exception as e:
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    import urllib3
    urllib3.disable_warnings()
    main()
