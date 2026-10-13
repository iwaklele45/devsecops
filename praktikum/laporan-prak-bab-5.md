> **Lampiran Dokumen PDF:** [LAPORAN DevSecOps BAB-5.pdf](./docker-lab/bab-5/LAPORAN%20DevSecOps%20BAB-5.pdf)

<object data="./docker-lab/bab-5/LAPORAN%20DevSecOps%20BAB-5.pdf" type="application/pdf" width="100%" height="600px">
  <p>Pratinjau PDF tidak didukung oleh viewer. Buka tautan file: <a href="./docker-lab/bab-5/LAPORAN%20DevSecOps%20BAB-5.pdf">LAPORAN DevSecOps BAB-5.pdf</a>.</p>
</object>

## **Verifikasi dan Skenario Pengujian**

\[ \] PostgreSQL berjalan dengan volume pg-data.

![Screenshot image2](./assets/bab-5/image2.png)

\[ \] Tabel students dibuat otomatis dari init script.

![Screenshot image3](./assets/bab-5/image3.png)

\[ \] pgAdmin dapat login dan terkoneksi ke database.

![Screenshot image4](./assets/bab-5/image4.png)

\[ \] Backup menghasilkan file dump di direktori host.

![Screenshot image5](./assets/bab-5/image5.png)

\[ \] Restore sudah diuji, bukan hanya diasumsikan berhasil.

![Screenshot image6](./assets/bab-5/image6.png)

## **Evaluasi dan Latihan Mandiri**

1. Mengapa init script tidak dijalankan ulang saat volume lama masih ada?

   Karena PostgreSQL hanya menjalankan script inisialisasi jika direktori data database kosong. Jika volume sudah ada dan berisi data, proses inisialisasi dilewati untuk mencegah penimpaan data yang sudah ada.

2. Apa risiko menaruh password database pada docker-compose.yml?

   Ketika di push di repo bisa terlihat, lebih baik dijadikan satu di file .env juga mempermudah maintenance

3. Bagaimana cara membuktikan backup dapat dipulihkan?

   Dengan cara data di hapus, terus di pulihkan dengan file backup

4. Apa bedanya logical backup pg\_dump dan backup filesystem volume mentah?

   pg\_dump melakukan backup secara logis (menghasilkan perintah SQL atau arsip terstruktur yang independen terhadap penyimpanan fisik), sedangkan backup filesystem menyalin direktori data fisik secara langsung di level sistem file.

5. Apa dampak docker compose down \-v terhadap database?

   Volumenya di hapus, data di database akan hilang karena container di mount di situ

   

## **Bukti minimum:**

* Screenshot docker compose ps atau docker ps yang menunjukkan service berjalan.

  ![Screenshot image7](./assets/bab-5/image7.png)

* Screenshot hasil curl/browser/API/dashboard sesuai target bab.

  ![Screenshot image8](./assets/bab-5/image8.png)

* Cuplikan log atau query yang membuktikan sistem bekerja.

  ![Screenshot image9](./assets/bab-5/image9.png)

## **Analisis wajib:**

1. Jelaskan satu masalah yang muncul dan cara Anda mendiagnosisnya.  
   * Masalah: Halaman UI pgAdmin tidak dapat diakses secara langsung menggunakan IP Virtual Machine (VM).  
   * Diagnosis & Solusi: Setelah memeriksa konfigurasi jaringan dan konektivitas antarmuka VM, masalah ditangani dengan melakukan SSH port forwarding / reverse port tunneling dari port VM ke PC lokal (localhost:5050), sehingga dashboard pgAdmin dapat dibuka dengan aman melalui browser di PC lokal.  
2. Jelaskan risiko keamanan atau operasional yang relevan pada bab ini.  
   * Risiko Keamanan:  
     * Penyimpanan kredensial/password database secara plain text di dalam file docker-compose.yml berisiko bocor apabila file ter-push ke repositori publik/VCS.  
     * Port komunikasi PostgreSQL (5432) dan pgAdmin dipublikasikan tanpa sertifikat enkripsi SSL/TLS, berisiko terkena serangan penyadapan (Man-in-the-Middle).  
   * Risiko Operasional:  
     * Eksekusi perintah docker compose down \-v secara tidak sengaja akan menghapus volume terikat (pg-data), menyebabkan kehilangan data permanen.  
     * Ketergantungan pada proses backup manual tanpa pengujian pemulihan (restore test) berkala berpotensi menyebabkan kegagalan saat insiden disaster recovery.  
3. Berikan rekomendasi perbaikan bila lab ini akan dibawa ke production-like environment.

   Tidak ada
