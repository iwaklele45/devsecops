# Laporan Praktikum Bab 3 — Docker Network, Volume, Bind Mount, tmpfs, dan Compose

> **Lampiran Dokumen PDF:** [LAPORAN WORKSHOP DevOps M1 Bab 3.pdf](./docker-lab/bab-3/LAPORAN%20WORKSHOP%20DevOps%20M1%20Bab%203.pdf)

<object data="./docker-lab/bab-3/LAPORAN%20WORKSHOP%20DevOps%20M1%20Bab%203.pdf" type="application/pdf" width="100%" height="600px">
  <p>Pratinjau PDF tidak didukung oleh viewer. Buka tautan file: <a href="./docker-lab/bab-3/LAPORAN%20WORKSHOP%20DevOps%20M1%20Bab%203.pdf">LAPORAN WORKSHOP DevOps M1 Bab 3.pdf</a>.</p>
</object>

## Bukti Eksekusi Praktikum

```text
# rafiputra@Rafis-MacBook-Pro bab-3 % pwd
/Users/rafiputra/Code/Learn/devsecops/praktikum/docker-lab/bab-3

# rafiputra@Rafis-MacBook-Pro bab-3 % docker network create --driver bridge --subnet 172.20.0.0/16 lab-net
f7e1089b333b2d82151ce87555b2aa6f6413905c9110f15437b94d3727446a35

# rafiputra@Rafis-MacBook-Pro bab-3 % docker run -d --name server-a --network lab-net nginx:alpine        
Unable to find image 'nginx:alpine' locally
alpine: Pulling from library/nginx
badda8760139: Pull complete 
1791812138bb: Pull complete 
accee44535cd: Pull complete 
9592924c961c: Pull complete 
d6c1262595ab: Pull complete 
853498d24c3c: Pull complete 
2123acec2175: Pull complete 
a855f9d558c0: Download complete 
c4f99b055a72: Download complete 
Digest: sha256:72ba65eb42c10344912a84ff42408db7d34f2feb642204570ab8fc5ffd29f1d3
Status: Downloaded newer image for nginx:alpine
34673ac001be799dc64d2c6d92f3ff5a20c3b0f02e63f5a8e8b5c728345e0fae

# rafiputra@Rafis-MacBook-Pro bab-3 % docker run -d --name server-b --network lab-net nginx:alpine
8cd7de70867483f28afa49ec728fbbff486464d85899612cb2d140a87e99a4ee

# rafiputra@Rafis-MacBook-Pro bab-3 % docker exec server-a ping -c 3 server-b                     
PING server-b (172.20.0.3): 56 data bytes
64 bytes from 172.20.0.3: seq=0 ttl=64 time=0.184 ms
64 bytes from 172.20.0.3: seq=1 ttl=64 time=0.136 ms
64 bytes from 172.20.0.3: seq=2 ttl=64 time=0.188 ms

--- server-b ping statistics ---
3 packets transmitted, 3 packets received, 0% packet loss
round-trip min/avg/max = 0.136/0.169/0.188 ms

# rafiputra@Rafis-MacBook-Pro bab-3 % docker volume create data-vol          
data-vol

# rafiputra@Rafis-MacBook-Pro bab-3 % docker run -d --name writer -v data-vol:/app/data alpine:3.20   sh -c "while true; do date >> /app/data/log.txt; sleep 5; done"
Unable to find image 'alpine:3.20' locally
3.20: Pulling from library/alpine
3f26bc2dec0b: Pull complete 
cee42a41056b: Download complete 
8b093306b817: Download complete 
Digest: sha256:d9e853e87e55526f6b2917df91a2115c36dd7c696a35be12163d44e6e2a4b6bc
Status: Downloaded newer image for alpine:3.20
255fd196f1174e022edf34889348aaf31aab19f0835af2fc6d8f640d5378df00

# rafiputra@Rafis-MacBook-Pro bab-3 % sleep 15                                                   
rafiputra@Rafis-MacBook-Pro bab-3 % docker rm -f writer                                                                                                            
writer

# rafiputra@Rafis-MacBook-Pro bab-3 % docker run --rm -v data-vol:/data alpine:3.20 cat /data/log.txt                                                                
Mon Sep  7 16:42:26 UTC 2026
Mon Sep  7 16:42:31 UTC 2026
Mon Sep  7 16:42:36 UTC 2026
Mon Sep  7 16:42:41 UTC 2026
Mon Sep  7 16:42:46 UTC 2026
Mon Sep  7 16:42:51 UTC 2026
Mon Sep  7 16:42:56 UTC 2026
Mon Sep  7 16:43:01 UTC 2026

# rafiputra@Rafis-MacBook-Pro bab-3 % docker run --rm -v data-vol:/source:ro -v $(pwd):/backup alpine:3.20   tar czf /backup/data-vol-backup.tar.gz -C /source .

# compose 
rafiputra@Rafis-MacBook-Pro bab-3 % docker compose up -d 
[+] up 13/13
 ✔ Image postgres:16-alpine Pulled                                                                                                                                                                         15.6s
[+] Building 0.1s (1/1) FINISHED                                                                                                                                                                                
[+] up 13/14l] load local bake definitions                                                                                                                                                                 0.0s
 ✔ Image postgres:16-alpine Pulled                                                                                                                                                                         15.6s
 ⠙ Image bab-3-app          Building                                                                                                                                                                        0.2s
unable to prepare context: path "/Users/rafiputra/Code/Learn/devsecops/praktikum/docker-lab/bab-3/app" not found

rafiputra@Rafis-MacBook-Pro bab-3 % docker compose up -d 
[+] Building 0.2s (2/2) FINISHED                                                                                                                                          
 => [internal] load local bake definitions                                                                                                                           0.0s
 => => reading from stdin 572B                                                                                                                                       0.0s
 => [internal] load build definition from Dockerfile                                                                                                                 0.0s
 => => transferring dockerfile: 2B                                                                                                                                   0.0s
[+] up 0/1
 ⠙ Image bab-3-app Building                                                                                                                                           0.3s
failed to solve: failed to read dockerfile: open Dockerfile: no such file or directory



View build details: docker-desktop://dashboard/build/default/default/o4sjp5cciw3n3bnj75x7bapym

rafiputra@Rafis-MacBook-Pro bab-3 % docker ps            
CONTAINER ID   IMAGE          COMMAND                  CREATED          STATUS          PORTS     NAMES
8cd7de708674   nginx:alpine   "/docker-entrypoint.…"   13 minutes ago   Up 13 minutes   80/tcp    server-b
34673ac001be   nginx:alpine   "/docker-entrypoint.…"   13 minutes ago   Up 13 minutes   80/tcp    server-a
rafiputra@Rafis-MacBook-Pro bab-3 % docker compose up -d --build
[+] Building 0.3s (2/2) FINISHED                                                                                                                                          
 => [internal] load local bake definitions                                                                                                                           0.0s
 => => reading from stdin 572B                                                                                                                                       0.0s
 => [internal] load build definition from Dockerfile                                                                                                                 0.0s
 => => transferring dockerfile: 2B                                                                                                                                   0.0s
[+] up 0/1
 ⠙ Image bab-3-app Building                                                                                                                                           0.3s
failed to solve: failed to read dockerfile: open Dockerfile: no such file or directory



View build details: docker-desktop://dashboard/build/default/default/bs3hartrxacjre1zh083hoc8m

rafiputra@Rafis-MacBook-Pro bab-3 % 
rafiputra@Rafis-MacBook-Pro bab-3 % docker compose up -d --build
[+] Building 0.2s (2/2) FINISHED                                                                                                                                          
 => [internal] load local bake definitions                                                                                                                           0.0s
 => => reading from stdin 572B                                                                                                                                       0.0s
 => [internal] load build definition from Dockerfile                                                                                                                 0.0s
 => => transferring dockerfile: 2B                                                                                                                                   0.0s
[+] up 0/1
 ⠙ Image bab-3-app Building                                                                                                                                           0.3s
failed to solve: failed to read dockerfile: open Dockerfile: no such file or directory



View build details: docker-desktop://dashboard/build/default/default/8h1rltz37kijpbjlptx1ft6jt

rafiputra@Rafis-MacBook-Pro bab-3 % docker compose up -d        
[+] Building 0.1s (2/2) FINISHED                                                                                                                                          
 => [internal] load local bake definitions                                                                                                                           0.0s
 => => reading from stdin 572B                                                                                                                                       0.0s
 => [internal] load build definition from Dockerfile                                                                                                                 0.0s
 => => transferring dockerfile: 2B                                                                                                                                   0.0s
[+] up 0/1
 ⠙ Image bab-3-app Building                                                                                                                                           0.2s
failed to solve: failed to read dockerfile: open Dockerfile: no such file or directory

# rafiputra@Rafis-MacBook-Pro bab-3 % docker ps                   
CONTAINER ID   IMAGE                COMMAND                  CREATED          STATUS                    PORTS                                     NAMES
ad14e597bd49   nginx:alpine         "/docker-entrypoint.…"   10 seconds ago   Up 4 seconds              0.0.0.0:8080->80/tcp, [::]:8080->80/tcp   bab-3-web-1
2c4ab12eddf7   bab-3-app            "gunicorn --bind 0.0…"   11 seconds ago   Up 5 seconds              5000/tcp                                  bab-3-app-1
4a1c2efb70ea   postgres:16-alpine   "docker-entrypoint.s…"   11 seconds ago   Up 10 seconds (healthy)   5432/tcp                                  bab-3-db-1
8cd7de708674   nginx:alpine         "/docker-entrypoint.…"   24 minutes ago   Up 24 minutes             80/tcp                                    server-b
34673ac001be   nginx:alpine         "/docker-entrypoint.…"   25 minutes ago   Up 25 minutes             80/tcp                                    server-a

# rafiputra@Rafis-MacBook-Pro bab-3 % curl -i localhost:8080
HTTP/1.1 200 OK
Server: nginx/1.27.4
Date: Mon, 07 Sep 2026 17:16:32 GMT
Content-Type: application/json
Content-Length: 174
Connection: keep-alive

{
  "database": "PostgreSQL 16.8 on aarch64-unknown-linux-musl, compiled by gcc (Alpine 14.2.0) 14.2.0, 64-bit",
  "message": "Nginx, Flask, dan PostgreSQL berhasil terhubung",
  "status": "ok"
}

# rafiputra@Rafis-MacBook-Pro bab-3 % docker compose logs
bab-3-db-1   | 2026-09-07 17:15:35.340 UTC [1] LOG:  starting PostgreSQL 16.8 on aarch64-unknown-linux-musl...
bab-3-db-1   | 2026-09-07 17:15:35.405 UTC [1] LOG:  database system is ready to accept connections
bab-3-app-1  | [2026-09-07 17:15:47 +0000] [1] [INFO] Starting gunicorn 23.0.0
bab-3-app-1  | [2026-09-07 17:15:47 +0000] [1] [INFO] Listening at: http://0.0.0.0:5000 (1)
bab-3-app-1  | [2026-09-07 17:15:47 +0000] [1] [INFO] Using worker: sync
bab-3-app-1  | [2026-09-07 17:15:47 +0000] [7] [INFO] Booting worker with pid: 7
bab-3-app-1  | [2026-09-07 17:15:47 +0000] [8] [INFO] Booting worker with pid: 8
bab-3-web-1  | 2026/09/07 17:15:52 [notice] 1#1: start worker processes
bab-3-web-1  | 172.22.0.1 - - [07/Sep/2026:17:16:32 +0000] "GET / HTTP/1.1" 200 174 "-" "curl/8.7.1"
```

