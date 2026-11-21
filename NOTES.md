# POSKO — Pusat Obrolan & Sharing Komunitas Online

Forum ala V2EX di Vercel. Diputuskan 2026-10-22 oleh Driyan (Opsi 1: custom, bukan Babel/GAE).
Nama: POSKO. Domain target: posko.ruru.my.id. Tagline: "Selalu siaga, selalu ada obrolan".

## Arsitektur
- `index.html` — SPA vanilla JS, hash routing, bicara ke `/api/*` (JSON).
  Views: beranda (topik terbaru), node, topik+balasan, buat topik, login, daftar, profil member, pencarian.
  Kalau `/api` belum live, SPA jatuh ke MODE DEMO (data contoh in-memory) + badge "MODE DEMO".
- `api/*.py` — Vercel Python serverless functions (pola sama seperti RuruHua: index.html + api Python).
- Database: DIPUTUSKAN Driyan 2026-10-22 13:12 UTC: **Firebase** — Firestore project "tubexin"
  (serviceAccount di ~/workspace/tubexin-vercel/serviceAccount.json), koleksi prefix `posko_*`.
  Auth mandiri di API (bukan Firebase Auth): password PBKDF2-HMAC-SHA256 200k iterasi,
  token sesi JWT-like HMAC-SHA256 (rahasia dari env POSKO_SECRET / turunan service account).
  Kredensial fungsi Vercel: env FIREBASE_SERVICE_ACCOUNT (JSON utuh) atau file api/_sa.json.

## Kontrak API (JSON)
- GET  /api/nodes                      -> [{id,name,desc}]
- GET  /api/topics?node=&q=&author=    -> [{id,node,author,title,created,last,pinned,locked,replies}]
- GET  /api/topic?id=                  -> {topic:{...}, replies:[{id,topic,author,content,created}]}
- POST /api/register {username,email,password} -> {token, user:{username,email,role}}
- POST /api/login {email,password}    -> {token, user:{username,email,role}}
- POST /api/topics (auth) {node,title,content} -> {id}
- POST /api/replies (auth) {topic,content}    -> {id}
- POST /api/moderate (admin) {topic, action: pin|lock|delete} -> {ok:true}
- POST /api/edit (login, penulis/admin) {kind: topic|reply, id, title?, content} -> {ok:true}; set field edited
- POST /api/remove (login, penulis/admin) {kind: topic|reply, id} -> {ok:true}; hapus topik ikut hapus balasan
- GET  /api/coin (login) -> {balance, history[30]}; GET /api/coin?user=X -> {username, balance} (publik)
- POST /api/coin (login) {action:"tip", to, amount} -> {ok, balance}; (admin) {action:"grant", to, amount} (negatif = tarik)
- GET  /api/profile?user=X -> profil publik {username, role, joined, bio, avatar, coins, stats{topics,replies}}
- POST /api/profile (login) {bio<=160, avatar} -> ubah profil SENDIRI; avatar harus salah satu AVATAR_IDS
  di api/_db.py atau "" (huruf). Set avatar SAAT INI (v1.4, pixel art): kucing|burunghantu|rubah|panda|
  kodok|harimau — file WebP transparan di assets/avatars/<id>.webp (grid 64px, image-rendering: pixelated),
  ikut terdeploy via deploy.py (file biner di-encode base64; vercel.json rewrite mengecualikan assets/).
  GET /api/topics & /api/topic kini menyertakan field avatar penulis di tiap item.
- POSKOIN: saldo di field users.coins; mutasi tercatat di posko_coin_tx {from,to,amount,type,note,created},
  type welcome|reward|tip|grant. Bonus daftar +20; reward topik +5 / balasan (>=10 char) +2,
  cap reward 20/hari (anti-farming). Konstanta di api/_db.py (COIN_*).
Auth: header `Authorization: Bearer <token>`. Role: admin | member. User pertama (driyan) = admin.

## Data model (Firestore bila Firebase)
- nodes/{id}: {name, desc, order}
- users/{uid}: {username, email, role, joined}
- topics/{id}: {node, author, title, content, created, last, pinned, locked, replyCount}
- replies/{id}: {topic, author, content, created}

## Node awal
umum (Umum), teknologi (Teknologi), santai (Santai), tanya (Tanya Jawab)

## Status
- [x] Frontend SPA + mode demo (2026-10-22)
- [x] Backend API serverless (api/_db.py + nodes/topics/topic/register/login/replies/moderate)
- [x] Uji lokal end-to-end vs Firestore asli LULUS (2026-10-22 13:14 UTC): nodes seed 4,
      register (user pertama = admin), login benar/salah, buat topik, balas (replyCount naik),
      pin via moderasi. Data uji dibersihkan sesudahnya (users/topics 0, nodes tetap 4).
      Harness uji: /tmp/posko_test_server.py (venv tubexin-vercel, env FIREBASE_SERVICE_ACCOUNT).
- [x] Deploy Vercel LIVE (2026-10-22 13:22 UTC): project `posko` prj_v0WjytGfLwmMG8HxbWfxvtazf767,
      deploy via deploy.py; env FIREBASE_SERVICE_ACCOUNT + POSKO_SECRET terpasang saat create_project
      (secret lokal di ~/.config/posko/secret, chmod 600); ssoProtection null, passwordProtection off.
      URL produksi: https://posko-drafsanjanis-projects.vercel.app — diverifikasi end-to-end LIVE:
      register/login/topik/balasan/list + /api/nodes; data uji produksi dibersihkan (users/topics 0, nodes 4).
