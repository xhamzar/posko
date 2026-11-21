# POSKO — Forum Online ala V2EX

Forum komunitas ringan: Python serverless (Vercel) + Firestore + frontend
vanilla HTML/CSS/JS. Live di https://poskoo.my.id

## Struktur

- `index.html`, `assets/` — frontend (SPA vanilla, tanpa build step)
- `api/` — endpoint Python (Vercel Serverless Functions): auth mandiri
  (PBKDF2 + token sesi HMAC), topik, balasan, moderasi, profil, koin
- `deploy.py` — deploy ke Vercel via MCP (butuh kredensial lokal, lihat bawah)
- `artikel-*.md` + `post_*.py` — draf artikel & skrip posting ke forum
- `avatar-lab/`, `avatar-lab2/` — eksperimen generator avatar
- `NOTES.md` — catatan pengembangan

## Kredensial (tidak ikut repo)

- `FIREBASE_SERVICE_ACCOUNT` — JSON service account Firebase (env Vercel)
- `POSKO_SECRET` — rahasia token sesi (env Vercel)
- `POSKO_IMGBB_KEY` — kunci upload gambar (env Vercel)

Jangan pernah commit `api/_sa.json`, `serviceAccount.json`, atau `.env`.

## Jalankan lokal

```bash
FIREBASE_SERVICE_ACCOUNT="$(cat serviceAccount.json)" python3 test_server.py
```