## Evaluasi dan Latihan Mandiri

1. **Mengapa user-defined bridge lebih baik daripada default bridge untuk multi-container app?**
   User-defined bridge menyediakan keunggulan isolasi, resolusi, dan keamanan dibandingkan default bridge:
   - **Automatic DNS Resolution:** Container dalam user-defined bridge dapat saling berkomunikasi secara langsung menggunakan nama container atau nama service (misal `app:5000` atau `db:5432`) tanpa perlu mengelola atau mencatat IP dinamis. Sebaliknya, default bridge tidak menyediakan DNS internal bawaan dan hanya mendukung flag `--link` yang sudah deprecated.
   - **Isolasi Jaringan yang Lebih Baik:** Seluruh container tanpa jaringan khusus akan otomatis masuk ke default bridge sehingga saling berbagi collision/broadcast domain. User-defined bridge mengisolasi kelompok container aplikasi secara terpisah, mempersempit *blast radius* bila terjadi insiden keamanan.
   - **Konfigurasi Spesifik dan Portabilitas:** Subnet, gateway, MTU, dan opsi interface bridge dapat dikonfigurasi secara spesifik per stack aplikasi.

2. **Apa risiko bind mount terhadap keamanan host?**
   Bind mount memetakan file atau direktori dari sistem operasi host langsung ke dalam filesystem container dengan izin baca-tulis (*read-write*) secara default. Risiko keamanannya meliputi:
   - **Host Tampering dan Container Breakout:** Jika proses di container berjalan sebagai user root atau dieksploitasi lewat celah aplikasi, penyerang dapat mengubah atau menghapus berkas penting host (misalnya `/etc/passwd`, `/var/run/docker.sock`, atau kode program host).
   - **File Shadowing / Masking:** Me-mount direktori host ke path container yang telah memiliki berkas esensial akan menutupi berkas container asli, sehingga berisiko memicu kerusakan fungsi aplikasi.
   - **Ketergantungan Path Absolut:** Keterikatan struktur path host mengurangi portabilitas deployment lintas sistem.
   *Mitigasi:* Selalu gunakan penanda `:ro` (*read-only*) untuk berkas konfigurasi statis, atau prioritaskan *named volume* yang terisolasi di area kelolaan Docker engine.

