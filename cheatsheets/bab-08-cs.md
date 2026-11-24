# Cheatsheet Bab 8 — Hardening Container, Secrets, Trivy, dan Private Registry

Cheatsheet ini mengikuti pola Bab 3–7. Setiap berkas yang perlu dibuat ditempatkan dalam **Kotak Script**. Perintah setup, validasi, pemindaian, pengujian negatif, distribusi image, dan cleanup ditempatkan dalam **Kotak Perintah** tersendiri.

> **Perbaikan keamanan terhadap draf awal.** Registry tidak dijalankan menggunakan HTTP anonim. Lab ini menggunakan TLS, autentikasi `htpasswd` bcrypt, dan port loopback. Trivy memindai arsip image sehingga container scanner tidak memerlukan mount `/var/run/docker.sock`.

> **Revisi November 2026.** (1) Network aplikasi dan registry tidak lagi `internal: true`, karena Docker tidak memasang port publish untuk container yang hanya terhubung ke network internal. (2) Secret dan aset registry dilindungi oleh direktori `0700`, sedangkan filenya `0444` dan di-bind-mount satu per satu, sehingga proses non-root dan proses tanpa capability DAC tetap dapat membacanya. (3) Health check membaca secret, bukan hanya memeriksa keberadaan file. (4) Push ke `localhost` tidak lagi dianggap bukti validasi TLS. (5) Negative test read-only, seccomp, swap, identitas image, dan pencarian nilai secret diperketat.

| Kotak | Nama file | Fungsi |
|---:|---|---|
| 1 | `.env.example` | Template identitas dan credential sintetis registry |
| 2 | `.gitignore` | Mencegah secret, private key, dan laporan lokal masuk Git |
| 3 | `.dockerignore` | Mengecilkan build context dan mencegah data sensitif masuk image |
| 4 | `app/requirements.txt` | Dependency Python yang dipin |
| 5 | `app/app.py` | Aplikasi Flask untuk pengujian hardening dan secret mount |
| 6 | `app/Dockerfile` | Multi-stage build dan user non-root |
| 7 | `secrets/app_secret.txt.example` | Contoh format secret tanpa nilai aktif |
| 8 | `compose.yaml` | Hardening runtime aplikasi dan registry TLS |
| 9 | `scripts/generate-registry-assets.sh` | Membuat sertifikat serta akun registry bcrypt |
| 10 | `scripts/scan-image.sh` | Scan image, konfigurasi, secret, SBOM, dan security gate |
| 11 | `scripts/push-registry.sh` | Push hanya setelah gate lulus dan verifikasi registry |
| 12 | `scripts/verify-hardening.sh` | Negative test terhadap identity, filesystem, capability, secret, dan registry |

## Arsitektur Ringkas

```mermaid
flowchart TD
    S["Source + Dockerfile"] -->|"build"| I["pens-web:1.0"]
    I -->|"save archive"| T["Trivy gate"]
    T -->|"PASS"| R["Registry TLS + auth"]
    I -->|"Compose hardening"| A["App non-root"]
    F["Secret file"] -->|"/run/secrets"| A
```

Image hanya dipromosikan ke registry apabila security gate menyatakan `PASS`. Hasil scan lengkap tetap harus ditriase karena severity scanner tidak otomatis sama dengan risiko aktual aplikasi.

## Kotak Perintah A — Menyiapkan Direktori Bab 8

```bash
mkdir -p ~/docker-lab/bab-8/{app,secrets,registry/certs,registry/auth,scripts,reports}
cd ~/docker-lab/bab-8
chmod 700 secrets registry registry/certs registry/auth
touch reports/.gitkeep
```

Direktori `secrets/` dan `registry/` bermode `0700` sehingga akun lain di host tidak dapat menelusuri isinya. Mode file di dalamnya diatur pada Kotak Script 7 dan 9.

Struktur akhir:

```text
bab-8/
├── .env.example
├── .env
├── .gitignore
├── .dockerignore
├── compose.yaml
├── app/
│   ├── app.py
│   ├── Dockerfile
│   └── requirements.txt
├── secrets/
│   ├── app_secret.txt.example
│   └── app_secret.txt
├── registry/
│   ├── auth/htpasswd
│   └── certs/
│       ├── domain.crt
│       └── domain.key
├── scripts/
│   ├── generate-registry-assets.sh
│   ├── scan-image.sh
│   ├── push-registry.sh
│   └── verify-hardening.sh
└── reports/
```

## Kotak Script 1 — File `.env.example`

> **Nama file:** `.env.example`  
> **Lokasi:** `~/docker-lab/bab-8/.env.example`  
> **Buka editor:** `nano .env.example`

```dotenv
APP_IMAGE=pens-web:1.0
REGISTRY_HOST=localhost:5000
REGISTRY_USER=labpublisher
REGISTRY_PASSWORD=registrypass123
```

Aktifkan konfigurasi lokal:

```bash
cp .env.example .env
chmod 600 .env
```

Credential tersebut hanya untuk laptop lab. `.env` bukan secret manager dan nilainya tidak boleh digunakan pada lingkungan nyata.

## Kotak Script 2 — File `.gitignore`

> **Nama file:** `.gitignore`  
> **Lokasi:** `~/docker-lab/bab-8/.gitignore`  
> **Buka editor:** `nano .gitignore`

```gitignore
.env
secrets/*.txt
!secrets/*.txt.example
registry/auth/*
registry/certs/*
reports/*
!reports/.gitkeep
*.tar
*.log
```

Private key TLS, password hash, secret aktif, arsip image, dan laporan scanner dapat memuat informasi sensitif sehingga tidak dimasukkan ke repository.

## Kotak Script 3 — File `.dockerignore`

> **Nama file:** `.dockerignore`  
> **Lokasi:** `~/docker-lab/bab-8/.dockerignore`  
> **Buka editor:** `nano .dockerignore`

