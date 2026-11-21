# POST /api/register {username,email,password} -> {token, user}
# User pertama & username "driyan" otomatis jadi admin.
from http.server import BaseHTTPRequestHandler
import os, re, sys
sys.path.insert(0, os.path.dirname(__file__))
from _db import (db, hash_password, make_token, now_iso, read_body, send_json,
                 COIN_WELCOME, coin_credit)

class handler(BaseHTTPRequestHandler):
    def do_POST(self):
        try:
            b = read_body(self)
            username = (b.get("username") or "").strip()
            email = (b.get("email") or "").strip()
            password = b.get("password") or ""
            if not re.fullmatch(r"[A-Za-z0-9_]{3,24}", username):
                return send_json(self, {"error": "Username 3-24 karakter: huruf, angka, underscore"}, 400)
            if "@" not in email or "." not in email:
                return send_json(self, {"error": "Email tidak valid"}, 400)
            if len(password) < 6:
                return send_json(self, {"error": "Password minimal 6 karakter"}, 400)
            col = db().collection("posko_users")
            if col.document(username.lower()).get().exists:
                return send_json(self, {"error": "Username sudah dipakai"}, 409)
            if list(col.where("email_lower", "==", email.lower()).limit(1).stream()):
                return send_json(self, {"error": "Email sudah terdaftar"}, 409)
            first = not list(col.limit(1).stream())
            role = "admin" if (first or username.lower() == "driyan") else "member"
            user = {"username": username, "email": email, "email_lower": email.lower(),
                    "role": role, "joined": now_iso()[:10], "bio": "", "avatar": ""}
            col.document(username.lower()).set(dict(user, **{"pass": hash_password(password)}))
            try:
                coin_credit(username, COIN_WELCOME, "welcome", "Bonus warga baru")
            except Exception:
                pass
            send_json(self, {"token": make_token(user),
                             "user": {"username": username, "email": email, "role": role,
                                      "coins": COIN_WELCOME, "bio": "", "avatar": ""}})
        except Exception as e:
            send_json(self, {"error": "Gagal daftar: %s" % e}, 500)
    def log_message(self, *a):
        pass