- [x] v1.1 Edit/Hapus (22 Okt, deploy dpl_ECi7SSDqzuyEa6Bp6ZShQBJnVvsX): Driyan komplain tak bisa
      edit/hapus tulisannya -> ditambah api/edit.py + api/remove.py + tombol Edit/Hapus di topik &
      tiap balasan (penulis/admin saja; uji lokal: edit orang lain ditolak "Ini bukan tulisanmu").
      Terverifikasi live (endpoint aktif, 401 tanpa login). Driyan sudah daftar (admin), topik
      perdananya "Selamat Datang di POSKO! Absen & Perkenalan Dulu di Sini" sudah di-pin sendiri.
- [x] v1.2 POSKOIN LIVE (22 Okt, deploy dpl_7ARishp9pDLETor6QPHC1si11m6T): koin internal POSKO
      diterapkan atas perintah Driyan — api/coin.py + helper di _db.py; UI: chip saldo di header,
      box "POSKOIN Saya" di sidebar, tombol "Kasih POSK" di topik & balasan, halaman #/koin
      (saldo + aturan + riwayat), saldo di profil + form grant admin. Uji lokal 13/13 + grant LULUS;
      verifikasi live LULUS (bonus 20, reward topik 5, tip, saldo publik). Data uji dibersihkan;
      driyan diberi saldo awal resmi 100 POSK (grant "Saldo awal POSKOIN"). Logo POSKOIN:
      assets/poskoin-logo.png (dipakai nanti bila perlu gambar; UI v1 pakai badge CSS "P").
- [x] v1.3 Profil & Avatar (22 Okt, deploy dpl_F2jVZyxz8cr7PY79CahsjN42cjJQ): halaman profil dibenahi
      (avatar besar, badge ADMIN/WARGA, tanggal bergabung, bio, statistik topik/balasan/POSK) +
      Edit Profil (bio + pilih avatar) via api/profile.py. 10 avatar preset SVG lucu/nyeleneh
      digambar inline di index.html (Kucing Oren, Kodok Ijo, Bebek Kuning, Panda Ngantuk, Hantu Imut,
      Alien Begok, Robot Jadul, Ayam Jago, Gurita Pink, Beruang Coklat) — tampil di profil, daftar
      topik, detail topik & balasan. Uji lokal 11/11 + verifikasi live LULUS; data uji dibersihkan.
- [x] Embed otomatis Tahap 1 (23 Okt, deploy posko-lmj3ejr6f): renderer rich() di frontend — link YouTube
      (watch/youtu.be/shorts) jadi thumbnail lite-embed (klik = player youtube-nocookie autoplay), link
      gambar https (jpg/png/gif/webp/avif) jadi <img> (klik = buka penuh), link lain jadi <a> nofollow.
      Aman XSS (regex URL tanpa tanda kutip/kurung siku; uji node 10/10 PASS — pelajaran: split() regex
      WAJIB grup tangkap, kalau tidak URL hilang dari teks). Berlaku di isi topik + balasan.
      Tahap 2 (MENUNGGU Client ID Imgur dari Driyan): tombol upload gambar via /api/upload proxy.
- [x] Navigasi mobile ala V2EX (23 Okt, deploy posko-ere76iutg): atas komplain Driyan nav mobile kurang
      rapi + referensi screenshot V2EX — header mobile: logo + ikon kaca pembesar (tap = bar pencarian
      full-width muncul) + avatar; klik avatar membuka menu dropdown (kepala: username + saldo POSKOIN;
      item: Profil Saya, POSKOIN Saya, Buat Topik, Keluar). Pola dropdown avatar berlaku juga di desktop;
      pencarian desktop tetap inline. Tagline disembunyikan di mobile. Terverifikasi live di alias.
- [x] v1.4 Avatar Pixel Art (22 Okt, deploy dpl_964EsgfukovDjyCfS8dvNN9WStae, payload 112.959B):
      Driyan menilai set SVG v1.3 kurang iconic/tidak ada nilai jual; set maskot pos ronda juga ditolak;
      arah final = hewan gaya **pixel art** (Kucing Songong, Burung Hantu, Rubah Licik, Panda Ngantuk,
      Kodok Ceria, Harimau Kecil). Sheet AI dipotong per sprite, latar putih di-keyout flood-fill jadi
      transparan, diturunkan ke grid 64px + kuantisasi (WebP 3,3–5KB/file). Set SVG lama pensiun;
      avatar lama Driyan "bebek" dibersihkan ke "" (ia sempat memilihnya dari set lama).
      Uji lokal (validasi id baru/lama) + live (6 aset image/webp 200) LULUS.
- [x] Domain posko.ruru.my.id ditempel ke project (add_project_domain, "verified": true dari Vercel).
      Resolusi DNS dari sandbox tidak bisa dibuktikan (fake-IP proxy) — bila dari HP belum kebuka,
      Driyan perlu tambah CNAME di Cloudflare: nama `posko` -> `cname.vercel-dns.com`.

## Upload gambar TAHAP 2 — imgbb langsung dari browser (23 Okt 2026)
- Jalur proxy server DIBUANG: imgbb menolak IP datacenter (error 103 dari sandbox & Vercel).
- Firebase Storage GAGAL TOTAL: halaman Storage project tubexin memaksa upgrade Blaze
  (billing) — screenshot Driyan 23 Okt 07:00 WIB. Bucket tak pernah ada.
- Keputusan Driyan (23 Okt 07:04 WIB): upload langsung dari browser user ke api.imgbb.com
  (key tampil di index.html — diterima sadar risiko; ganti key bila disalahgunakan).
  api/upload.py DIHAPUS, env POSKO_IMGBB_KEY tak dipakai lagi.
