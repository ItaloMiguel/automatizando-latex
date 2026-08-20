"""Inicializador simples: execute `python3 __init__.py` na raiz do projeto."""

from pathlib import Path

from automatizando_latex.web_home import serve_home


if __name__ == "__main__":
    serve_home()