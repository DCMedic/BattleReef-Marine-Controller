#!/usr/bin/env bash
set -euo pipefail

CERT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)/certs"
mkdir -p "$CERT_DIR"
chmod 700 "$CERT_DIR"

CA_KEY="$CERT_DIR/ca.key"
CA_CERT="$CERT_DIR/ca.crt"

issue_client() {
  local name="$1"
  openssl genrsa -out "$CERT_DIR/${name}.key" 2048
  openssl req -new -key "$CERT_DIR/${name}.key" -out "$CERT_DIR/${name}.csr" -subj "/CN=${name}"
  openssl x509 -req -in "$CERT_DIR/${name}.csr" -CA "$CA_CERT" -CAkey "$CA_KEY" \
    -CAcreateserial -out "$CERT_DIR/${name}.crt" -days 825 -sha256 \
    -extfile <(printf 'extendedKeyUsage=clientAuth\nkeyUsage=digitalSignature,keyEncipherment\n')
  rm -f "$CERT_DIR/${name}.csr"
  chmod 600 "$CERT_DIR/${name}.key"
}

echo "Generating BattleReef development MQTT CA..."
openssl genrsa -out "$CA_KEY" 4096
openssl req -x509 -new -nodes -key "$CA_KEY" -sha256 -days 3650 \
  -out "$CA_CERT" -subj "/CN=BattleReef Development MQTT CA"

cat > "$CERT_DIR/server.ext" <<'EOF'
subjectAltName=DNS:mosquitto,DNS:localhost,IP:127.0.0.1
extendedKeyUsage=serverAuth
keyUsage=digitalSignature,keyEncipherment
EOF

openssl genrsa -out "$CERT_DIR/server.key" 2048
openssl req -new -key "$CERT_DIR/server.key" -out "$CERT_DIR/server.csr" -subj "/CN=mosquitto"
openssl x509 -req -in "$CERT_DIR/server.csr" -CA "$CA_CERT" -CAkey "$CA_KEY" \
  -CAcreateserial -out "$CERT_DIR/server.crt" -days 825 -sha256 -extfile "$CERT_DIR/server.ext"
rm -f "$CERT_DIR/server.csr" "$CERT_DIR/server.ext"
chmod 600 "$CERT_DIR/server.key" "$CA_KEY"

issue_client "broker-health"
issue_client "battlereef-backend"
issue_client "simulator_node"
issue_client "device-simulator"

chmod 644 "$CERT_DIR"/*.crt

echo
printf '%s\n' "Development PKI created in: $CERT_DIR" \
  "Client certificate CN values are MQTT identities." \
  "Do not commit this directory or reuse this development CA in production."
