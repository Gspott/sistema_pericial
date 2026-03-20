#!/bin/bash

set -u

PROJECT_DIR="$(cd "$(dirname "$0")/.." && pwd)"
cd "$PROJECT_DIR" || exit 1

if [ -f ".env" ]; then
    set -a
    . ./.env
    set +a
fi

DOMAIN="${DUCKDNS_DOMAIN:-}"
TOKEN="${DUCKDNS_TOKEN:-}"

if [ -z "$DOMAIN" ] || [ -z "$TOKEN" ]; then
    echo "DuckDNS no configurado; se omite la actualización."
    exit 0
fi

RESPONSE="$(curl -fsS "https://www.duckdns.org/update?domains=${DOMAIN}&token=${TOKEN}&ip=" 2>/dev/null || true)"

if [ "$RESPONSE" = "OK" ]; then
    echo "DuckDNS actualizado para ${DOMAIN}.duckdns.org"
    exit 0
fi

echo "No se pudo actualizar DuckDNS para ${DOMAIN}.duckdns.org"
exit 1