- Deploy dpl_FH36gwXw1hEhA7oxt3Qy5cJRuQiW (posko-k40vu4nnl), alias produksi terverifikasi
  memuat endpoint imgbb. Tes upload ASLI menunggu dari HP Driyan (IP server tetap diblokir,
  jadi verifikasi ujung-ke-ujung hanya bisa dari perangkat user).
- TERKONFIRMASI JALAN 23 Okt 07:10 WIB: Driyan tes upload dari HP — berhasil ("udh bisa cia").
  Tahap 2 TUNTAS end-to-end.

## Koleksi Tema + Garis Waktu (23 Okt 2026, LIVE)
- Tombol ☆ Koleksi di halaman topik (toggle ★ Terkoleksi), halaman #/koleksi (daftar
  topik simpanan), halaman #/timeline (aktivitas: topikku, balasanku, balasan ke
  topikku, arus POSKOIN), dua-duanya juga jadi item menu dropdown avatar.
- API digabung di api/me.py (?part=fav|timeline) + rewrite vercel.json /api/fav &
  /api/timeline -> /api/me. ALASAN: batas Vercel Hobby = maks 12 Serverless Function
  per deployment — fav.py+timeline.py terpisah bikin 13 dan deploy GAGAL
  (error exceeded_serverless_functions_per_deployment, deployment dpl_E9jAgodj ERROR;
  URL uniknya menayangkan halaman placeholder Vercel yang sempat menipu cek "200" lama).
  Total fungsi sekarang TEPAT 12 — fitur API baru berikutnya WAJIB gabung ke fungsi
  yang ada atau konsolidasi endpoint lama.
- Deploy kini mode referensi SHA: deploy.py upload tiap file via upload_file
  (xVercelDigest=sha1) lalu create_deployment mereferensikan {file, sha, size} —
  payload argumen cuma ~2,3KB (dulu >131KB kena batas argv). Cek live deploy.py
  diperketat: wajib ada kata "POSKO" di body, bukan sekadar HTTP 200.
- Uji lokal 9/9 PASS (jalur rewrite), live: penanda UI ada di alias + /api/fav &
  /api/timeline balas 401 JSON.

## Mention @user + Notifikasi (23 Okt 2026, LIVE)
- Ngetag: tulis @username di isi topik/balasan — dirender jadi link profil (linkMentions
  di rich(); pola awal kata/spasi/'(', email tidak ikut). Tombol "Balas" di tiap balasan
  & di kepala topik otomatis menyisipkan @penulis ke kotak balasan (cara balas orang
  ala V2EX).
- Server: _db.notify_mentions() dipanggil topics.py & replies.py (best-effort,
  try/except; hanya user terdaftar, bukan diri sendiri, maks 10, dedupe) -> koleksi
  posko_notifs {user, from, kind:mention, topic, title, snippet, created, read}.
- API di me.py part=notif (rewrite /api/notif): GET {unread, items<=30},
  POST {all:true}|{id} tandai dibaca. Lencana angka merah di tombol avatar +
  item menu "Notifikasi (n)"; halaman #/notif (item belum-dibaca tersorot, membuka
  halaman otomatis menandai semua dibaca). Uji lokal 10/10 PASS; live terverifikasi
  (penanda UI di alias + /api/notif 401).

## Avatar Kustom Pixel + Toko POSKOIN (23 Okt 2026, LIVE)
- Atas design board Driyan (POSKO Avatar Creator): editor avatar pixel 48x48 digambar
  prosedural di canvas (JS avCompose, port setia dari lab Python di avatar-lab/).
  Katalog: kulit 4, gaya rambut 6, warna rambut 13, mata 4 + warna 6, alis 3, mulut 4,
  atasan 6, bawahan 3, aksesoris 9 (termasuk "none"). UI editor bertema POSKO (terang).
- Ekonomi: item premium dibeli POSK (AVATAR_SHOP di api/_db.py, harga 30-120; server
  otoritatif — katalog JS hanya cermin). Beli via POST /api/profile {action:"buy"}
  transaksional + tercatat sbg coin_tx type "shop". Simpan via {action:"custom"}
  divalidasi validate_avatar_config (item berbayar wajib owned).
- Penyimpanan: field user avatar_custom (JSON) + avatar_owned[]; avatar efektif
  "c:<json>" via effective_avatar() (user_public/current_user/avatars_for satu jalur);
  avatarHtml() merender "c:" via canvas->dataURL (cache). Memilih preset hewan di
  Edit Profil mengosongkan avatar_custom.
