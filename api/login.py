# POST /api/login {email,password} -> {token, user}
from http.server import BaseHTTPRequestHandler
import os, sys
sys.path.insert(0, os.path.dirname(__file__))
from _db import db, make_token, read_body, send_json, verify_password

class handler(BaseHTTPRequestHandler):
    def do_POST(self):
        try:
            b = read_body(self)
            email = (b.get("email") or "").strip().lower()
            password = b.get("password") or ""
            found = list(db().collection("posko_users").where("email_lower", "==", email).limit(1).stream())
            if not found:
                return send_json(self, {"error": "Email atau password salah"}, 401)
            u = found[0].to_dict()
            if not verify_password(password, u.get("pass", "")):
                return send_json(self, {"error": "Email atau password salah"}, 401)
            user = {"username": u["username"], "email": u["email"], "role": u["role"],
                    "coins": int(u.get("coins", 0) or 0),
                    "bio": u.get("bio", ""), "avatar": u.get("avatar", "")}
            send_json(self, {"token": make_token(user), "user": user})
        except Exception as e:
            send_json(self, {"error": "Gagal masuk: %s" % e}, 500)
    def log_message(self, *a):
        pass
