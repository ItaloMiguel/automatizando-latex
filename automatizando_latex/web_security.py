"""Infraestrutura HTTP compartilhada pelos serviços locais."""

from __future__ import annotations

import os
import webbrowser
from http import HTTPStatus
from http.server import BaseHTTPRequestHandler
from pathlib import Path


MAX_BODY_BYTES = 1_048_576


class SecureHandler(BaseHTTPRequestHandler):
    """Aplica headers básicos de segurança às respostas HTTP locais."""

    def end_headers(self) -> None:
        self.send_header("X-Content-Type-Options", "nosniff")
        self.send_header("X-Frame-Options", "SAMEORIGIN")
        self.send_header("Referrer-Policy", "no-referrer")
        self.send_header(
            "Content-Security-Policy",
            "default-src 'self'; frame-src 'self'; style-src 'unsafe-inline'; script-src 'unsafe-inline'",
        )
        super().end_headers()


def open_browser(url: str) -> bool:
    """Abre o navegador quando há GUI; no WSL headless, apenas mantém a URL impressa."""
    is_wsl = bool(os.environ.get("WSL_INTEROP") or os.environ.get("WSL_DISTRO_NAME"))
    if not is_wsl:
        try:
            is_wsl = "microsoft" in Path("/proc/version").read_text().lower()
        except OSError:
            pass
    if is_wsl and not any(
        os.environ.get(variable) for variable in ("DISPLAY", "WAYLAND_DISPLAY", "BROWSER")
    ):
        return False
    try:
        return webbrowser.open(url)
    except (OSError, webbrowser.Error):
        return False


def send_text(handler: BaseHTTPRequestHandler, body: bytes, content_type: str, status: HTTPStatus = HTTPStatus.OK) -> None:
    """Envia uma resposta textual com tamanho explícito."""
    handler.send_response(status)
    handler.send_header("Content-Type", content_type)
    handler.send_header("Content-Length", str(len(body)))
    handler.end_headers()
    handler.wfile.write(body)
