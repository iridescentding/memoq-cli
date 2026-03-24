#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
List all types available in the Resource service WSDL
"""

from zeep import Client
from zeep.transports import Transport
from requests import Session
from memoq_cli.wsapi.client import APIKeyPlugin


def main():
    """List all available types"""
    SERVER_URL = "https://memoq.datalsp.com:8081"
    API_KEY = "lNWFkQ2VJm2AlfDCpEuUdduVMLO5GsGrzx8VBchJ"

    wsdl_url = f"{SERVER_URL}/memoqservices/resource?wsdl"

    print(f"\n{'='*80}")
    print(f"Listing All Types in Resource Service WSDL")
    print(f"{'='*80}\n")

    session = Session()
    session.verify = False
    session.trust_env = False

    transport = Transport(session=session, timeout=30)
    plugins = [APIKeyPlugin(API_KEY)]

    try:
        client = Client(wsdl_url, transport=transport, plugins=plugins)

        print("Available types:\n")

        # List all types
        for schema in client.wsdl.types.schemas:
            print(f"\nNamespace: {schema._target_namespace}")
            print("-" * 80)

            # List types in this schema
            if hasattr(schema, '_types'):
                for qname in schema._types.keys():
                    type_name = qname.localname if hasattr(qname, 'localname') else str(qname)
                    if 'resource' in type_name.lower() or 'template' in type_name.lower():
                        print(f"  ⭐ {type_name}")
                    else:
                        print(f"     {type_name}")

        # Also list service operations
        print(f"\n\n{'='*80}")
        print("Available Service Operations:")
        print("="*80)
        for service in client.wsdl.services.values():
            for port in service.ports.values():
                operations = sorted(port.binding._operations.keys())
                for op in operations:
                    print(f"  - {op}")

    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    import urllib3
    urllib3.disable_warnings()
    main()
