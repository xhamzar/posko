# POSKOIN — koin internal POSKO.
# GET  /api/coin (auth)            -> {balance, history:[...]} saldo + riwayat sendiri
# GET  /api/coin?user=<username>   -> {username, balance} publik (buat halaman profil)
# POST /api/coin (auth)  {action:"tip", to, amount}   -> {ok:true, balance}
# POST /api/coin (admin) {action:"grant", to, amount} -> {ok:true, balance}
#   grant amount negatif = tarik saldo (revoke).
from http.server import BaseHTTPRequestHandler
from urllib.parse import urlparse, parse_qs
import os, sys
sys.path.insert(0, os.path.dirname(__file__))
from _db import (db, current_user, read_body, send_json,
                 coin_balance, coin_credit, coin_tip, coin_revoke, coin_unlock)

MAX_TIP = 1000
MAX_GRANT = 100000

class handler(BaseHTTPRequestHandler):
    def do_GET(self):
        try:
            q = parse_qs(urlparse(self.path).query)
            uname = (q.get("user") or [""])[0].strip()
            if uname:
                snap = db().collection("posko_users").document(uname.lower()).get()
                if not snap.exists:
                    return send_json(self, {"error": "User tidak ditemukan"}, 404)
                u = snap.to_dict()
                return send_json(self, {"username": u["username"],
                                        "balance": int(u.get("coins", 0) or 0)})
            user = current_user(self)
            if not user:
                return send_json(self, {"error": "Harus masuk dulu"}, 401)
            me = user["username"]
            seen, hist = {}, []
            col = db().collection("posko_coin_tx")
            for field in ("from", "to"):
                for s in col.where(field, "==", me).stream():
                    if s.id not in seen:
                        seen[s.id] = True
                        d = s.to_dict()
                        hist.append({"from": d.get("from"), "to": d.get("to"),
                                     "amount": int(d.get("amount", 0) or 0),
                                     "type": d.get("type", ""), "note": d.get("note", ""),
                                     "created": d.get("created", "")})
            hist.sort(key=lambda x: x["created"], reverse=True)
            send_json(self, {"balance": coin_balance(me), "history": hist[:30]})
        except Exception as e:
            send_json(self, {"error": "Gagal memuat POSKOIN: %s" % e}, 500)

    def do_POST(self):
        try:
            user = current_user(self)
            if not user:
                return send_json(self, {"error": "Harus masuk dulu"}, 401)
            b = read_body(self)
            action = (b.get("action") or "").strip()
            if action == "unlock":
                kind = (b.get("kind") or "").strip()
                ref = (b.get("id") or "").strip()
                try:
                    idx = int(b.get("idx"))
                except Exception:
                    return send_json(self, {"error": "Blok tidak valid"}, 400)
                if kind not in ("topic", "reply") or not ref:
                    return send_json(self, {"error": "Konten tidak valid"}, 400)
                bal = coin_unlock(user["username"], kind, ref, idx)
                return send_json(self, {"ok": True, "balance": bal})
            to = (b.get("to") or "").strip()
            try:
                amount = int(b.get("amount"))
            except Exception:
                return send_json(self, {"error": "Jumlah POSK tidak valid"}, 400)
            target = db().collection("posko_users").document(to.lower()).get()
            if not target.exists:
                return send_json(self, {"error": "User tujuan tidak ditemukan"}, 404)
            to_name = target.to_dict()["username"]
            if action == "tip":
                if to_name.lower() == user["username"].lower():
                    return send_json(self, {"error": "Tidak bisa kasih tip ke diri sendiri"}, 400)
                if amount < 1 or amount > MAX_TIP:
                    return send_json(self, {"error": "Tip antara 1 sampai %d POSK" % MAX_TIP}, 400)
                bal = coin_tip(user["username"], to_name, amount)
                return send_json(self, {"ok": True, "balance": bal})
            if action == "grant":
                if user["role"] != "admin":
                    return send_json(self, {"error": "Hanya admin yang bisa grant POSKOIN"}, 403)
                if amount == 0 or abs(amount) > MAX_GRANT:
                    return send_json(self, {"error": "Jumlah grant tidak valid"}, 400)
                if amount > 0:
                    bal = coin_credit(to_name, amount, "grant",
                                      "Grant dari admin " + user["username"],
                                      frm=user["username"])
                else:
                    bal = coin_revoke(to_name, -amount, user["username"])
                return send_json(self, {"ok": True, "balance": bal})
            send_json(self, {"error": "Aksi tidak dikenal"}, 400)
        except ValueError as e:
            send_json(self, {"error": str(e)}, 400)
        except Exception as e:
            send_json(self, {"error": "Gagal memproses POSKOIN: %s" % e}, 500)
    def log_message(self, *a):
        pass
