# Laporan Praktikum Bab 2 — Konsep Container dan Instalasi Docker

> **Lampiran Dokumen PDF:** [LAPORAN WORKSHOP DevOps M1 Bab 3.pdf](./docker-lab/bab-3/LAPORAN%30WORKSHOP%20DevOps%20M1%20Bab%202.pdf)

<object data="./docker-lab/bab-2/LAPORAN%20WORKSHOP%20DevOps%20M1%20Bab%202.pdf" type="application/pdf" width="100%" height="600px">
  <p>Pratinjau PDF tidak didukung oleh viewer. Buka tautan file: <a href="./docker-lab/bab-2/LAPORAN%20WORKSHOP%20DevOps%20M1%20Bab%202.pdf">LAPORAN WORKSHOP DevOps M1 Bab 2.pdf</a>.</p>
</object>

## Bukti Eksekusi Praktikum

```text
# rafiputra@Rafis-MacBook-Pro bab-2 % docker pull nginx:1.26
1.26: Pulling from library/nginx
626e38e6405b: Download complete 
a3d21a61f738: Download complete 
a6a46f042848: Download complete 
626e38e6405b: Pull complete 
a3d21a61f738: Pull complete 
a6a46f042848: Pull complete 
16c9c4a8e9ee: Pull complete 
4f9e2a2ff866: Pull complete 
cfe8af76b576: Pull complete 
d383161bfb60: Pull complete 


Digest: sha256:41b194461e4bae16f9b25d68b0976ed4735b89ca625c89aad88e1c1c3b7e8860
Status: Downloaded newer image for nginx:1.26
docker.io/library/nginx:1.26

What's next:
    View a summary of image vulnerabilities and recommendations → docker scout quickview nginx:1.26

# rafiputra@Rafis-MacBook-Pro bab-2 % docker run -d --name web-public -p 8080:80 nginx:1.26
1db38733e76e4527fa4bedbbb378ed1bb9de78d08046eddd8c59edcf113b6d03

# rafiputra@Rafis-MacBook-Pro bab-2 % docker ps                                            
CONTAINER ID   IMAGE        COMMAND                  CREATED              STATUS              PORTS                                     NAMES
1db38733e76e   nginx:1.26   "/docker-entrypoint.…"   About a minute ago   Up About a minute   0.0.0.0:8080->80/tcp, [::]:8080->80/tcp   web-public

# rafiputra@Rafis-MacBook-Pro bab-2 % docker logs --tail 20 web-public
/docker-entrypoint.sh: Launching /docker-entrypoint.d/20-envsubst-on-templates.sh
/docker-entrypoint.sh: Launching /docker-entrypoint.d/30-tune-worker-processes.sh
/docker-entrypoint.sh: Configuration complete; ready for start up
2026/09/07 15:15:31 [notice] 1#1: using the "epoll" event method
2026/09/07 15:15:31 [notice] 1#1: nginx/1.26.3
2026/09/07 15:15:31 [notice] 1#1: built by gcc 12.2.0 (Debian 12.2.0-14) 
2026/09/07 15:15:31 [notice] 1#1: OS: Linux 7.0.12-linuxkit
2026/09/07 15:15:31 [notice] 1#1: getrlimit(RLIMIT_NOFILE): 1048576:1048576
2026/09/07 15:15:31 [notice] 1#1: start worker processes
2026/09/07 15:15:31 [notice] 1#1: start worker process 29
2026/09/07 15:15:31 [notice] 1#1: start worker process 30
2026/09/07 15:15:31 [notice] 1#1: start worker process 31
2026/09/07 15:15:31 [notice] 1#1: start worker process 32
2026/09/07 15:15:31 [notice] 1#1: start worker process 33
2026/09/07 15:15:31 [notice] 1#1: start worker process 34
2026/09/07 15:15:31 [notice] 1#1: start worker process 35
2026/09/07 15:15:31 [notice] 1#1: start worker process 36
2026/09/07 15:15:31 [notice] 1#1: start worker process 37
2026/09/07 15:15:31 [notice] 1#1: start worker process 38
2026/09/07 15:15:31 [notice] 1#1: start worker process 39

# rafiputra@Rafis-MacBook-Pro bab-2 % curl http://localhost:8080                    
<!DOCTYPE html>
<html>
<head>
<title>Welcome to nginx!</title>
<style>
html { color-scheme: light dark; }
body { width: 35em; margin: 0 auto;
font-family: Tahoma, Verdana, Arial, sans-serif; }
</style>
</head>
<body>
<h1>Welcome to nginx!</h1>
<p>If you see this page, the nginx web server is successfully installed and
working. Further configuration is required.</p>

<p>For online documentation and support please refer to
<a href="http://nginx.org/">nginx.org</a>.<br/>
Commercial support is available at
<a href="http://nginx.com/">nginx.com</a>.</p>

<p><em>Thank you for using nginx.</em></p>
</body>
</html>

# rafiputra@Rafis-MacBook-Pro bab-2 % docker run -it --name ubuntu-test ubuntu:22.04 /bin/bash
Unable to find image 'ubuntu:22.04' locally
22.04: Pulling from library/ubuntu
231032373bb3: Pull complete 
fd16aa656128: Download complete 
Digest: sha256:2edbbc5dc405e9612ba3584ce95480277e3eb374407b5505fe26f17df77c7dbc
Status: Downloaded newer image for ubuntu:22.04
root@ec117c617d8e:/# 

# root@ec117c617d8e:/# cat /etc/os-release 
PRETTY_NAME="Ubuntu 22.04.5 LTS"
NAME="Ubuntu"
VERSION_ID="22.04"
VERSION="22.04.5 LTS (Jammy Jellyfish)"
VERSION_CODENAME=jammy
ID=ubuntu
ID_LIKE=debian
HOME_URL="https://www.ubuntu.com/"
SUPPORT_URL="https://help.ubuntu.com/"
BUG_REPORT_URL="https://bugs.launchpad.net/ubuntu/"
PRIVACY_POLICY_URL="https://www.ubuntu.com/legal/terms-and-policies/privacy-policy"
UBUNTU_CODENAME=jammy

# rafiputra@Rafis-MacBook-Pro bab-2 % cd custom-web                           
rafiputra@Rafis-MacBook-Pro custom-web % cat > index.html << 'EOF'
<h1>Docker Lab PENS</h1>
<p>Container berhasil berjalan.</p>
EOF
cat > Dockerfile << 'EOF'
FROM nginx:1.26-alpine
LABEL maintainer="admin@pens.ac.id"
COPY index.html /usr/share/nginx/html/index.html
EXPOSE 80
CMD ["nginx", "-g", "daemon off;"]
EOF

# rafiputra@Rafis-MacBook-Pro custom-web % docker build -t pens-web:1.0 .

[+] Building 12.6s (7/7) FINISHED                                                                                                     docker:desktop-linux
 => [internal] load build definition from Dockerfile                                                                                                  0.0s
 => => transferring dockerfile: 192B                                                                                                                  0.0s
 => [internal] load metadata for docker.io/library/nginx:1.26-alpine                                                                                  3.8s
 => [internal] load .dockerignore                                                                                                                     0.0s
 => => transferring context: 2B                                                                                                                       0.0s
 => [internal] load build context                                                                                                                     0.0s
 => => transferring context: 98B                                                                                                                      0.0s
 => [1/2] FROM docker.io/library/nginx:1.26-alpine@sha256:1eadbb07820339e8bbfed18c771691970baee292ec4ab2558f1453d26153e22d                            8.7s
 => => resolve docker.io/library/nginx:1.26-alpine@sha256:1eadbb07820339e8bbfed18c771691970baee292ec4ab2558f1453d26153e22d                            0.0s
 => => sha256:1ee6408ae620ef4a046179fb57fbd4f6fcb7c0bb4e3d8de3c49334a1facdfea6 15.73MB / 15.73MB                                                      7.0s
 => => sha256:fca9948dfc2c8a0bda75fb117df98825d3b23ceae22003753f7485b8a912347a 1.40kB / 1.40kB                                                        1.0s
 => => sha256:4431f52ff81db291b1025ec00511013b534349a0c740be431c48299ed5a088f0 1.21kB / 1.21kB                                                        1.1s
 => => sha256:014925e14361cfca96943aa9367c39a19fc6e806cbae3e1f30cd65bdc8bf46de 404B / 404B                                                            1.0s
 => => sha256:21b8c2c2584bcf9471f52b43f4fee4d54c7fb76517da72f07ff21a2439bc9125 956B / 956B                                                            0.5s
 => => sha256:4f7bb1290dbfa2b305786f6c84cb49c209de2afa4d149cbe0b4bfa050e925246 627B / 627B                                                            0.5s
 => => sha256:3b5b7a2d0351a33e1d34149cfd8d0cc4c7b3bbc6ecfee67809fe22ed10b33425 1.79MB / 1.79MB                                                        6.5s
 => => sha256:94e9d8af22013aabf0edcaf42950c88b0a1350c3a9ce076d61b98a535a673dd9 4.09MB / 4.09MB                                                        6.8s
 => => extracting sha256:94e9d8af22013aabf0edcaf42950c88b0a1350c3a9ce076d61b98a535a673dd9                                                             0.1s
 => => extracting sha256:3b5b7a2d0351a33e1d34149cfd8d0cc4c7b3bbc6ecfee67809fe22ed10b33425                                                             0.1s
 => => extracting sha256:4f7bb1290dbfa2b305786f6c84cb49c209de2afa4d149cbe0b4bfa050e925246                                                             0.0s
 => => extracting sha256:21b8c2c2584bcf9471f52b43f4fee4d54c7fb76517da72f07ff21a2439bc9125                                                             0.0s
 => => extracting sha256:014925e14361cfca96943aa9367c39a19fc6e806cbae3e1f30cd65bdc8bf46de                                                             0.0s
 => => extracting sha256:4431f52ff81db291b1025ec00511013b534349a0c740be431c48299ed5a088f0                                                             0.0s
 => => extracting sha256:fca9948dfc2c8a0bda75fb117df98825d3b23ceae22003753f7485b8a912347a                                                             0.0s
 => => extracting sha256:1ee6408ae620ef4a046179fb57fbd4f6fcb7c0bb4e3d8de3c49334a1facdfea6                                                             0.2s
 => [2/2] COPY index.html /usr/share/nginx/html/index.html                                                                                            0.1s
 => exporting to image                                                                                                                                0.0s
 => => exporting layers                                                                                                                               0.0s
 => => exporting manifest sha256:09832790fc1fd245eccb7c3023f096795fb5a5e8aa937d62f3f980ad4837830b                                                     0.0s
 => => exporting config sha256:ad8b89d2008ca0a3a739631a3babb2e6a6c009c80ca41111c811582642710017                                                       0.0s
 => => exporting attestation manifest sha256:cdd73213df01984c9adec8b2d6910d07b334d313b592e70ef47253128054f9a7                                         0.0s
 => => exporting manifest list sha256:8794924d09a47d09364edb3f8dba96d611bc4a4a2be50216ee776f2a7fa8b191                                                0.0s
 => => naming to docker.io/library/pens-web:1.0                                                                                                       0.0s
 => => unpacking to docker.io/library/pens-web:1.0                                                                                                    0.0s

View build details: docker-desktop://dashboard/build/desktop-linux/desktop-linux/1kewb3211xaww0thv3hqp24cd

# rafiputra@Rafis-MacBook-Pro custom-web % docker run -d --name pens-app -p 9090:80 pens-web:1.0   
224bf2ce5e7892f75ff99d2dd21bf1d53677d9d97ec686f5f061f75ec123f42e
```

