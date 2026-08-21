"""Recepção pública somente leitura do projeto."""

from __future__ import annotations

import threading
from http import HTTPStatus
from http.server import ThreadingHTTPServer

from .web_security import SecureHandler, open_browser as launch_browser, send_text


HOME_HTML = r"""<!doctype html>
<html lang="pt-BR">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <meta name="description" content="Automatizando LaTeX: escrita, documentação e versionamento de publicações ABNT.">
  <title>Automatizando LaTeX</title>
  <style>
    :root { --ink: #172936; --muted: #687a80; --paper: #f4f6f3; --line: #d9e1e2; --accent: #d87539; --link: #176b87; }
    * { box-sizing: border-box; } body { margin: 0; color: var(--ink); background: var(--paper); font: 17px/1.7 Georgia, 'Times New Roman', serif; }
    header { display: flex; justify-content: space-between; align-items: center; padding: 22px 7vw; border-bottom: 1px solid var(--line); background: #fff; }
    header strong { font-size: 17px; letter-spacing: .04em; } header span { color: var(--muted); font: 11px ui-monospace, monospace; }
    main { max-width: 980px; margin: 0 auto; padding: 12vh 7vw 15vh; } .kicker { color: var(--accent); font: 12px ui-monospace, monospace; letter-spacing: .14em; text-transform: uppercase; }
    h1 { max-width: 760px; margin: 20px 0; color: var(--ink); font-size: clamp(42px, 8vw, 86px); font-weight: normal; line-height: 1.02; }
    .intro { max-width: 660px; color: var(--muted); font-size: 20px; } .actions { display: flex; flex-wrap: wrap; gap: 12px; margin-top: 34px; }
    a { display: inline-block; padding: 11px 15px; border: 1px solid var(--ink); color: var(--ink); text-decoration: none; font: 13px ui-monospace, monospace; }
    a.primary { border-color: var(--accent); color: #fff; background: var(--accent); } a:hover { border-color: var(--link); }
    .note { margin-top: 72px; padding-top: 20px; border-top: 1px solid var(--line); color: var(--muted); font-size: 14px; }
  </style>
</head>
<body><header><strong>Automatizando LaTeX</strong><span>ABNT · LATEX · GIT</span></header>
<main><p class="kicker">Escrita acadêmica aberta</p><h1>Do primeiro rascunho à publicação.</h1>
<p class="intro">Uma pequena oficina para criar artigos ABNT, editar LaTeX, acompanhar versões e manter a documentação do projeto em um só lugar.</p>
<div class="actions"><a class="primary" href="/docs/">Ler documentação</a><a href="/editor/">Abrir editor</a></div>
<p class="note">A recepção roda localmente por padrão. Os serviços de documentação e edição são iniciados separadamente para manter cada superfície simples e segura.</p></main></body></html>"""


class HomeHandler(SecureHandler):
    """Entrega somente a página inicial do projeto."""

    def do_GET(self) -> None:
        if self.path != "/":
            self.send_error(HTTPStatus.NOT_FOUND)
            return
        send_text(self, HOME_HTML.encode("utf-8"), "text/html; charset=utf-8")

    def log_message(self, format: str, *args: object) -> None:
        return


def serve_home(host: str = "127.0.0.1", port: int = 8000, open_browser: bool = True) -> None:
    """Inicia a recepção local sem endpoints de escrita."""
    server = ThreadingHTTPServer((host, port), HomeHandler)
    url = f"http://{host}:{server.server_port}/"
    print(f"Automatizando LaTeX disponível em {url}")
    if open_browser:
        threading.Timer(0.4, launch_browser, args=(url,)).start()
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\nRecepção encerrada.")
    finally:
        server.server_close()
