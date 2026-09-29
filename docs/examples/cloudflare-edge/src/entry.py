import importlib.metadata
import importlib.resources
import json
import sys
from urllib.parse import urlsplit

import pyodide
import snowballstemmer
from workers import Response, WorkerEntrypoint

REQUEST_COUNT = 0
STEMMER = snowballstemmer.stemmer("english")


def package_resource():
    resource = importlib.resources.files("certifi").joinpath("cacert.pem")
    text = resource.read_text(encoding="ascii")
    return {"package": "certifi", "resource": "cacert.pem", "bytes": len(text.encode("ascii")), "certificate_count": text.count("-----BEGIN CERTIFICATE-----")}


class Default(WorkerEntrypoint):
    async def fetch(self, request):
        global REQUEST_COUNT
        REQUEST_COUNT += 1
        path = urlsplit(request.url).path
        if request.method == "GET" and path == "/":
            return Response.json({"message": "Python in a workerd isolate", "python": sys.version.split()[0], "platform": sys.platform, "pyodide": pyodide.__version__, "request_count": REQUEST_COUNT, "binding": self.env.LAB_MESSAGE})
        if request.method == "GET" and path == "/packages":
            return Response.json({"versions": {name: importlib.metadata.version(name) for name in ["snowballstemmer", "certifi"]}, "stems": STEMMER.stemWords(["running", "jumping"]), "resource": package_resource()})
        if request.method == "POST" and path == "/stem":
            try:
                body = json.loads(await request.text())
            except (ValueError, TypeError):
                return Response.json({"error": "Expected JSON"}, status=400)
            words = body.get("words") if isinstance(body, dict) else None
            if not isinstance(words, list) or not all(isinstance(word, str) for word in words):
                return Response.json({"error": "words must be a list of strings"}, status=400)
            return Response.json({"words": words, "stems": STEMMER.stemWords(words)})
        if request.method == "GET" and path == "/resources":
            probes = {}
            try:
                import threading
                thread = threading.Thread(target=lambda: None)
                thread.start()
                thread.join(timeout=0.1)
                probes["thread"] = {"started": True, "alive": thread.is_alive()}
            except Exception as error:
                probes["thread"] = {"type": type(error).__name__, "message": str(error)}
            try:
                from pathlib import Path
                target = Path("/tmp/cloudflare-edge-probe.txt")
                existed_before = target.exists()
                target.write_text("temporary Wasm file", encoding="utf-8")
                probes["file"] = {"path": str(target), "existed_before": existed_before, "roundtrip": target.read_text(encoding="utf-8")}
            except Exception as error:
                probes["file"] = {"type": type(error).__name__, "message": str(error)}
            return Response.json(probes)
        return Response.json({"error": "Not found"}, status=404)