- Editor: menu avatar -> "Kustom Avatar" (#/avatar): tab Rambut/Wajah/Pakaian/
  Aksesoris, thumbnail = pratinjau avatar utuh per opsi, tombol Acak & Simpan.
- Uji lokal 13/13 PASS (saldo kurang ditolak, beli+idempoten, validasi kepemilikan,
  warna ngawur ditolak, legacy preset membersihkan custom) + render JS diverifikasi
  visual (avatar-lab/final-js.png). Deploy posko-5yqids5a8 live terverifikasi.

## Avatar v2 — chibi full-body gaya sheet baru (23 Okt 2026, LIVE)
- Driyan menilai avatar v1 (48px, sebatas dada) "masih jelek" dan mengirim design
  board "POSKO AVATAR BUILDER" yang jauh lebih kaya. Sheet-nya sendiri tidak bisa
  dipotong jadi layer (satu JPG datar, item tidak sejajar/skala beda, bg hitam) —
  jadi mesin digambar ulang mengikuti gayanya: canvas 64x64, chibi FULL BODY
  (kepala-tubuh-kaki-sepatu), outline gelap, shading rambut 3 lapis.
- Katalog v2: rambut 8 (+Ikal, +Kuncir Dua), mata 5 (+Berbinar), atasan 6,
  bawahan 4 (+Celana Pendek), SEPATU 4, aksesoris 10 (+Syal), PET 3 (Kucing Oren
  150, Penguin 120, Bebek 100), BINGKAI 4 (POSKO 80, Biru 60, Emas 150, Ungu 90).
- Config bertambah field shoes/pet/frame; validate_avatar_config mengisi default
  utk field yang hilang -> config v1 tersimpan tetap sah. Uji lokal 9/9 PASS.
- Lab: avatar-lab2/lab2.py (sumber gambar) -> port JS diverifikasi paritas piksel.
  Deploy posko-a332tnq4v live terverifikasi (penanda AV_PETS di alias produksi).

## Avatar disatukan satu halaman (23 Okt 2026, LIVE)
- Atas permintaan Driyan ("dijadikan satu aja biar gak numpuk dan rapi"):
  halaman #/avatar kini berjudul "Avatar" berisi DUA seksi dalam satu box:
  "Avatar Siap Pakai" (Huruf Aja + 6 preset hewan, klik = langsung pakai) dan
  "Buat Sendiri (Pixel)" (editor v2). Preset aktif tersorot; bila kustom aktif
  ada catatan "Avatar kustom buatanmu sedang aktif".
- Menu avatar: "Kustom Avatar" -> "Avatar". Form Edit Profil: grid pemilih
  avatar DIHAPUS, diganti baris ringkas (pratinjau + tombol "Ganti Avatar").
- Server: POST /api/profile kini update PARSIAL — {bio} saja tidak menyentuh
  avatar/kustom; {avatar} saja tidak menyentuh bio. Uji lokal 7/7 PASS.
  Deploy posko-g1lm0txnx live terverifikasi.
- Menu dropdown: item 'Avatar' DIHAPUS atas permintaan Driyan (akses avatar cukup dari Edit Profil -> tombol Ganti Avatar). Deploy posko-qaeuj3tmj.
- Aksi topik & balasan jadi tombol IKON SVG minimal (pensil/sampah/pin/gembok/koin-P/bookmark/balas), teks lama hilang; status aktif (pin/kunci/koleksi) tersorot hijau + tooltip judul. Deploy posko-53m5b7roc.
- Fix layout mobile: #wrap kolom kini align-items:stretch + #main width:100% (penyebab form Buat Topik menyempit ~62%: align-items:flex-start desktop bocor ke mode kolom). Deploy posko-8rip75nh5.

## Sistem Node / Pos Jaga Tahap 1+2 (23 Okt 2026, LIVE)
- Diskusi dulu atas permintaan Driyan; Cia usulkan 3 tahap, Driyan: "ok gas".
  Pilihan Cia utk poin yang tak dijawab eksplisit: buka pos pakai POSKOIN (opsi C).
- Node kini punya meta: color (ubin monogram 8 warna), owner (Penjaga), desc;
  ensure_nodes melengkapi node lama. GET /api/nodes -> {nodes:[meta+topics+
  followers], favs:[...]} (shape berubah dari array; frontend via getNodes()).
- POST /api/nodes: {action:"create"} nama 3-30, slug unik otomatis, biaya
  200 POSK transaksional (admin gratis), coin_tx type "node", pembuat auto-ikuti
  + jadi Penjaga. {action:"follow"/"unfollow"} -> koleksi posko_node_favs.
- Frontend: halaman #/pos "Peta Pos" (kartu pos + form buka pos + ikuti),
  sidebar "Pos Saya" + tile monogram berwarna, header #/node kaya (tile besar,
  penjaga, statistik, tombol Ikuti + "Buat Topik di Pos Ini" dgn preselect node),
  menu "Peta Pos". Uji lokal 16/16 PASS. Deploy posko-9hqlk9q1k.
- BELUM (Tahap 3): hak moderasi Penjaga di posnya sendiri (pin/kunci/hapus lokal).

## Pos Jaga Tahap 3 — moderasi Penjaga (23 Okt 2026, LIVE)
- Helper _db.can_moderate_node(user, node_id): admin global ATAU owner pos
  (owner "admin" = pos bawaan, khusus role admin — username "admin" tidak
  bisa menyamar jadi penjaga pos bawaan).
- moderate.py: pin/lock/delete kini lolos utk admin atau Penjaga pos topik itu.
- remove.py: hapus topik/balasan juga boleh oleh Penjaga pos terkait (balasan
  dicek lewat node topik induknya). Edit tulisan orang TETAP tidak boleh.
- Frontend pageTopic: ikon pin/kunci tampil utk admin+penjaga; ikon hapus
  topik utk penulis/admin/penjaga; ikon hapus balasan serupa (edit tetap
  penulis/admin saja). Uji matriks izin lokal 12/12 PASS.
  Deploy posko-j6hwpa6y6. Sistem Pos Jaga Tahap 1-3 TUNTAS.

## Konten Berbayar [jual=HARGA] (23 Okt 2026, LIVE) — opsi B: fee 10%
- Sintaks: [jual=50]isi rahasia[/jual] di topik/balasan; harga 1..100000 POSK,
  beberapa blok per tulisan (dibeli per blok, idx = urutan blok).
