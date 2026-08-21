from http.server import BaseHTTPRequestHandler


class SecureHandler(BaseHTTPRequestHandler):
    """Adiciona headers mínimos de segurança aos servidores locais."""

    def end_headers(self) -> None:
        self.send_header("X-Content-Type-Options", "nosniff")
        self.send_header("X-Frame-Options", "SAMEORIGIN")
        self.send_header("Referrer-Policy", "no-referrer")
        self.send_header("Content-Security-Policy", "default-src 'self'; frame-src 'self'; style-src 'unsafe-inline'; script-src 'unsafe-inline'")
        super().end_headers()
