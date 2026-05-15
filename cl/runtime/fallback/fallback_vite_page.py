# Copyright (C) 2023-present The Project Contributors
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#    http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

import logging
import socket
import threading
import html as html_module
from http.server import BaseHTTPRequestHandler
from http.server import HTTPServer
from cl.runtime.settings.vite_settings import ViteSettings

_LOGGER = logging.getLogger(__name__)

_FALLBACK_HTML = """<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8" />
    <meta name="viewport" content="width=device-width, initial-scale=1.0" />
    <title>Vite failed to start</title>
    <style>
        body {{
            margin: 0;
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Helvetica, Arial, sans-serif;
            background-color: #f5f5f5;
            color: #333;
        }}
        .main {{
            display: flex;
            flex-direction: column;
            align-items: center;
            justify-content: center;
            min-height: 100vh;
            padding: 2rem;
        }}
        .card {{
            background: #fff;
            border-radius: 8px;
            box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);
            padding: 2rem 3rem;
            max-width: 600px;
            width: 100%;
        }}
        h1 {{
            font-size: 1.4rem;
            margin-top: 0;
        }}
        .subtitle {{
            color: #666;
            margin-bottom: 0.5rem;
        }}
        hr {{
            border: none;
            border-top: 1px solid #eee;
        }}
        code {{
            background: #f0f0f0;
            padding: 0.15rem 0.4rem;
            border-radius: 4px;
            font-size: 0.95em;
        }}
        ul {{
            line-height: 1.8;
        }}
        .error-box {{
            background: #fdf2f2;
            border: 1px solid #e8c4c4;
            border-radius: 6px;
            padding: 1rem 1.25rem;
            margin-top: 1rem;
            word-break: break-word;
        }}
        .error-box .error-label {{
            font-weight: 600;
            color: #b91c1c;
            margin-bottom: 0.35rem;
        }}
        .error-box .error-text {{
            color: #555;
            margin: 0;
            font-size: 0.95em;
            white-space: pre-wrap;
        }}
    </style>
</head>
<body>
<main class="main">
    <div class="card">
        <h1>Vite failed to start on {vite_host}:{vite_port}</h1>
        <p class="subtitle">How to start</p>
        <hr />
        <ul>
            <li>
                Run <code>run_vite.cmd</code> or <code>python -m cl.runtime --vite</code> to start both the Vite dev server and the backend.
            </li>
            <li>
                Run <code>init_vite.cmd</code> first before the first run. This will install frontend npm dependencies.
            </li>
        </ul>
        {error_section}
    </div>
</main>
</body>
</html>
"""


def _is_port_open(host: str, port: int) -> bool:
    """Return True if a server is accepting connections on host:port."""
    try:
        with socket.create_connection((host, port), timeout=0.5):
            return True
    except OSError:
        return False


_ERROR_SECTION_HTML = """<div class="error-box">
            <p class="error-label">Error message:</p>
            <p class="error-text">{error_message}</p>
        </div>"""


def start_fallback_vite_server(error_message: str | None = None) -> None:
    """Start a fallback HTTP server on the Vite host:port if Vite is not running.

    The server runs in a daemon thread and stops automatically when the main process exits.
    """
    vite_settings = ViteSettings.instance()
    host = vite_settings.vite_host
    port = vite_settings.vite_port

    if _is_port_open(host, port):
        _LOGGER.info(f"Vite dev server is already running on {host}:{port}, skipping fallback.")
        return

    if error_message is not None:
        escaped_message = html_module.escape(error_message)
        error_section = _ERROR_SECTION_HTML.format(error_message=escaped_message)
    else:
        error_section = ""

    html_bytes = _FALLBACK_HTML.format(
        vite_host=host, vite_port=port, error_section=error_section,
    ).encode("utf-8")

    class _Handler(BaseHTTPRequestHandler):
        def do_GET(self):
            self.send_response(200)
            self.send_header("Content-Type", "text/html; charset=utf-8")
            self.send_header("Content-Length", str(len(html_bytes)))
            self.end_headers()
            self.wfile.write(html_bytes)

        def log_message(self, format, *args):
            pass

    try:
        server = HTTPServer((host, port), _Handler)
    except OSError:
        _LOGGER.warning(f"Could not bind fallback server to {host}:{port}.")
        return

    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    _LOGGER.info(f"Fallback page is being served on http://{host}:{port}")
