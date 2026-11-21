# GET  /api/topics?node=&q=&author=&tag=&page=&per_page= -> daftar topik (pin dulu, lalu aktivitas terbaru)
#   tanpa page: array semua topik (kompatibel lama); dengan page: {topics,total,page,per_page,pages}
# POST /api/topics (login) {node,title,content} -> {id}
from http.server import BaseHTTPRequestHandler
from urllib.parse import urlparse, parse_qs
import os, sys
sys.path.insert(0, os.path.dirname(__file__))
from _db import (db, current_user, now_iso, read_body, send_json, topic_out,
                 coin_award_activity, coin_balance, avatars_for,
                 notify_mentions, jual_strip, normalize_tags)

class handler(BaseHTTPRequestHandler):
    def do_GET(self):
        try:
            q = parse_qs(urlparse(self.path).query)
            node = (q.get("node") or [""])[0]
            query = (q.get("q") or [""])[0].lower()
            author = (q.get("author") or [""])[0]
            tag = (q.get("tag") or [""])[0].strip().lower()
            try: page = max(0, int((q.get("page") or [""])[0] or 0))
            except ValueError: page = 0
            try: per_page = min(50, max(1, int((q.get("per_page") or ["20"])[0] or 20)))
            except ValueError: per_page = 20
            out = []
            for snap in db().collection("posko_topics").stream():
                d = snap.to_dict()
                if node and d.get("node") != node:
                    continue
                if author and d.get("author") != author:
                    continue
                if tag and tag not in (d.get("tags") or []):
                    continue
                if query and query not in (d.get("title", "") + " " + jual_strip(d.get("content", "")) + " " + " ".join(d.get("tags") or [])).lower():
                    continue
                t = topic_out(snap.id, d)
                t["content"] = jual_strip(t["content"])
                out.append(t)
            out.sort(key=lambda t: t["last"], reverse=True)
            out.sort(key=lambda t: not t["pinned"])
            if not page:
                av = avatars_for([t["author"] for t in out])
                for t in out:
                    t["avatar"] = av.get(t["author"], "")
                return send_json(self, out)
            total = len(out)
            pages = max(1, (total + per_page - 1) // per_page)
            page = min(page, pages)
            items = out[(page - 1) * per_page:page * per_page]
            av = avatars_for([t["author"] for t in items])
            for t in items:
                t["avatar"] = av.get(t["author"], "")
            send_json(self, {"topics": items, "total": total, "page": page,
                             "per_page": per_page, "pages": pages})
        except Exception as e:
            send_json(self, {"error": "Gagal memuat topik: %s" % e}, 500)

    def do_POST(self):
        try:
            user = current_user(self)
            if not user:
                return send_json(self, {"error": "Harus masuk dulu"}, 401)
            b = read_body(self)
            title = (b.get("title") or "").strip()
            content = (b.get("content") or "").strip()
            node = (b.get("node") or "umum").strip()
            if len(title) < 3 or len(content) < 2:
                return send_json(self, {"error": "Judul minimal 3 karakter dan isi tidak boleh kosong"}, 400)
            ts = now_iso()
            ref = db().collection("posko_topics").document()
            ref.set({"node": node, "author": user["username"], "title": title[:160],
                     "content": content[:20000], "created": ts, "last": ts,
                     "pinned": False, "locked": False, "replyCount": 0, "views": 0,
                     "tags": normalize_tags(b.get("tags"))})
            try:
                notify_mentions(user["username"], content, ref.id, title)
            except Exception:
                pass
            awarded = 0
            try:
                awarded = coin_award_activity(user["username"], "topic")
            except Exception:
                pass
            send_json(self, {"id": ref.id, "awarded": awarded,
                             "balance": coin_balance(user["username"])})
        except Exception as e:
            send_json(self, {"error": "Gagal membuat topik: %s" % e}, 500)
    def log_message(self, *a):
        pass