```dockerignore
.git
.gitignore
.env
secrets/
registry/
reports/
scripts/
compose.yaml
**/__pycache__/
**/*.py[cod]
**/*.log
**/*.tar
```

Karena build context pada Compose menggunakan root Bab 8, Dockerfile akan menyalin berkas aplikasi secara eksplisit dari `app/`. `.dockerignore` menjadi lapisan pencegahan tambahan agar secret tidak ikut terkirim ke builder.

## Kotak Script 4 — File `app/requirements.txt`

> **Nama file:** `requirements.txt`  
> **Lokasi:** `~/docker-lab/bab-8/app/requirements.txt`  
> **Buka editor:** `nano app/requirements.txt`

```text
Flask==3.1.3
gunicorn==26.2.0
```

Versi dipin agar build lebih dapat direproduksi. Untuk pipeline produksi, gunakan lock file beserta hash paket dan proses pembaruan dependency terjadwal.

## Kotak Script 5 — File `app/app.py`

> **Nama file:** `app.py`  
> **Lokasi:** `~/docker-lab/bab-8/app/app.py`  
> **Buka editor:** `nano app/app.py`

```python
import os
from pathlib import Path

from flask import Flask, jsonify


app = Flask(__name__)
SECRET_PATH = Path("/run/secrets/app_secret")
MIN_SECRET_BYTES = 32


def secret_ready() -> bool:
    """Secret siap bila dapat dibaca UID aplikasi dan cukup panjang."""
    try:
        return len(SECRET_PATH.read_bytes().strip()) >= MIN_SECRET_BYTES
    except OSError:
        return False


@app.get("/")
def index():
    return jsonify(
        service="pens-web",
        status="running",
        uid=os.getuid(),
        gid=os.getgid(),
        secret_ready=secret_ready(),
    )


@app.get("/health")
def health():
    if not secret_ready():
        return jsonify(status="degraded", reason="secret_unavailable"), 503
    return jsonify(status="ok"), 200
```

Aplikasi membaca secret untuk memastikan nilainya benar-benar tersedia bagi UID aplikasi, tetapi tidak pernah mengembalikan atau mencatat nilainya. Pemeriksaan `is_file()` saja tidak cukup: file dapat ada di `/run/secrets` tetapi tidak dapat dibaca karena mode file di host. Logging secret, hash secret, atau sebagian token tetap dapat memperluas informasi yang tersedia bagi penyerang.

## Kotak Script 6 — File `app/Dockerfile`

> **Nama file:** `Dockerfile`  
> **Lokasi:** `~/docker-lab/bab-8/app/Dockerfile`  
> **Buka editor:** `nano app/Dockerfile`

```dockerfile
# syntax=docker/dockerfile:1

FROM python:3.11.18-slim AS builder

ENV PIP_DISABLE_PIP_VERSION_CHECK=1 \
    PIP_NO_CACHE_DIR=1

WORKDIR /build

COPY app/requirements.txt ./requirements.txt

RUN python -m venv /opt/venv \
    && /opt/venv/bin/pip install --no-cache-dir --requirement requirements.txt


FROM python:3.11.18-slim AS runtime

ARG APP_UID=10001
ARG APP_GID=10001

ENV PATH="/opt/venv/bin:${PATH}" \
    PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

RUN groupadd --gid "${APP_GID}" appgroup \
    && useradd \
        --uid "${APP_UID}" \
        --gid "${APP_GID}" \
        --no-create-home \
        --shell /usr/sbin/nologin \
        appuser

WORKDIR /app

COPY --from=builder /opt/venv /opt/venv
COPY --chown=10001:10001 app/app.py ./app.py

USER 10001:10001

EXPOSE 8080

HEALTHCHECK --interval=10s --timeout=3s --start-period=5s --retries=3 \
    CMD ["python", "-c", "import urllib.request; urllib.request.urlopen('http://127.0.0.1:8080/health', timeout=2)"]

CMD ["gunicorn", "--bind=0.0.0.0:8080", "--workers=2", "--threads=2", "--worker-tmp-dir=/tmp", "--access-logfile=-", "--error-logfile=-", "app:app"]
```

Multi-stage build memisahkan tahap pemasangan dependency dari runtime. User numerik mengurangi ambiguitas pemetaan akun, tetapi base image dan dependency tetap harus dipindai serta diperbarui.

Tag versi patch, misalnya `3.11.18-slim`, berhenti dibangun ulang setelah rilis patch berikutnya. Sebelum kelas, verifikasi rilis patch Python 3.11 terbaru, catat digest base image, dan perbarui kedua baris `FROM` bila perlu. Tanpa langkah ini, security gate dapat berstatus `BLOCKED` karena paket OS pada image lama, dan `docker compose build --pull` tidak mengubah hasilnya.

## Kotak Script 7 — File `secrets/app_secret.txt.example`

> **Nama file:** `app_secret.txt.example`  
> **Lokasi:** `~/docker-lab/bab-8/secrets/app_secret.txt.example`  
> **Buka editor:** `nano secrets/app_secret.txt.example`

```text
GANTI_DENGAN_NILAI_ACAK_KHUSUS_LAB
```

Jangan menyalin nilai contoh sebagai secret aktif. Buat nilai acak:

```bash
chmod 700 secrets
openssl rand -hex 32 > secrets/app_secret.txt
chmod 444 secrets/app_secret.txt
```

Compose tanpa Swarm memasang secret berbasis file sebagai bind mount. Atribut `uid`, `gid`, dan `mode` pada service tidak diterapkan untuk sumber berupa file, sehingga mode file di host terbawa apa adanya ke `/run/secrets`. Mode `0600` milik akun host membuat UID 10001 di container tidak dapat membaca secret. Karena itu, file dibuat `0444` agar terbaca di container, sedangkan perlindungan terhadap akun lain di host diberikan oleh direktori induk `secrets/` bermode `0700`. Pendekatan ini sesuai untuk laptop lab satu pengguna; akun root host tetap dapat membaca secret.

