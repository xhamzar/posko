# GET  /api/nodes            -> {nodes: [...meta], favs: [id...] (bila login)}
# POST /api/nodes (login) {action:"create", name, desc, color} -> buka Pos Jaga
# POST /api/nodes (login) {action:"follow"|"unfollow", node}  -> ikuti pos
from http.server import BaseHTTPRequestHandler
import os, sys
sys.path.insert(0, os.path.dirname(__file__))
from _db import (db, ensure_nodes, send_json, read_body, current_user,
                 node_meta, make_node_id, NODE_COLORS, NODE_CREATE_COST,
                 _coin_tx, now_iso)


class handler(BaseHTTPRequestHandler):
    def do_GET(self):
        try:
            nodes = ensure_nodes()
            favs = []
            user = current_user(self)
            if user:
                favs = [d.to_dict()["node"] for d in db().collection("posko_node_favs")
                        .where("user", "==", user["username"]).stream()]
            send_json(self, {"nodes": [node_meta(n) for n in nodes], "favs": favs})
        except Exception as e:
            send_json(self, {"error": "Gagal memuat node: %s" % e}, 500)

    def do_POST(self):
        try:
            user = current_user(self)
            if not user:
                return send_json(self, {"error": "Harus masuk dulu"}, 401)
            b = read_body(self)
            action = b.get("action") or ""
            d = db()
            if action in ("follow", "unfollow"):
                node_id = (b.get("node") or "").strip()
                if not d.collection("posko_nodes").document(node_id).get().exists:
                    return send_json(self, {"error": "Pos tidak ditemukan"}, 404)
                ref = d.collection("posko_node_favs").document(
                    "%s__%s" % (user["username"].lower(), node_id))
                if action == "follow":
                    ref.set({"user": user["username"], "node": node_id,
                             "created": now_iso()})
                else:
                    ref.delete()
                n = node_meta({"id": node_id})
                return send_json(self, {"fav": action == "follow",
                                        "followers": n["followers"]})
            if action == "create":
                name = (b.get("name") or "").strip()
                desc = (b.get("desc") or "").strip()[:120]
                color = b.get("color") or NODE_COLORS[0]
                if len(name) < 3 or len(name) > 30:
                    return send_json(self, {"error": "Nama pos 3-30 karakter"}, 400)
                if color not in NODE_COLORS:
                    return send_json(self, {"error": "Warna tidak dikenal"}, 400)
                existing = [n["id"] for n in ensure_nodes()]
                node_id = make_node_id(name, set(existing))
                uname = user["username"]
                is_admin = user.get("role") == "admin"
                col = d.collection("posko_nodes")
                if not is_admin:
                    from firebase_admin import firestore as _fs
                    uref = d.collection("posko_users").document(uname.lower())
                    tx = d.transaction()

                    @_fs.transactional
                    def _pay(tx):
                        snap = uref.get(transaction=tx)
                        bal = int(snap.to_dict().get("coins", 0) or 0)
                        if bal < NODE_CREATE_COST:
                            raise ValueError(
                                "Saldo POSK tidak cukup (butuh %d)" % NODE_CREATE_COST)
                        tx.update(uref, {"coins": bal - NODE_CREATE_COST})

                    try:
                        _pay(tx)
                    except ValueError as ve:
                        return send_json(self, {"error": str(ve)}, 400)
                    _coin_tx(uname, None, NODE_CREATE_COST, "node",
                             "Buka Pos Jaga " + name)
                order = max([n.get("order", 0) for n in ensure_nodes()] + [0]) + 1
                doc = {"id": node_id, "name": name, "desc": desc,
                       "color": color, "owner": uname, "order": order,
                       "created": now_iso()}
                col.document(node_id).set(doc)
                d.collection("posko_node_favs").document(
                    "%s__%s" % (uname.lower(), node_id)).set(
                    {"user": uname, "node": node_id, "created": now_iso()})
                return send_json(self, {"node": node_meta(doc)}, 201)
            return send_json(self, {"error": "Aksi tidak dikenal"}, 400)
        except Exception as e:
            send_json(self, {"error": "Gagal memproses node: %s" % e}, 500)

    def log_message(self, *a):
        pass
