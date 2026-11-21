Baru nemu info menarik dari thread di X: KataBump, layanan hosting asal Prancis, lagi bagi-bagi domain gratis berakhiran .kdns.fr. Kedengarannya kayak subdomain gratisan biasa, tapi ternyata kontrol DNS-nya full, mirip domain yang dibeli sendiri.

Cara klaimnya gampang:

1. Daftar akun dulu di dashboard KataBump.
2. Masuk menu My domains, klik Order my first domain (atau tombol Order a domain).
3. Isi nama yang diinginkan. Aturannya: huruf kecil, angka, dan tanda hubung, 3 sampai 63 karakter. Ekstensinya pilih .kdns.fr, ada label Free.
4. Buat nameserver, pilih KataBump NS yang direkomendasikan biar zona DNS-nya langsung siap. Ada juga pilihan External NS kalau mau pakai nameserver sendiri.
5. Centang persetujuan syarat penggunaan, lalu klik Order the domain. Selesai, domain langsung jadi dan zona DNS-nya bisa diatur.

Yang didapat dari domain gratis ini:

- Zona DNS sendiri sampai 500 record
- Jenis record lengkap: A, AAAA, CNAME, MX, TXT, SRV, CAA, NS, DS
- Ada fitur import dan export record, jadi gampang kalau mau mindahin settingan
- DNSSEC tersedia, tinggal diaktifkan
- Status domainnya Delegated, bukan sekadar redirect atau parkir

Karena DNS-nya full, domain ini fleksibel banget buat diarahkan ke mana aja. Contohnya: CNAME ke Vercel buat web, ke Cloudflare Tunnel buat layanan di rumah, alamat server Minecraft, atau sekadar nama buat proyek eksperimen biar nggak ngabisin subdomain domain utama.

Catatan jujurnya: .kdns.fr ini tetap subdomain milik KataBump, bukan domain yang kita miliki penuh kayak .com atau .my.id. Kalau KataBump tutup atau akun kita bermasalah, namanya ikut hilang. Jadi cocoknya buat tes, proyek iseng, dan endpoint cadangan, bukan buat aset utama yang serius.

Ada yang udah coba? Lumayan nih buat koleksi nama gratisan yang beneran bisa dipakai.

Sumber:
https://x.com/miss_perigriine/status/2113708156928815580
https://dashboard.katabump.com