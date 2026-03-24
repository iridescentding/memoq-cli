#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Discover what ResourceType enum values are available on the server
"""

from zeep import Client
from zeep.transports import Transport
from requests import Session
from memoq_cli.wsapi.client import APIKeyPlugin


def main():
    """Discover ResourceType enum values"""
    SERVER_URL = "https://memoq.datalsp.com:8081"
    API_KEY = "lNWFkQ2VJm2AlfDCpEuUdduVMLO5GsGrzx8VBchJ"

    wsdl_url = f"{SERVER_URL}/memoqservices/resource?wsdl"

    print(f"\n{'='*80}")
    print(f"Discovering ResourceType Enum Values")
    print(f"{'='*80}\n")

    session = Session()
    session.verify = False
    session.trust_env = False

    transport = Transport(session=session, timeout=30)
    plugins = [APIKeyPlugin(API_KEY)]

    try:
        client = Client(wsdl_url, transport=transport, plugins=plugins)

        # Get the ResourceType enum
        resource_type = client.get_type('ns0:ResourceType')

        print("Available ResourceType enum values:\n")
        print(f"{'Value':<20} {'Name':<30}")
        print("="*50)

        # Get all enum members
        if hasattr(resource_type, '__members__'):
            for name, value in resource_type.__members__.items():
                print(f"{value:<20} {name:<30}")
                if 'template' in name.lower() or 'project' in name.lower():
                    print(f"  ⭐ ^ This one looks relevant!")

    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    import urllib3
    urllib3.disable_warnings()
    main()