## Kotak Script 8 — File `compose.yaml`

> **Nama file:** `compose.yaml`  
> **Lokasi:** `~/docker-lab/bab-8/compose.yaml`  
> **Buka editor:** `nano compose.yaml`  
> **Petunjuk:** gunakan spasi, bukan tab.

```yaml
services:
  app:
    build:
      context: .
      dockerfile: app/Dockerfile
    image: ${APP_IMAGE}
    user: "10001:10001"
    init: true
    read_only: true
    tmpfs:
      - /tmp:rw,noexec,nosuid,size=64m,mode=1777
    cap_drop:
      - ALL
    security_opt:
      - no-new-privileges:true
    pids_limit: 100
    cpus: 0.50
    mem_limit: 256m
    memswap_limit: 256m
    secrets:
      - app_secret
    ports:
      - "127.0.0.1:8088:8080"
    networks:
      - app-net
    healthcheck:
      test:
        - CMD
        - python
        - -c
        - "import urllib.request; urllib.request.urlopen('http://127.0.0.1:8080/health', timeout=2)"
      interval: 10s
      timeout: 3s
      retries: 3
      start_period: 5s
    restart: unless-stopped

  registry:
    image: registry:3.1.1
    environment:
      REGISTRY_HTTP_ADDR: 0.0.0.0:5000
      REGISTRY_HTTP_TLS_CERTIFICATE: /certs/domain.crt
      REGISTRY_HTTP_TLS_KEY: /certs/domain.key
      REGISTRY_AUTH: htpasswd
      REGISTRY_AUTH_HTPASSWD_REALM: DevSecOps Registry
      REGISTRY_AUTH_HTPASSWD_PATH: /auth/htpasswd
      REGISTRY_STORAGE_DELETE_ENABLED: "false"
      OTEL_TRACES_EXPORTER: none
    read_only: true
    tmpfs:
      - /tmp:rw,noexec,nosuid,size=32m
    cap_drop:
      - ALL
    security_opt:
      - no-new-privileges:true
    ports:
      - "127.0.0.1:5000:5000"
    volumes:
      - registry-data:/var/lib/registry
      - ./registry/certs/domain.crt:/certs/domain.crt:ro
      - ./registry/certs/domain.key:/certs/domain.key:ro
      - ./registry/auth/htpasswd:/auth/htpasswd:ro
    networks:
      - registry-net
    restart: unless-stopped

  trivy:
    image: aquasec/trivy:0.74.0
    profiles:
      - tools
    read_only: true
    tmpfs:
      - /tmp:rw,noexec,nosuid,size=64m
    volumes:
      - .:/workspace:ro
      - trivy-cache:/root/.cache
    security_opt:
      - no-new-privileges:true

secrets:
  app_secret:
    file: ./secrets/app_secret.txt

volumes:
  registry-data:
  trivy-cache:

networks:
  # Jangan memakai internal: true di sini. Docker tidak memasang port publish
  # untuk container yang hanya terhubung ke network internal.
  app-net: {}
  registry-net: {}
```

`cap_drop: ALL`, filesystem read-only, `no-new-privileges`, batas PID, CPU, memory, dan swap memperkecil blast radius. Kontrol tersebut harus diuji terhadap fungsi aplikasi; hardening yang membuat fungsi sah gagal bukan konfigurasi yang selesai.

Aplikasi dan registry tetap berada pada network terpisah sehingga keduanya tidak dapat saling menjangkau. Karena network tidak internal, keduanya memiliki akses jaringan keluar; port publish tetap hanya diikat ke `127.0.0.1`. Pembatasan egress memerlukan kontrol host atau platform dan dicatat sebagai residual risk.

Aset registry dipasang per file, bukan per direktori. Proses registry berjalan tanpa capability `DAC_OVERRIDE` sehingga tidak dapat menelusuri direktori host bermode `0700` milik akun lain; bind mount per file tidak memerlukan penelusuran tersebut. Konsekuensinya, penggantian file saat rotasi baru terlihat setelah container registry dibuat ulang.

## Kotak Script 9 — File `scripts/generate-registry-assets.sh`

> **Nama file:** `generate-registry-assets.sh`  
> **Lokasi:** `~/docker-lab/bab-8/scripts/generate-registry-assets.sh`  
> **Buka editor:** `nano scripts/generate-registry-assets.sh`  
> **Tujuan:** membuat sertifikat self-signed dengan SAN `localhost` dan akun registry menggunakan bcrypt.

```bash
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

: "${REGISTRY_USER:?REGISTRY_USER belum diatur}"
: "${REGISTRY_PASSWORD:?REGISTRY_PASSWORD belum diatur}"

command -v openssl >/dev/null || {
    echo "[FAIL] OpenSSL tidak tersedia." >&2
    exit 1
}

mkdir -p registry/certs registry/auth
umask 077

if [[ -e registry/certs/domain.key || -e registry/auth/htpasswd ]]; then
    echo "[FAIL] Aset registry sudah ada; rotasi harus dilakukan secara sadar." >&2
    exit 1
fi

openssl req \
    -newkey rsa:3072 \
    -nodes \
    -sha256 \
    -x509 \
    -days 365 \
    -keyout registry/certs/domain.key \
    -out registry/certs/domain.crt \
    -subj "/CN=localhost/O=DevSecOps Lab" \
    -addext "subjectAltName=DNS:localhost,IP:127.0.0.1" \
    -addext "extendedKeyUsage=serverAuth"

printf '%s\n' "$REGISTRY_PASSWORD" \
    | docker run --rm -i \
        --entrypoint htpasswd \
        httpd:2.4-alpine \
        -Bni "$REGISTRY_USER" \
    > registry/auth/htpasswd

grep -qF "${REGISTRY_USER}:\$2y\$" registry/auth/htpasswd || {
    echo "[FAIL] htpasswd tidak berisi hash bcrypt untuk $REGISTRY_USER." >&2
    exit 1
}

# Direktori 0700 menutup akses akun lain di host. File 0444 diperlukan karena
# registry berjalan tanpa capability DAC dan tidak dapat membaca file 0600
# milik akun host.
chmod 700 registry registry/certs registry/auth
chmod 644 registry/certs/domain.crt
chmod 444 registry/certs/domain.key registry/auth/htpasswd

echo "[PASS] Sertifikat dan htpasswd berhasil dibuat."
echo "[INFO] Sertifikat berlaku 365 hari untuk localhost."
```