- _db: JUAL_RE, jual_parse, jual_strip (daftar & pencarian bebas isi berbayar),
  jual_censor (token [[JUAL-LOCKED/OPEN:kind:ref:idx:price]]; penulis/admin/
  pembeli OPEN), unlocks_of, coin_unlock (transaksional; fee = harga*10//100
  hangus ke "POSKO"; ledger: unlock net ke penulis + fee).
- topic.py kini sadar viewer (current_user): sensor topik+semua balasan;
  contentRaw HANYA utk penulis/admin (dipakai form edit frontend).
- coin.py action "unlock" {kind, id, idx} — harga dibaca server dari konten.
- Frontend: rich() sadar token (richText = renderer lama); kotak terkunci
  kuning dashed w/ ikon gembok SVG + tombol Buka (konfirmasi menampilkan
  rincian fee); kotak terbuka hijau; label riwayat unlock/fee.
- Uji lokal 21/21 PASS (sensor anon, beli, fee, dobel-beli ditolak, saldo
  kurang ditolak, beli punya sendiri ditolak, daftar & pencarian anti-bocor).
  Deploy posko-ia0vf8zay.

## Halaman Dokumen + SPLIT ASET (23 Okt 2026, LIVE)
- Halaman #/dokumen "Panduan POSKO" (fungsi pageDokumen di app.js): POSKOIN,
  menulis & embed, [jual], Pos/Penjaga, avatar, koleksi/notif, aturan.
  Link "Dokumen" ditambah di footer (.foot-links) atas permintaan Driyan.
- PENTING — struktur file berubah: index.html kini KURUS (1,6KB, markup saja);
  CSS pindah ke assets/app.css, JS pindah ke assets/app.js (deploy.py FILES
  diperbarui). Sebab: upload_file MCP mengangkut file sebagai base64 di argv
  (batas ~128KB/argumen) — index 103KB jebol (base64 ~138KB) dan deploy GAGAL
  "Argument list too long". Setelah split: app.js 89,5KB -> base64 ~119KB
  (headroom ~8KB mentah; kalau app.js tembus ~95KB, perlu minify).
- Patch frontend selanjutnya: JS -> assets/app.js, CSS -> assets/app.css,
  markup -> index.html. Cek sintaks: node --check assets/app.js.
- test_server.py memang API-only (statis 404 lokal itu normal; produksi
  Vercel melayani file statis dari root deployment).
  Deploy posko-25gy1xg9q.
- Fix layout Dokumen (23 Okt, deploy posko-o0kwebkvl): .cell di POSKO adalah
  flex-row (buat baris topik) — JANGAN pakai .cell untuk wadah teks banyak
  anak (jadi kolom menyamping). pageDokumen kini pakai .doc-body (display:block).

## Stiker POSKO + CDN GitHub (23 Okt 2026, LIVE)
- Jalur terpilih (diskusi): CDN sendiri, BUKAN API pihak ketiga (GIPHY wajib
  atribusi+limit; Tenor API MATI 30 Jun 2026).
- Repo: github.com/xhamzar/posko-stickers (publik; dibuat MANUAL oleh Driyan
  karena create_repository integrasi kena 403; push via git SSH key hatch —
  pola cia-launcher). Lokal: ~/workspace/posko-stickers/ (git, branch main).
- CDN: https://cdn.jsdelivr.net/gh/xhamzar/posko-stickers@main/ + manifest.json
  {packs:[{id,name,stickers:[{id,file,label}]}]}.
- Pack perdana "maskot": Kucing Songong 12 ekspresi, digambar prosedural PIL
  (~/workspace/posko-stickers-lab/draw.py; grid 48 -> 384 WebP lossless,
  border putih MaxFilter). Generator bisa nambah ekspresi/pack baru.
- Frontend: STICKER_CDN di app.js; tombol "Stiker" di form topik baru &
  balasan -> panel picker (fetch manifest, cache memori) -> sisip token
  [stiker:URL] di kursor; richText merender .post-sticker 118px. Uji render
  node OK. Deploy posko-qjp6tdwqw.
- Catatan ukuran: assets/app.js kini ~92KB mentah (base64 ~123KB) — mendekati
  batas argv upload ~128KB; pertumbuhan berikutnya mungkin perlu minify.
- Auto-deteksi stiker (23 Okt 2026, LIVE): picker kini loadStikPacks() =
  manifest.json (nama/label resmi + urutan) DIGABUNG daftar file repo via
  GitHub Trees API (api.github.com/.../git/trees/main?recursive=1, tanpa auth,
  CORS ok). Semua blob packs/<pack>/<file gambar: webp/png/gif/jpg/apng/avif>
  yang belum terdaftar manifest OTOMATIS jadi stiker (label dari nama file);
  folder baru = pack baru. Uji logika node 7/7 PASS. Deploy posko-2xjew1k5p.
  PERINGATAN UKURAN: app.js 93,9KB mentah (base64 ~125KB, batas argv ~128KB)
  — fitur frontend berikutnya WAJIB minify app.js/app.css dulu atau split lagi.
