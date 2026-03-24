#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Explore memoQ WSAPI to find project template operations
"""

from zeep import Client
from zeep.transports import Transport
from requests import Session
from memoq_cli.wsapi.client import APIKeyPlugin


def explore_service(service_name, wsdl_url, api_key):
    """Explore a WSAPI service"""
    print(f"\n{'='*80}")
    print(f"Exploring {service_name} Service")
    print(f"WSDL: {wsdl_url}")
    print(f"{'='*80}\n")

    session = Session()
    session.verify = False
    session.trust_env = False

    transport = Transport(session=session, timeout=30)
    plugins = [APIKeyPlugin(api_key)]

    try:
        client = Client(wsdl_url, transport=transport, plugins=plugins)

        print("Available operations:")
        for service in client.wsdl.services.values():
            for port in service.ports.values():
                operations = sorted(port.binding._operations.keys())
                for op in operations:
                    if 'template' in op.lower() or 'project' in op.lower():
                        print(f"  ⭐ {op}  (contains 'template' or 'project')")
                    else:
                        print(f"  - {op}")

    except Exception as e:
        print(f"Error exploring {service_name}: {e}")


def main():
    """Main function"""
    SERVER_URL = "https://memoq.datalsp.com:8081"
    API_KEY = "lNWFkQ2VJm2AlfDCpEuUdduVMLO5GsGrzx8VBchJ"

    services = {
        "ServerProject": f"{SERVER_URL}/memoqservices/serverproject?wsdl",
        "Resource": f"{SERVER_URL}/memoqservices/resource?wsdl",
        "Security": f"{SERVER_URL}/memoqservices/security?wsdl",
    }

    for name, url in services.items():
        explore_service(name, url, API_KEY)


if __name__ == "__main__":
    import urllib3
    urllib3.disable_warnings()
    main()
