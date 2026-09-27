"""Build and serve a fresh local preview, printing its exact URL."""

import argparse
import subprocess
import sys
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from functools import partial


ROOT = Path(__file__).resolve().parents[1]


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--port", type=int, default=0, help="Port to use (default: any free port)")
    parser.add_argument("--company", default="co-aapl", help="Initial company ID")
    args = parser.parse_args()

    subprocess.run([sys.executable, str(ROOT / "scripts/stage-site.py")], cwd=ROOT, check=True)
    site = ROOT / ".site-build"
    handler = partial(SimpleHTTPRequestHandler, directory=str(site))
    try:
        server = ThreadingHTTPServer(("127.0.0.1", args.port), handler)
    except OSError as exc:
        parser.error(f"Port {args.port} is unavailable: {exc}. Omit --port to use a free port.")
    server.allow_reuse_address = False
    port = server.server_address[1]
    print(f"Fresh preview: http://127.0.0.1:{port}/map.html?company={args.company}&view=map&tab=map&lang=ja", flush=True)
    print("Press Ctrl+C to stop the preview.", flush=True)
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        pass
    finally:
        server.server_close()


if __name__ == "__main__":
    main()
