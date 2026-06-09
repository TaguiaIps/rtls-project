# mqtt-transport-security Specification

## Purpose
Secure MQTT transport with TLS encryption, mutual TLS gateway authentication, and broker certificate validation for production-grade gateway-to-broker communication.
## Requirements
### Requirement: Enforced Broker TLS Encryption
The MQTT broker SHALL require TLS encryption for all client connections originating from outside the internal network.

#### Scenario: Client attempts unencrypted connection
- **WHEN** a client attempts to connect to the MQTT broker via an unencrypted port (e.g., 1883) from an external network
- **THEN** the broker SHALL refuse the connection

#### Scenario: Client connects via TLS
- **WHEN** a client initiates a TLS handshake on the secure MQTT port (e.g., 8883) with a valid server certificate
- **THEN** the broker SHALL proceed with the secure connection establishment

### Requirement: Mutual TLS (mTLS) for Gateway Identity
The MQTT broker SHALL require Mutual TLS (mTLS) authentication for all gateways, necessitating a client certificate signed by the platform's trusted Internal Certificate Authority (ICA).

#### Scenario: Gateway connects with valid certificate
- **WHEN** a gateway provides a valid client certificate signed by the trusted ICA during the TLS handshake
- **THEN** the broker SHALL authenticate the gateway identity based on the certificate's Common Name (CN) or Subject Alternative Name (SAN)

#### Scenario: Gateway connects with untrusted certificate
- **WHEN** a gateway provides a client certificate that is not signed by the trusted ICA or is expired
- **THEN** the broker SHALL terminate the TLS handshake and reject the connection

### Requirement: Broker Certificate Validation by Ingestion Worker
The platform's ingestion worker SHALL validate the MQTT broker's server certificate against the trusted Root CA before establishing a connection.

#### Scenario: Ingestion worker connects to broker with valid certificate
- **WHEN** the ingestion worker initiates a connection to the broker and the broker presents a valid certificate signed by the trusted Root CA
- **THEN** the ingestion worker SHALL proceed with the connection

#### Scenario: Ingestion worker connects to broker with invalid certificate
- **WHEN** the ingestion worker initiates a connection and the broker presents an invalid, untrusted, or hostname-mismatched certificate
- **THEN** the ingestion worker SHALL abort the connection and log a security alert

