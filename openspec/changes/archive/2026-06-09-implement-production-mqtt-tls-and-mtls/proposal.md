## Why

The current MQTT ingestion baseline relies on unencrypted connections and simple identifier checks, which are insufficient for production deployments. To ensure data privacy, integrity, and non-repudiation of gateway identity, the platform must transition to a production-grade secure transport layer using TLS for encryption and Mutual TLS (mTLS) for gateway authentication.

## What Changes

- **Broker TLS Enforcement**: Configure the MQTT broker (Mosquitto) to require TLS for all external connections, ensuring data is encrypted in transit.
- **Mutual TLS (mTLS) for Gateways**: Require gateways to present a valid client certificate signed by a trusted Internal Certificate Authority (ICA) to establish identity.
- **Broker-Side Authorization**: Implement broker-enforced Access Control Lists (ACLs) to ensure clients can only publish to or subscribe from authorized topics based on their certificate identity.
- **Certificate Management Infrastructure**: Define the workflow and tooling for certificate provisioning, rotation, and revocation for gateways and internal services.
- **Ingestion Worker Security**: Update the ingestion worker to validate broker certificates and support mTLS handshakes.
- **Local Stack Hardening**: Update the local development stack to support TLS/mTLS for integration testing.

## Capabilities

### New Capabilities
- `mqtt-transport-security`: Defines the requirements for the TLS/mTLS infrastructure, including CA trust models, broker certificate validation, and client certificate requirements.
- `mqtt-client-authorization`: Defines the requirements for broker-enforced authorization and topic-level access control.

### Modified Capabilities
- `gateway-telemetry-ingestion`: Update requirements to mandate encrypted and mutually authenticated transport for all telemetry and heartbeat data.
- `local-runtime-stack`: Update requirements to include MQTT TLS/mTLS configuration and certificate management utilities in the local development environment.

## Impact

- **Infrastructure**: Mosquitto configuration changes; addition of a certificate management utility or service.
- **API/Worker**: Configuration updates to handle certificates and private keys; TLS library integration.
- **Mobile/Gateways**: Requirements for gateways to store and manage certificates.
- **Security**: Significantly improved posture through cryptographic identity and encryption.
