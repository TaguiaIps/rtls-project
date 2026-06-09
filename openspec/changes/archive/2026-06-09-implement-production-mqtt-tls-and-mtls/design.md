## Context

The platform uses MQTT for real-time telemetry ingestion. Currently, the Mosquitto broker is configured with `allow_anonymous true` and listens on an unencrypted port (1883). For production readiness, we must transition to a secure model that ensures data encryption in transit and cryptographic verification of gateway identities.

## Goals / Non-Goals

**Goals:**
- Transition all MQTT traffic to TLS-encrypted connections.
- Implement mTLS for all gateways to ensure strong identity verification.
- Implement topic-level authorization (ACLs) to prevent cross-gateway eavesdropping or spoofing.
- Provide a clear certificate management workflow for provisioning and rotation.

**Non-Goals:**
- Implementing a full-blown PKI service (we will start with a managed Internal CA or automated scripts).
- Implementing WebSockets over TLS (WSS) in this phase (focus is on gateway-to-broker and worker-to-broker).

## Decisions

### Decision: Use Mosquitto with mTLS and ACLs
We will continue using Mosquitto but harden its configuration to enforce TLS, mTLS, and ACL-based authorization.
- **Rationale**: Mosquitto is lightweight, production-proven, and natively supports these security features.
- **Alternatives**: Cloud-managed IoT hubs (AWS IoT, Azure IoT) were considered but rejected to maintain platform portability and minimize external dependencies in the current phase.

### Decision: Internal CA (ICA) for Client Certificates
The platform will use a dedicated Internal Certificate Authority (ICA) to sign client certificates for gateways and internal services.
- **Rationale**: Provides full control over certificate issuance and revocation without the cost and complexity of public CAs, which are not suitable for private IoT device identity.
- **Implementation**: For the first phase, a scriptable OpenSSL-based CA or a tool like `step-ca` will be used to generate certificates.

### Decision: Topic-Level ACLs based on Common Name (CN)
We will use Mosquitto's built-in ACL support, mapping the gateway's certificate Common Name (CN) to its authorized topics.
- **Rationale**: Simplifies authorization logic by leveraging the cryptographic identity established during the mTLS handshake.
- **Pattern**: Gateways will be authorized to publish to `telemetry/<CN>/+` and subscribe to `commands/<CN>/+`.

### Decision: Ingestion Worker TLS Configuration
The Python-based ingestion worker will use the `paho-mqtt` library configured with the Root CA to validate the broker and a client certificate/key pair for its own mTLS identity.
- **Rationale**: Ensures the worker only talks to the legitimate platform broker and is itself authenticated by the broker.

## Risks / Trade-offs

- **[Risk] Certificate Expiration** → **Mitigation**: Implement health monitoring for certificate expiration and define a clear rotation workflow.
- **[Risk] Revocation Complexity** → **Mitigation**: Use Certificate Revocation Lists (CRLs) in Mosquitto to invalidate compromised certificates.
- **[Risk] Latency Increase** → **Mitigation**: TLS handshakes add overhead, but for long-lived MQTT connections, this is negligible after the initial connection.

## Migration Plan

1. **Phase 1 (Local)**: Update `ops/mosquitto/` to support TLS/mTLS. Create certificate generation scripts.
2. **Phase 2 (Worker)**: Update the ingestion worker to support TLS/mTLS via environment variables.
3. **Phase 3 (Testing)**: Run integration tests with valid/invalid certificates.
4. **Phase 4 (Docs)**: Update the runbook for gateway provisioning with certificates.

## Open Questions

- Should we use a dynamic ACL plugin for Mosquitto to integrate with the backend API for real-time authorization updates? (Deferred to Wave 6+).