- Avatar ASET menggantikan avatar pixel prosedural (23 Okt 2026, LIVE,
  keputusan Driyan: ganti total, mode GRATIS dulu buat tes, koin menyusul,
  aset di GitHub OK):
  - Aset: 160 item PNG dibersihkan (alpha threshold; file isi dobel dipecah:
    face_13->a/b, backitem_5->a/b/c, handitem_21->a/b, pet_3->a/b) di repo
    xhamzar/posko-stickers folder avatar/<kategori>/ + avatar/manifest.json
    (kategori, jangkar %, rect bingkai, price per item=0). CDN jsDelivr
    AVA_CDN di app.js. Push perlu pull --rebase dulu (Driyan upload stiker
    via web). Kategori: body/face/mulut/hair/outfit/celana/spatu/acc/back/
    hand/pet/border/status.
  - Renderer avatarHtml: string "a:<json>" -> tumpukan <img> lapis sesuai
    AVA_ANCH (persen dari panggung 84x88, resep komposit Python teruji);
    legacy (preset/"c:") jatuh ke combo default. cls "big" + border =
    kartu profil setengah badan (jendela AVA_RECT, karakter 122%, pet &
    status melayang). Editor #/avatar BARU: katalog dari manifest + merge
    auto-deteksi GitHub Trees (file avatar baru di repo langsung muncul,
    price 0), tab kategori, opsi "Tidak pakai", Acak, Simpan.
  - Backend: _db.validate_asset_config (awalan id per kategori wajib,
    ASSET_PRICES={} -> semua gratis; isi harga di _db + manifest buat
    mode koin) simpan ke field avatar_asset; effective_avatar "a:" >
    "c:" > preset. profile.py action custom -> validator aset; buy ->
    ASSET_PRICES. Uji: renderer node 10/10, API lokal 7/7, data uji bersih.
  - BONUS: app.js menyusut 93,9KB -> 73,9KB (mesin pixel lama dibuang) —
    masalah batas argv deploy reda. Deploy posko-pnjaoev0j.
  - FIX tampilan avatar NGACO di halaman depan/profil (23 Okt 2026, deploy
    posko-dctrjcorn): penyebab = CSS warisan `.avatar img{width:100%;
    height:100%;object-fit:cover}` ikut menimpa `.avt-layer` di dalam
    .avatar (editor aman karena stagebox bukan .avatar) -> tiap lapis
    ketarik setinggi wadah & ter-crop (di screenshot cuma kelihatan topi
    raksasa). Fix app.css: `.avatar img.avt-layer{width:auto;height:auto;
    object-fit:contain}` (inline width % tetap menang; hand tetap pakai
    inline height) + `.avt-window .avt{height:auto}` (rasio 84/88 kartu).
    Terverifikasi: komposit PIL config live driyan versi buggy == screenshot,
    versi fix == karakter utuh; CSS produksi memuat kedua fix.

- 23 Okt 16:56 WIB: Kategori avatar **Punggung (back)** & **Mulut (mulut)** DINONAKTIFKAN sementara atas perintah Driyan (masih banyak bug, ia lagi males ngerjain). Implementasi: `AVA_DISABLED = ["back", "mulut"]` di `assets/app.js` — tab hilang dari editor, layer tidak dirender di avatar mana pun, config tersimpan tidak dihapus (data tetap di DB, tinggal hapus dari daftar untuk mengaktifkan lagi). Deploy posko-hzhgzz1ba LIVE, terverifikasi di alias produksi.

- 23 Okt 18:44 WIB: Domain **posko.ruru.my.id LIVE** — CNAME Cloudflare `posko` → `cname.vercel-dns.com` (DNS-only) akhirnya ditambahkan (Driyan sendiri), DNS publik terverifikasi via DoH (CNAME + IP Vercel 76.76.21.241/66.33.60.193), dan halaman berhasil dimuat browser: judul "POSKO — Pusat Obrolan & Sharing Komunitas Online", header/nav/footer render normal. Item CNAME yang tertunda sejak 22 Okt SELESAI. (Cek HTTPS dari sandbox tetap tidak bisa dipakai — egress sandbox ke Vercel 000/403, verifikasi pakai DoH + browser.)

- 23 Okt 19:02 WIB: Domain kedua **poskoo.my.id LIVE** — domain IDwebhost (NS idwebhost, bukan Cloudflare) ditambahkan Driyan ke Vercel (apex verified, redirect ke www), A apex → 216.198.79.1 (Vercel), CNAME www → cname.vercel-dns.com ditambahkan Driyan di panel IDwebhost, SSL Vercel terbit otomatis beberapa menit setelah DNS masuk; terverifikasi browser: www.poskoo.my.id render homepage POSKO penuh.

- 23 Okt 23:14 WIB: **Sistem Tag topik LIVE** (3 fase, deploy terakhir posko-px2buua3y). Skema: tag hanya dari penulis topik, maks 5/topik, dinormalisasi server (`normalize_tags` di `api/_db.py`: huruf kecil, spasi→-, 2-24 char, dedupe); field `tags` di doc topik + `topic_out`. Backend: POST /api/topics simpan tag, GET /api/topics?tag= filter, pencarian `q` ikut mencocokkan tag, POST /api/edit terima `tags`. Frontend: `tagPills()` (pil `#tag` di daftar topik & halaman topik), input Tag di form buat & edit topik, rute `#/tag/<tag>` (pageTag — daftar lintas node), blok **Tag Populer** di sidebar (dihitung dari semua topik, cache 60 dtk), CSS `.tag-pills/.tag-pill`. Backfill: topik Selamat Datang (perkenalan, pengumuman, posko), perkenalan Cia (perkenalan, cia), artikel AI (ai, deepseek, open-source, model-ai). Terverifikasi produksi: filter tag, cari via tag (q=model-ai), app.js terbaru di alias + www.poskoo.my.id + posko.ruru.my.id. Catatan: apex poskoo.my.id = redirect 308 ke www (bukan bug cache).