Sertifikat self-signed hanya untuk pembelajaran. Produksi harus memakai nama DNS nyata, CA yang dipercaya, prosedur rotasi, dan perlindungan private key yang sesuai.

## Kotak Script 10 — File `scripts/scan-image.sh`

> **Nama file:** `scan-image.sh`  
> **Lokasi:** `~/docker-lab/bab-8/scripts/scan-image.sh`  
> **Buka editor:** `nano scripts/scan-image.sh`  
> **Tujuan:** menghasilkan laporan lengkap, SBOM CycloneDX, scan konfigurasi, serta gate untuk temuan HIGH/CRITICAL yang sudah memiliki perbaikan.

```bash
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

mkdir -p reports
archive_name="pens-web-1.0.tar"

# Identitas image yang dipindai; push-registry.sh menolak image dengan ID lain.
docker image inspect "$APP_IMAGE" --format '{{.Id}}' > reports/scanned-image-id.txt
docker image save --output "reports/$archive_name" "$APP_IMAGE"

run_trivy() {
    docker compose --profile tools run --rm --no-deps trivy "$@"
}

run_trivy --version > reports/trivy-version.txt

run_trivy image \
    --input "/workspace/reports/$archive_name" \
    --scanners vuln,secret \
    --image-config-scanners misconfig,secret \
    --format json \
    > reports/trivy-image.json

run_trivy image \
    --input "/workspace/reports/$archive_name" \
    --format cyclonedx \
    > reports/pens-web-1.0.cdx.json

# Trivy memeriksa Dockerfile, tetapi tidak memiliki pemeriksaan bawaan untuk
# Docker Compose. Konfigurasi Compose diuji melalui verify-hardening.sh.
run_trivy config \
    --severity MEDIUM,HIGH,CRITICAL \
    /workspace/app \
    > reports/trivy-config.txt

run_trivy fs \
    --scanners secret \
    /workspace/app \
    > reports/trivy-secret.txt

set +e
run_trivy image \
    --input "/workspace/reports/$archive_name" \
    --scanners vuln \
    --severity HIGH,CRITICAL \
    --ignore-unfixed \
    --exit-code 1 \
    > reports/trivy-gate.txt
gate_status=$?
set -e

if [[ "$gate_status" -eq 0 ]]; then
    printf 'PASS\n' > reports/gate-status.txt
    echo "[PASS] Security gate lulus."
else
    printf 'BLOCKED\n' > reports/gate-status.txt
    echo "[BLOCKED] Temuan HIGH/CRITICAL yang dapat diperbaiki terdeteksi." >&2
    echo "[INFO] Tinjau reports/trivy-gate.txt dan perbarui image." >&2
    exit 1
fi

sha256sum \
    reports/scanned-image-id.txt \
    reports/trivy-version.txt \
    reports/trivy-image.json \
    reports/pens-web-1.0.cdx.json \
    reports/trivy-config.txt \
    reports/trivy-secret.txt \
    reports/trivy-gate.txt \
    > reports/SHA256SUMS

echo "[PASS] Laporan, SBOM, dan checksum berhasil dibuat."
```

`--ignore-unfixed` hanya digunakan pada keputusan gate agar lab tidak berhenti pada temuan yang belum mempunyai perbaikan. Temuan tanpa perbaikan tetap tercatat pada `trivy-image.json` dan tetap membutuhkan triage, mitigasi, atau penerimaan risiko yang terdokumentasi.

Image yang dibangun lokal belum memiliki `RepoDigests` sebelum di-push. Karena itu, identitas image yang dipindai dicatat sebagai image ID (`.Id`). Registry digest baru tersedia setelah push dan dicatat oleh `push-registry.sh`.

Trivy sendiri juga merupakan dependency rantai pasok. Pada Maret 2026, image `aquasec/trivy` versi 0.69.4, 0.69.5, dan 0.69.6 serta tag `latest` pada periode tertentu diketahui memuat malware. Gunakan versi yang dipin, catat digest image scanner setelah diverifikasi, dan jangan memasang Docker socket ke container scanner.

## Kotak Script 11 — File `scripts/push-registry.sh`

> **Nama file:** `push-registry.sh`  
> **Lokasi:** `~/docker-lab/bab-8/scripts/push-registry.sh`  
> **Buka editor:** `nano scripts/push-registry.sh`

```bash
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
```

Tanpa credential helper, `docker login` menyimpan credential pada `~/.docker/config.json`; `trap` memastikan credential tersebut dihapus ketika script selesai atau gagal. Format `user = "..."` pada konfigurasi curl tidak mendukung tanda kutip ganda di dalam password, sehingga password lab hanya memakai huruf, angka, dan tanda hubung.

## Kotak Script 12 — File `scripts/verify-hardening.sh`

> **Nama file:** `verify-hardening.sh`  
> **Lokasi:** `~/docker-lab/bab-8/scripts/verify-hardening.sh`  
> **Buka editor:** `nano scripts/verify-hardening.sh`

