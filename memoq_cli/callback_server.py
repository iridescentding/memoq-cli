# -*- coding: utf-8 -*-
"""
memoQ callback receiver.

The callback contract mirrors memoQ's SOAP operations:
TestCallback(data) and DocumentDelivery(projectInfo, deliveredItems).
"""

from __future__ import annotations

import json
import urllib.error
import urllib.parse
import urllib.request
import xml.etree.ElementTree as ET
from dataclasses import dataclass
from datetime import datetime, timezone
from html import escape
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from typing import Any, Dict, Optional


CALLBACK_PATH = "/memoq-callback.asmx"
MEMOQ_CALLBACK_NS = "http://kilgray.com/memoq/v1"
SOAP11_NS = "http://schemas.xmlsoap.org/soap/envelope/"


class CallbackParseError(ValueError):
    """Raised when a SOAP callback body cannot be parsed."""


@dataclass
class CallbackServerConfig:
    """Runtime settings for the callback HTTP server."""

    events_path: str
    forward_url: Optional[str] = None
    api_key_header: Optional[str] = None
    api_key: Optional[str] = None
    timeout_seconds: int = 10


def build_callback_url(base_url: str, path: str = CALLBACK_PATH) -> str:
    """Build a memoQ callback URL ending in /memoq-callback.asmx."""
    if not base_url:
        raise ValueError("base_url is required")

    normalized_path = path if path.startswith("/") else f"/{path}"
    parsed = urllib.parse.urlparse(base_url.strip())
    if not parsed.scheme or not parsed.netloc:
        raise ValueError("base_url must include scheme and host")

    current_path = parsed.path.rstrip("/")
    if current_path == normalized_path.rstrip("/"):
        final_path = parsed.path
    else:
        final_path = f"{current_path}{normalized_path}" if current_path else normalized_path

    return urllib.parse.urlunparse(
        parsed._replace(path=final_path, params="", query="", fragment="")
    )


def parse_callback_envelope(raw_body: bytes) -> Dict[str, Any]:
    """Parse a memoQ SOAP callback request into a JSON-serializable event."""
    try:
        root = ET.fromstring(raw_body)
    except ET.ParseError as exc:
        raise CallbackParseError(f"Invalid XML: {exc}") from exc

    body = _first_child(root, "Body")
    if body is None:
        raise CallbackParseError("SOAP Body not found")

    operation = _first_element_child(body)
    if operation is None:
        raise CallbackParseError("SOAP operation not found")

    operation_name = _local_name(operation.tag)
    if operation_name == "TestCallback":
        return {
            "event_type": "TestCallback",
            "data": _child_text(operation, "data"),
        }

    if operation_name == "DocumentDelivery":
        project_elem = _first_child(operation, "projectInfo")
        items_elem = _first_child(operation, "deliveredItems")
        return {
            "event_type": "DocumentDelivery",
            "project": _element_children_to_dict(project_elem),
            "delivered_items": _delivery_items_to_list(items_elem),
        }

    raise CallbackParseError(f"Unsupported SOAP operation: {operation_name}")


def build_soap_response(operation_name: str, result_text: str = "") -> bytes:
    """Build a SOAP 1.1 response body for memoQ callback operations."""
    if operation_name == "TestCallback":
        body = (
            f'<TestCallbackResponse xmlns="{MEMOQ_CALLBACK_NS}">'
            f"<TestCallbackResult>{escape(result_text)}</TestCallbackResult>"
            "</TestCallbackResponse>"
        )
    elif operation_name == "DocumentDelivery":
        body = f'<DocumentDeliveryResponse xmlns="{MEMOQ_CALLBACK_NS}" />'
    else:
        raise ValueError(f"Unsupported SOAP operation: {operation_name}")

    envelope = (
        '<?xml version="1.0" encoding="utf-8"?>'
        f'<s:Envelope xmlns:s="{SOAP11_NS}"><s:Body>'
        f"{body}"
        "</s:Body></s:Envelope>"
    )
    return envelope.encode("utf-8")


def write_callback_event(event: Dict[str, Any], events_path: str) -> Dict[str, Any]:
    """Append a callback event to a JSONL audit file."""
    record = dict(event)
    record["received_at"] = datetime.now(timezone.utc).isoformat()

    path = Path(events_path)
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a", encoding="utf-8") as f:
        f.write(json.dumps(record, ensure_ascii=False) + "\n")

    return record


def forward_callback_event(
    event: Dict[str, Any],
    forward_url: str,
    api_key_header: Optional[str] = None,
    api_key: Optional[str] = None,
    timeout_seconds: int = 10,
) -> None:
    """Forward the parsed callback event as JSON to another HTTP endpoint."""
    payload = json.dumps(event, ensure_ascii=False).encode("utf-8")
    headers = {"Content-Type": "application/json"}
    if api_key_header and api_key:
        headers[api_key_header] = api_key

    request = urllib.request.Request(
        forward_url,
        data=payload,
        headers=headers,
        method="POST",
    )
    with urllib.request.urlopen(request, timeout=timeout_seconds) as response:
        if response.status >= 400:
            raise urllib.error.HTTPError(
                forward_url,
                response.status,
                response.reason,
                response.headers,
                None,
            )


