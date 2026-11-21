# Profil member POSKO.
# GET  /api/profile?user=<username> -> profil publik + statistik {topics, replies}
# POST /api/profile (login) {bio, avatar} -> ubah profil sendiri -> profil terbaru
from http.server import BaseHTTPRequestHandler
from urllib.parse import urlparse, parse_qs
import os, sys
sys.path.insert(0, os.path.dirname(__file__))
from _db import (db, current_user, read_body, send_json, user_public,
                 AVATAR_IDS, ASSET_PRICES, validate_asset_config, _coin_tx)

class handler(BaseHTTPRequestHandler):
    def do_GET(self):
        try:
            q = parse_qs(urlparse(self.path).query)
            uname = (q.get("user") or [""])[0].strip()
            p = user_public(uname)
            if not p:
                return send_json(self, {"error": "User tidak ditemukan"}, 404)
            name = p["username"]
            topics = sum(1 for _ in db().collection("posko_topics").where("author", "==", name).stream())
            replies = sum(1 for _ in db().collection("posko_replies").where("author", "==", name).stream())
            p["stats"] = {"topics": topics, "replies": replies}
            send_json(self, p)
        except Exception as e:
            send_json(self, {"error": "Gagal memuat profil: %s" % e}, 500)

    def do_POST(self):
        try:
            user = current_user(self)
            if not user:
                return send_json(self, {"error": "Harus masuk dulu"}, 401)
            b = read_body(self)
            action = b.get("action") or ""
            uref = db().collection("posko_users").document(user["username"].lower())
            if action == "buy":
                item = (b.get("item") or "").strip()
                price = ASSET_PRICES.get(item)
                if price is None:
                    return send_json(self, {"error": "Item tidak dijual"}, 400)
                owned = list(user.get("owned") or [])
                if item in owned:
                    p = user_public(user["username"])
                    return send_json(self, {"owned": p["owned"], "balance": p["coins"]})
                from firebase_admin import firestore as _fs
                d = db()
                tx = d.transaction()

                @_fs.transactional
                def _buy(tx):
                    snap = uref.get(transaction=tx)
                    bal = int(snap.to_dict().get("coins", 0) or 0)
                    if bal < price:
                        raise ValueError("Saldo POSK tidak cukup (butuh %d)" % price)
                    cur = list(snap.to_dict().get("avatar_owned", []) or [])
                    if item not in cur:
                        cur.append(item)
                    tx.update(uref, {"coins": bal - price, "avatar_owned": cur})

                try:
                    _buy(tx)
                except ValueError as ve:
                    return send_json(self, {"error": str(ve)}, 400)
                _coin_tx(user["username"], None, price, "shop", "Beli item avatar " + item)
                p = user_public(user["username"])
                return send_json(self, {"owned": p["owned"], "balance": p["coins"]})
            if action == "custom":
                cfg_json, err = validate_asset_config(b.get("config"),
                                                      user.get("owned") or [])
                if err:
                    return send_json(self, {"error": err}, 400)
                uref.update({"avatar_asset": cfg_json, "avatar_custom": ""})
                return send_json(self, user_public(user["username"]))
            # update parsial: kirim "bio" saja / "avatar" saja juga bisa,
            # field lain tidak disentuh (avatar & editor kustom kini satu halaman)
            updates = {}
            if "bio" in b:
                updates["bio"] = (b.get("bio") or "").strip()[:160]
            if "avatar" in b:
                avatar = (b.get("avatar") or "").strip()
                if avatar and avatar not in AVATAR_IDS:
                    return send_json(self, {"error": "Avatar tidak dikenal"}, 400)
                updates["avatar"] = avatar
                updates["avatar_custom"] = ""
            if updates:
                uref.update(updates)
            send_json(self, user_public(user["username"]))
        except Exception as e:
            send_json(self, {"error": "Gagal menyimpan profil: %s" % e}, 500)
    def log_message(self, *a):
        pass
