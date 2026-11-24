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

scanned_id="$(< reports/scanned-image-id.txt)"
current_id="$(docker image inspect "$APP_IMAGE" --format '{{.Id}}')"
if [[ "$current_id" != "$scanned_id" ]]; then
    echo "[BLOCKED] Image berubah sejak dipindai. Jalankan ulang scan-image.sh." >&2
    exit 1
fi

# Password dikirim melalui stdin agar tidak terlihat pada daftar proses.
registry_get() {
    printf 'user = "%s:%s"\n' "$REGISTRY_USER" "$REGISTRY_PASSWORD" \
        | curl --config - \
            --fail --silent --show-error \
            --cacert registry/certs/domain.crt \
            "https://$REGISTRY_HOST$1"
}

# Credential login dihapus walaupun script berhenti di tengah jalan.
trap 'docker logout "$REGISTRY_HOST" >/dev/null 2>&1 || true' EXIT

printf '%s\n' "$REGISTRY_PASSWORD" \
    | docker login "$REGISTRY_HOST" \
        --username "$REGISTRY_USER" \
        --password-stdin

remote_image="$REGISTRY_HOST/pens-web:1.0"

docker tag "$APP_IMAGE" "$remote_image"
docker push "$remote_image"

# Hapus tag registry lokal agar pull benar-benar mengambil manifest dari registry.
docker image rm "$remote_image" >/dev/null
docker pull "$remote_image"

pulled_id="$(docker image inspect "$remote_image" --format '{{.Id}}')"
if [[ "$pulled_id" != "$scanned_id" ]]; then
    echo "[FAIL] Image hasil pull berbeda dari image yang dipindai." >&2
    exit 1
fi

registry_get /v2/_catalog | tee reports/registry-catalog.json
registry_get /v2/pens-web/tags/list | tee reports/registry-tags.json

docker image inspect "$remote_image" \
    --format '{{json .RepoDigests}}' \
    | tee reports/registry-digests.json

echo "[PASS] Push, pull, identitas image, katalog, tag, dan digest telah diverifikasi."
