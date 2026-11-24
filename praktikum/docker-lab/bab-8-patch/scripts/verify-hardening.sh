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
