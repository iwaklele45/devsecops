# Laporan Praktikum Bab 1 — Fondasi Teoretis dan Kerangka Kerja DevSecOps

## 1. Rekaman Baseline Tool dan Lingkungan

```text
docker version:
Docker version 29.6.2, build dfc4efb1e2

docker compose version:
Docker Compose version v5.4.0

git --version:
git version 2.55.0

openssl version:
OpenSSL 3.6.3 9 Jun 2026 (Library: OpenSSL 3.6.3 9 Jun 2026)

curl --version:
curl 8.7.1 (x86_64-apple-darwin25.0) libcurl/8.7.1 (SecureTransport) LibreSSL/3.3.6 zlib/1.2.12 nghttp2/1.68.1

docker info --format '{{json .SecurityOptions}}':
["name=seccomp,profile=builtin","name=cgroupns"]
```

## 2. Threat Statement

Aktor ancaman eksternal (unauthenticated external attacker) mengeksploitasi celah injeksi kode atau kerentanan dependensi pihak ketiga pada antarmuka web publik (jalur serangan) untuk memperoleh akses tidak sah ke database dan direktori kredensial/kunci aplikasi (aset), yang berdampak pada kebocoran data sensitif pengguna, kegagalan kepatuhan regulasi, serta terhentinya operasional layanan (dampak).

## 3. Evaluasi dan Latihan Mandiri

1. **Mengapa DevSecOps tidak dapat direduksi menjadi penambahan scanner pada pipeline?**
   DevSecOps adalah sistem sosio-teknis yang mengintegrasikan budaya kerja, perbaikan proses, arsitektur sistem, dan manajemen risiko bersama antara Development, Security, dan Operations. Menambahkan scanner otomatis (SAST/DAST/SCA) tanpa kriteria penerimaan, triase risiko, dan pemahaman bersama hanya akan memicu kelelahan peringatan (*alert fatigue*), *bottleneck* pengiriman, atau pengabaian peringatan (*bypass gate*). Keamanan harus ditanamkan sejak perancangan arsitektur (*threat modeling*, *shift-left*) hingga operasional produksi (*runtime protection*, *observability*, *shift-right*).

2. **Evidence apa yang membedakan klaim kontrol dari kontrol yang benar-benar terverifikasi?**
   Klaim kontrol hanyalah pernyataan kepatuhan prosedural di atas kertas. Sebaliknya, kontrol terverifikasi dibuktikan oleh artefak audit (*immutable evidence*) yang dapat direproduksi dan diuji keabsahannya, seperti:
   - Commit SHA dan identitas peninjau di version control.
   - Hash kriptografis dan digest OCI image yang ditandatangani (*cryptographic signature/Cosign*).
   - Laporan pemindaian otomatis berserta metadata stempel waktu dan basis data kerentanan yang digunakan.
   - Software Bill of Materials (SBOM) dan bukti asal-usul artefak (*SLSA provenance*).

3. **Bagaimana shared responsibility memengaruhi ownership risiko dan tindak lanjut temuan?**
   *Shared responsibility* mematahkan sekat (*silo*) di mana tim keamanan sebelumnya dianggap sebagai satu-satunya pihak yang bertanggung jawab atas keamanan sistem. Tim pengembang memiliki tanggung jawab langsung atas keamanan kode sumber dan pemilihan dependensi sejak awal iterasi; tim operasi bertanggung jawab atas hardening konfigurasi infrastruktur dan runtime; sedangkan tim keamanan bertindak sebagai enabler penyedia standar kebijakan, otomatisasi gate, dan pendamping triase. Pola ini mendekatkan *ownership* risiko ke pembuat perubahan langsung, mempercepat mitigasi (*shift-left*), serta mencegah pelemparan tanggung jawab saat ditemukan insiden.