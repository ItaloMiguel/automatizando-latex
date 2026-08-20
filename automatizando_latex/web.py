"""Interface web local para editar e compilar um projeto LaTeX."""

from __future__ import annotations

import json
import threading
import webbrowser
from http import HTTPStatus
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import parse_qs, urlparse

from .cli import REQUIRED_PROJECT_FILES, build_project, check_project


EDITOR_FILES = (*REQUIRED_PROJECT_FILES,)


HTML = r"""<!doctype html>
<html lang="pt-BR">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>Ateliê ABNT</title>
  <style>
    :root { --ink: #17212b; --muted: #6f7b83; --line: #dbe2e5; --paper: #f5f6f2; --blue: #176b87; --orange: #e07a35; }
    * { box-sizing: border-box; }
    body { margin: 0; min-height: 100vh; color: var(--ink); background: var(--paper); font: 15px/1.5 Georgia, serif; }
    header { display: flex; align-items: center; justify-content: space-between; padding: 18px 28px; color: #fff; background: var(--ink); }
    header h1 { margin: 0; font-size: 20px; letter-spacing: .02em; }
    header p { margin: 0; color: #b9cbd1; font: 13px ui-monospace, monospace; }
    main { display: grid; grid-template-columns: minmax(290px, 38%) 1fr; min-height: calc(100vh - 66px); }
    .workspace { display: flex; flex-direction: column; min-width: 0; border-right: 1px solid var(--line); }
    .toolbar { display: flex; flex-wrap: wrap; gap: 8px; align-items: center; padding: 14px 18px; border-bottom: 1px solid var(--line); background: #fff; }
    select, button { border: 1px solid var(--line); border-radius: 4px; padding: 8px 11px; background: #fff; color: var(--ink); font: 13px ui-monospace, monospace; }
    select { flex: 1; min-width: 180px; }
    button { cursor: pointer; }
    button.primary { border-color: var(--blue); color: #fff; background: var(--blue); }
    button:hover { border-color: var(--orange); }
    #editor { flex: 1; width: 100%; min-height: 480px; resize: none; border: 0; outline: 0; padding: 22px; color: #283640; background: #fbfcfa; font: 14px/1.7 ui-monospace, SFMono-Regular, Consolas, monospace; tab-size: 2; }
    .status { min-height: 40px; padding: 10px 18px; border-top: 1px solid var(--line); color: var(--muted); background: #fff; font: 12px ui-monospace, monospace; }
    .preview { display: flex; flex-direction: column; min-width: 0; background: #cfd6d7; }
    .preview-head { display: flex; align-items: center; justify-content: space-between; padding: 14px 20px; color: #fff; background: #314650; font: 13px ui-monospace, monospace; }
    #pdf { flex: 1; width: 100%; min-height: 600px; border: 0; background: #fff; }
    .empty { display: grid; place-items: center; height: 100%; padding: 40px; text-align: center; color: #617177; font-size: 18px; }
    @media (max-width: 800px) { main { display: block; } .workspace { min-height: 65vh; border-right: 0; } #editor { min-height: 420px; } .preview { min-height: 70vh; } }
  </style>
</head>
<body>
  <header><h1>Ateliê ABNT</h1><p id="project">carregando projeto...</p></header>
  <main>
    <section class="workspace" aria-label="Editor do projeto">
      <div class="toolbar">
        <select id="file" aria-label="Arquivo para editar"></select>
        <button id="save">Salvar</button>
        <button id="compile" class="primary">Compilar PDF</button>
      </div>
      <textarea id="editor" spellcheck="false" aria-label="Editor de texto"></textarea>
      <div id="status" class="status">Pronto.</div>
    </section>
    <section class="preview" aria-label="Visualização do PDF">
      <div class="preview-head"><span>Visualização</span><span id="build-state">PDF ainda não compilado</span></div>
      <iframe id="pdf" title="Visualização do PDF"></iframe>
    </section>
  </main>
  <script>
    const fileSelect = document.querySelector('#file');
    const editor = document.querySelector('#editor');
    const status = document.querySelector('#status');
    const pdf = document.querySelector('#pdf');
    const buildState = document.querySelector('#build-state');
    let timer;

    function message(text, error = false) {
      status.textContent = text;
      status.style.color = error ? '#a33b2c' : '';
    }

    async function request(url, options = {}) {
      const response = await fetch(url, options);
      const data = await response.json();
      if (!response.ok) throw new Error(data.error || 'Não foi possível concluir a operação.');
      return data;
    }

    async function loadFile() {
      const name = fileSelect.value;
      const data = await request(`/api/file?name=${encodeURIComponent(name)}`);
      editor.value = data.content;
      message(`${name} carregado.`);
    }

    async function saveFile(silent = false) {
      const name = fileSelect.value;
      await request('/api/file', { method: 'PUT', headers: {'Content-Type': 'application/json'}, body: JSON.stringify({name, content: editor.value}) });
      if (!silent) message(`${name} salvo.`);
    }

    async function compile() {
      try {
        await saveFile(true);
        buildState.textContent = 'compilando...';
        message('Salvo. Compilando LaTeX e BibTeX...');
        await request('/api/build', {method: 'POST'});
        const stamp = Date.now();
        pdf.src = `/api/pdf?cache=${stamp}`;
        buildState.textContent = 'PDF atualizado';
        message('PDF atualizado com sucesso.');
      } catch (error) {
        buildState.textContent = 'falha na compilação';
        message(error.message, true);
      }
    }

    fileSelect.addEventListener('change', loadFile);
    document.querySelector('#save').addEventListener('click', () => saveFile());
    document.querySelector('#compile').addEventListener('click', compile);
    editor.addEventListener('input', () => {
      clearTimeout(timer);
      timer = setTimeout(() => saveFile(true).then(() => message('Alterações salvas automaticamente.')).catch(error => message(error.message, true)), 900);
    });

    request('/api/project').then(data => {
      document.querySelector('#project').textContent = data.name;
      data.files.forEach(name => fileSelect.add(new Option(name, name)));
      return loadFile();
    }).catch(error => message(error.message, true));
  </script>
</body>
</html>"""


