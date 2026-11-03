"""Servidor local del visualizador. Solo usa la biblioteca estándar.

Solo sirve ficheros: la página ejecuta el código Python en el navegador con Pyodide, igual que
en GitHub Pages. Los módulos que necesita los sirve bajo py/, con la misma estructura que el
sitio publicado (ver .github/workflows/pages.yml).

python -m visualizer            # abre http://127.0.0.1:8000 en el navegador
python -m visualizer --port 9000 --no-browser
"""

from __future__ import annotations

import argparse
import webbrowser
from functools import partial
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import urlparse

import mlkem

STATIC_DIR = Path(__file__).parent / "static"
# py/mlkem/*.py y py/visualizer/*.py: el código que Pyodide descarga y ejecuta en el navegador
PYTHON_DIRS = {"mlkem": Path(mlkem.__file__).parent, "visualizer": Path(__file__).parent}


class Handler(SimpleHTTPRequestHandler):
    def translate_path(self, path: str) -> str:
        parts = urlparse(path).path.split("/")
        if len(parts) == 4 and parts[1] == "py" and parts[2] in PYTHON_DIRS and parts[3].endswith(".py"):
            return str(PYTHON_DIRS[parts[2]] / parts[3])
        return super().translate_path(path)

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
