"""Interface de linha de comando para criar projetos de artigos."""

from __future__ import annotations

import argparse
import re
import subprocess
from dataclasses import dataclass
from pathlib import Path


DEFAULT_OUTPUT_DIR = "projetos"


TEMPLATE = r"""\documentclass[12pt,oneside,a4paper]{abntex2}

\usepackage[T1]{fontenc}
\usepackage[utf8]{inputenc}
\usepackage[brazil]{babel}
\usepackage{lmodern}
\usepackage{microtype}
\usepackage{indentfirst}
\usepackage{csquotes}
\usepackage{graphicx}
\usepackage{booktabs}

\input{configuracao}

\begin{document}

\imprimircapa
\imprimirfolhaderosto

\begin{resumo}
Escreva aqui o resumo do artigo. Substitua este texto antes da submissão.

\vspace{\onelineskip}
\noindent
\textbf{Palavras-chave}: palavra-chave 1. Palavra-chave 2. Palavra-chave 3.
\end{resumo}

\pdfbookmark[0]{\contentsname}{toc}
\tableofcontents*
\clearpage

\textual
\chapter{Introdução}

Apresente o tema, o problema de pesquisa e os objetivos do artigo.

\chapter{Desenvolvimento}

Organize a fundamentação teórica e a análise em seções. Para citar uma obra,
use o arquivo de referências, por exemplo: \cite{exemplo2026}.

\chapter{Conclusão}

Retome os resultados e indique possíveis trabalhos futuros.

\postextual
\bibliography{referencias}

\end{document}
"""

CONFIG_TEMPLATE = r"""% Dados usados na capa e na folha de rosto.
\titulo{Título do artigo}
\autor{Nome do autor}
\local{Cidade}
\data{\today}
\instituicao{Instituição de ensino}
\tipotrabalho{Artigo científico}
\preambulo{Artigo apresentado como requisito para publicação.}

\orientador{Nome do orientador}
"""


@dataclass(frozen=True)
class PublicationProfile:
    """Metadados específicos de um tipo de publicação."""

    label: str
    preambulo: str


PUBLICATION_PROFILES = {
    "artigo": PublicationProfile(
        "Artigo científico",
        "Artigo apresentado como requisito para publicação.",
    ),
    "tcc": PublicationProfile(
        "Trabalho de conclusão de curso",
        "Trabalho de conclusão de curso apresentado como requisito para obtenção do grau.",
    ),
    "monografia": PublicationProfile(
        "Monografia",
        "Monografia apresentada como requisito para obtenção do título.",
    ),
    "dissertacao": PublicationProfile(
        "Dissertação",
        "Dissertação apresentada como requisito para obtenção do título de mestre.",
    ),
    "tese": PublicationProfile(
        "Tese",
        "Tese apresentada como requisito para obtenção do título de doutor.",
    ),
}

BIB_TEMPLATE = r"""@article{exemplo2026,
  author  = {Sobrenome, Nome},
  title   = {Título da obra citada},
  journal = {Nome do Periódico},
  year    = {2026},
  volume  = {1},
  number  = {1},
  pages   = {1--10}
}
"""


def _slug(value: str) -> str:
    """Converte um nome de projeto em um diretório simples e previsível."""
    normalized = re.sub(r"[^a-zA-Z0-9_-]+", "-", value.strip()).strip("-")
    if not normalized:
        raise ValueError("o nome do projeto precisa conter letras ou números")
    return normalized.lower()


def _latex_escape(value: str) -> str:
    """Escapa caracteres reservados nos campos de metadados LaTeX."""
    replacements = {
        "\\": r"\textbackslash{}",
        "&": r"\&",
        "%": r"\%",
        "$": r"\$",
        "#": r"\#",
        "_": r"\_",
        "{": r"\{",
        "}": r"\}",
        "~": r"\textasciitilde{}",
        "^": r"\textasciicircum{}",
    }
    return "".join(replacements.get(character, character) for character in value)


