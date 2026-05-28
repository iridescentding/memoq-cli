# -*- coding: utf-8 -*-
"""
Tests for the memoQ callback receiver helpers.
"""

import json
import threading
import urllib.request

import pytest

from memoq_cli.callback_server import (
    CallbackServerConfig,
    MemoQCallbackHTTPServer,
    MemoQCallbackHandler,
    build_callback_url,
    build_soap_response,
    parse_callback_envelope,
)


def test_build_callback_url_appends_default_asmx_path():
    assert (
        build_callback_url("https://callback.example.com/")
        == "https://callback.example.com/memoq-callback.asmx"
    )


def test_build_callback_url_keeps_existing_asmx_path():
    assert (
        build_callback_url("https://callback.example.com/memoq-callback.asmx")
        == "https://callback.example.com/memoq-callback.asmx"
    )


def test_parse_test_callback_envelope():
    envelope = b"""<?xml version="1.0" encoding="utf-8"?>
<s:Envelope xmlns:s="http://schemas.xmlsoap.org/soap/envelope/">
  <s:Body>
    <TestCallback xmlns="http://kilgray.com/memoq/v1">
      <data>ping-from-memoq</data>
    </TestCallback>
  </s:Body>
</s:Envelope>
"""

    event = parse_callback_envelope(envelope)

    assert event["event_type"] == "TestCallback"
    assert event["data"] == "ping-from-memoq"


def test_parse_document_delivery_envelope():
    envelope = b"""<?xml version="1.0" encoding="utf-8"?>
<s:Envelope xmlns:s="http://schemas.xmlsoap.org/soap/envelope/">
  <s:Body>
    <DocumentDelivery xmlns="http://kilgray.com/memoq/v1">
      <projectInfo>
        <ProjectGuid>c25f0cdb-4242-f111-966c-a38328e9a256</ProjectGuid>
        <ProjectName>Callback Test Project</ProjectName>
      </projectInfo>
      <deliveredItems>
        <DeliveryItem>
          <DocumentGuid>aaaaaaaa-bbbb-cccc-dddd-eeeeeeeeeeee</DocumentGuid>
          <DocumentName>sample.docx</DocumentName>
          <ExternalDocumentId>EXT-1</ExternalDocumentId>
          <TargetLanguageCode>zho-CN</TargetLanguageCode>
          <NewWorkflowStatus>Delivered</NewWorkflowStatus>
          <PreviousWorkflowStatus>Translation</PreviousWorkflowStatus>
        </DeliveryItem>
      </deliveredItems>
    </DocumentDelivery>
  </s:Body>
</s:Envelope>
"""

    event = parse_callback_envelope(envelope)

    assert event["event_type"] == "DocumentDelivery"
    assert event["project"]["ProjectGuid"] == "c25f0cdb-4242-f111-966c-a38328e9a256"
    assert event["project"]["ProjectName"] == "Callback Test Project"
    assert event["delivered_items"][0]["DocumentName"] == "sample.docx"
    assert event["delivered_items"][0]["TargetLanguageCode"] == "zho-CN"


def test_build_test_callback_response():
    response = build_soap_response("TestCallback", "OK")

    assert b"TestCallbackResponse" in response
    assert b"TestCallbackResult" in response
    assert b"OK" in response


def test_build_document_delivery_response():
    response = build_soap_response("DocumentDelivery", "")

    assert b"DocumentDeliveryResponse" in response


def test_http_server_accepts_test_callback_and_writes_event(tmp_path):
    events_path = tmp_path / "events.jsonl"
    try:
        server = MemoQCallbackHTTPServer(
            ("127.0.0.1", 0),
            MemoQCallbackHandler,
            CallbackServerConfig(events_path=str(events_path)),
        )
    except PermissionError as exc:
        pytest.skip(f"socket bind not available in this sandbox: {exc}")
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    try:
        port = server.server_address[1]
        request = urllib.request.Request(
            f"http://127.0.0.1:{port}/memoq-callback.asmx",
            data=b"""<?xml version="1.0" encoding="utf-8"?>
<s:Envelope xmlns:s="http://schemas.xmlsoap.org/soap/envelope/">
  <s:Body>
    <TestCallback xmlns="http://kilgray.com/memoq/v1">
      <data>http-smoke</data>
    </TestCallback>
  </s:Body>
</s:Envelope>
""",
            headers={"Content-Type": "text/xml; charset=utf-8"},
            method="POST",
        )

        with urllib.request.urlopen(request, timeout=5) as response:
            response_body = response.read()

        assert response.status == 200
        assert b"TestCallbackResponse" in response_body

        event = json.loads(events_path.read_text(encoding="utf-8").splitlines()[0])
        assert event["event_type"] == "TestCallback"
        assert event["data"] == "http-smoke"
        assert "received_at" in event
    finally:
        server.shutdown()
        server.server_close()
        thread.join(timeout=5)
