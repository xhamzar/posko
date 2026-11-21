# POST /api/moderate (admin) {topic, action: pin|lock|delete} -> {ok:true}
from http.server import BaseHTTPRequestHandler
import os, sys
sys.path.insert(0, os.path.dirname(__file__))
from _db import db, current_user, read_body, send_json, can_moderate_node

class handler(BaseHTTPRequestHandler):
    def do_POST(self):
        try:
            user = current_user(self)
            if not user:
                return send_json(self, {"error": "Harus masuk dulu"}, 401)
            b = read_body(self)
            tid = (b.get("topic") or "").strip()
            action = (b.get("action") or "").strip()
            tref = db().collection("posko_topics").document(tid)
            snap = tref.get()
            if not snap.exists:
                return send_json(self, {"error": "Topik tidak ditemukan"}, 404)
            d = snap.to_dict()
            if not can_moderate_node(user, d.get("node")):
                return send_json(self, {"error": "Khusus admin POSKO atau Penjaga pos ini"}, 403)
            if action == "pin":
                tref.update({"pinned": not d.get("pinned", False)})
            elif action == "lock":
                tref.update({"locked": not d.get("locked", False)})
            elif action == "delete":
                for r in db().collection("posko_replies").where("topic", "==", tid).stream():
                    r.reference.delete()
                tref.delete()
            else:
                return send_json(self, {"error": "Aksi tidak dikenal"}, 400)
            send_json(self, {"ok": True})
        except Exception as e:
            send_json(self, {"error": "Gagal moderasi: %s" % e}, 500)
    def log_message(self, *a):
        pass