```bash
#!/usr/bin/env bash
set -Eeuo pipefail

cd "$(dirname "$0")/.."

pass_count=0

pass() {
    echo "[PASS] $1"
    pass_count=$((pass_count + 1))
}

fail() {
    echo "[FAIL] $1" >&2
    exit 1
}

uid="$(docker compose exec -T app id -u)"
[[ "$uid" == "10001" ]] \
    && pass "Proses aplikasi berjalan sebagai UID 10001." \
    || fail "UID aplikasi adalah $uid."

# /app/app.py dimiliki UID 10001. Penulisan hanya ditolak bila rootfs read-only,
# sehingga uji ini membedakan read_only dari sekadar permission file.
ro_error="$(docker compose exec -T app sh -c 'touch /app/app.py 2>&1' || true)"
if [[ "$ro_error" == *"Read-only file system"* ]]; then
    pass "Penulisan ke filesystem root ditolak karena rootfs read-only."
else
    fail "Rootfs tidak read-only: ${ro_error:-penulisan berhasil}"
fi

docker compose exec -T app sh -c 'touch /tmp/allowed-write && rm /tmp/allowed-write' \
    && pass "tmpfs /tmp dapat digunakan aplikasi." \
    || fail "tmpfs /tmp tidak dapat digunakan."

cap_eff="$(
    docker compose exec -T app sh -c \
        "awk '/CapEff/ {print \$2}' /proc/1/status"
)"
[[ "$cap_eff" == "0000000000000000" ]] \
    && pass "Seluruh Linux capability efektif telah dihapus." \
    || fail "Capability efektif masih tersedia: $cap_eff"

no_new_privs="$(
    docker compose exec -T app sh -c \
        "awk '/NoNewPrivs/ {print \$2}' /proc/1/status"
)"
[[ "$no_new_privs" == "1" ]] \
    && pass "NoNewPrivs aktif." \
    || fail "NoNewPrivs tidak aktif."

seccomp_mode="$(
    docker compose exec -T app sh -c \
        "awk '/^Seccomp:/ {print \$2}' /proc/1/status"
)"
[[ "$seccomp_mode" == "2" ]] \
    && pass "Profil seccomp aktif (mode filter)." \
    || fail "Seccomp tidak aktif: mode $seccomp_mode."

docker compose exec -T app test -r /run/secrets/app_secret \
    && pass "Secret dapat dibaca UID aplikasi." \
    || fail "Secret tidak dapat dibaca UID aplikasi; periksa mode file di host."

if docker compose exec -T app env | grep -q '^APP_SECRET='; then
    fail "Secret ditemukan sebagai environment variable."
else
    pass "Secret tidak diekspos sebagai APP_SECRET."
fi

docker compose exec -T app test ! -S /var/run/docker.sock \
    && pass "Docker socket tidak tersedia di container aplikasi." \
    || fail "Docker socket terpasang ke container aplikasi."

container_id="$(docker compose ps -q app)"
read -r memory memory_swap nano_cpus pids readonly_root <<<"$(
    docker inspect "$container_id" \
        --format '{{.HostConfig.Memory}} {{.HostConfig.MemorySwap}} {{.HostConfig.NanoCpus}} {{.HostConfig.PidsLimit}} {{.HostConfig.ReadonlyRootfs}}'
)"

if (( memory > 0 && memory_swap == memory && nano_cpus > 0 && pids > 0 )) \
    && [[ "$readonly_root" == "true" ]]; then
    pass "Limit memory, swap, CPU, PID, dan read-only rootfs aktif."
else
    fail "Runtime limit tidak lengkap."
fi

app_ready="false"
for attempt in {1..30}; do
    if curl --fail --silent --show-error \
        http://127.0.0.1:8088/health >/dev/null 2>&1; then
        app_ready="true"
        break
    fi
    sleep 2
done

[[ "$app_ready" == "true" ]] \
    && pass "Health endpoint aplikasi merespons sukses." \
    || fail "Health endpoint aplikasi gagal."

unauth_code=""
for attempt in {1..30}; do
    unauth_code="$(
        curl --silent \
            --output /dev/null \
            --write-out '%{http_code}' \
            --cacert registry/certs/domain.crt \
            https://localhost:5000/v2/ \
            || true
    )"
    [[ "$unauth_code" == "401" ]] && break
    sleep 2
done
[[ "$unauth_code" == "401" ]] \
    && pass "Registry menolak akses anonim dengan HTTP 401." \
    || fail "Registry memberi status anonim $unauth_code."

# Klien tanpa CA lab harus menolak sertifikat self-signed (curl exit 60).
tls_rc=0
curl --silent --output /dev/null https://localhost:5000/v2/ || tls_rc=$?
[[ "$tls_rc" -eq 60 ]] \
    && pass "Klien tanpa CA lab menolak sertifikat registry." \
    || fail "Validasi sertifikat tidak berjalan sesuai harapan (curl exit $tls_rc)."

echo "[PASS] Total kontrol terverifikasi: $pass_count"
```

Pemeriksaan pada `/proc/1/status` membaca proses init container karena `init: true`. Proses aplikasi mewarisi user, capability, `NoNewPrivs`, dan seccomp yang sama; nilai `uid` pada response aplikasi menjadi evidence pelengkap.

## Kotak Perintah B — Izin Eksekusi dan Validasi Statis

```bash
chmod +x scripts/*.sh

bash -n scripts/generate-registry-assets.sh
bash -n scripts/scan-image.sh
bash -n scripts/push-registry.sh
bash -n scripts/verify-hardening.sh

python3 -m py_compile app/app.py
docker compose config --quiet
```

Validasi struktur Dockerfile dan Compose dengan Trivy dilakukan kembali setelah image dibangun karena database pemeriksaan Trivy dapat berubah.

## Kotak Perintah C — Membuat Secret, Sertifikat, dan Akun Registry

