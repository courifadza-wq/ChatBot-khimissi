# -*- coding: utf-8 -*-
"""
Serveur d'admin pour le bot WhatsApp.
Utilise UNIQUEMENT la bibliothèque standard Python : AUCUNE installation requise.

Lancement :   py admin_server.py
Puis ouvre :  http://localhost:8080

Fonctions :
  GET  /            -> sert l'interface (formulaire)
  GET  /api/data    -> renvoie le contenu actuel de intents.yaml (JSON)
  POST /api/save    -> sauvegarde intents.yaml depuis le JSON recu
"""
import json
import sys
import io
import os
from http.server import BaseHTTPRequestHandler, HTTPServer
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent
DATA_DIR = BASE_DIR / "data"
INTENTS_FILE = DATA_DIR / "intents.yaml"
HTML_FILE = BASE_DIR / "interface_admin.html"
PORT = int(os.environ.get("ADMIN_PORT", "8080"))


def read_yaml_intents():
    """Lit intents.yaml et renvoie un dict {intention: {"patterns": [...]}}."""
    if not INTENTS_FILE.exists():
        return {}
    text = INTENTS_FILE.read_text(encoding="utf-8")
    intents = {}
    cur = None
    in_patterns = False
    for raw in text.splitlines():
        line = raw.rstrip()
        if not line.strip() or line.lstrip().startswith("#"):
            continue
        indent = len(line) - len(line.lstrip(" "))
        # intention au niveau 2 :  "nom":
        if indent == 2 and line.rstrip().endswith(":"):
            cur = _unquote(line.rstrip()[:-1].strip())
            intents[cur] = {"patterns": []}
            in_patterns = False
        elif indent == 4 and line.rstrip().endswith(":"):
            in_patterns = True
        elif line.lstrip().startswith("-"):
            val = line.strip()[1:].strip()
            if cur and in_patterns:
                intents[cur]["patterns"].append(_unquote(val))
    return intents


def _unquote(s):
    s = s.strip()
    if len(s) >= 2 and s[0] == '"' and s[-1] == '"':
        s = s[1:-1].replace('\\"', '"').replace("\\\\", "\\")
    elif len(s) >= 2 and s[0] == "'" and s[-1] == "'":
        s = s[1:-1].replace("''", "'")
    return s


def _q(s):
    return '"' + str(s).replace("\\", "\\\\").replace('"', '\\"') + '"'


def write_yaml_intents(intents):
    """Réécrit intents.yaml depuis le dict, en préservant arabe + UTF-8."""
    lines = ["intents:"]
    for name in sorted(intents.keys()):
        lines.append("  " + _q(name) + ":")
        lines.append("    " + _q("patterns") + ":")
        pats = intents[name].get("patterns", []) or []
        if not pats:
            lines.append("      []")
        for p in pats:
            if p and str(p).strip():
                lines.append("      - " + _q(str(p)))
    INTENTS_FILE.write_text("\n".join(lines) + "\n", encoding="utf-8")


class Handler(BaseHTTPRequestHandler):
    def _send(self, code, body, ctype="application/json"):
        data = body.encode("utf-8") if isinstance(body, str) else body
        self.send_response(code)
        self.send_header("Content-Type", ctype)
        self.send_header("Content-Length", str(len(data)))
        self.send_header("Access-Control-Allow-Origin", "*")
        self.end_headers()
        self.wfile.write(data)

    def log_message(self, fmt, *args):  # silencieux
        pass

    def do_GET(self):
        if self.path in ("/", "/index.html"):
            if HTML_FILE.exists():
                html = HTML_FILE.read_text(encoding="utf-8")
                self._send(200, html, "text/html; charset=utf-8")
            else:
                self._send(500, "interface_admin.html introuvable")
        elif self.path == "/api/data":
            self._send(200, json.dumps({"intents": read_yaml_intents()}, ensure_ascii=False))
        else:
            self._send(404, "Not found")

    def do_OPTIONS(self):
        self.send_response(200)
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "GET, POST, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "Content-Type")
        self.end_headers()

    def do_POST(self):
        if self.path == "/api/save":
            try:
                length = int(self.headers.get("Content-Length", 0))
                raw = self.rfile.read(length).decode("utf-8")
                payload = json.loads(raw)
                intents = payload.get("intents", {})
                write_yaml_intents(intents)
                count = len(intents)
                self._send(200, json.dumps({"ok": True, "saved": count}, ensure_ascii=False))
            except Exception as e:
                self._send(500, json.dumps({"ok": False, "error": str(e)}))
        else:
            self._send(404, "Not found")


def main():
    print("=" * 55)
    print("  ADMIN BOT WHATSAPP - serveur local")
    print(f"  Ouvre dans ton navigateur :  http://localhost:{PORT}")
    print("  (Appuie sur CTRL+C dans cette fenetre pour arreter)")
    print("=" * 55)
    server = HTTPServer(("0.0.0.0", PORT), Handler)
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        pass
    finally:
        server.server_close()
        print("\nServeur arrete.")


if __name__ == "__main__":
    # force utf-8 pour la console
    try:
        sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
    except Exception:
        pass
    main()
