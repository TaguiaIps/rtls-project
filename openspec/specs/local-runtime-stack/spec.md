# local-runtime-stack Specification

## Purpose
Define the Docker Compose-based local runtime, required service roles, and environment conventions used to run the RTLS Analytics Platform implementation baseline.
## Requirements
### Requirement: Local container runtime
The RTLS Analytics Platform SHALL provide a Docker Compose-based local runtime for development and integration work.

#### Scenario: A contributor starts the local stack
- **WHEN** the documented local runtime command is executed
- **THEN** the repository SHALL start the defined containerized development stack needed for the first implementation baseline

### Requirement: Required local services
The local runtime SHALL include the service roles required for the first implementation baseline: web, API, worker, MQTT broker, Redis, TimescaleDB, and object storage.

#### Scenario: The initial runtime is provisioned
- **WHEN** the local container stack is defined
- **THEN** it SHALL include service definitions for web delivery, backend API, background processing, telemetry ingestion entry, cache or coordination, primary data storage, and object storage

### Requirement: Pilot-aligned configuration model
The local runtime SHALL use service naming and configuration conventions that can be reused for an initial pilot-server deployment without redefining the basic runtime topology.

#### Scenario: The team prepares a pilot environment
- **WHEN** the local runtime conventions are reviewed for a first pilot deployment
- **THEN** the service boundaries and configuration model SHALL remain compatible with a small container-based server deployment

### Requirement: Environment and secret conventions
The local runtime SHALL document environment variable and secret handling conventions for local development without hardcoding sensitive values into source-controlled application code.

#### Scenario: Local credentials are configured
- **WHEN** a contributor sets up the local runtime
- **THEN** the workspace SHALL provide a documented mechanism for configuring environment variables and service credentials outside application source files

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

