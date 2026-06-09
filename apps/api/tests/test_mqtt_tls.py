"""Integration tests for MQTT TLS/mTLS broker configuration and worker connections."""

from __future__ import annotations

import ssl
import subprocess
import time
from pathlib import Path

import pytest

CERTS_DIR = Path(__file__).resolve().parents[3] / "ops" / "certs"
SCRIPT = CERTS_DIR / "generate-certs.sh"


def _generate_certs() -> None:
    subprocess.run(
        ["bash", str(SCRIPT), "--all"],
        check=True,
        capture_output=True,
    )


@pytest.fixture(scope="module")
def certs(tmp_path_factory):
    tmp = tmp_path_factory.mktemp("certs")
    script = tmp / "generate-certs.sh"
    script.write_text(
        Path(__file__)
        .resolve()
        .parents[3]
        .joinpath("ops", "certs", "generate-certs.sh")
        .read_text()
    )
    subprocess.run(
        ["bash", str(script), "--all", "--days", "1"],
        check=True,
        capture_output=True,
        cwd=tmp,
    )
    return {
        "ca_cert": tmp / "ca.crt",
        "ca_key": tmp / "ca.key",
        "broker_cert": tmp / "broker.crt",
        "broker_key": tmp / "broker.key",
        "worker_cert": tmp / "worker.crt",
        "worker_key": tmp / "worker.key",
        "gateway_cert": tmp / "gateway-001.crt",
        "gateway_key": tmp / "gateway-001.key",
    }


def _make_tls_context(
    ca_cert: Path, cert: Path | None = None, key: Path | None = None
) -> ssl.SSLContext:
    ctx = ssl.SSLContext(ssl.PROTOCOL_TLS_CLIENT)
    ctx.minimum_version = ssl.TLSVersion.TLSv1_2
    ctx.check_hostname = False
    ctx.load_verify_locations(cafile=str(ca_cert))
    if cert and key:
        ctx.load_cert_chain(certfile=str(cert), keyfile=str(key))
    return ctx


def _try_connect(host: str, port: int, tls_ctx: ssl.SSLContext) -> bool:
    import socket

    try:
        with socket.create_connection((host, port), timeout=5) as sock:
            with tls_ctx.wrap_socket(sock, server_hostname=host):
                return True
    except (ConnectionRefusedError, ssl.SSLError, OSError):
        return False


class TestMTLSConnection:
    """Integration tests that verify mTLS connections to the broker.

    These tests require a running Mosquitto broker with TLS configured.
    Mark with pytest.mark.integration to run separately.
    """

    @pytest.mark.integration
    def test_valid_client_cert_connects_successfully(self, certs):
        ctx = _make_tls_context(
            certs["ca_cert"],
            certs["gateway_cert"],
            certs["gateway_key"],
        )
        assert _try_connect("localhost", 8883, ctx)

    @pytest.mark.integration
    def test_no_client_cert_is_rejected(self, certs):
        ctx = _make_tls_context(certs["ca_cert"])
        assert not _try_connect("localhost", 8883, ctx)

    @pytest.mark.integration
    def test_untrusted_client_cert_is_rejected(self, certs, tmp_path):
        subprocess.run(
            ["bash", str(SCRIPT), "--ca", "--days", "1"],
            check=True,
            capture_output=True,
            cwd=tmp_path,
        )
        subprocess.run(
            ["bash", str(SCRIPT), "--client", "rogue", "--days", "1"],
            check=True,
            capture_output=True,
            cwd=tmp_path,
        )
        rogue_ctx = _make_tls_context(
            tmp_path / "ca.crt",
            tmp_path / "rogue.crt",
            tmp_path / "rogue.key",
        )
        assert not _try_connect("localhost", 8883, rogue_ctx)


class TestACLEnforcement:
    """Tests verifying topic-level ACLs are enforced by the broker.

    Requires a running Mosquitto broker with ACLs configured.
    """

    @pytest.mark.integration
    def test_gateway_cannot_publish_to_other_gateway_topic(self, certs):
        try:
            import paho.mqtt.client as mqtt
        except ImportError:
            pytest.skip("paho-mqtt not installed")

        connected = False

        def on_connect(client, userdata, flags, reason_code, properties=None):
            nonlocal connected
            connected = int(reason_code) == 0

        client = mqtt.Client(client_id="test-acl-gateway-001")
        client.tls_set_context(
            _make_tls_context(certs["ca_cert"], certs["gateway_cert"], certs["gateway_key"])
        )
        client.on_connect = on_connect
        client.connect("localhost", 8883, keepalive=60)
        client.loop_start()
        time.sleep(1)

        if not connected:
            client.loop_stop()
            pytest.skip("Cannot connect to broker for ACL test")

        mid = client.publish("telemetry/gateway-002/some-data", b"{}", qos=1)
        mid.wait_for_publish(timeout=5)
        client.loop_stop()

        assert mid.rc != 0, "Broker should reject publish to unauthorized topic"


class TestWorkerTLSConfiguration:
    """Unit tests for the worker TLS configuration path."""

    def test_configure_tls_sets_ssl_context(self, monkeypatch, tmp_path):
        from rtls_api import worker

        ca = tmp_path / "ca.crt"
        cert = tmp_path / "client.crt"
        key = tmp_path / "client.key"
        ca.write_bytes(b"fake-ca")
        cert.write_bytes(b"fake-cert")
        key.write_bytes(b"fake-key")

        called_with = {}

        class FakeMQTTClient:
            def tls_set_context(self, ctx):
                called_with["context"] = ctx

        class FakeSettings:
            mqtt_tls_enabled = True
            mqtt_ca_cert = str(ca)
            mqtt_client_cert = str(cert)
            mqtt_client_key = str(key)

        monkeypatch.setattr(worker, "get_settings", lambda: FakeSettings())

        client = FakeMQTTClient()
        worker._configure_tls(client, FakeSettings())

        assert "context" in called_with
        assert isinstance(called_with["context"], ssl.SSLContext)