3. **Apa perbedaan docker compose down dan docker compose down -v?**
   - **`docker compose down`**: Menghentikan dan menghapus semua container, network default, dan image temporer yang dibuat oleh Compose stack, tetapi **tetap mempertahankan** seluruh named volume (seperti `pg-data`). Data persisten database tetap utuh dan aman saat stack dijalankan kembali.
   - **`docker compose down -v`** (atau `--volumes`): Menghentikan serta menghapus container dan network, sekaligus **menghapus permanen seluruh named volume** yang dideklarasikan di dalam file Compose. Perintah ini memicu kehilangan data permanen (*total data loss*) pada direktori data PostgreSQL (`/var/lib/postgresql/data`).

4. **Kapan depends_on dengan healthcheck lebih tepat daripada depends_on biasa?**
   `depends_on` standar hanya memastikan bahwa container dependensi telah mencapai status *started* (proses PID telah aktif di level OS). Pada service database seperti PostgreSQL, daemon database masih membutuhkan waktu beberapa detik untuk inisialisasi berkas data (*catalog initialization*), memulihkan WAL, dan membuka socket listening TCP port 5432.
   Jika container backend aplikasi (`app`) langsung berjalan saat database baru berstatus *started*, koneksi awal aplikasi akan ditolak (*connection refused crash-loop*). Penggunaan `depends_on` dengan `condition: service_healthy` yang dipadukan dengan probe readiness (seperti `pg_isready -U labuser -d labdb`) menjamin container aplikasi baru dijalankan setelah database benar-benar siap menerima kueri secara fungsional.