```bash
chmod 700 secrets
openssl rand -hex 32 > secrets/app_secret.txt
chmod 444 secrets/app_secret.txt
./scripts/generate-registry-assets.sh
```

Periksa mode akhir:

```bash
stat -c '%a %n' secrets secrets/app_secret.txt \
  registry registry/certs registry/auth \
  registry/certs/domain.crt registry/certs/domain.key registry/auth/htpasswd
```

Hasil yang diharapkan: direktori `700`, `domain.crt` `644`, serta `app_secret.txt`, `domain.key`, dan `htpasswd` `444`.

Periksa SAN dan masa berlaku sertifikat:

```bash
openssl x509 \
  -in registry/certs/domain.crt \
  -noout \
  -subject \
  -issuer \
  -dates \
  -ext subjectAltName
```

## Kotak Perintah D — Memahami Validasi TLS pada Docker Engine

Docker Engine memperlakukan registry pada `127.0.0.0/8` dan `::1/128` sebagai insecure secara default. Untuk registry insecure, Engine tetap mencoba HTTPS tetapi mengabaikan kesalahan sertifikat. Periksa konfigurasi efektif:

```bash
docker info --format '{{json .RegistryConfig.InsecureRegistryCIDRs}}'
```

Bila keluaran memuat `127.0.0.0/8`, push dan pull ke `localhost:5000` **bukan** bukti bahwa Docker memvalidasi sertifikat registry. Pada lab ini, validasi TLS dibuktikan dengan dua uji klien: `curl --cacert registry/certs/domain.crt` berhasil, dan `curl` tanpa CA lab gagal dengan exit code 60. Kedua uji dijalankan oleh `verify-hardening.sh`. Karena itu, lab ini tidak memerlukan penyalinan CA ke trust store Docker maupun restart daemon.

Untuk registry dengan nama DNS nyata, misalnya `registry.lab.example:5000`, Engine memvalidasi sertifikat. CA ditempatkan pada `/etc/docker/certs.d/<host:port>/ca.crt` untuk Engine native, atau `~/.config/docker/certs.d/<host:port>/ca.crt` untuk Engine rootless. Untuk Docker Desktop, ikuti panduan sertifikat Docker Desktop sesuai sistem operasi. Restart daemon menghentikan atau memengaruhi container lain; lakukan secara terencana.

## Kotak Perintah E — Build dan Menjalankan Runtime yang Diperkeras

```bash
docker compose build --pull app
docker compose up -d app registry
docker compose ps
```

Verifikasi response aplikasi:

```bash
curl --fail --silent --show-error \
  http://127.0.0.1:8088/ \
  | python3 -m json.tool
```

Output harus menunjukkan `uid` dan `gid` bernilai `10001`, serta `secret_ready` bernilai `true`. Bila `secret_ready` bernilai `false`, periksa mode `secrets/app_secret.txt` pada Kotak Perintah C sebelum mengubah konfigurasi lain.

## Kotak Perintah F — Menjalankan Negative Test Hardening

```bash
./scripts/verify-hardening.sh
```

Periksa konfigurasi runtime efektif sebagai evidence tambahan:

```bash
docker inspect "$(docker compose ps -q app)" \
  --format '{{json .HostConfig}}' \
  > reports/app-hostconfig.json

docker image inspect pens-web:1.0 \
  --format '{{json .Config}}' \
  > reports/app-image-config.json
```

## Kotak Perintah G — Trivy, SBOM, dan Security Gate

```bash
./scripts/scan-image.sh
```

Periksa status gate dan checksum:

```bash
cat reports/gate-status.txt
cat reports/trivy-version.txt
cat reports/scanned-image-id.txt
sha256sum --check reports/SHA256SUMS
```

Jika gate berstatus `BLOCKED`, jangan mengubah status secara manual. Perbarui base image atau dependency, bangun ulang image, dokumentasikan triage, lalu ulangi pemindaian.

## Kotak Perintah H — Menguji dan Mengisi Private Registry

Sebelum login, buktikan bahwa endpoint anonim ditolak:

```bash
curl --silent \
  --output /dev/null \
  --write-out 'HTTP %{http_code}\n' \
  --cacert registry/certs/domain.crt \
  https://localhost:5000/v2/
```

Hasil yang diharapkan adalah `HTTP 401`. Setelah gate lulus:

```bash
./scripts/push-registry.sh
```

Registry API tetap memakai path `/v2/` karena Distribution Registry 3 mempertahankan kompatibilitas Docker Registry HTTP API V2.

## Kotak Perintah I — Membuktikan Secret Tidak Masuk Image

Cari nilai secret aktif pada history dan filesystem image. Nilai dibaca dari file dan dikirim melalui stdin sehingga tidak muncul pada argumen perintah:

```bash
docker history --no-trunc pens-web:1.0 > reports/docker-history.txt

if grep -qF -f secrets/app_secret.txt reports/docker-history.txt; then
  echo "[FAIL] Nilai secret ditemukan pada history image."
else
  echo "[PASS] Nilai secret tidak ditemukan pada history image."
fi

docker run --rm -i \
  --network none \
  --entrypoint sh \
  pens-web:1.0 \
  -c 'read -r s
      if grep -rqsF -- "$s" /app /opt /etc /usr/local; then
        echo "[FAIL] Nilai secret ditemukan pada filesystem image."; exit 1
      fi
      echo "[PASS] Nilai secret tidak ditemukan pada filesystem image."' \
  < secrets/app_secret.txt
```

PASS membuktikan nilai secret aktif tidak tertanam pada history image maupun direktori aplikasi, dependency, dan konfigurasi. Uji ini tidak mencakup file yang tidak dapat dibaca UID 10001 dan belum membuktikan seluruh riwayat build bebas secret; laporan secret scanner dan audit build context tetap diperlukan.

## Tabel Verifikasi PASS/FAIL

