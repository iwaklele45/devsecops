#!/usr/bin/env bash
set -Eeuo pipefail

cd "$(dirname "$0")/.."

if [[ ! -f .env ]]; then
    echo "[FAIL] File .env tidak ditemukan." >&2
    exit 1
fi

set -a
source .env
set +a

: "${APP_IMAGE:?APP_IMAGE belum diatur}"
: "${REGISTRY_HOST:?REGISTRY_HOST belum diatur}"
: "${REGISTRY_USER:?REGISTRY_USER belum diatur}"
: "${REGISTRY_PASSWORD:?REGISTRY_PASSWORD belum diatur}"

if [[ ! -f reports/gate-status.txt ]] \
    || [[ "$(< reports/gate-status.txt)" != "PASS" ]]; then
    echo "[BLOCKED] Image belum lulus security gate." >&2
    exit 1
fi

printf '%s\n' "$REGISTRY_PASSWORD" \
    | docker login "$REGISTRY_HOST" \
        --username "$REGISTRY_USER" \
        --password-stdin

remote_image="$REGISTRY_HOST/pens-web:1.0"

docker tag "$APP_IMAGE" "$remote_image"
docker push "$remote_image"
docker pull "$remote_image"

curl --fail --silent --show-error \
    --cacert registry/certs/domain.crt \
    --user "$REGISTRY_USER:$REGISTRY_PASSWORD" \
    "https://$REGISTRY_HOST/v2/_catalog" \
    | tee reports/registry-catalog.json

curl --fail --silent --show-error \
    --cacert registry/certs/domain.crt \
    --user "$REGISTRY_USER:$REGISTRY_PASSWORD" \
    "https://$REGISTRY_HOST/v2/pens-web/tags/list" \
    | tee reports/registry-tags.json

docker image inspect "$remote_image" \
    --format '{{json .RepoDigests}}' \
    | tee reports/registry-digests.json

docker logout "$REGISTRY_HOST"
echo "[PASS] Push, pull, katalog, tag, dan digest telah diverifikasi."
