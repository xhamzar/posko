# POST /api/edit (login) {kind: topic|reply, id, title?, content}
# Hanya penulis asli atau admin yang boleh mengedit.
from http.server import BaseHTTPRequestHandler
import os, sys
sys.path.insert(0, os.path.dirname(__file__))
from _db import db, current_user, now_iso, read_body, send_json, normalize_tags

class handler(BaseHTTPRequestHandler):
    def do_POST(self):
        try:
            user = current_user(self)
            if not user:
                return send_json(self, {"error": "Harus masuk dulu"}, 401)
            b = read_body(self)
            kind = (b.get("kind") or "").strip()
            did = (b.get("id") or "").strip()
            content = (b.get("content") or "").strip()
            col = {"topic": "posko_topics", "reply": "posko_replies"}.get(kind)
            if not col:
                return send_json(self, {"error": "Jenis tidak dikenal"}, 400)
            ref = db().collection(col).document(did)
            snap = ref.get()
            if not snap.exists:
                return send_json(self, {"error": "Tidak ditemukan"}, 404)
            d = snap.to_dict()
            if d.get("author") != user["username"] and user["role"] != "admin":
                return send_json(self, {"error": "Ini bukan tulisanmu"}, 403)
            if not content:
                return send_json(self, {"error": "Isi tidak boleh kosong"}, 400)
            upd = {"content": content[:20000], "edited": now_iso()}
            if kind == "topic":
                title = (b.get("title") or "").strip()
                if len(title) < 3:
                    return send_json(self, {"error": "Judul minimal 3 karakter"}, 400)
                upd["title"] = title[:160]
                if "tags" in b:
                    upd["tags"] = normalize_tags(b.get("tags"))
            ref.update(upd)
            send_json(self, {"ok": True})
        except Exception as e:
            send_json(self, {"error": "Gagal mengedit: %s" % e}, 500)
    def log_message(self, *a):
        pass