## Evaluasi dan Latihan Mandiri

1. **Mengapa penggunaan tag latest tidak dianjurkan untuk deployment yang harus reproducible?**
   Tag `latest` merupakan *mutable pointer* (tag dinamis), bukan penanda versi tetap. Ketika image di-build atau di-deploy ulang di waktu atau lingkungan berbeda, Docker engine akan menarik (*pull*) image terbaru yang menunjuk tag tersebut. Hal ini menyebabkan builds dan deployments tidak bersifat deterministik (*non-reproducible*), sehingga berpotensi memicu kegagalan sistem mendadak akibat *breaking changes* atau dependensi baru yang belum diuji. Untuk deployment produksi dan reproducible, wajib menggunakan tag versi spesifik yang tersemat (*pinned version*, misal `nginx:1.26.3-alpine`) atau lebih aman menggunakan cryptographic digest (`nginx@sha256:...`).

2. **Jelaskan peran containerd dan runc dalam arsitektur Docker.**
   - **`containerd`** bertindak sebagai *high-level container runtime*. Bertanggung jawab atas pengelolaan siklus hidup container secara makro: transfer dan distribusi image dari registry, manajemen storage snapshot/layer, pengelolaan endpoint network, serta pengawasan status proses container.
   - **`runc`** bertindak sebagai *low-level container runtime* (implementasi referensi standar OCI). Bertugas mengeksekusi container langsung di level kernel Linux: membuat isolasi proses via namespaces (PID, mount, net, ipc, uts, user), menerapkan pembatasan resource melalui cgroups, memuat profil keamanan seccomp dan LSM (AppArmor/SELinux), lalu keluar (*exit*) setelah proses container berjalan mandiri di bawah supervisi containerd-shim.

