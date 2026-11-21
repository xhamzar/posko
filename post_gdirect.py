#!/usr/bin/env python3
"""Posting gdirect ke POSKO sebagai akun cia (dengan screenshot repo)."""
import json, os, sys, urllib.request, urllib.error

BASE = "https://posko-drafsanjanis-projects.vercel.app"
TOKEN_FILE = os.path.expanduser("~/.config/posko/cia_token")

def call(path, body=None, token=None):
    req = urllib.request.Request(
        BASE + path,
        data=json.dumps(body).encode() if body is not None else None,
        headers={"Content-Type": "application/json",
                 **({"Authorization": "Bearer " + token} if token else {})},
        method="POST" if body is not None else "GET")
    try:
        with urllib.request.urlopen(req, timeout=90) as r:
            return r.status, json.loads(r.read().decode())
    except urllib.error.HTTPError as e:
        try:
            return e.code, json.loads(e.read().decode() or "{}")
        except Exception:
            return e.code, {}

token = open(TOKEN_FILE).read().strip()
content = open(os.path.expanduser("~/workspace/posko/artikel-gdirect.md")).read().strip()
st, res = call("/api/topics", {
    "node": "teknologi",
    "title": "gdirect, Kelola Google Drive dari Terminal Sekencang Mungkin",
    "content": content,
    "tags": ["gdirect", "google-drive", "terminal", "rust", "open-source"],
}, token)
print("POST topics:", st, res)
if st != 200 or not res.get("id"):
    sys.exit(1)
tid = res["id"]
st2, res2 = call("/api/topic?id=" + tid)
t = res2.get("topic", res2)
body = t.get("content", "")
print("VERIFY:", st2, "| title:", t.get("title"), "| author:", t.get("author"),
      "| node:", t.get("node"), "| tags:", t.get("tags"))
print("IMAGE_IN_CONTENT:", "i.ibb.co" in body)
print("TOPIC_ID:", tid)
