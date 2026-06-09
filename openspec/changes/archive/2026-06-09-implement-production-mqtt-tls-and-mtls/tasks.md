## 1. Infrastructure and Broker Configuration

- [x] 1.1 Update `ops/mosquitto/mosquitto.conf` to enable TLS on port 8883
- [x] 1.2 Configure Mosquitto to require client certificates (mTLS) for the secure port
- [x] 1.3 Implement Mosquitto ACL file to restrict gateway and worker topic access
- [x] 1.4 Update `docker-compose.yml` to mount certificate and ACL files into the Mosquitto container

## 2. Certificate Management Utility

- [x] 2.1 Create a shell script or Python utility to generate a local Root CA
- [x] 2.2 Add functionality to the utility to issue server certificates for the Mosquitto broker
- [x] 2.3 Add functionality to the utility to issue client certificates and private keys for gateways and the ingestion worker
- [x] 2.4 Document the certificate provisioning workflow in a new `docs/operations/mqtt-security.md` file

## 3. Ingestion Worker Security Updates

- [x] 3.1 Update `apps/api/src/rtls_api/config.py` to include settings for CA certificates, client certificates, and private keys
- [x] 3.2 Modify `create_mqtt_client` in `apps/api/src/rtls_api/worker.py` to configure `paho-mqtt` with TLS/mTLS parameters
- [x] 3.3 Implement certificate validation logic to ensure the worker only connects to a trusted broker
- [x] 3.4 Update worker initialization to log secure connection status and handle TLS handshake failures gracefully

## 4. Validation and Testing

- [x] 4.1 Create an integration test in `apps/api/tests/` that verifies a successful mTLS connection to the local broker
- [x] 4.2 Create a negative test case verifying that connections without a valid certificate are rejected by the broker
- [x] 4.3 Verify that ACLs correctly prevent a gateway from publishing to another gateway's telemetry topic
- [x] 4.4 Update `Makefile` with a command to generate local development certificates (e.g., `make certs`)
