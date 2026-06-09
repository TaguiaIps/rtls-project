#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
CERT_DIR="${SCRIPT_DIR}"
CA_KEY="${CERT_DIR}/ca.key"
CA_CERT="${CERT_DIR}/ca.crt"
BROKER_KEY="${CERT_DIR}/broker.key"
BROKER_CERT="${CERT_DIR}/broker.crt"
WORKER_KEY="${CERT_DIR}/worker.key"
WORKER_CERT="${CERT_DIR}/worker.crt"
VALIDITY_DAYS="${CERT_DAYS:-365}"

usage() {
    echo "Usage: $0 [--ca | --server | --client NAME | --all] [--days N]"
    echo ""
    echo "  --ca       Generate a self-signed Root CA"
    echo "  --server   Generate a server certificate for the MQTT broker"
    echo "  --client NAME  Generate a client certificate for NAME (CN=NAME)"
    echo "  --all      Generate everything: CA, broker cert, worker cert, gateway cert"
    echo "  --days N   Certificate validity in days (default: ${VALIDITY_DAYS})"
    exit 1
}

generate_ca() {
    echo "==> Generating Root CA..."
    openssl req -x509 -new -nodes -newkey rsa:4096 \
        -keyout "$CA_KEY" -out "$CA_CERT" \
        -days "$VALIDITY_DAYS" \
        -subj "/CN=RTLS-Local-CA/O=RTLS-Platform"
    chmod 600 "$CA_KEY"
    echo "    CA key:  ${CA_KEY}"
    echo "    CA cert: ${CA_CERT}"
}

generate_server() {
    if [[ ! -f "$CA_KEY" || ! -f "$CA_CERT" ]]; then
        echo "ERROR: Root CA not found. Run --ca first." >&2
        exit 1
    fi
    echo "==> Generating broker server certificate..."
    openssl req -new -nodes -newkey rsa:2048 \
        -keyout "$BROKER_KEY" -out "${BROKER_CERT}.csr" \
        -subj "/CN=mqtt-broker/O=RTLS-Platform"
    openssl x509 -req -in "${BROKER_CERT}.csr" \
        -CA "$CA_CERT" -CAkey "$CA_KEY" \
        -CAcreateserial -out "$BROKER_CERT" \
        -days "$VALIDITY_DAYS" \
        -extfile <(printf "subjectAltName=DNS:localhost,DNS:mqtt-broker,IP:127.0.0.1")
    rm -f "${BROKER_CERT}.csr" "${CERT_DIR}/ca.srl"
    chmod 600 "$BROKER_KEY"
    echo "    Broker key:  ${BROKER_KEY}"
    echo "    Broker cert: ${BROKER_CERT}"
}

generate_client() {
    local cn="$1"
    if [[ -z "$cn" ]]; then
        echo "ERROR: --client requires a name (CN)." >&2
        exit 1
    fi
    if [[ ! -f "$CA_KEY" || ! -f "$CA_CERT" ]]; then
        echo "ERROR: Root CA not found. Run --ca first." >&2
        exit 1
    fi

    local client_key="${CERT_DIR}/${cn}.key"
    local client_cert="${CERT_DIR}/${cn}.crt"

    echo "==> Generating client certificate for CN=${cn}..."
    openssl req -new -nodes -newkey rsa:2048 \
        -keyout "$client_key" -out "${client_cert}.csr" \
        -subj "/CN=${cn}/O=RTLS-Platform"
    openssl x509 -req -in "${client_cert}.csr" \
        -CA "$CA_CERT" -CAkey "$CA_KEY" \
        -CAcreateserial -out "$client_cert" \
        -days "$VALIDITY_DAYS"
    rm -f "${client_cert}.csr" "${CERT_DIR}/ca.srl"
    chmod 600 "$client_key"
    echo "    Client key:  ${client_key}"
    echo "    Client cert: ${client_cert}"
}

CMD=""
CLIENT_CN=""
while [[ $# -gt 0 ]]; do
    case "$1" in
        --ca)    CMD="ca" ;;
        --server) CMD="server" ;;
        --client) shift; CLIENT_CN="$1" ; CMD="client" ;;
        --all)   CMD="all" ;;
        --days)  shift; VALIDITY_DAYS="$1" ;;
        --help|-h) usage ;;
        *) echo "Unknown option: $1" >&2; usage ;;
    esac
    shift
done

if [[ -z "$CMD" ]]; then usage; fi

mkdir -p "$CERT_DIR"

case "$CMD" in
    ca)     generate_ca ;;
    server) generate_server ;;
    client) generate_client "$CLIENT_CN" ;;
    all)
        generate_ca
        generate_server
        generate_client "worker"
        generate_client "gateway-001"
        ;;
esac

echo "==> Done."
