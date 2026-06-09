## ADDED Requirements

### Requirement: Local MQTT TLS support
The local runtime SHALL support MQTT TLS and mTLS configurations to facilitate secure development and testing of ingestion pipelines.

#### Scenario: Contributor runs stack with security enabled
- **WHEN** the local stack is started with security configurations enabled
- **THEN** the MQTT broker SHALL listen on a secure port and require certificate-based authentication as defined in the platform security specs

### Requirement: Automated certificate generation for local development
The platform SHALL provide utility scripts or tools to generate the necessary Root CA, server certificates, and client certificates required for local TLS/mTLS development.

#### Scenario: Developer generates local certificates
- **WHEN** the certificate generation utility is executed in the local environment
- **THEN** it SHALL produce valid, non-expired certificates and private keys suitable for local broker and client configuration
