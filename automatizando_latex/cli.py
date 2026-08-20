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

REQUIRED_PROJECT_FILES = ("main.tex", "configuracao.tex", "referencias.bib")


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


def _bib_escape(value: str) -> str:
    """Escapa valores básicos de uma entrada BibTeX."""
    return value.replace("{", "\\{").replace("}", "\\}").replace("\n", " ").strip()


def _project_file(project_dir: Path, filename: str) -> Path:
    if not project_dir.is_dir():
        raise FileNotFoundError(f"diretório do projeto não encontrado: {project_dir}")
    path = project_dir / filename
    if not path.is_file():
        raise FileNotFoundError(f"arquivo obrigatório não encontrado: {path}")
    return path


def insert_section(
    project_dir: Path,
    title: str,
    content: str = "Escreva o conteúdo desta seção.\n",
    level: str = "chapter",
) -> Path:
    """Insere uma seção no texto antes da bibliografia."""
    if level not in {"part", "chapter", "section", "subsection", "subsubsection"}:
        raise ValueError("nível inválido; use part, chapter, section, subsection ou subsubsection")
    path = _project_file(project_dir, "main.tex")
    document = path.read_text(encoding="utf-8")
    marker = "\\postextual"
    if marker not in document:
        raise ValueError(f"marcador {marker} não encontrado em {path}")
    section = f"\\{level}{{{_latex_escape(title)}}}\n\n{content.rstrip()}\n\n"
    path.write_text(document.replace(marker, section + marker, 1), encoding="utf-8")
    return path


def add_table(
    project_dir: Path,
    caption: str,
    columns: list[str],
    rows: list[list[str]],
) -> Path:
    """Adiciona uma tabela simples antes da bibliografia."""
    if not columns:
        raise ValueError("a tabela precisa de pelo menos uma coluna")
    if any(len(row) != len(columns) for row in rows):
        raise ValueError("cada linha precisa ter a mesma quantidade de valores das colunas")
    path = _project_file(project_dir, "main.tex")
    document = path.read_text(encoding="utf-8")
    alignment = " ".join("l" for _ in columns)
    lines = [
        "\\begin{table}[htbp]",
        "\\centering",
        f"\\caption{{{_latex_escape(caption)}}}",
        f"\\begin{{tabular}}{{{alignment}}}",
        "\\toprule",
        " & ".join(_latex_escape(column) for column in columns) + r" \\",
        "\\midrule",
    ]
    lines.extend(
        " & ".join(_latex_escape(value) for value in row) + r" \\"
        for row in rows
    )
    lines.extend(["\\bottomrule", "\\end{tabular}", "\\end{table}", ""])
    marker = "\\postextual"
    if marker not in document:
        raise ValueError(f"marcador {marker} não encontrado em {path}")
    path.write_text(document.replace(marker, "\n".join(lines) + marker, 1), encoding="utf-8")
    return path


def add_reference(
    project_dir: Path,
    key: str,
    author: str,
    title: str,
    year: str,
    journal: str,
) -> Path:
    """Adiciona uma referência de artigo ao banco BibTeX."""
    if not re.fullmatch(r"[A-Za-z][A-Za-z0-9:_-]*", key):
        raise ValueError("a chave deve começar com letra e conter apenas letras, números, :, _ ou -")
    path = _project_file(project_dir, "referencias.bib")
    document = path.read_text(encoding="utf-8")
    if re.search(rf"^\s*@\w+\s*\{{\s*{re.escape(key)}\s*,", document, re.MULTILINE):
        raise ValueError(f"a referência já existe: {key}")
    entry = (
        f"@article{{{key},\n"
        f"  author  = {{{_bib_escape(author)}}},\n"
        f"  title   = {{{_bib_escape(title)}}},\n"
        f"  journal = {{{_bib_escape(journal)}}},\n"
        f"  year    = {{{_bib_escape(year)}}}\n"
        "}\n"
    )
    separator = "\n" if document and not document.endswith("\n\n") else ""
    path.write_text(document + separator + entry, encoding="utf-8")
    return path


def check_project(project_dir: Path) -> list[Path]:
    """Valida e retorna os arquivos essenciais de um projeto."""
    return [_project_file(project_dir, filename) for filename in REQUIRED_PROJECT_FILES]


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
    section_parser = subparsers.add_parser(
        "section", help="insere uma seção no arquivo principal"
    )
    section_parser.add_argument("project", type=Path, help="diretório do projeto")
    section_parser.add_argument("title", help="título da seção")
    section_parser.add_argument(
        "--level", choices=("part", "chapter", "section", "subsection", "subsubsection"),
        default="section",
    )
    section_parser.add_argument(
        "--content", default="Escreva o conteúdo desta seção.", help="conteúdo inicial"
    )
    table_parser = subparsers.add_parser("table", help="insere uma tabela no arquivo principal")
    table_parser.add_argument("project", type=Path, help="diretório do projeto")
    table_parser.add_argument("caption", help="legenda da tabela")
    table_parser.add_argument(
        "--columns", required=True, help="colunas separadas por vírgula"
    )
    table_parser.add_argument(
        "--row", action="append", default=[], help="linha separada por vírgula; repita para novas linhas"
    )
    reference_parser = subparsers.add_parser(
        "reference", help="adiciona um artigo ao arquivo BibTeX"
    )
    reference_parser.add_argument("project", type=Path, help="diretório do projeto")
    reference_parser.add_argument("key", help="chave usada em \\cite{...}")
    reference_parser.add_argument("--author", required=True)
    reference_parser.add_argument("--title", required=True)
    reference_parser.add_argument("--year", required=True)
    reference_parser.add_argument("--journal", required=True)
    check_parser = subparsers.add_parser(
        "check", help="verifica os arquivos essenciais de um projeto"
    )
    check_parser.add_argument("project", type=Path, help="diretório do projeto")
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
    elif args.command == "section":
        try:
            path = insert_section(args.project, args.title, args.content, args.level)
        except (FileNotFoundError, ValueError) as error:
            print(f"Erro: {error}")
            return 1
        print(f"Seção adicionada em {path}")
    elif args.command == "table":
        try:
            columns = [column.strip() for column in args.columns.split(",")]
            rows = [[value.strip() for value in row.split(",")] for row in args.row]
            path = add_table(args.project, args.caption, columns, rows)
        except (FileNotFoundError, ValueError) as error:
            print(f"Erro: {error}")
            return 1
        print(f"Tabela adicionada em {path}")
    elif args.command == "reference":
        try:
            path = add_reference(
                args.project,
                args.key,
                args.author,
                args.title,
                args.year,
                args.journal,
            )
        except (FileNotFoundError, ValueError) as error:
            print(f"Erro: {error}")
            return 1
        print(f"Referência adicionada em {path}")
    elif args.command == "check":
        try:
            files = check_project(args.project)
        except FileNotFoundError as error:
            print(f"Erro: {error}")
            return 1
        print(f"Projeto válido: {args.project}")
        for path in files:
            print(f"  - {path.name}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())