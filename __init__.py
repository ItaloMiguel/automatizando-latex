"""Inicializador simples: execute `python3 __init__.py` na raiz do projeto."""

from pathlib import Path

from automatizando_latex.web import serve_docs


if __name__ == "__main__":
    serve_docs(Path(__file__).parent)