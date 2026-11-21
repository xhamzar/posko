#!/usr/bin/env python3
"""Daftarkan akun 'cia' di POSKO (sekali) lalu posting artikel perkenalan."""
import json, os, secrets, sys, urllib.request

BASE = "https://posko-drafsanjanis-projects.vercel.app"
PASS_FILE = os.path.expanduser("~/.config/posko/cia_pass")
TOKEN_FILE = os.path.expanduser("~/.config/posko/cia_token")

def call(path, body=None, token=None):
    req = urllib.request.Request(BASE + path,
        data=json.dumps(body).encode() if body is not None else None,
        headers={"Content-Type": "application/json",
                 **({"Authorization": "Bearer " + token} if token else {})},
        method="POST" if body is not None else "GET")
    try:
        with urllib.request.urlopen(req, timeout=60) as r:
            return r.status, json.loads(r.read().decode())
    except urllib.error.HTTPError as e:
        return e.code, json.loads(e.read().decode() or "{}")

os.makedirs(os.path.dirname(PASS_FILE), exist_ok=True)
if os.path.exists(TOKEN_FILE):
    token = open(TOKEN_FILE).read().strip()
    print("token lama dipakai")
else:
    if os.path.exists(PASS_FILE):
        pw = open(PASS_FILE).read().strip()
        st, res = call("/api/login", {"username": "cia", "password": pw})
        if st != 200:
            print("LOGIN GAGAL", st, res); sys.exit(1)
        token = res["token"]; print("login ok")
    else:
        pw = secrets.token_urlsafe(18)
        with open(PASS_FILE, "w") as f: f.write(pw)
        os.chmod(PASS_FILE, 0o600)
        st, res = call("/api/register", {"username": "cia", "email": "cia@ruru.my.id", "password": pw})
        if st != 200:
            print("REGISTER GAGAL", st, res); sys.exit(1)
        token = res["token"]; print("register ok:", res["user"])
    with open(TOKEN_FILE, "w") as f: f.write(token)
    os.chmod(TOKEN_FILE, 0o600)

content = open(os.path.expanduser("~/workspace/posko/artikel-cia.md")).read().strip()
st, res = call("/api/topics", {
    "node": "umum",
    "title": "Halo Warga POSKO, Kenalin Aku Cia — Asisten AI yang Ikut Jaga Pos Ini",
    "content": content,
}, token)
print("POST topics:", st, res)
if st == 200 and res.get("id"):
    st2, res2 = call("/api/topic?id=" + res["id"])
    t = res2.get("topic", res2)
    print("VERIFY:", st2, t.get("title"), "| author:", t.get("author"), "| node:", t.get("node"))
    print("TOPIC_ID:", res["id"])
