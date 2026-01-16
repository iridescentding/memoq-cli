# -*- coding: utf-8 -*-
"""
memoQ CLI - WSAPI Client Base Class
"""

from typing import Optional, Dict, Any
from zeep import Client
from zeep.transports import Transport
from requests import Session

from ..config import get_config
from ..utils import get_logger


# memoQ WSAPI service endpoints
WSAPI_SERVICES = {
    "ServerProject": "serverproject?wsdl",
    "FileManager": "filemanager?wsdl",
    "Security": "security?wsdl",
    "Resource": "resource?wsdl",
    "TM": "tm?wsdl",
    "TB": "tb?wsdl",
}


class WSAPIClient:
    """
    memoQ WSAPI (SOAP) Client Base Class

    Provides connection management and authentication for memoQ SOAP services.
    """

    def __init__(
        self,
        host: Optional[str] = None,
        port: Optional[int] = None,
        api_key: Optional[str] = None,
        verify_ssl: bool = False,
        timeout: int = 30
    ):
        """
        Initialize WSAPI client.

        Args:
            host: Server host (e.g., https://memoq.example.com)
            port: WSAPI port (default 8080)
            api_key: API Key for authentication
            verify_ssl: Whether to verify SSL certificates
            timeout: Request timeout in seconds
        """
        self.config = get_config()
        self.logger = get_logger("wsapi")

        self._host = host or self.config.server_host
        self._port = port or self.config.wsapi_port
        self._api_key = api_key or self.config.api_key
        self._verify_ssl = verify_ssl
        self._timeout = timeout

        # Client cache
        self._clients: Dict[str, Client] = {}

        # Session for HTTP requests
        self._session = Session()
        self._session.verify = verify_ssl

    @property
    def base_url(self) -> str:
        """Get WSAPI base URL"""
        host = self._host.rstrip("/")
        return f"{host}:{self._port}/memoqservices"

    def get_client(self, service_name: str) -> Client:
        """
        Get or create a Zeep SOAP client for the specified service.

        Args:
            service_name: Service name (e.g., "ServerProject", "FileManager")

        Returns:
            Zeep Client instance

        Raises:
            ValueError: If service name is not recognized
        """
        if service_name in self._clients:
            return self._clients[service_name]

        if service_name not in WSAPI_SERVICES:
            raise ValueError(
                f"Unknown service: {service_name}. "
                f"Available: {list(WSAPI_SERVICES.keys())}"
            )

        wsdl_path = WSAPI_SERVICES[service_name]
        wsdl_url = f"{self.base_url}/{wsdl_path}"

        self.logger.debug(f"Creating SOAP client for {service_name}: {wsdl_url}")

        transport = Transport(
            session=self._session,
            timeout=self._timeout,
            operation_timeout=self._timeout
        )

        client = Client(wsdl_url, transport=transport)
        self._clients[service_name] = client

        return client

    def _get_auth_header(self) -> Any:
        """
        Create authentication SOAP header.

        Returns:
            SOAP header element with API key
        """
        # Get client to access types (use any service)
        if "ServerProject" not in self._clients:
            self.get_client("ServerProject")

        client = self._clients.get("ServerProject") or list(self._clients.values())[0]

        # Create authentication header type
        try:
            header_type = client.get_type("ns0:ApiKeyAuth")
            return header_type(ApiKey=self._api_key)
        except Exception:
            # Fallback: try alternative header structure
            header_type = client.get_type("{http://kilgray.com/memoqservices/2007}ApiKeyAuth")
            return header_type(ApiKey=self._api_key)

    def close(self):
        """Close the session and clean up resources"""
        self._session.close()
        self._clients.clear()

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.close()