3. **Apa konsekuensi keamanan dari memasukkan user ke group docker?**
   Memasukkan user non-root ke group `docker` memberikan hak akses penuh (baca dan tulis) ke Unix Domain Socket Docker daemon (`/var/run/docker.sock`). Karena Docker daemon berjalan dengan privilege `root`, user di group `docker` setara dengan memiliki akses root penuh pada host (*root-equivalent privilege escalation*). User tersebut dapat dengan mudah melakukan eskalasi hak akses host secara trivial tanpa password sudo, misalnya dengan menjalankan perintah `docker run -v /:/host-root alpine ...` untuk membaca, memanipulasi, atau menghapus file sistem host mana pun (termasuk `/etc/shadow` atau file SSH keys).

4. **Bandingkan layer image nginx:1.26-alpine dan image custom yang Anda buat.**
   - Image dasar **`nginx:1.26-alpine`** terdiri atas layer sistem dasar Alpine Linux (userspace minimal ~5 MB) ditambah layer instalasi paket biner Nginx, konfigurasi bawaan, serta runtime library pendukung (total ukuran ~15–20 MB). Seluruh layer ini bersifat *read-only*.
   - Image custom **`pens-web:1.0`** dibangun di atas `nginx:1.26-alpine` sebagai *parent image* (berbagi layer read-only yang sama tanpa menduplikasi data). Image custom hanya menambahkan satu layer tipis baru di atasnya, yaitu hasil instruksi `COPY index.html /usr/share/nginx/html/index.html` (berukuran sangat kecil, hanya beberapa puluh byte), serta metadata eksekusi (`LABEL`, `EXPOSE`, dan `CMD`).

