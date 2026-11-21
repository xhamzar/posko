# Harness uji lokal POSKO: satu server, dispatch /api/<nama> ke handler modulnya.
# Pakai: FIREBASE_SERVICE_ACCOUNT="$(cat serviceAccount.json)" venv/bin/python test_server.py
import importlib.util, os, sys
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

API_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "api")
sys.path.insert(0, API_DIR)
mods = {}
for name in ["nodes", "topics", "topic", "register", "login", "replies", "moderate", "edit", "remove", "coin", "profile", "me"]:
    spec = importlib.util.spec_from_file_location(name, os.path.join(API_DIR, name + ".py"))
    m = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(m)
    mods[name] = m

class Dispatch(BaseHTTPRequestHandler):
    def _go(self):
        name = self.path.split("?")[0].strip("/").split("/")[-1]
        if name in ("fav", "timeline", "notif"):
            self.path = "/api/me?part=" + name
            name = "me"
        m = mods.get(name)
        if not m:
            self.send_response(404); self.end_headers(); return
        fn = getattr(m.handler, "do_" + self.command, None)
        if fn is None:
            self.send_response(405); self.end_headers(); return
        fn(self)
    do_GET = _go
    do_POST = _go
    def log_message(self, *a):
        pass

if __name__ == "__main__":
    ThreadingHTTPServer(("127.0.0.1", 8901), Dispatch).serve_forever()