| No. | Kontrol | Evidence yang sahih | PASS | FAIL |
|---:|---|---|---|---|
| 1 | User non-root | `id -u` dan response aplikasi | UID `10001` | UID `0`/tidak sesuai |
| 2 | Read-only rootfs | Negative test `touch /app/app.py` pada file milik UID 10001 | Galat `Read-only file system` | Berhasil menulis atau galat lain |
| 3 | Writable path terkontrol | File sementara pada `/tmp` | Berhasil dan dapat dihapus | Aplikasi tidak dapat memakai `/tmp` |
| 4 | Capability | `CapEff` pada `/proc/1/status` | Seluruh bit nol | Masih ada capability |
| 5 | Privilege escalation | `NoNewPrivs` | Nilai `1` | Nilai `0` |
| 6 | Seccomp | `Seccomp` pada `/proc/1/status` | Nilai `2` | Nilai `0` |
| 7 | Secret injection | `test -r` dan `secret_ready` | Terbaca UID 10001; tidak ada `APP_SECRET` | Tidak terbaca, hilang, atau berada di env |
| 8 | Docker socket | Pemeriksaan socket | Tidak tersedia | Socket terpasang |
| 9 | Resource limit | `docker inspect` | Memory, CPU, PID terbatas; swap sama dengan memory | Salah satu tidak dibatasi |
| 10 | Healthcheck | `docker compose ps` dan `/health` | `healthy`, HTTP 200 | `unhealthy`/non-200 |
| 11 | Scan lengkap | Laporan JSON, konfigurasi, secret, SBOM, versi Trivy | Artefak ada dan checksum valid | Laporan hilang/tidak konsisten |
| 12 | Security gate | `gate-status.txt` dan `scanned-image-id.txt` | `PASS`; image ID sama saat push | `BLOCKED` atau image berubah |
| 13 | TLS registry | `curl` dengan dan tanpa CA lab | Dengan CA berhasil; tanpa CA exit 60 | Tanpa CA berhasil atau dengan CA gagal |
| 14 | Authentication | Request `/v2/` anonim | HTTP 401 | HTTP 200 anonim |
| 15 | Distribusi | Push, pull, image ID, katalog, dan digest | Image hasil pull identik dengan image yang dipindai | Push/pull/query gagal atau ID berbeda |
| 16 | Secret tidak tertanam | Kotak Perintah I | Nilai tidak ditemukan | Nilai ditemukan |

## Troubleshooting dan Analisis Hasil

| Gejala | Diagnosis yang mungkin | Pemeriksaan | Tindakan korektif |
|---|---|---|---|
| Build gagal saat memasang dependency | Tag base image, jaringan, atau versi paket tidak tersedia | Log BuildKit; PyPI; tag image | Verifikasi versi resmi, jaringan, dan bangun ulang tanpa memasukkan secret |
| `curl 127.0.0.1:8088` atau push ke `localhost:5000` gagal walaupun container `Up` | Service hanya terhubung ke network `internal: true` sehingga port tidak dipasang | `docker compose config`; `docker port <container>` | Hubungkan service yang dipublikasikan ke network non-internal |
| Aplikasi `unhealthy` | Secret belum dibuat, tidak terbaca UID 10001, atau `/tmp` tidak dapat ditulis | `docker compose logs app`; `stat -c '%a' secrets/app_secret.txt`; inspect health | Buat secret dengan mode `0444` di direktori `0700`, verifikasi tmpfs, dan uji endpoint dari dalam container |
| `permission denied` pada aplikasi | User non-root membutuhkan direktori tulis yang belum disediakan | Log aplikasi; `id`; mount efektif | Tambahkan tmpfs/volume pada jalur paling sempit; jangan mengubah container menjadi root |
| Trivy tidak menemukan image | Image belum dibangun atau nama berbeda | `docker image ls`; `.env` | Bangun image dan verifikasi `APP_IMAGE` |
| Gate berubah tanpa perubahan image | Database vulnerability Trivy diperbarui | Simpan versi Trivy, waktu, digest, dan laporan | Lakukan triage ulang; image yang sama dapat memperoleh temuan baru |
| Trivy kehabisan waktu saat pertama kali | Database scanner sedang diunduh | Log Trivy; konektivitas registry database | Ulangi setelah cache tersedia; jangan memakai database usang tanpa mencatatnya |
| Registry gagal startup dengan `permission denied` | `domain.key` atau `htpasswd` bermode `0600`, atau direktori dipasang alih-alih file | `docker compose logs registry`; `stat -c '%a %n' registry/*/*` | Gunakan mode `0444` di direktori `0700` dan bind mount per file |
| Registry gagal startup karena konfigurasi | `htpasswd` bukan bcrypt atau TLS salah | `docker compose logs registry` | Buat ulang aset secara sadar dan periksa path mount |
| `curl --cacert` gagal `SSL certificate problem` | Path CA salah atau SAN tidak memuat `localhost` | `openssl x509 -noout -ext subjectAltName` | Perbaiki path atau buat ulang sertifikat; Docker Engine sendiri mengabaikan galat sertifikat untuk `localhost` |
| Push ditolak karena image berubah | Image dibangun ulang setelah dipindai | `docker image inspect --format '{{.Id}}'`; `reports/scanned-image-id.txt` | Jalankan ulang `scan-image.sh` sebelum push |
| Registry memberi HTTP 200 tanpa login | Autentikasi tidak termuat | Log registry; environment efektif; file htpasswd | Hentikan registry dan perbaiki `REGISTRY_AUTH*`; jangan lanjutkan push |
| Push ditolak script | Gate belum `PASS` | `reports/gate-status.txt`; laporan gate | Perbarui image atau dependency; jangan mengedit status manual |
| Memory limit tampak tidak bekerja | Perbedaan dukungan cgroup/WSL 2 | `docker info`; inspect; metric Bab 7 | Catat platform dan uji pada host Linux bila validasi kernel penuh diperlukan |
| Docker Bench menghasilkan banyak temuan | Benchmark memeriksa host, bukan hanya aplikasi | Tinjau scope dan evidence setiap kontrol | Triage per kontrol; jangan menyamakan seluruh warning dengan exploit yang terkonfirmasi |