5. **Kapan sebaiknya memilih VM daripada container?**
   Virtual Machine (VM) lebih tepat dipilih daripada container ketika:
   - **Kebutuhan Kernel Berbeda**: Aplikasi memerlukan OS guest dengan kernel berbeda dari host (misalnya menjalankan Windows Server di atas host Linux, atau membutuhkan modul kernel khusus).
   - **Isolasi Keamanan Tingkat Keras (Hardware Isolation)**: Menjalankan beban kerja multi-tenant, lingkungan untrusted code execution, atau sistem dengan standar kepatuhan regulasi ketat yang mensyaratkan batas isolasi berbasis perangkat keras/hypervisor (container berbagi kernel host yang rentan terhadap risiko *kernel escape*).
   - **Alokasi Resource Eksklusif**: Aplikasi memerlukan kontrol langsung ke hardware tertentu (seperti PCI passthrough) atau jaminan resource host tanpa berbagi scheduler kernel.

---

## Laporan Praktikum dan Analisis Wajib

### 1. Masalah yang Dihadapi dan Diagnosis

- **Sintaks Kesalahan:**
  ```text
  rafiputra@Rafis-MacBook-Pro custom-web % docker build -t pens-web:1.0
  ERROR: docker: 'docker buildx build' requires 1 argument
  Usage:  docker buildx build [OPTIONS] PATH | URL | -
  ```
