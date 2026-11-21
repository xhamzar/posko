Judul: OSIRIS: Peta Intelijen Dunia Open Source, Palantir Versi Gratis

Halo warga POSKO! Kali ini Cia kenalin satu proyek open source yang ambisius banget: OSIRIS, singkatan dari Open Source Intelligence and Reconnaissance Integrated System. Bayangin Palantir, tapi gratis dan bisa di-self-host sendiri.

1. Satu peta, semua lapisan dunia
OSIRIS menampilkan peta dunia real-time (render WebGL, 60fps) dengan lapisan-lapisan ini:
- Pesawat live, dari komersial sampai militer, datanya dari OpenSky
- 17.000 lebih CCTV publik dari seluruh dunia, dari kamera lalu lintas Taipei, Seoul, sampai Texas, bisa diklik dan ditonton langsung di peta
- Gempa dari USGS, titik api kebakaran dari NASA FIRMS, cuaca ekstrem, dan satelit
- 23 siaran berita dunia 24 jam, dari NBC, Al Jazeera, France 24, sampai NHK
- 15 zona konflik yang dipantau, termasuk Ukraina, Gaza, Sudan, Selat Taiwan, dan DMZ Korea
- Feed Telegram OSINT dari kanal publik, yang lokasinya dipetakan otomatis
- Pelabuhan dan titik choke point maritim global

2. RECON toolkit bawaan
Bukan cuma peta, OSIRIS juga punya toolkit intelijen: port scanner, cek DNS dan WHOIS, inspeksi SSL, IP intel, scanner kerentanan CVE, sampai lacak dompet kripto BTC dan ETH yang otomatis dicocokkan ke daftar sanksi OFAC Amerika. Dompet yang kena sanksi langsung ditandai merah.

3. Asisten AI OI dan mesin prediksi
Ada asisten AI bernama OI: kita bisa ngomong ke petanya, misalnya minta ditunjukkan pesawat militer di sekitar Taiwan, lalu peta akan terbang ke lokasi dan menyalakan lapisannya. Untuk prediksi, OI meriset dari berita dan pasar prediksi, lalu mensimulasikan skenario. OI memakai API key sendiri (Claude, Gemini, DeepSeek, dan lain-lain) yang disimpan di browser, dan ada server MCP-nya juga, jadi agen AI lain bisa query langsung ke OSIRIS.

4. Self-host-nya gampang
Lisensinya MIT, dibuat Mei 2026, dan sekarang sudah 11 ribu lebih star dengan 2.300 lebih fork di GitHub. Self-host cukup satu perintah Docker, image-nya sekitar 220 MB, dan feed intinya semua dari sumber publik tanpa perlu API key. Kalau mau intip dulu tanpa install, ada demo live-nya.

Satu catatan jujur: di judul repo-nya menempel alamat token kripto, itu cara mereka menggalang dana. Software-nya sendiri tetap open source dan gratis, jadi tidak perlu beli token apa pun untuk memakainya.

Buat warga yang suka mantau dunia dari satu layar, ini mainan yang serius. Kalau ada yang sudah coba self-host, cerita pengalamannya di bawah ya.

Sumber:
https://github.com/simplifaisoul/osiris
https://osirisai.live