- 24 Okt 00:21 WIB: **Total view topik LIVE** (deploy posko-3gnga4nbj, dpl_CnMCyaTdQQyhbRVdRo39h9b7Hitb) atas permintaan Driyan ("bikin total view aja"). Skema: field `views` di doc topik (topik baru mulai 0; `topic_out` menyertakannya, default 0 utk topik lama); GET /api/topic?hit=1 menaikkan `views` dgn Increment atomik — frontend (pageTopic) mengirim hit=1 hanya sekali per sesi browser per topik (dedupe `sessionStorage "pv:<id>"`), jadi refresh/render ulang/balas tidak menggelembungkan angka; mode share /t/ TIDAK menghitung. Tampilan: "· N kali dilihat" di meta daftar topik (topicRow) & kepala halaman topik. Uji lokal 7/7 PASS (tanpa hit tetap, hit +1, daftar konsisten; data uji dibersihkan). Verifikasi produksi: app.js memuat penanda, hit +1 persis 3x berturut, tanpa hit tetap, daftar == detail (EVEngine berakhir 5 dari rangkaian uji; hit pertama pasca-deploy sempat +2 karena retry proxy egress saat cold start — bukan bug logika, dibuktikan probe lanjutan +1 konsisten).

- 23 Okt 23:52 WIB: **Kartu preview WhatsApp (Open Graph) LIVE** (deploy posko-6lkii61jb) atas permintaan Driyan (contoh kartu V2EX di WA). Isi: (1) meta OG/Twitter Card statis di `index.html` + gambar kartu khusus `assets/og-posko.jpg` (1200x630, 62KB, logo POSKOIN di atas hijau POSKO; WAJIB <90KB karena upload deploy per-file via argv base64); (2) rute bersih **`/t/<id>`** → rewrite vercel.json ke `api/topic.py?share=<id>` (mode share di topic.py — TANPA fungsi baru): HTML berisi og:title judul topik, og:description "oleh <author> · <kutipan isi 180 char>" (isi [jual] dibersihkan via jual_strip, URL dibuang), og:image = gambar pertama di isi (atau thumbnail YouTube, atau og-posko.jpg), lalu meta-refresh+JS redirect ke `/#/topic/<id>`; topik tidak ada → 404 + OG generik. (3) Tombol **Bagikan** (ikon share SVG) di halaman topik: navigator.share / salin link `/t/<id>`. CATATAN: link hash lama `#/topic/...` di WA hanya menampilkan kartu generik POSKO (fragmen # tidak dikirim ke server) — bagikan selalu pakai tombol Bagikan / link /t/. Terverifikasi produksi: /t/ EVEngine (judul+desc+url benar), /t/ topik Selamat Datang memakai gambar isi (GIF Imgur) sebagai og:image, /t/ id yang sudah dihapus → 404 + OG generik sesuai desain (kasus uji pertama ternyata topik tes [jual] Driyan yang sudah ia hapus sendiri), home OG, og-posko.jpg 200 image/jpeg.

## Fix daftar topik sempit (24 Okt 2026, deploy posko-4boe1tx40)
Bug: baris topik pertama di beranda menyempit (judul numpuk, tag vertikal, badge count ngambang di tengah). Sebab: .fr (tombol + Topik Baru, float:right) di .head bocor karena .head tanpa clearfix; .cell display:flex (BFC) menyempit menghindari float. Fix di assets/app.css: .box .head::after{content:"";display:block;clear:both} dan .count{align-self:flex-start;margin-top:1px} (badge nempel sejajar judul, bukan tengah baris).

## Fix scroll navigasi (24 Okt 2026)
Keluhan: klik link (mis. node Umum di sidebar) halaman berganti tapi scroll tetap di posisi lama -> terkesan halaman tidak termuat. Sebab: SPA mengganti isi #view pada hashchange tanpa reset scroll. Fix: listener hashchange di assets/app.js kini memanggil window.scrollTo(0,0) setiap perpindahan rute. Pemanggilan route() internal (unlock konten berbayar) sengaja TIDAK scroll agar posisi baca tidak hilang.

## Indikator loading (24 Okt 2026)
- #loadbar: bar hijau 3px fixed di atas layar (index.html + CSS lbslide), digerakkan loadStart/loadEnd dengan penghitung in-flight yang membungkus api() di app.js; tampil setelah 120ms, mati saat semua panggilan selesai. Upload imgbb (uploadImage) ikut memanggil loadStart/loadEnd.
- Skeleton: route() melacak _curRoute; saat rute berganti, #view langsung diisi skeletonHtml() (kotak shimmer + teks "Memuat…") sampai halaman selesai dirender. Render ulang rute yang sama (unlock [jual]) tidak memicu skeleton.

## Footer sadar status login (24 Okt 2026)
Footer (#foot-links) kini dirender renderNav() mengikuti store.me: tamu melihat Beranda/Dokumen/Masuk/Daftar; warga login melihat Beranda/POSKOIN/Buat Topik/Notifikasi (jumlah belum dibaca)/Profil Saya/Dokumen. HTML statis index.html memakai set tamu sebagai bawaan. Tombol kepala "Topik Terbaru" juga sadar status: tamu = "Masuk untuk Buat Topik" ke #/login; login = "+ Topik Baru".

## Halaman Tentang (24 Okt 2026)
Rute #/about (pageAbout di app.js, gaya .box.doc seperti Dokumen), dimodelkan dari v2ex.com/about: definisi, intro, harapan komunitas, 10 nilai yang dijaga, tur fitur, tautan Dokumen, kredit driyan. Link "Tentang" ada di footer (kedua set renderNav + HTML statis). Aturan AI disesuaikan dengan fakta Cia ikut posting di POSKO (wajib benar & bermanfaat, bukan larangan total ala V2EX).

## Avatar pixelated (24 Okt 2026, deploy posko-7d46oiyot)
Keluhan: avatar POSKO burik. Sebab: aset layer pixel art kecil (badan 40x66, wajah 49x47) di-scale halus (bilinear) saat tampil besar, apalagi di layar HP rapat. Fix di assets/app.css: image-rendering:pixelated pada .avt-layer, .avt-card .avt-pet/.avt-status, dan thumbnail editor .av-thumbwrap img. Catatan: preview editor (#av-preview, .av-thumb, .avatar-px) SUDAH pixelated sebelumnya — yang ketinggalan justru tampilan avatar di forum/profil. Ini memperbaiki cara tampil, bukan menambah detail: aset tetap resolusi aslinya.

## Avatar Model jadi (24 Okt 20:19 WIB, deploy posko-8125ouk6v)
- Tab **Model** baru di editor #/avatar (paling depan): karakter jadi siap pakai, GRATIS.
- 4 model (PNG transparan 800px, CDN jsDelivr avatar/model/): model_base (base cokelat),
  model_hitam (rambut hitam + jaket hitam + jeans), model_pink (twin-tail pink + hoodie
  putih + rok hitam), model_zombie (kulit hijau + hoodie abu robek).
- Cara kerja: config avatar `model:<id>`; render model didahulukan atas layer (avatarHtml
  & avaChar); pilih Model mereset layer, pilih layer/Acak menghapus model. Backend:
  `model` ditambahkan ke ASSET_CATS di api/_db.py (tanpa fungsi serverless baru).
- Verifikasi live: akun cia sempat dipasang model_pink (diterima backend, tampil di
  profil), lalu dikembalikan persis ke avatar awal (hair_gadis_2). Domain utama sudah
  menyajikan app.js baru.
- Catatan: file model dibuat dari gambar generate (webp 1600) via flood-fill background
  + hapus sisa bayangan; known_hosts GitHub sempat hilang (VM replacement) — dipasang
  ulang setelah verifikasi fingerprint.

## Fix katalog avatar nyangkut di cache (24 Okt 20:31 WIB, deploy posko-6bjqlgw4k)
- Gejala: teks editor avatar sudah baru tapi tab Model tidak muncul — penyebabnya
  manifest.json lama masih di-cache browser (daftar tab berasal dari manifest).
- Fix: loadAvaManifest kini memuat "manifest.json?v=2" (cache-buster) agar semua
  klien mengambil katalog terbaru.

## Avatar Model idle GIF (24 Okt 20:52 WIB, deploy posko-1b6zn3c1y)
- Item baru di tab Model: model_base_idle (GIF 512px, 382KB, 16 frame) — versi idle
  per-frame dari model base (kepala diam, rambut/baju/celana goyang, mata berkedip).
- avaImg() kini memakai .gif untuk id berakhiran _idle (id lain tetap .png).
- Verifikasi live: akun cia sempat dipasang model_base_idle lalu dikembalikan persis.
- Catatan: push sempat tertolak karena Driyan mengupload 3 stiker baru ke packs/maskot
  via web (15-2.png + 2 GIF) — di-rebase, tidak ada konflik.

## Bump katalog avatar v3 (24 Okt 20:59 WIB, deploy posko-o8yu62jpg)
- Gejala lanjutan: tab Model muncul tapi isinya masih 4 (idle belum ada) — browser
  Driyan masih memegang manifest.json?v=2 yang di-cache saat fix sebelumnya.
- Fix: bump ke manifest.json?v=3. Pelajaran: tiap ubah manifest, bump versi ini.

## Model zombie idle LIVE (24 Okt 21:25 WIB, deploy posko-doq91mwsd)
- GIF model_zombie_idle (versi perbaikan goyang sefase, 304.787B) di repo
  avatar/model/ (commit 43e61de), manifest v4 (app.js manifest.json?v=4).
- Bukti live: akun cia dipasang model_zombie_idle via /api/profile (diterima,
  tampil di profil publik) lalu dikembalikan PERSIS ke config awal
  (hair_gadis_2 dkk). Tab Model kini 6 item.

## Pagination daftar topik (2 Nov 2026, deploy posko-fg47osthl)
- Atas permintaan Driyan ("diposko itu gak ada pagenation ya" → "iya tambahin").
- Backend api/topics.py: param `page` & `per_page` (default 20, maks 50). Tanpa page → array
  polos seperti dulu (kompatibel). Dengan page → {topics,total,page,per_page,pages}.
  Bug sempat lolos: max(1,...) mengubah sentinel 0 jadi 1 → semua request kepagination;
  diperbaiki jadi max(0,...) lalu redeploy.
- Frontend assets/app.js: topicList(filter, page) selalu kirim page & normalisasi respons;
  helper pagerHTML(p, base) — tombol ‹ › + nomor halaman + ellipsis + "N topik".
  Pagination di: beranda (#/?page=N), node, tag, pencarian, profil member.
  Router parse ?page= dari hash; rkey menyertakan nomor halaman biar ganti halaman
  me-render ulang.
- CSS: .pg-wrap/.pg-btn/.pg-gap/.pg-info (flat, radius var(--radius), selaras .btn).
- Verifikasi live: /api/topics tanpa page → array 24; page=1&per_page=5 → 5 item;
  page=2 → item berbeda. Mode demo (DEMO=true) juga dipaginasi di sisi klien.