- **Diagnosis:**
  Perintah `docker build` (yang di-forward ke plugin Buildx) memerlukan argumen *build context* di akhir perintah untuk menentukan direktori sumber yang akan diunggah ke builder context. Kegagalan terjadi karena argumen direktori konteks (`.`) tidak disertakan di akhir perintah.
- **Tindakan Korektif:**
  Menjalankan perintah build dengan menyertakan titik (`.`) sebagai konteks lokal:
  ```bash
  docker build -t pens-web:1.0 .
  ```
  Build berhasil selesai dalam 12.6 detik dengan 7 step layer.

### 2. Analisis Risiko Keamanan dan Operasional

1. **Eksekusi Default sebagai Root:**
   Container Nginx berjalan dengan user default root di dalam container. Jika penyerang menemukan kerentanan RCE pada Nginx, penyerang memiliki privilege root di dalam container namespace dan memperbesar kemungkinan *container breakout*.
2. **Port Binding 0.0.0.0 (Unrestricted Public Exposure):**
   Penggunaan opsi `-p 8080:80` dan `-p 9090:80` secara default mengikat port ke `0.0.0.0`, mengekspos port ke seluruh antarmuka jaringan host (termasuk jaringan lokal/LAN publik), bukan hanya `127.0.0.1` (localhost).
3. **Privilege Escalation via Docker Group:**
   User praktikan ditambahkan ke group `docker`, yang membuka celah eskalasi hak akses setara root pada host melalui Docker socket.
4. **Ketiadaan Resource Limits:**
   Container dijalankan tanpa limit memori (`--memory`) dan CPU (`--cpus`). Satu container yang mengalami *memory leak* atau diserang DoS dapat menghabiskan resource host dan mengganggu container lain.

### 3. Rekomendasi Perbaikan untuk Lingkungan Production-Like

1. **Enforce Non-Root Execution:**
   Jalankan proses web server menggunakan user unprivileged di Dockerfile:
   ```dockerfile
   USER nginx
   ```
   (Atau gunakan image *unprivileged* seperti `nginxinc/nginx-unprivileged`).
2. **Restriksi Port Binding dan Gunakan Reverse Proxy Ber-TLS:**
   Hindari publikasi langsung ke `0.0.0.0`. Ikat ke localhost (`127.0.0.1:9090:80`) dan gunakan satu ingress reverse proxy ber-TLS (HTTPS) terpusat untuk traffic masuk.
3. **Pinning Base Image dengan Cryptographic Digest:**
   Ganti base image dinamis dengan hash SHA256 immutable:
   ```dockerfile
   FROM nginx:1.26-alpine@sha256:1eadbb07820339e8bbfed18c771691970baee292ec4ab2558f1453d26153e22d
   ```
4. **Terapkan Resource Limiting (cgroups):**
   Batasi resource penggunaan container untuk mencegah exhaustion host:
   ```bash
   docker run -d --name pens-app --memory="256m" --cpus="0.5" -p 127.0.0.1:9090:80 pens-web:1.0
   ```
5. **Integrasi Vulnerability Scanning Otomatis:**
   Integrasikan pemindai kerentanan OCI image (seperti Trivy atau Docker Scout) sebelum image di-push atau di-deploy ke registry produksi.