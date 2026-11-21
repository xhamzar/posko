#!/usr/bin/env python3
# Deploy POSKO ke Vercel via MCP (pola sama seperti project Driyan lainnya).
# - Project baru "posko" dibuat dengan env FIREBASE_SERVICE_ACCOUNT + POSKO_SECRET
#   dan ssoProtection mati, lalu deployment production dari file lokal.
# - Batas argv 128KB: total file POSKO ~38KB, aman.
import json, os, secrets, subprocess, sys, time, urllib.request

VERCEL = "/opt/hatch/bin/vercel"
HERE = os.path.dirname(os.path.abspath(__file__))
NAME = "posko"
SA_PATH = os.path.expanduser("~/workspace/tubexin-vercel/serviceAccount.json")
SECRET_PATH = os.path.expanduser("~/.config/posko/secret")

FILES = ["index.html", "assets/app.css", "assets/app.js", "vercel.json", "requirements.txt",
         "api/_db.py", "api/nodes.py", "api/topics.py", "api/topic.py",
         "api/register.py", "api/login.py", "api/replies.py", "api/moderate.py",
         "api/edit.py", "api/remove.py", "api/coin.py", "api/profile.py",
         "api/me.py",
         "assets/avatars/kucing.webp", "assets/avatars/burunghantu.webp",
         "assets/avatars/rubah.webp", "assets/avatars/panda.webp",
         "assets/avatars/kodok.webp", "assets/avatars/harimau.webp",
         "assets/og-posko.jpg"]

def call_tool(name, args, allow_fail=False):
    arg_json = json.dumps(args, separators=(",", ":"), ensure_ascii=False)
    r = subprocess.run([VERCEL, "call-tool", "--name", name,
                        "--arguments-json", arg_json],
                       capture_output=True, text=True)
    out = r.stdout.strip()
    if not out:
        print("CALL GAGAL:", name, r.stderr[-1500:], flush=True)
        if allow_fail:
            return None
        sys.exit(1)
    d = json.loads(out)
    txt = d["result"]["content"][0]["text"]
    try:
        return json.loads(txt)["result"]
    except Exception:
        print("RESPON ANEH", name, txt[:500], flush=True)
        if allow_fail:
            return None
        sys.exit(1)

def get_secret():
    if os.path.exists(SECRET_PATH):
        with open(SECRET_PATH) as f:
            return f.read().strip()
    os.makedirs(os.path.dirname(SECRET_PATH), exist_ok=True)
    s = secrets.token_hex(32)
    with open(SECRET_PATH, "w") as f:
        f.write(s)
    os.chmod(SECRET_PATH, 0o600)
    return s

# (teamId sengaja tidak dipakai — pola deploy project lain: konteks tim default)
with open(SA_PATH) as f:
    sa_json = f.read()
envs = [
    {"key": "FIREBASE_SERVICE_ACCOUNT", "value": sa_json,
     "type": "encrypted", "target": ["production", "preview"]},
    {"key": "POSKO_SECRET", "value": get_secret(),
     "type": "encrypted", "target": ["production", "preview"]},
    {"key": "POSKO_IMGBB_KEY",
     "value": open(os.path.expanduser("~/.config/posko/imgbb_key")).read().strip(),
     "type": "encrypted", "target": ["production", "preview"]},
]

# 2) buat project (kalau sudah ada, lanjut saja)
proj = call_tool("create_project",
                 {"requestBody": {"name": NAME, "framework": None,
                                  "ssoProtection": None,
                                  "environmentVariables": envs}},
                 allow_fail=True)
print("create_project:", json.dumps(proj)[:300] if proj else "gagal/sudah ada", flush=True)
if not proj:
    # project mungkin sudah ada dari percobaan sebelumnya: pastikan env terpasang
    for e in envs:
        r = call_tool("create_project_env",
                      {"idOrName": NAME, "requestBody": e},
                      allow_fail=True)
        print("env", e["key"], "->", "ok" if r else "gagal", flush=True)

# 3) deployment — file di-upload dulu per berkas (upload_file), lalu
# create_deployment cukup mereferensikan {file, sha, size}: payload argumen
# jadi mungil dan batas argv 128KB tidak lagi mengancam walau app membesar.
import base64, hashlib
payload_files = []
for rel in FILES:
    path = os.path.join(HERE, rel)
    with open(path, "rb") as f:
        raw = f.read()
    sha = hashlib.sha1(raw).hexdigest()
    up = call_tool("upload_file",
                   {"requestBody": base64.b64encode(raw).decode(),
                    "xVercelDigest": sha, "contentLength": len(raw)},
                   allow_fail=True)
    print("upload", rel, len(raw), "B ->", "ok" if up is not None else "GAGAL", flush=True)
    payload_files.append({"file": rel, "sha": sha, "size": len(raw)})
args = {"requestBody": {"name": NAME, "target": "production", "project": NAME,
                        "projectSettings": {"framework": None, "buildCommand": None,
                                            "outputDirectory": None, "installCommand": None,
                                            "devCommand": None, "rootDirectory": None},
                        "files": payload_files}}
arg_json = json.dumps(args, separators=(",", ":"))
print("payload bytes:", len(arg_json), flush=True)

dep = call_tool("create_deployment", args)["deployment"]
print("deployment:", dep["id"], dep.get("readyState") or dep.get("state"), flush=True)
url = dep.get("url")
print("url:", url, flush=True)

# 4) tunggu live
for _ in range(18):
    time.sleep(10)
    try:
        resp = urllib.request.urlopen("https://" + url, timeout=25)
        body = resp.read().decode("utf-8", "ignore")
        code = int(resp.getcode()) if "POSKO" in body else 0
    except Exception as e:
        code = getattr(e, "code", 0)
    print("cek https://%s -> %s" % (url, code), flush=True)
    if code == 200:
        print("LIVE: https://" + url, flush=True)
        break
else:
    print("belum 200 setelah 3 menit", flush=True)
