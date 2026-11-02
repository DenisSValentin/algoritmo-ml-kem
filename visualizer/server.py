"""Servidor local del visualizador. Solo usa la biblioteca estándar.

python -m visualizer            # abre http://127.0.0.1:8000 en el navegador
python -m visualizer --port 9000 --no-browser
"""

from __future__ import annotations

import argparse
import json
import webbrowser
from functools import partial
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import parse_qs, urlparse

from mlkem import PARAMETER_SETS

from .trace import benchmark, run_exchange

STATIC_DIR = Path(__file__).parent / "static"


class Handler(SimpleHTTPRequestHandler):
    def do_GET(self) -> None:
        url = urlparse(self.path)
        query = {key: values[0] for key, values in parse_qs(url.query).items()}
        if url.path == "/api/exchange":
            params = query.get("params", "ML-KEM-768")
            if params not in PARAMETER_SETS:
                return self._json({"error": f"conjunto de parámetros desconocido: {params}"}, status=400)
            seed = query.get("seed") or None
            return self._json(run_exchange(params, tamper=query.get("tamper") == "1", seed=seed))
        if url.path == "/api/benchmark":
            return self._json(benchmark())
        return super().do_GET()

    def _json(self, payload, status: int = 200) -> None:
        body = json.dumps(payload).encode()
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def end_headers(self) -> None:
        # Sin caché: así un cambio en static/ se ve al recargar
        self.send_header("Cache-Control", "no-store")
        super().end_headers()

    def log_message(self, format: str, *args) -> None:  # silencia el log de cada petición
        pass


def main() -> None:
    parser = argparse.ArgumentParser(description="Visualizador interactivo de ML-KEM")
    parser.add_argument("--port", type=int, default=8000)
    parser.add_argument("--host", default="127.0.0.1")
    parser.add_argument("--no-browser", action="store_true")
    args = parser.parse_args()

    server = ThreadingHTTPServer((args.host, args.port), partial(Handler, directory=str(STATIC_DIR)))
    url = f"http://{args.host}:{args.port}"
    print(f"Visualizador de ML-KEM en {url}  (Ctrl+C para salir)")
    if not args.no_browser:
        webbrowser.open(url)
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\nHasta pronto.")


if __name__ == "__main__":
    main()
