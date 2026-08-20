"""Interface web local para editar e compilar um projeto LaTeX."""

from __future__ import annotations

import json
import html
import os
import re
import subprocess
import threading
import urllib.error
import urllib.request
import webbrowser
from http import HTTPStatus
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import parse_qs, urlparse

from .cli import REQUIRED_PROJECT_FILES, build_project, check_project


EDITOR_FILES = (*REQUIRED_PROJECT_FILES,)
DOC_SKIP_DIRS = {".git", ".venv", "__pycache__", "node_modules", "projetos"}
GITHUB_API = "https://api.github.com"


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
    .preview-tabs { display: flex; gap: 6px; align-items: center; }
    .preview-tabs button { padding: 5px 8px; border-color: #66808b; color: #dce8e6; background: transparent; }
    .preview-tabs button.active { color: #17212b; background: #fff; }
    .preview-pane { flex: 1; overflow: auto; min-height: 600px; background: #fff; }
    #pdf { width: 100%; min-height: 600px; border: 0; background: #fff; }
    #latex-preview { max-width: 780px; margin: 0 auto; padding: 52px clamp(24px, 7vw, 78px) 90px; color: #24343b; background: #fff; font: 16px/1.75 Georgia, 'Times New Roman', serif; }
    #latex-preview h1, #latex-preview h2, #latex-preview h3 { color: #172936; font-weight: normal; line-height: 1.18; }
    #latex-preview h1 { margin-top: 0; font-size: 36px; }
    #latex-preview h2 { margin-top: 38px; padding-top: 10px; border-top: 1px solid #d9e1e2; font-size: 27px; }
    #latex-preview h3 { margin-top: 28px; font-size: 21px; }
    #latex-preview p { margin: 0 0 18px; }
    #latex-preview .preview-meta { color: #728087; font: 12px ui-monospace, monospace; }
    #latex-preview code { padding: 2px 5px; color: #9a4e25; background: #f7f3ed; font: .86em ui-monospace, monospace; }
    .welcome { display: grid; place-items: center; min-height: calc(100vh - 66px); padding: 48px 24px; background: radial-gradient(circle at 80% 20%, #e5eee8 0, transparent 34%), var(--paper); }
    .welcome-card { max-width: 620px; padding: 52px; border: 1px solid var(--line); background: #fff; box-shadow: 12px 12px 0 #dfe7e1; }
    .welcome-card .kicker { margin: 0 0 12px; color: var(--orange); font: 12px ui-monospace, monospace; letter-spacing: .12em; text-transform: uppercase; }
    .welcome-card h2 { margin: 0 0 18px; color: var(--ink); font-size: clamp(34px, 6vw, 58px); font-weight: normal; line-height: 1.05; }
    .welcome-card p { max-width: 490px; color: var(--muted); font-size: 17px; }
    .welcome-actions { display: flex; gap: 10px; align-items: center; margin-top: 28px; }
    .language { border-color: #66808b; color: #dce8e6; background: transparent; }
    .language option { color: var(--ink); background: #fff; }
    .hidden { display: none !important; }
    .empty { display: grid; place-items: center; height: 100%; padding: 40px; text-align: center; color: #617177; font-size: 18px; }
    @media (max-width: 800px) { main { display: block; } .workspace { min-height: 65vh; border-right: 0; } #editor { min-height: 420px; } .preview { min-height: 70vh; } }
  </style>
</head>
<body>
  <header><h1 data-i18n="brand">Ateliê ABNT</h1><div><select id="language" class="language" aria-label="Idioma"><option value="pt">Português</option><option value="en">English</option></select><p id="project">carregando projeto...</p></div></header>
  <section id="welcome" class="welcome" aria-labelledby="welcome-title">
    <div class="welcome-card">
      <p class="kicker" data-i18n="kicker">Escrita acadêmica</p>
      <h2 id="welcome-title" data-i18n="welcomeTitle">Seu artigo, lado a lado.</h2>
      <p data-i18n="welcomeText">Edite o código LaTeX e acompanhe uma leitura formatada em tempo real. A compilação PDF fica disponível quando o TeX estiver instalado.</p>
      <div class="welcome-actions"><button id="start-editor" class="primary" data-i18n="start">Começar edição</button><span class="preview-meta" data-i18n="welcomeHint">Arquivos salvos automaticamente</span></div>
    </div>
  </section>
  <main id="editor-app" class="hidden">
    <section class="workspace" aria-label="Editor do projeto">
      <div class="toolbar">
        <select id="file" aria-label="Arquivo para editar"></select>
        <button id="save" data-i18n="save">Salvar</button>
        <button id="compile" class="primary" data-i18n="compile">Compilar PDF</button>
      </div>
      <textarea id="editor" spellcheck="false" aria-label="Editor de texto"></textarea>
      <div id="status" class="status">Pronto.</div>
    </section>
    <section class="preview" aria-label="Visualização do PDF">
      <div class="preview-head"><span data-i18n="preview">Visualização</span><div class="preview-tabs"><button id="html-tab" class="active" data-i18n="reading">Leitura</button><button id="pdf-tab">PDF</button><span id="build-state">ao vivo</span></div></div>
      <div id="html-pane" class="preview-pane"><article id="latex-preview"></article></div>
      <div id="pdf-pane" class="preview-pane" hidden><iframe id="pdf" title="Visualização do PDF"></iframe></div>
    </section>
  </main>
  <script>
    const fileSelect = document.querySelector('#file');
    const editor = document.querySelector('#editor');
    const status = document.querySelector('#status');
    const pdf = document.querySelector('#pdf');
    const latexPreview = document.querySelector('#latex-preview');
    const htmlPane = document.querySelector('#html-pane');
    const pdfPane = document.querySelector('#pdf-pane');
    const buildState = document.querySelector('#build-state');
    const language = document.querySelector('#language');
    const welcome = document.querySelector('#welcome');
    const editorApp = document.querySelector('#editor-app');
    let timer;

    const translations = {
      pt: { brand: 'Ateliê ABNT', kicker: 'Escrita acadêmica', welcomeTitle: 'Seu artigo, lado a lado.', welcomeText: 'Edite o código LaTeX e acompanhe uma leitura formatada em tempo real. A compilação PDF fica disponível quando o TeX estiver instalado.', start: 'Começar edição', welcomeHint: 'Arquivos salvos automaticamente', save: 'Salvar', compile: 'Compilar PDF', preview: 'Visualização', reading: 'Leitura' },
      en: { brand: 'ABNT Atelier', kicker: 'Academic writing', welcomeTitle: 'Your article, side by side.', welcomeText: 'Edit LaTeX code and follow a formatted reading preview in real time. PDF compilation is available when TeX is installed.', start: 'Start editing', welcomeHint: 'Files are saved automatically', save: 'Save', compile: 'Compile PDF', preview: 'Preview', reading: 'Reading' }
    };

    // Keep the welcome screen separate from the editor so the first visit is calm and readable.
    function setLanguage(code) {
      document.documentElement.lang = code === 'en' ? 'en' : 'pt-BR';
      document.querySelectorAll('[data-i18n]').forEach(element => { element.textContent = translations[code][element.dataset.i18n]; });
      localStorage.setItem('ateliê-language', code);
    }

    function openEditor() {
      welcome.classList.add('hidden'); editorApp.classList.remove('hidden');
      editor.focus();
    }

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
      renderLatex(data.content);
      message(`${name} carregado.`);
    }

    function escapeHtml(value) {
      return value.replace(/[&<>"']/g, character => ({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[character]));
    }

    function renderLatex(source) {
      // This lightweight renderer favors immediate feedback; the real PDF remains optional.
      let output = escapeHtml(source);
      output = output.replace(/%.*$/gm, '');
      output = output.replace(/\\(chapter|section|subsection|subsubsection)\{([^{}]*)\}/g, (_, level, title) => `<h${level === 'chapter' ? 1 : level === 'section' ? 2 : 3}>${title}</h${level === 'chapter' ? 1 : level === 'section' ? 2 : 3}>`);
      output = output.replace(/\\textbf\{([^{}]*)\}/g, '<strong>$1</strong>');
      output = output.replace(/\\emph\{([^{}]*)\}/g, '<em>$1</em>');
      output = output.replace(/\\cite\{([^{}]*)\}/g, '<code>cite:$1</code>');
      output = output.replace(/\\(begin|end)\{[^{}]*\}/g, '');
      output = output.replace(/\\(documentclass|usepackage|input|imprimir\w+|pdfbookmark|tableofcontents|clearpage|textual|postextual|bibliographystyle|bibliography|vspace|noindent)\b[^\n]*/g, '');
      output = output.split(/\n\s*\n/).map(block => block.trim()).filter(Boolean).map(block => block.startsWith('<h') ? block : `<p>${block.replace(/\n/g, '<br>')}</p>`).join('');
      latexPreview.innerHTML = output || '<p class="preview-meta">Comece a escrever seu documento...</p>';
    }

    function showPreview(kind) {
      const pdfActive = kind === 'pdf';
      htmlPane.hidden = pdfActive; pdfPane.hidden = !pdfActive;
      document.querySelector('#html-tab').classList.toggle('active', !pdfActive);
      document.querySelector('#pdf-tab').classList.toggle('active', pdfActive);
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
        showPreview('pdf');
        buildState.textContent = 'PDF atualizado';
        message('PDF atualizado com sucesso.');
      } catch (error) {
        buildState.textContent = 'falha na compilação';
        message(error.message, true);
      }
    }

    fileSelect.addEventListener('change', loadFile);
    document.querySelector('#start-editor').addEventListener('click', openEditor);
    language.addEventListener('change', () => setLanguage(language.value));
    setLanguage(localStorage.getItem('ateliê-language') || 'pt');
    document.querySelector('#save').addEventListener('click', () => saveFile());
    document.querySelector('#compile').addEventListener('click', compile);
    document.querySelector('#html-tab').addEventListener('click', () => showPreview('html'));
    document.querySelector('#pdf-tab').addEventListener('click', () => showPreview('pdf'));
    editor.addEventListener('input', () => {
      renderLatex(editor.value);
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


DOCS_HTML = r"""<!doctype html>
<html lang="pt-BR">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>Ateliê ABNT | Documentação</title>
  <style>
  :root { --navy: #172936; --navy-soft: #213b4a; --ink: #26343b; --muted: #728087; --line: #d9e1e2; --paper: #f4f6f3; --white: #fff; --accent: #d87539; --link: #176b87; }
  * { box-sizing: border-box; }
  body { margin: 0; color: var(--ink); background: var(--paper); font: 16px/1.7 Georgia, 'Times New Roman', serif; }
  .shell { display: grid; grid-template-columns: 286px minmax(0, 1fr); min-height: 100vh; }
  aside { position: sticky; top: 0; height: 100vh; overflow-y: auto; padding: 30px 20px; color: #edf4f1; background: var(--navy); }
  .brand { display: flex; gap: 12px; align-items: center; margin-bottom: 38px; }
  .mark { display: grid; place-items: center; width: 37px; height: 37px; border: 1px solid #688391; color: #fff; font: bold 17px Georgia, serif; }
  .brand strong { display: block; font-size: 16px; letter-spacing: .04em; }
  .brand small { display: block; color: #9db2b9; font: 11px ui-monospace, monospace; }
  .eyebrow { margin: 0 0 9px; color: #8ea8b1; font: 10px ui-monospace, monospace; letter-spacing: .12em; text-transform: uppercase; }
  .search { width: 100%; margin-bottom: 22px; padding: 9px 10px; border: 1px solid #496575; border-radius: 2px; outline: 0; color: #fff; background: var(--navy-soft); font: 12px ui-monospace, monospace; }
  .search::placeholder { color: #9db2b9; }
  nav a { display: block; margin: 2px 0; padding: 8px 10px; border-left: 2px solid transparent; color: #c8d6d7; text-decoration: none; font-size: 14px; }
  nav a:hover, nav a.active { border-left-color: var(--accent); color: #fff; background: #294553; }
  nav a small { display: block; overflow: hidden; color: #8fa5ac; font: 10px ui-monospace, monospace; text-overflow: ellipsis; white-space: nowrap; }
  .content-wrap { min-width: 0; }
  header { display: flex; justify-content: space-between; align-items: center; padding: 22px clamp(22px, 6vw, 86px); border-bottom: 1px solid var(--line); background: var(--white); }
  header span { color: var(--muted); font: 11px ui-monospace, monospace; letter-spacing: .06em; text-transform: uppercase; }
  header a { color: var(--link); font: 12px ui-monospace, monospace; text-decoration: none; }
  article { max-width: 900px; padding: 66px clamp(22px, 7vw, 100px) 100px; background: var(--white); }
  article h1 { margin: 0 0 22px; color: var(--navy); font-size: clamp(34px, 5vw, 54px); font-weight: normal; line-height: 1.08; }
  article h2 { margin: 48px 0 13px; padding-top: 10px; border-top: 1px solid var(--line); color: var(--navy); font-size: 27px; font-weight: normal; }
  article h3 { margin: 32px 0 8px; color: var(--navy-soft); font-size: 20px; }
  article p { max-width: 730px; margin: 0 0 18px; }
  article a { color: var(--link); text-decoration-thickness: 1px; text-underline-offset: 3px; }
  article code { padding: 2px 5px; border: 1px solid #e1e7e5; border-radius: 2px; color: #9a4e25; background: #f7f3ed; font: .86em ui-monospace, monospace; }
  article pre { overflow-x: auto; margin: 22px 0; padding: 18px; border-left: 3px solid var(--accent); color: #e8f0ee; background: #172936; font: 13px/1.65 ui-monospace, monospace; }
  article pre code { padding: 0; border: 0; color: inherit; background: transparent; }
  article ul, article ol { max-width: 730px; padding-left: 26px; }
  article li { padding-left: 5px; }
  article blockquote { margin: 24px 0; padding: 8px 22px; border-left: 3px solid var(--accent); color: #607179; background: #f5f7f4; }
  article table { width: 100%; margin: 24px 0; border-collapse: collapse; font-size: 14px; }
  article th, article td { padding: 9px 12px; border-bottom: 1px solid var(--line); text-align: left; }
  article th { color: var(--navy); background: #f1f5f3; font-weight: bold; }
  .meta { margin-bottom: 38px; color: var(--muted); font: 12px ui-monospace, monospace; }
  .empty { color: var(--muted); font-family: ui-monospace, monospace; }
  @media (max-width: 760px) { .shell { display: block; } aside { position: static; height: auto; padding: 20px; } .brand { margin-bottom: 20px; } nav { max-height: 210px; overflow-y: auto; } header { padding: 16px 22px; } article { padding-top: 40px; } }
  </style>
</head>
<body>
  <div class="shell">
  <aside>
    <div class="brand"><div class="mark">A</div><div><strong>Ateliê ABNT</strong><small>DOCUMENTAÇÃO DO PROJETO</small></div></div>
    <p class="eyebrow">Arquivos Markdown</p>
    <input id="search" class="search" type="search" placeholder="Filtrar documentos..." aria-label="Filtrar documentos">
    <nav id="nav" aria-label="Documentos"></nav>
    <p class="eyebrow" style="margin-top:28px">GitHub Documents</p>
    <nav id="github-nav" aria-label="Documentos do GitHub"></nav>
  </aside>
  <div class="content-wrap">
    <header><span id="path">Documentação</span><a href="https://github.com" target="_blank" rel="noreferrer">GitHub ↗</a></header>
    <article id="article"><p class="empty">Carregando documentação...</p></article>
  </div>
  </div>
  <script>
  const nav = document.querySelector('#nav');
  const article = document.querySelector('#article');
  const pathLabel = document.querySelector('#path');
  const search = document.querySelector('#search');
  let documents = [];
  let githubDocuments = [];
  async function request(url) { const response = await fetch(url); const data = await response.json(); if (!response.ok) throw new Error(data.error || 'Falha ao carregar documentação.'); return data; }
  function drawNav(filter = '') {
    nav.innerHTML = '';
    documents.filter(doc => `${doc.title} ${doc.path}`.toLowerCase().includes(filter.toLowerCase())).forEach((doc, index) => {
    const link = document.createElement('a'); link.href = `#${encodeURIComponent(doc.path)}`; link.dataset.path = doc.path;
    link.innerHTML = `${doc.title}<small>${doc.path}</small>`; link.addEventListener('click', event => { event.preventDefault(); loadDoc(doc.path); }); nav.appendChild(link);
    });
  }
    function drawGithubNav(filter = '') {
      const target = document.querySelector('#github-nav'); target.innerHTML = '';
      githubDocuments.filter(doc => `${doc.title} ${doc.path}`.toLowerCase().includes(filter.toLowerCase())).forEach(doc => {
        const link = document.createElement('a'); link.href = '#github-' + encodeURIComponent(doc.path); link.innerHTML = `${doc.title}<small>${doc.path}</small>`;
        link.addEventListener('click', event => { event.preventDefault(); loadGithubDoc(doc.path); }); target.appendChild(link);
      });
      if (!githubDocuments.length) target.innerHTML = '<span style="display:block;padding:8px 10px;color:#8fa5ac;font:11px ui-monospace,monospace">repositório não configurado</span>';
    }
    async function loadGithubDoc(path) {
      try { const doc = await request(`/api/github-doc?path=${encodeURIComponent(path)}`); article.innerHTML = doc.html; pathLabel.textContent = 'GitHub / ' + doc.path; document.querySelectorAll('nav a').forEach(link => link.classList.remove('active')); }
      catch (error) { article.innerHTML = `<p class="empty">${error.message}</p>`; }
    }
  async function loadDoc(path) {
    try { const doc = await request(`/api/doc?path=${encodeURIComponent(path)}`); article.innerHTML = doc.html; pathLabel.textContent = doc.path; document.querySelectorAll('nav a').forEach(link => link.classList.toggle('active', link.dataset.path === path)); history.replaceState({}, '', `#${encodeURIComponent(path)}`); }
    catch (error) { article.innerHTML = `<p class="empty">${error.message}</p>`; }
  }
  search.addEventListener('input', () => { drawNav(search.value); drawGithubNav(search.value); });
  Promise.all([request('/api/docs'), request('/api/github-docs')]).then(([local, remote]) => { documents = local.documents; githubDocuments = remote.documents; drawNav(); drawGithubNav(); const initial = decodeURIComponent(location.hash.slice(1)); if (initial.startsWith('github-')) loadGithubDoc(initial.slice(7)); else loadDoc(documents.some(doc => doc.path === initial) ? initial : documents[0].path); }).catch(error => { article.innerHTML = `<p class="empty">${error.message}</p>`; });
  </script>
</body>
</html>"""


def _inline_markdown(value: str) -> str:
  escaped = html.escape(value, quote=False)
  escaped = re.sub(r"`([^`]+)`", r"<code>\1</code>", escaped)
  escaped = re.sub(r"\*\*([^*]+)\*\*", r"<strong>\1</strong>", escaped)
  escaped = re.sub(r"\[([^\]]+)\]\(([^)]+)\)", r'<a href="\2">\1</a>', escaped)
  return escaped


def markdown_to_html(markdown: str) -> str:
  """Renderiza o subconjunto de Markdown usado na documentação do projeto."""
  output: list[str] = []
  paragraph: list[str] = []
  in_code = False
  code_lines: list[str] = []
  in_list = False
  list_tag = "ul"

  def flush_paragraph() -> None:
    if paragraph:
      output.append(f"<p>{_inline_markdown(' '.join(paragraph))}</p>")
      paragraph.clear()

  def close_list() -> None:
    nonlocal in_list
    if in_list:
      output.append(f"</{list_tag}>")
      in_list = False

  lines = markdown.replace("\r\n", "\n").split("\n")
  index = 0
  while index < len(lines):
    line = lines[index]
    if line.startswith("```"):
      flush_paragraph(); close_list()
      if in_code:
        code = html.escape("\n".join(code_lines))
        output.append(f"<pre><code>{code}</code></pre>")
        code_lines.clear()
        in_code = False
      else:
        in_code = True
      index += 1
      continue
    if in_code:
      code_lines.append(line); index += 1; continue
    heading = re.match(r"^(#{1,3})\s+(.+)$", line)
    if heading:
      flush_paragraph(); close_list(); level = len(heading.group(1)); output.append(f"<h{level}>{_inline_markdown(heading.group(2))}</h{level}>"); index += 1; continue
    table_match = index + 1 < len(lines) and "|" in line and re.match(r"^\s*\|?\s*:?-+:?\s*(\|\s*:?-+:?\s*)+\|?\s*$", lines[index + 1])
    if table_match:
      flush_paragraph(); close_list()
      headers = [cell.strip() for cell in line.strip("|").split("|")]
      rows = []
      index += 2
      while index < len(lines) and "|" in lines[index] and lines[index].strip():
        rows.append([cell.strip() for cell in lines[index].strip("|").split("|")]); index += 1
      output.append("<table><thead><tr>" + "".join(f"<th>{_inline_markdown(cell)}</th>" for cell in headers) + "</tr></thead><tbody>" + "".join("<tr>" + "".join(f"<td>{_inline_markdown(cell)}</td>" for cell in row) + "</tr>" for row in rows) + "</tbody></table>")
      continue
    list_match = re.match(r"^\s*([-*]|\d+\.)\s+(.+)$", line)
    if list_match:
      flush_paragraph(); tag = "ol" if list_match.group(1)[0].isdigit() else "ul"
      if not in_list or tag != list_tag:
        close_list(); list_tag = tag; output.append(f"<{list_tag}>"); in_list = True
      output.append(f"<li>{_inline_markdown(list_match.group(2))}</li>"); index += 1; continue
    if line.startswith(">"):
      flush_paragraph(); close_list(); output.append(f"<blockquote>{_inline_markdown(line[1:].strip())}</blockquote>"); index += 1; continue
    if not line.strip():
      flush_paragraph(); close_list()
    else:
      paragraph.append(line.strip())
    index += 1
  flush_paragraph(); close_list()
  if in_code:
    code = html.escape("\n".join(code_lines))
    output.append(f"<pre><code>{code}</code></pre>")
  return "\n".join(output)


def discover_markdown(root: Path) -> list[dict[str, str]]:
  """Encontra documentos Markdown sem sair da raiz informada."""
  if not root.is_dir():
    raise FileNotFoundError(f"raiz da documentação não encontrada: {root}")
  documents = []
  for path in root.rglob("*.md"):
    relative_parts = path.relative_to(root).parts
    if any(part in DOC_SKIP_DIRS or part.startswith(".") for part in relative_parts):
      continue
    content = path.read_text(encoding="utf-8")
    title_match = re.search(r"^#\s+(.+)$", content, re.MULTILINE)
    documents.append({"path": path.relative_to(root).as_posix(), "title": title_match.group(1).strip() if title_match else path.stem.replace("-", " ").title()})
  return sorted(documents, key=lambda item: (item["path"].lower() != "readme.md", item["path"].lower()))


def github_repository(root: Path) -> str | None:
  """Obtém owner/repositório a partir do remote origin, quando disponível."""
  try:
    remote = subprocess.check_output(
      ["git", "-C", str(root), "config", "--get", "remote.origin.url"],
      text=True,
      stderr=subprocess.DEVNULL,
    ).strip()
  except (OSError, subprocess.CalledProcessError):
    return None
  match = re.search(r"github\.com[:/]([^/]+)/([^/]+?)(?:\.git)?$", remote)
  return f"{match.group(1)}/{match.group(2)}" if match else None


def discover_github_markdown(root: Path, repository: str | None = None, branch: str = "main") -> list[dict[str, str]]:
  """Lista Markdown do repositório GitHub pela API de árvores Git."""
  repository = repository or github_repository(root)
  if not repository:
    return []
  url = f"{GITHUB_API}/repos/{repository}/git/trees/{branch}?recursive=1"
  request = urllib.request.Request(url, headers={"Accept": "application/vnd.github+json", "User-Agent": "automatizando-latex"})
  token = os.environ.get("GITHUB_TOKEN")
  if token:
    request.add_header("Authorization", f"Bearer {token}")
  try:
    with urllib.request.urlopen(request, timeout=8) as response:
      tree = json.loads(response.read().decode("utf-8"))
  except (urllib.error.URLError, json.JSONDecodeError, TimeoutError):
    return []
  documents = []
  for item in tree.get("tree", []):
    path = item.get("path", "")
    if item.get("type") == "blob" and path.lower().endswith(".md"):
      documents.append({"path": path, "title": Path(path).stem.replace("-", " ").title()})
  return sorted(documents, key=lambda item: (item["path"].lower() != "readme.md", item["path"].lower()))


def fetch_github_markdown(repository: str, path: str, branch: str = "main") -> str:
  """Baixa um Markdown específico do GitHub e renderiza apenas seu conteúdo."""
  if not re.fullmatch(r"[A-Za-z0-9_.-]+/[A-Za-z0-9_.-]+", repository) or ".." in Path(path).parts:
    raise ValueError("documento GitHub inválido")
  url = f"https://raw.githubusercontent.com/{repository}/{branch}/{path}"
  request = urllib.request.Request(url, headers={"User-Agent": "automatizando-latex"})
  try:
    with urllib.request.urlopen(request, timeout=8) as response:
      return response.read().decode("utf-8")
  except (urllib.error.URLError, UnicodeDecodeError) as error:
    raise FileNotFoundError(f"documento GitHub não encontrado: {path}") from error


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


class DocsHandler(BaseHTTPRequestHandler):
    """Endpoints do portal de documentação Markdown."""

    docs_root: Path
    github_repo: str | None = None
    github_branch: str = "main"

    def _send_json(self, payload: dict, status: HTTPStatus = HTTPStatus.OK) -> None:
        body = json.dumps(payload, ensure_ascii=False).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def _error(self, error: Exception, status: HTTPStatus = HTTPStatus.BAD_REQUEST) -> None:
        self._send_json({"error": str(error)}, status)

    def _safe_doc(self, relative_path: str) -> Path:
        root = self.docs_root.resolve()
        candidate = (root / relative_path).resolve()
        if root not in candidate.parents or candidate.suffix.lower() != ".md":
            raise ValueError("documento não permitido")
        if not candidate.is_file():
            raise FileNotFoundError(f"documento não encontrado: {relative_path}")
        return candidate

    def do_GET(self) -> None:
        parsed = urlparse(self.path)
        try:
            if parsed.path == "/":
                body = DOCS_HTML.encode("utf-8")
                self.send_response(HTTPStatus.OK)
                self.send_header("Content-Type", "text/html; charset=utf-8")
                self.send_header("Content-Length", str(len(body)))
                self.end_headers()
                self.wfile.write(body)
            elif parsed.path == "/api/docs":
                self._send_json({"documents": discover_markdown(self.docs_root)})
            elif parsed.path == "/api/doc":
                relative_path = parse_qs(parsed.query).get("path", [""])[0]
                path = self._safe_doc(relative_path)
                self._send_json({"path": relative_path, "html": markdown_to_html(path.read_text(encoding="utf-8"))})
            elif parsed.path == "/api/github-docs":
              self._send_json({"repository": self.github_repo, "documents": discover_github_markdown(self.docs_root, self.github_repo, self.github_branch)})
            elif parsed.path == "/api/github-doc":
              relative_path = parse_qs(parsed.query).get("path", [""])[0]
              repository = self.github_repo or github_repository(self.docs_root)
              if not repository:
                raise ValueError("repositório GitHub não configurado")
              self._send_json({"path": relative_path, "html": markdown_to_html(fetch_github_markdown(repository, relative_path, self.github_branch))})
            else:
                self._error(ValueError("rota não encontrada"), HTTPStatus.NOT_FOUND)
        except FileNotFoundError as error:
            self._error(error, HTTPStatus.NOT_FOUND)
        except (ValueError, OSError) as error:
            self._error(error)

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


def serve_docs(root: Path, host: str = "127.0.0.1", port: int = 8766, open_browser: bool = True, github_repo: str | None = None, github_branch: str = "main") -> None:
    """Inicia o portal local que exibe os Markdown da raiz informada."""
    discover_markdown(root)
    handler = type("BoundDocsHandler", (DocsHandler,), {"docs_root": root.resolve(), "github_repo": github_repo, "github_branch": github_branch})
    server = ThreadingHTTPServer((host, port), handler)
    url = f"http://{host}:{server.server_port}/"
    print(f"Documentação disponível em {url}")
    if open_browser:
        threading.Timer(0.4, webbrowser.open, args=(url,)).start()
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\nDocumentação encerrada.")
    finally:
        server.server_close()