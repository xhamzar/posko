# POST /api/replies (login) {topic,content} -> {id}; update last + replyCount topik.
from http.server import BaseHTTPRequestHandler
import os, sys
sys.path.insert(0, os.path.dirname(__file__))
from _db import (db, current_user, now_iso, read_body, send_json,
                 COIN_MIN_REPLY_LEN, coin_award_activity, coin_balance,
                 notify_mentions)
from firebase_admin import firestore as _fs

class handler(BaseHTTPRequestHandler):
    def do_POST(self):
        try:
            user = current_user(self)
            if not user:
                return send_json(self, {"error": "Harus masuk dulu"}, 401)
            b = read_body(self)
            tid = (b.get("topic") or "").strip()
            content = (b.get("content") or "").strip()
            if not content:
                return send_json(self, {"error": "Balasan tidak boleh kosong"}, 400)
            tref = db().collection("posko_topics").document(tid)
            tsnap = tref.get()
            if not tsnap.exists:
                return send_json(self, {"error": "Topik tidak ditemukan"}, 404)
            if tsnap.to_dict().get("locked"):
                return send_json(self, {"error": "Topik ini terkunci"}, 403)
            ts = now_iso()
            ref = db().collection("posko_replies").document()
            ref.set({"topic": tid, "author": user["username"],
                     "content": content[:20000], "created": ts})
            tref.update({"last": ts, "replyCount": _fs.Increment(1)})
            try:
                notify_mentions(user["username"], content, tid,
                                tsnap.to_dict().get("title", ""))
            except Exception:
                pass
            awarded = 0
            try:
                if len(content) >= COIN_MIN_REPLY_LEN:
                    awarded = coin_award_activity(user["username"], "reply")
            except Exception:
                pass
            send_json(self, {"id": ref.id, "awarded": awarded,
                             "balance": coin_balance(user["username"])})
        except Exception as e:
            send_json(self, {"error": "Gagal mengirim balasan: %s" % e}, 500)
    def log_message(self, *a):
        pass
