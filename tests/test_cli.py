from pathlib import Path
import tempfile
import unittest

from automatizando_latex.cli import (
    DEFAULT_OUTPUT_DIR,
    PUBLICATION_PROFILES,
    _slug,
    build_parser,
    create_article,
)


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