## Catatan Keamanan Windows dan Linux

- Pada Windows, jalankan perintah Bash melalui WSL 2. Docker Desktop menjalankan Linux containers di mesin virtual; bukti limit resource harus ditafsirkan terhadap VM tersebut.
- Lokasi trust store Docker berbeda antara Engine native, Engine rootless, dan Docker Desktop. Menyalin CA hanya ke browser tidak otomatis membuat Docker daemon mempercayainya. Untuk `localhost`, daemon tidak memvalidasi sertifikat sama sekali (Kotak Perintah D).
- Simpan direktori lab pada filesystem WSL, misalnya `~/docker-lab`, bukan `/mnt/c/...`. Pada filesystem Windows, `chmod` dapat tidak berpengaruh sehingga mode `0700` dan `0444` tidak dapat dijamin.
- Keanggotaan grup `docker`, akses Docker Desktop, atau akses ke Docker socket memberi kemampuan administratif yang kuat. Praktikum harus memakai laptop lab atau akun yang sesuai kebijakan institusi.
- Default seccomp Docker sengaja tidak dinonaktifkan. Kustomisasi profil hanya dilakukan setelah kebutuhan syscall diukur dan diuji.

## Kotak Perintah J — Cleanup

Menghentikan service tanpa menghapus registry:

```bash
docker compose --profile tools down --remove-orphans
```

Menghapus container, network, registry, dan cache Trivy:

```bash
docker compose --profile tools down --volumes --remove-orphans
```

Perintah kedua menghapus artefak pada volume registry. Laporan di direktori `reports/` tetap berada pada host, tetapi dapat memuat informasi keamanan dan harus dilindungi.

Apabila sertifikat lab tidak lagi digunakan, hapus CA dari trust store Docker sesuai platform dan restart Docker secara terencana.

## Latihan Mandiri

1. Tambahkan negative test yang mencoba membuat lebih dari 100 proses dan analisis perilaku `pids_limit` tanpa membuat host tidak stabil.
2. Bandingkan hasil Trivy ketika `--ignore-unfixed` dipakai dan tidak dipakai. Jelaskan risiko menerima temuan tanpa perbaikan.
3. Buat dependency lock dengan hash dan ukur perubahan reproduktibilitas build.
4. Catat digest base image dan image aplikasi. Jelaskan perbedaan jaminan tag dengan digest.
5. Rancang prosedur rotasi password registry dan sertifikat tanpa kehilangan image yang tersimpan.
6. Tambahkan akun registry kedua dan jelaskan mengapa autentikasi basic bawaan belum menyediakan otorisasi repository yang granular.
7. Jalankan Docker Bench for Security dari sumber resmi yang telah diverifikasi. Pisahkan temuan host, daemon, image, dan runtime.
8. Susun dokumen exception untuk satu CVE yang belum dapat diperbaiki: cantumkan owner, alasan, mitigasi, masa berlaku, dan bukti persetujuan.
9. Ubah sementara `app-net` menjadi `internal: true`, jalankan ulang aplikasi, dan buktikan bahwa port `8088` tidak lagi dipasang. Rancang kontrol egress pengganti yang tetap memungkinkan port publish.
10. Ubah mode `secrets/app_secret.txt` menjadi `0600`, buat ulang container aplikasi, lalu jelaskan hasil `verify-hardening.sh` dan `/health`. Mengapa `is_file()` tidak cukup sebagai bukti secret tersedia?

## Rujukan Utama

1. [NIST SP 800-190 — Application Container Security Guide](https://csrc.nist.gov/pubs/sp/800/190/final).
2. [Docker — Building best practices](https://docs.docker.com/build/building/best-practices/).
3. [Docker — Resource constraints](https://docs.docker.com/engine/containers/resource_constraints/).
4. [Docker — Seccomp profiles](https://docs.docker.com/engine/security/seccomp/).
5. [Docker — Manage secrets in Compose](https://docs.docker.com/compose/how-tos/use-secrets/).
6. [Docker — Verify registry certificates](https://docs.docker.com/engine/security/certificates/).
7. [CNCF Distribution — Deploy a registry](https://distribution.github.io/distribution/about/deploying/).
8. [CNCF Distribution — Registry configuration](https://distribution.github.io/distribution/about/configuration/).
9. [Trivy — Container image scanning](https://trivy.dev/docs/latest/guide/target/container_image/).
10. [Trivy — Exit code and scanners](https://trivy.dev/docs/latest/guide/configuration/others/).
11. [OWASP Docker Security Cheat Sheet](https://cheatsheetseries.owasp.org/cheatsheets/Docker_Security_Cheat_Sheet.html).
12. [Compose Specification — Services: configs dan secrets](https://compose-spec.github.io/compose-spec/05-services.html).
13. [Docker Engine API — RegistryServiceConfig (insecure registry default)](https://docs.docker.com/reference/api/engine/version/v1.57/schemas/RegistryServiceConfig/).
14. [moby/moby #36174 — Container pada network internal tidak dapat mempublikasikan port](https://github.com/moby/moby/issues/36174).
15. [GHSA-69fq-xp46-6x23 — Trivy ecosystem supply chain compromise](https://github.com/aquasecurity/trivy/security/advisories/GHSA-69fq-xp46-6x23).

Versi scanner, database vulnerability, base image, dan dependency berubah dari waktu ke waktu. Sebelum kelas dimulai, verifikasi tag, simpan digest image, dan jalankan seluruh negative test pada platform yang akan digunakan mahasiswa.