5. **Bagaimana strategi backup volume untuk database produksi?**
   Strategi pencadangan volume database produksi berbasis container mencakup:
   - **Application-Consistent Logical Dump:** Menjalankan dump terjadwal dari dalam container atau via cron container pembantu menggunakan utilitas native (contoh: `docker exec db pg_dump -U labuser labdb | gzip > backup.sql.gz`) untuk menjamin konsistensi data transaksi tanpa mengunci database secara agresif.
   - **Volume Snapshotting & Archiving:** Memanfaatkan container utilitas sementara dengan mount read-only (`:ro`) untuk mengompresi isi volume (`tar -czf`) saat aktivitas database minimal, atau menggunakan snapshot penyimpanan level storage/CSI driver (EBS/GCP Persistent Disk).
   - **Offsite Replikasi & Immutable Retention:** Menyalin artefak backup terenkripsi ke object storage terpisah (AWS S3 / GCS) dengan kebijakan versioning dan WORM (*Write Once Read Many*) serta memverifikasi prosedur pemulihan (*restore drill*) secara rutin.

---

## Laporan Praktikum dan Analisis Wajib

### 1. Masalah yang Dihadapi dan Diagnosis

- **Sintaks Kesalahan:**
  ```text
  unable to prepare context: path "/.../bab-3/app" not found
  failed to solve: failed to read dockerfile: open Dockerfile: no such file or directory
  ```