class ProjectHandler(BaseHTTPRequestHandler):
    """Endpoints mínimos para a interface local."""

    project_dir: Path

    def _send_json(self, payload: dict, status: HTTPStatus = HTTPStatus.OK) -> None:
        body = json.dumps(payload, ensure_ascii=False).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def _error(self, error: Exception, status: HTTPStatus = HTTPStatus.BAD_REQUEST) -> None:
        self._send_json({"error": str(error)}, status)

    def _safe_file(self, name: str) -> Path:
        if name not in EDITOR_FILES:
            raise ValueError("arquivo não permitido")
        return self.project_dir / name

    def do_GET(self) -> None:
        parsed = urlparse(self.path)
        try:
            if parsed.path == "/":
                body = HTML.encode("utf-8")
                self.send_response(HTTPStatus.OK)
                self.send_header("Content-Type", "text/html; charset=utf-8")
                self.send_header("Content-Length", str(len(body)))
                self.end_headers()
                self.wfile.write(body)
            elif parsed.path == "/api/project":
                check_project(self.project_dir)
                self._send_json({"name": self.project_dir.name, "files": list(EDITOR_FILES)})
            elif parsed.path == "/api/file":
                name = parse_qs(parsed.query).get("name", [""])[0]
                self._send_json({"name": name, "content": self._safe_file(name).read_text(encoding="utf-8")})
            elif parsed.path == "/api/pdf":
                pdf = self.project_dir / "main.pdf"
                if not pdf.is_file():
                    raise FileNotFoundError("main.pdf ainda não existe; compile o projeto primeiro")
                body = pdf.read_bytes()
                self.send_response(HTTPStatus.OK)
                self.send_header("Content-Type", "application/pdf")
                self.send_header("Content-Length", str(len(body)))
                self.end_headers()
                self.wfile.write(body)
            else:
                self._error(ValueError("rota não encontrada"), HTTPStatus.NOT_FOUND)
        except FileNotFoundError as error:
            self._error(error, HTTPStatus.NOT_FOUND)
        except (ValueError, OSError) as error:
            self._error(error)

    def do_PUT(self) -> None:
        if urlparse(self.path).path != "/api/file":
            self._error(ValueError("rota não encontrada"), HTTPStatus.NOT_FOUND)
            return
        try:
            length = int(self.headers.get("Content-Length", "0"))
            data = json.loads(self.rfile.read(length))
            path = self._safe_file(data["name"])
            path.write_text(data["content"], encoding="utf-8")
            self._send_json({"saved": data["name"]})
        except (KeyError, json.JSONDecodeError, TypeError, ValueError, OSError) as error:
            self._error(error)

    def do_POST(self) -> None:
        if self.path != "/api/build":
            self._error(ValueError("rota não encontrada"), HTTPStatus.NOT_FOUND)
            return
        try:
            commands = build_project(self.project_dir)
            self._send_json({"commands": commands})
        except (FileNotFoundError, RuntimeError) as error:
            self._error(error, HTTPStatus.INTERNAL_SERVER_ERROR)

    def log_message(self, format: str, *args: object) -> None:
        return


def serve_project(project_dir: Path, host: str = "127.0.0.1", port: int = 8765, open_browser: bool = True) -> None:
    """Inicia o servidor local da interface de edição."""
    check_project(project_dir)
    handler = type("BoundProjectHandler", (ProjectHandler,), {"project_dir": project_dir.resolve()})
    server = ThreadingHTTPServer((host, port), handler)
    url = f"http://{host}:{server.server_port}/"
    print(f"Ateliê ABNT disponível em {url}")
    if open_browser:
        threading.Timer(0.4, webbrowser.open, args=(url,)).start()
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\nInterface encerrada.")
    finally:
        server.server_close()