def create_article(
    destination: Path,
    title: str,
    author: str,
    publication_type: str = "artigo",
) -> list[Path]:
    """Cria um projeto de artigo e retorna os arquivos criados."""
    if destination.exists():
        raise FileExistsError(f"o diretório já existe: {destination}")
    try:
        profile = PUBLICATION_PROFILES[publication_type]
    except KeyError as error:
        valid_types = ", ".join(PUBLICATION_PROFILES)
        raise ValueError(
            f"tipo de publicação inválido: {publication_type}; use: {valid_types}"
        ) from error

    destination.mkdir(parents=True)
    files = {
        "main.tex": TEMPLATE,
        "configuracao.tex": CONFIG_TEMPLATE.replace(
            "Título do artigo", _latex_escape(title)
        ).replace(
            "Nome do autor", _latex_escape(author)
        ).replace(
            "Artigo científico", profile.label
        ).replace(
            "Artigo apresentado como requisito para publicação.", profile.preambulo
        ),
        "referencias.bib": BIB_TEMPLATE,
        "README.md": (
            f"# {title}\n\n"
            f"Projeto de {profile.label.lower()} iniciado com `automatizando-latex`. "
            "Edite `main.tex`, "
            "`configuracao.tex` e `referencias.bib`.\n"
        ),
    }
    created = []
    for filename, content in files.items():
        path = destination / filename
        path.write_text(content, encoding="utf-8")
        created.append(path)
    return created


def build_project(project_dir: Path, tex_file: str = "main.tex") -> list[str]:
    """Compila um projeto com as passagens necessárias para atualizar referências."""
    source = project_dir / tex_file
    if not project_dir.is_dir():
        raise FileNotFoundError(f"diretório do projeto não encontrado: {project_dir}")
    if not source.is_file():
        raise FileNotFoundError(f"arquivo LaTeX não encontrado: {source}")

    document = source.stem
    commands = [
        ["pdflatex", "-interaction=nonstopmode", tex_file],
        ["bibtex", document],
        ["pdflatex", "-interaction=nonstopmode", tex_file],
        ["pdflatex", "-interaction=nonstopmode", tex_file],
    ]
    for command in commands:
        try:
            result = subprocess.run(
                command,
                cwd=project_dir,
                check=True,
                capture_output=True,
                text=True,
            )
        except FileNotFoundError as error:
            raise RuntimeError(
                f"comando não encontrado: {command[0]}. "
                "Instale uma distribuição LaTeX com BibTeX."
            ) from error
        except subprocess.CalledProcessError as error:
            output = (error.stdout or "") + (error.stderr or "")
            raise RuntimeError(
                f"falha ao executar {' '.join(command)}:\n{output[-4000:]}"
            ) from error
    return [" ".join(command) for command in commands]


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="abnt", description="Cria projetos de artigos LaTeX no padrão ABNT."
    )
    subparsers = parser.add_subparsers(dest="command", required=True)
    init_parser = subparsers.add_parser("init", help="cria um novo projeto de artigo")
    init_parser.add_argument("name", help="nome do diretório do artigo")
    init_parser.add_argument("--title", default="Título do artigo")
    init_parser.add_argument("--author", default="Nome do autor")
    init_parser.add_argument(
        "--output-dir",
        default=DEFAULT_OUTPUT_DIR,
        help=f"pasta para os projetos (padrão: {DEFAULT_OUTPUT_DIR}/)",
    )
    init_parser.add_argument(
        "--type",
        dest="publication_type",
        choices=tuple(PUBLICATION_PROFILES),
        default="artigo",
        help="tipo de publicação (padrão: artigo)",
    )
    build_parser = subparsers.add_parser(
        "build", help="compila um projeto com LaTeX e BibTeX"
    )
    build_parser.add_argument("project", type=Path, help="diretório do projeto")
    build_parser.add_argument(
        "--tex-file", default="main.tex", help="arquivo principal (padrão: main.tex)"
    )
    return parser


def main() -> int:
    args = build_parser().parse_args()
    if args.command == "init":
        output_dir = Path(args.output_dir)
        if not output_dir.is_absolute():
            output_dir = Path.cwd() / output_dir
        destination = output_dir / _slug(args.name)
        try:
            created = create_article(
                destination, args.title, args.author, args.publication_type
            )
        except (FileExistsError, ValueError) as error:
            print(f"Erro: {error}")
            return 1
        print(f"Projeto criado em {destination}")
        for path in created:
            print(f"  - {path.name}")
    elif args.command == "build":
        try:
            commands = build_project(args.project, args.tex_file)
        except (FileNotFoundError, RuntimeError) as error:
            print(f"Erro: {error}")
            return 1
        print(f"Projeto compilado em {args.project}")
        for command in commands:
            print(f"  - {command}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())