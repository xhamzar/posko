# Fungsi gabungan area pribadi (hemat kuota 12 fungsi Vercel Hobby):
#   /api/fav      -> rewrite ke /api/me?part=fav      (Koleksi Tema)
#   /api/timeline -> rewrite ke /api/me?part=timeline (Garis Waktu)
from http.server import BaseHTTPRequestHandler
from urllib.parse import urlparse, parse_qs
import os, sys
sys.path.insert(0, os.path.dirname(__file__))
from _db import db, send_json, read_body, current_user, topic_out, avatars_for, now_iso

# ---------------- Koleksi Tema (bookmark topik) ----------------

def _fav_doc(username, topic_id):
    return username.lower() + "__" + topic_id

def fav_get(h):
    me = current_user(h)
    if not me:
        return send_json(h, {"error": "Harus masuk dulu"}, 401)
    favs = []
    q = db().collection("posko_favs").where("user", "==", me["username"])
    for s in q.stream():
        d = s.to_dict()
        favs.append({"topic": d.get("topic", ""), "created": d.get("created", "")})
    favs.sort(key=lambda x: x["created"], reverse=True)
    topics = []
    for f in favs:
        snap = db().collection("posko_topics").document(f["topic"]).get()
        if snap.exists:
            topics.append(topic_out(snap.id, snap.to_dict()))
    av = avatars_for([t["author"] for t in topics])
    for t in topics:
        t["avatar"] = av.get(t["author"], "")
    send_json(h, {"ids": [t["id"] for t in topics], "topics": topics})

def fav_post(h):
    me = current_user(h)
    if not me:
        return send_json(h, {"error": "Harus masuk dulu"}, 401)
    body = read_body(h)
    tid = str(body.get("topic") or "").strip()
    if not tid:
        return send_json(h, {"error": "Topik kosong"}, 400)
    if not db().collection("posko_topics").document(tid).get().exists:
        return send_json(h, {"error": "Topik tidak ditemukan"}, 404)
    ref = db().collection("posko_favs").document(_fav_doc(me["username"], tid))
    if ref.get().exists:
        ref.delete()
        return send_json(h, {"fav": False})
    ref.set({"user": me["username"], "topic": tid, "created": now_iso()})
    send_json(h, {"fav": True})

# ---------------- Garis Waktu (umpan aktivitas pribadi) ----------------

def _title_of(tid, cache):
    if tid not in cache:
        snap = db().collection("posko_topics").document(tid).get()
        cache[tid] = snap.to_dict().get("title", "") if snap.exists else "(topik terhapus)"
    return cache[tid]

def timeline_get(h):
    me = current_user(h)
    if not me:
        return send_json(h, {"error": "Harus masuk dulu"}, 401)
    name = me["username"]
    d = db()
    events = []
    titles = {}

    my_topics = []
    for s in d.collection("posko_topics").where("author", "==", name).stream():
        t = s.to_dict()
        my_topics.append(s.id)
        titles[s.id] = t.get("title", "")
        events.append({"kind": "topic", "ts": t.get("created", ""),
                       "topic": s.id, "title": t.get("title", "")})

    for s in d.collection("posko_replies").where("author", "==", name).stream():
        r = s.to_dict()
        events.append({"kind": "reply", "ts": r.get("created", ""),
                       "topic": r.get("topic", ""),
                       "title": _title_of(r.get("topic", ""), titles),
                       "snippet": (r.get("content", "") or "")[:90]})

    for i in range(0, len(my_topics), 30):
        chunk = my_topics[i:i + 30]
        if not chunk:
            continue
        for s in d.collection("posko_replies").where("topic", "in", chunk).stream():
            r = s.to_dict()
            if r.get("author") == name:
                continue
            events.append({"kind": "reply_in", "ts": r.get("created", ""),
                           "topic": r.get("topic", ""),
                           "title": _title_of(r.get("topic", ""), titles),
                           "author": r.get("author", ""),
                           "snippet": (r.get("content", "") or "")[:90]})

    seen_tx = set()
    for field in ("to", "from"):
        for s in d.collection("posko_coin_tx").where(field, "==", name).stream():
            if s.id in seen_tx:
                continue
            seen_tx.add(s.id)
            x = s.to_dict()
            events.append({"kind": "coin", "ts": x.get("created", ""),
                           "amount": int(x.get("amount", 0) or 0),
                           "type": x.get("type", ""), "note": x.get("note", ""),
                           "from": x.get("from"), "to": x.get("to")})

    events.sort(key=lambda e: e["ts"], reverse=True)
    send_json(h, {"events": events[:60]})

# ---------------- Notifikasi (mention) ----------------

def notif_get(h):
    me = current_user(h)
    if not me:
        return send_json(h, {"error": "Harus masuk dulu"}, 401)
    items = []
    q = db().collection("posko_notifs").where("user", "==", me["username"])
    for s in q.stream():
        d = s.to_dict()
        items.append({"id": s.id, "from": d.get("from", ""), "kind": d.get("kind", ""),
                      "topic": d.get("topic", ""), "title": d.get("title", ""),
                      "snippet": d.get("snippet", ""), "created": d.get("created", ""),
                      "read": bool(d.get("read"))})
    items.sort(key=lambda x: x["created"], reverse=True)
    unread = sum(1 for x in items if not x["read"])
    send_json(h, {"unread": unread, "items": items[:30]})

def notif_post(h):
    me = current_user(h)
    if not me:
        return send_json(h, {"error": "Harus masuk dulu"}, 401)
    body = read_body(h)
    d = db()
    if body.get("id"):
        ref = d.collection("posko_notifs").document(str(body["id"]))
        snap = ref.get()
        if snap.exists and snap.to_dict().get("user") == me["username"]:
            ref.update({"read": True})
    else:  # tandai semua dibaca
        q = d.collection("posko_notifs").where("user", "==", me["username"]).where("read", "==", False)
        for s in q.stream():
            s.reference.update({"read": True})
    unread = 0
    q = d.collection("posko_notifs").where("user", "==", me["username"]).where("read", "==", False)
    unread = len(list(q.stream()))
    send_json(h, {"unread": unread})

# ---------------- dispatcher ----------------

def _part(h):
    q = parse_qs(urlparse(h.path).query)
    return (q.get("part") or [""])[0]

class handler(BaseHTTPRequestHandler):
    def do_GET(self):
        try:
            if _part(self) == "timeline":
                return timeline_get(self)
            if _part(self) == "notif":
                return notif_get(self)
            return fav_get(self)
        except Exception as e:
            send_json(self, {"error": "Gagal memuat: %s" % e}, 500)

    def do_POST(self):
        try:
            if _part(self) == "timeline":
                return send_json(self, {"error": "Tidak didukung"}, 405)
            if _part(self) == "notif":
                return notif_post(self)
            return fav_post(self)
        except Exception as e:
            send_json(self, {"error": "Gagal mengubah koleksi: %s" % e}, 500)

    def log_message(self, *a):
        pass