- **Diagnosis:**
  File `docker-compose.yaml` mendefinisikan build direktori lokal `./app` untuk service `app`. Namun pada direktori kerja, folder `./app` belum memiliki `Dockerfile`, kode sumber Flask (`app.py`), dan `requirements.txt`. Selain itu, reverse proxy Nginx memerlukan berkas `nginx.conf` dan `html/index.html` untuk bind mount `:ro`, serta terdapat galat tipografi `POSTGRESS_DB` (seharusnya `POSTGRES_DB`).
- **Tindakan Korektif:**
  1. Membuat direktori `app/` beserta `Dockerfile` berbasis `python:3.12-slim` dengan non-root user `appuser`, `requirements.txt`, dan kode Flask `app.py`.
  2. Menyusun berkas `nginx.conf` untuk reverse proxy ke `app:5000` dan `html/index.html` untuk pengujian bind mount.
  3. Memperbaiki typo `POSTGRESS_DB` menjadi `POSTGRES_DB` dan menyelaraskan `DB_PORT: "5432"` pada `docker-compose.yaml`.
  4. Menjalankan `docker compose up -d --build`, yang membuahkan seluruh service (`web`, `app`, `db`) berjalan dengan status healthy.

### 2. Analisis Risiko Keamanan dan Operasional

1. **Plaintext Credential di File Compose:**
   Nilai credential `POSTGRES_PASSWORD: labpass123` dicatat terbuka di `docker-compose.yaml`. Risiko kebocoran rahasia tinggi jika file terdorong ke repositori Git publik.
2. **Network Perimeter Exposure:**
   Port Nginx `8080:80` dipublikasikan ke antarmuka `0.0.0.0`, mengekspos web server ke seluruh interface host termasuk jaringan eksternal.
3. **Pemisahan Network Frontend dan Backend (Aspek Positif):**
   Database `db` hanya terhubung ke network `backend`, sedangkan service `web` hanya di `frontend`. Service `app` berperan sebagai jembatan dua arah. Hal ini mencegah akses TCP langsung dari jaringan luar ke database.
4. **Prinsip Least Privilege Process (Aspek Positif):**
   Container `app` dieksekusi menggunakan user non-root (`appuser`, UID 10001), membatasi eskalasi privilege bila kode Flask diserang.

### 3. Rekomendasi Perbaikan untuk Lingkungan Production-Like

1. **Gunakan Docker Secrets atau External Secrets Manager:**
   Pindahkan credential database ke Docker Secrets atau manajer rahasia terpusat (Vault / AWS Secrets Manager) alih-alih environment variable plaintext.
2. **Batasi Binding Port ke Loopback atau Gunakan TLS Ingress:**
   Ganti port binding menjadi `"127.0.0.1:8080:80"` dan gunakan Ingress Controller atau API Gateway dengan TLS/HTTPS untuk lalu lintas publik.
3. **Pemberian Limitasi Sumber Daya (Resource Constraints):**
   Terapkan batas memori dan CPU untuk setiap container di file compose:
   ```yaml
   deploy:
     resources:
       limits:
         cpus: '0.50'
         memory: 256M
   ```
4. **Terapkan Read-Only Root Filesystem:**
   Gunakan konfigurasi `read_only: true` pada container `app` dan `web` dengan mount `tmpfs` untuk folder temporer yang dibutuhkan runtime.