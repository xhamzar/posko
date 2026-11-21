Halo warga POSKO, kali ini aku nemu tool terminal yang menarik banget buat yang sering berkutat sama Google Drive. Namanya gdirect, ditulis pakai Rust.

https://i.ibb.co/ZRNtjS0C/gdirect-ss.jpg

Jadi gdirect ini bisa buat browse, download, upload, sampai mount Google Drive jadi folder lokal, semuanya dari terminal. Ada mode browse-nya juga yang pakai keyboard ala yazi.

Yang bikin dia beda: sebelum transfer, dia otomatis nyari IP Google mana yang bisa dijangkau dari jaringanmu dan paling cepat, terus trafik Drive dikirim langsung ke IP itu selama 24 jam. Jadi kalau akses Googlemu lambat atau sebagian diblokir, jalurnya bisa jauh lebih kencang. Tenang, pengecekan nama host dan sertifikatnya tetap jalan, jadi bukan ngakalin keamanan.

Downloadnya pakai mesin aria2, jadi bisa multi-koneksi sampai 16 jalur sekaligus, bisa resume kalau putus, dan habis download dicek MD5-nya sama yang dari Drive. Uploadnya selalu bikin file baru, tidak pernah nimpa file lama.

Setupnya sekali saja sekitar 10 menit: bikin OAuth client sendiri di Google Cloud, login sekali lewat browser, habis itu token dan setting kesimpen lokal di file SQLite. Tersedia buat macOS, Linux, dan Windows, lisensinya GPL alias gratis dan open source.

Sumber: https://github.com/mizorewww/gdirect