class MemoQCallbackHTTPServer(ThreadingHTTPServer):
    """HTTP server that stores callback runtime config."""

    def __init__(self, server_address, RequestHandlerClass, config):
        super().__init__(server_address, RequestHandlerClass)
        self.callback_config = config


class MemoQCallbackHandler(BaseHTTPRequestHandler):
    """HTTP handler for /memoq-callback.asmx."""

    server: MemoQCallbackHTTPServer

    def do_GET(self) -> None:
        parsed = urllib.parse.urlparse(self.path)
        if parsed.path == "/health":
            self._send_json({"status": "ok", "callback_path": CALLBACK_PATH})
            return

        if parsed.path == CALLBACK_PATH:
            self._send_json(
                {
                    "message": "memoQ callback endpoint is ready",
                    "method": "POST",
                    "path": CALLBACK_PATH,
                }
            )
            return

        self.send_error(404, "Not found")

    def do_POST(self) -> None:
        parsed = urllib.parse.urlparse(self.path)
        if parsed.path != CALLBACK_PATH:
            self.send_error(404, "Not found")
            return

        length = int(self.headers.get("Content-Length", "0"))
        raw_body = self.rfile.read(length)

        try:
            event = parse_callback_envelope(raw_body)
            event = write_callback_event(
                event,
                self.server.callback_config.events_path,
            )
            self._forward_if_configured(event)
            response = build_soap_response(
                event["event_type"],
                "TestCallback accepted",
            )
        except CallbackParseError as exc:
            self.send_error(400, str(exc))
            return
        except Exception as exc:
            self.send_error(502, f"Callback handling failed: {exc}")
            return

        self.send_response(200)
        self.send_header("Content-Type", "text/xml; charset=utf-8")
        self.send_header("Content-Length", str(len(response)))
        self.end_headers()
        self.wfile.write(response)

    def log_message(self, format, *args) -> None:
        """Keep stdlib access logs concise."""
        print(f"{self.address_string()} - {format % args}")

    def _send_json(self, payload: Dict[str, Any], status: int = 200) -> None:
        response = json.dumps(payload, ensure_ascii=False).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(response)))
        self.end_headers()
        self.wfile.write(response)

    def _forward_if_configured(self, event: Dict[str, Any]) -> None:
        config = self.server.callback_config
        if not config.forward_url:
            return

        forward_callback_event(
            event,
            config.forward_url,
            api_key_header=config.api_key_header,
            api_key=config.api_key,
            timeout_seconds=config.timeout_seconds,
        )


def start_callback_server(
    host: str = "0.0.0.0",
    port: int = 8088,
    events_path: str = "memoq_callback_events.jsonl",
    forward_url: Optional[str] = None,
    api_key_header: Optional[str] = None,
    api_key: Optional[str] = None,
    timeout_seconds: int = 10,
) -> MemoQCallbackHTTPServer:
    """Start the memoQ callback HTTP server and block forever."""
    config = CallbackServerConfig(
        events_path=events_path,
        forward_url=forward_url,
        api_key_header=api_key_header,
        api_key=api_key,
        timeout_seconds=timeout_seconds,
    )
    server = MemoQCallbackHTTPServer((host, port), MemoQCallbackHandler, config)
    server.serve_forever()
    return server


def _local_name(tag: str) -> str:
    return tag.rsplit("}", 1)[-1] if "}" in tag else tag


def _first_child(element: ET.Element, local_name: str) -> Optional[ET.Element]:
    for child in list(element):
        if _local_name(child.tag) == local_name:
            return child
    return None


def _first_element_child(element: ET.Element) -> Optional[ET.Element]:
    for child in list(element):
        if isinstance(child.tag, str):
            return child
    return None


def _child_text(element: ET.Element, local_name: str) -> str:
    child = _first_child(element, local_name)
    return (child.text or "").strip() if child is not None else ""


def _element_children_to_dict(element: Optional[ET.Element]) -> Dict[str, str]:
    if element is None:
        return {}

    result = {}
    for child in list(element):
        if isinstance(child.tag, str):
            result[_local_name(child.tag)] = (child.text or "").strip()
    return result


def _delivery_items_to_list(element: Optional[ET.Element]) -> list[Dict[str, str]]:
    if element is None:
        return []

    items = []
    for child in list(element):
        if not isinstance(child.tag, str):
            continue
        if _local_name(child.tag) == "DeliveryItem":
            items.append(_element_children_to_dict(child))
    return items
