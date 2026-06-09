# MQTT TLS/mTLS Security

## Overview

All MQTT traffic uses TLS encryption on port 8883 with mutual TLS (mTLS) for client authentication. The broker validates client certificates signed by the platform's Internal Certificate Authority (ICA), and clients validate the broker's server certificate.

## Certificate Management

### Local Development

Generate all certificates for local development:

```bash
make certs
```

Or directly:

```bash
./ops/certs/generate-certs.sh --all
```

### Individual Certificate Operations

```bash
# Generate only the Root CA
./ops/certs/generate-certs.sh --ca

# Generate only the broker server certificate
./ops/certs/generate-certs.sh --server

# Generate a client certificate for a gateway
./ops/certs/generate-certs.sh --client gateway-002

# Override default validity (default: 365 days)
./ops/certs/generate-certs.sh --client gateway-003 --days 730
```

### Generated Files

| File | Purpose |
|------|---------|
| `ops/certs/ca.crt` | Root CA certificate (trusted by all parties) |
| `ops/certs/ca.key` | Root CA private key (protect this) |
| `ops/certs/broker.crt` | Mosquitto broker server certificate |
| `ops/certs/broker.key` | Mosquitto broker private key |
| `ops/certs/worker.crt` | Ingestion worker client certificate |
| `ops/certs/worker.key` | Ingestion worker private key |
| `ops/certs/<gateway-id>.crt` | Gateway client certificate |
| `ops/certs/<gateway-id>.key` | Gateway private key |

## Architecture

```
Gateway ──mTLS──> Mosquitto (port 8883) <──mTLS── Worker
                    │
                    ├── Validates client certs against CA
                    ├── Uses cert CN as username
                    └── Enforces ACLs per CN
```

## ACL Model

The broker enforces topic-level authorization based on the client certificate CN:

- Gateways can **publish** to `telemetry/<CN>/#` and **read** `commands/<CN>/#`
- The worker can **publish** and **subscribe** to all `telemetry/#` topics

The ACL file is at `ops/mosquitto/acl` and uses `%u` as the Mosquitto username placeholder, which maps to the certificate CN via `use_identity_as_username`.

## Worker Configuration

The ingestion worker connects via mTLS using these environment variables:

| Variable | Default | Description |
|----------|---------|-------------|
| `RTLS_MQTT_TLS_ENABLED` | `true` | Enable TLS for worker connections |
| `RTLS_MQTT_CA_CERT` | `/mosquitto/certs/ca.crt` | Path to CA certificate |
| `RTLS_MQTT_CLIENT_CERT` | `/mosquitto/certs/worker.crt` | Path to worker client cert |
| `RTLS_MQTT_CLIENT_KEY` | `/mosquitto/certs/worker.key` | Path to worker private key |

## Gateway Provisioning

1. Generate a client certificate with the gateway's registered ID as the CN
2. Deploy the client certificate, private key, and CA cert to the gateway
3. Configure the gateway to connect to port 8883 with mTLS
4. The gateway's CN must match its registered gateway ID for telemetry to be accepted

## Certificate Rotation

1. Generate a new client certificate for the gateway
2. Deploy the new certificate to the gateway
3. Restart the gateway to pick up the new certificate
4. The old certificate will naturally expire and connections will fail

## Security Notes

- Private keys (`*.key`) have restrictive permissions (600) and must never be committed to version control
- Add `ops/certs/*.key` to `.gitignore`
- The Root CA key (`ca.key`) should be stored securely; compromise allows arbitrary certificate issuance
