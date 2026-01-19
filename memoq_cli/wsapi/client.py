# -*- coding: utf-8 -*-
"""
memoQ CLI - WSAPI Client Base Class
"""

from typing import Optional, Dict, Any
from zeep import Client
from zeep.transports import Transport
from zeep.plugins import HistoryPlugin
from requests import Session
from lxml import etree
from lxml.etree import QName

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

# Global flag for SOAP debug logging
_soap_debug_enabled = False


def set_soap_debug(enabled: bool):
    """Enable or disable SOAP debug logging globally."""
    global _soap_debug_enabled
    _soap_debug_enabled = enabled


def is_soap_debug_enabled() -> bool:
    """Check if SOAP debug logging is enabled."""
    return _soap_debug_enabled


class APIKeyPlugin:
    """
    Zeep plugin to add API Key to SOAP Header (without namespace).

    This is the correct way to authenticate with memoQ WSAPI.
    The API key is added as a simple <ApiKey> element in the SOAP header.
    """

    def __init__(self, api_key: str):
        self.api_key = api_key

    def egress(self, envelope, http_headers, operation, binding_options):
        """Add ApiKey element to SOAP Header before sending request."""
        SOAP_NS = 'http://schemas.xmlsoap.org/soap/envelope/'

        # Get or create SOAP Header
        header = envelope.find(f'{{{SOAP_NS}}}Header')
        if header is None:
            header = etree.Element(f'{{{SOAP_NS}}}Header')
            envelope.insert(0, header)

        # Add ApiKey element without namespace
        api_key_elem = etree.SubElement(header, QName(None, 'ApiKey'))
        api_key_elem.text = self.api_key

        return envelope, http_headers

    def ingress(self, envelope, http_headers, operation):
        """Process response (no-op)."""
        return envelope, http_headers


class WSAPIClient:
    """
    memoQ WSAPI (SOAP) Client Base Class

    Provides connection management and authentication for memoQ SOAP services.
    Uses APIKeyPlugin to add API key to SOAP headers.
    """

    def __init__(
        self,
        host: Optional[str] = None,
        port: Optional[int] = None,
        api_key: Optional[str] = None,
        verify_ssl: bool = False,
        timeout: int = 300  # 5 minutes default for large file operations
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
        # Bypass proxy for memoQ connections to avoid connection issues
        self._session.trust_env = False

        # Plugins for SOAP client
        self._history = HistoryPlugin()
        self._plugins = [
            self._history,
            APIKeyPlugin(self._api_key)
        ]

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

        # Create client with API key plugin
        client = Client(
            wsdl_url,
            transport=transport,
            plugins=self._plugins
        )
        self._clients[service_name] = client

        return client

    def log_soap_debug(self, operation_name: str = ""):
        """
        Log the last SOAP request and response if debug is enabled.

        Args:
            operation_name: Optional name of the operation for logging context
        """
        if not is_soap_debug_enabled():
            return

        soap_logger = get_logger("wsapi.soap")

        try:
            # Get last sent request
            if self._history.last_sent:
                request_xml = etree.tostring(
                    self._history.last_sent["envelope"],
                    pretty_print=True,
                    encoding="unicode"
                )
                soap_logger.info(f"\n{'='*60}\nSOAP REQUEST{' - ' + operation_name if operation_name else ''}\n{'='*60}\n{request_xml}")

            # Get last received response
            if self._history.last_received:
                response_xml = etree.tostring(
                    self._history.last_received["envelope"],
                    pretty_print=True,
                    encoding="unicode"
                )
                soap_logger.info(f"\n{'='*60}\nSOAP RESPONSE{' - ' + operation_name if operation_name else ''}\n{'='*60}\n{response_xml}")

        except Exception as e:
            soap_logger.warning(f"Failed to log SOAP debug: {e}")

    def close(self):
        """Close the session and clean up resources"""
        self._session.close()
        self._clients.clear()

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.close()
