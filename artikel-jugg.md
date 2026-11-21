Halo warga POSKO!

Buat yang pernah ngoding Android, pasti tahu rasanya lagi semangat ngubah satu tombol atau benerin teks, terus harus nunggu Gradle build selesai dulu sebelum hasilnya kelihatan. Kadang yang diubah cuma sebaris, tapi waktu nunggunya cukup buat bikin kopi dulu.

Nah, Cia baru nemu plugin yang cukup menarik namanya Jugg. Ini plugin Android Studio buatan tim engineering Tencent Music. Fokusnya satu: bikin perubahan kode atau resource bisa cepat tampil di HP atau emulator, klaimnya sekitar 3 detik untuk perubahan harian.

Cara kerjanya sebenarnya simpel. Build Gradle normal tetap dipakai sekali untuk bikin baseline. Setelah itu, Jugg memantau apa saja yang berubah, lalu hanya mengompilasi bagian yang berubah beserta kode yang ikut terdampak. Hasilnya langsung dikirim ke aplikasi yang sedang jalan lewat hot reload. Kalau hot reload tidak cocok, masih ada jalur hot fix, update APK incremental, atau kembali ke build Gradle biasa.

Yang Cia suka, plugin ini tidak minta proyek dirombak. Tidak perlu nambah SDK khusus dan tidak perlu mengubah script Gradle cuma buat mencobanya. Jugg punya Run Configuration sendiri yang bisa hidup berdampingan dengan konfigurasi bawaan Android Studio. Jadi kalau lagi pengin cepat, pakai Jugg. Kalau mau jalur standar, tinggal pindah lagi.

Dukungannya juga cukup luas: Java, Kotlin, Jetpack Compose, Compose Multiplatform, resource, assets, AndroidManifest, sampai library native. Wajar sih, soalnya teknologi ini sebelumnya dipakai di aplikasi-aplikasi besar Tencent Music seperti QQ Music, JOOX, dan Kugou, dengan klaim sudah melewati lebih dari 800 ribu kali incremental build.

Tapi jangan dibayangkan ini sulap yang selalu berhasil ya. Build pertama tetap harus jalan untuk bikin baseline. Perubahan yang terlalu rumit juga bisa jatuh kembali ke proses Gradle biasa. Pembuatnya sendiri bilang Jugg lebih cocok buat debug dan iterasi harian, bukan untuk bikin paket release final yang mau dipublikasikan. Buat rilis resmi, jalur build standar tetap yang paling aman.

Ada cerita lucu juga di balik namanya. Jugg terinspirasi dari Juggernaut, hero Dota yang dijuluki Jian Sheng. Pembuatnya memang fans Dota. Ikon awalnya bahkan jauh lebih mirip, tapi setelah dibantu cek dan dibilang ada risiko copyright, ikonnya akhirnya digambar manual supaya lebih aman. Jadi selain jago bikin tools Android, dia juga hati-hati soal logo, hehe.

Menurut Cia, Jugg ini bagus dan layak dicoba kalau proyek Android kalian sudah besar dan tiap build terasa lama banget. Buat proyek kecil, manfaatnya mungkin tidak terlalu kerasa karena build biasa juga belum tentu lama. Tapi idenya keren: waktu developer harusnya habis buat mikir dan ngoding, bukan buat bengong menatap progress bar Gradle.

Nah, warga POSKO yang ngoding Android, rekor build terlama kalian berapa menit? Dan biasanya kalian tungguin, tinggal ngopi, atau tinggal tidur sekalian?

Sumber:
https://github.com/tencentmusic/jugg
https://www.v2ex.com/t/1239220
