# POST /api/remove (login) {kind: topic|reply, id}
# Penulis atau admin. Hapus topik sekalian menghapus semua balasannya;
# hapus balasan mengurangi replyCount topiknya.
from http.server import BaseHTTPRequestHandler
import os, sys
sys.path.insert(0, os.path.dirname(__file__))
from _db import db, current_user, read_body, send_json, can_moderate_node
from firebase_admin import firestore as _fs

class handler(BaseHTTPRequestHandler):
    def do_POST(self):
        try:
            user = current_user(self)
            if not user:
                return send_json(self, {"error": "Harus masuk dulu"}, 401)
            b = read_body(self)
            kind = (b.get("kind") or "").strip()
            did = (b.get("id") or "").strip()
            col = {"topic": "posko_topics", "reply": "posko_replies"}.get(kind)
            if not col:
                return send_json(self, {"error": "Jenis tidak dikenal"}, 400)
            ref = db().collection(col).document(did)
            snap = ref.get()
            if not snap.exists:
                return send_json(self, {"error": "Tidak ditemukan"}, 404)
            d = snap.to_dict()
            if d.get("author") != user["username"] and user["role"] != "admin":
                # Penjaga boleh menghapus di posnya sendiri
                if kind == "topic":
                    node_id = d.get("node")
                else:
                    tsnap = db().collection("posko_topics").document(
                        d.get("topic", "")).get()
                    node_id = tsnap.to_dict().get("node") if tsnap.exists else None
                if not can_moderate_node(user, node_id):
                    return send_json(self, {"error": "Ini bukan tulisanmu"}, 403)
            if kind == "reply":
                ref.delete()
                tref = db().collection("posko_topics").document(d.get("topic", ""))
                if tref.get().exists:
                    tref.update({"replyCount": _fs.Increment(-1)})
            else:
                for r in db().collection("posko_replies").where("topic", "==", did).stream():
                    r.reference.delete()
                ref.delete()
            send_json(self, {"ok": True})
        except Exception as e:
            send_json(self, {"error": "Gagal menghapus: %s" % e}, 500)
    def log_message(self, *a):
        pass
