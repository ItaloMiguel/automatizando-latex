from pathlib import Path
import tempfile
import json
import threading
import unittest
from http.server import ThreadingHTTPServer
from urllib.error import HTTPError
from urllib.request import Request, urlopen
from unittest.mock import patch

from automatizando_latex.cli import (
    DEFAULT_OUTPUT_DIR,
    PUBLICATION_PROFILES,
    _slug,
    build_parser,
    build_project,
    add_reference,
    add_table,
    check_project,
    create_article,
    insert_section,
)
from automatizando_latex.web import EDITOR_FILES, ProjectHandler, HTML


class CreateArticleTests(unittest.TestCase):
    def test_cli_uses_private_projects_directory_by_default(self):
        arguments = build_parser().parse_args(["init", "artigo"])

        self.assertEqual(arguments.output_dir, DEFAULT_OUTPUT_DIR)

    def test_cli_accepts_custom_output_directory(self):
        arguments = build_parser().parse_args(
            ["init", "artigo", "--output-dir", "rascunhos"]
        )

        self.assertEqual(arguments.output_dir, "rascunhos")

    def test_slug_normalizes_project_name(self):
        self.assertEqual(_slug("Meu Artigo 2026"), "meu-artigo-2026")

    def test_create_article_escapes_latex_metadata(self):
        with tempfile.TemporaryDirectory() as directory:
            configuration = create_article(
                Path(directory) / "artigo", "Paul_Dirac", "ItaloMiguel"
            )[1].read_text(encoding="utf-8")

            self.assertIn("\\titulo{Paul\\_Dirac}", configuration)

    def test_create_article_writes_abnt_project(self):
        with tempfile.TemporaryDirectory() as directory:
            destination = Path(directory) / "artigo"
            files = create_article(destination, "Pesquisa sobre tecnologia", "Ana Silva")

            self.assertEqual(
                {path.name for path in files},
                {"main.tex", "configuracao.tex", "referencias.bib", "README.md"},
            )
            main = (destination / "main.tex").read_text(encoding="utf-8")
            self.assertIn("\\documentclass[12pt,oneside,a4paper]{abntex2}", main)
            self.assertIn("\\bibliographystyle{abntex2-alf}", main)
            configuration = (destination / "configuracao.tex").read_text(
                encoding="utf-8"
            )
            self.assertIn("\\titulo{Pesquisa sobre tecnologia}", configuration)
            self.assertIn("\\autor{Ana Silva}", configuration)

    def test_create_article_supports_all_publication_types(self):
        for publication_type, profile in PUBLICATION_PROFILES.items():
            with self.subTest(publication_type=publication_type):
                with tempfile.TemporaryDirectory() as directory:
                    configuration = create_article(
                        Path(directory) / publication_type,
                        "Título",
                        "Autor",
                        publication_type,
                    )[1].read_text(encoding="utf-8")

                    self.assertIn(f"\\tipotrabalho{{{profile.label}}}", configuration)
                    self.assertIn(f"\\preambulo{{{profile.preambulo}}}", configuration)

    def test_create_article_rejects_unknown_publication_type(self):
        with tempfile.TemporaryDirectory() as directory:
            with self.assertRaises(ValueError):
                create_article(Path(directory) / "artigo", "Título", "Autor", "livro")

    def test_create_article_does_not_overwrite_existing_directory(self):
        with tempfile.TemporaryDirectory() as directory:
            destination = Path(directory) / "artigo"
            destination.mkdir()

            with self.assertRaises(FileExistsError):
                create_article(destination, "Título", "Autor")

    @patch("automatizando_latex.cli.subprocess.run")
    def test_build_project_runs_latex_and_bibtex_sequence(self, run):
        with tempfile.TemporaryDirectory() as directory:
            project = Path(directory)
            (project / "main.tex").write_text("\\documentclass{article}", encoding="utf-8")

            commands = build_project(project)

            self.assertEqual(run.call_count, 4)
            self.assertEqual(
                [call.args[0] for call in run.call_args_list],
                [
                    ["pdflatex", "-interaction=nonstopmode", "main.tex"],
                    ["bibtex", "main"],
                    ["pdflatex", "-interaction=nonstopmode", "main.tex"],
                    ["pdflatex", "-interaction=nonstopmode", "main.tex"],
                ],
            )
            self.assertEqual(len(commands), 4)

    def test_insert_section_adds_content_before_posttextual(self):
        with tempfile.TemporaryDirectory() as directory:
            project = Path(directory) / "projeto"
            create_article(project, "Título", "Autor")

            insert_section(project, "Método", "Descreva o método.", "section")
            document = (project / "main.tex").read_text(encoding="utf-8")

            self.assertIn("\\section{Método}\n\nDescreva o método.", document)
            self.assertLess(document.index("\\section{Método}"), document.index("\\postextual"))

    def test_add_table_generates_latex_table(self):
        with tempfile.TemporaryDirectory() as directory:
            project = Path(directory) / "projeto"
            create_article(project, "Título", "Autor")

            add_table(project, "Resultados", ["Nome", "Valor"], [["A", "10"]])
            document = (project / "main.tex").read_text(encoding="utf-8")

            self.assertIn("\\caption{Resultados}", document)
            self.assertIn("Nome & Valor", document)
            self.assertIn("A & 10", document)

    def test_add_reference_appends_bibtex_entry_and_rejects_duplicate(self):
        with tempfile.TemporaryDirectory() as directory:
            project = Path(directory) / "projeto"
            create_article(project, "Título", "Autor")

            add_reference(project, "silva2026", "Silva, Ana", "Pesquisa", "2026", "Revista")
            bibliography = (project / "referencias.bib").read_text(encoding="utf-8")

            self.assertIn("@article{silva2026,", bibliography)
            with self.assertRaises(ValueError):
                add_reference(project, "silva2026", "Silva, Ana", "Outra", "2026", "Revista")

    def test_check_project_returns_required_files(self):
        with tempfile.TemporaryDirectory() as directory:
            project = Path(directory) / "projeto"
            create_article(project, "Título", "Autor")

            self.assertEqual(
                {path.name for path in check_project(project)},
                {"main.tex", "configuracao.tex", "referencias.bib"},
            )

    def test_web_interface_reads_and_saves_project_files(self):
        with tempfile.TemporaryDirectory() as directory:
            project = Path(directory) / "projeto"
            create_article(project, "Título", "Autor")
            handler = type(
                "TestProjectHandler", (ProjectHandler,), {"project_dir": project}
            )
            server = ThreadingHTTPServer(("127.0.0.1", 0), handler)
            thread = threading.Thread(target=server.serve_forever, daemon=True)
            thread.start()
            base_url = f"http://127.0.0.1:{server.server_port}"
            try:
                with urlopen(f"{base_url}/api/project") as response:
                    project_data = json.loads(response.read())
                self.assertEqual(project_data["files"], list(EDITOR_FILES))

                payload = json.dumps(
                    {"name": "main.tex", "content": "conteúdo atualizado"}
                ).encode("utf-8")
                request = Request(
                    f"{base_url}/api/file",
                    data=payload,
                    method="PUT",
                    headers={"Content-Type": "application/json"},
                )
                with urlopen(request) as response:
                    self.assertEqual(response.status, 200)
                self.assertEqual(
                    (project / "main.tex").read_text(encoding="utf-8"),
                    "conteúdo atualizado",
                )
            finally:
                server.shutdown()
                server.server_close()

    def test_web_interface_does_not_expose_other_files(self):
        self.assertIn("Ateliê ABNT", HTML)
        with tempfile.TemporaryDirectory() as directory:
            project = Path(directory) / "projeto"
            create_article(project, "Título", "Autor")
            (project / "segredo.txt").write_text("segredo", encoding="utf-8")
            handler = type(
                "TestProjectHandler", (ProjectHandler,), {"project_dir": project}
            )
            server = ThreadingHTTPServer(("127.0.0.1", 0), handler)
            thread = threading.Thread(target=server.serve_forever, daemon=True)
            thread.start()
            try:
                with self.assertRaises(HTTPError) as error:
                    urlopen(f"http://127.0.0.1:{server.server_port}/api/file?name=segredo.txt")
                self.assertEqual(error.exception.code, 400)
                error.exception.close()
            finally:
                server.shutdown()
                server.server_close()