# Automatizando LaTeX

A small tool for creating, editing, documenting, and versioning ABNT-style
LaTeX publications.

## Quick start

Clone the repository and run the root launcher:

```bash
git clone REPOSITORY_URL
cd automatizando-latex
python3 __init__.py
```

Open `http://127.0.0.1:8766`. The portal displays local Markdown files and a
**GitHub Documents** section loaded through the GitHub API. It also provides a
welcome screen with Portuguese/English translation and a live HTML reading
preview for LaTeX files in the article editor.

## Create and edit a publication

```bash
python -m automatizando_latex.cli init my-article \
  --title "My article" \
  --author "Your Name"
python -m automatizando_latex.cli serve projetos/my-article
```

The editor automatically saves `main.tex`, `configuracao.tex`, and
`referencias.bib`. The **Leitura** tab updates as you type without requiring a
LaTeX installation. The **PDF** tab becomes available after pressing
**Compilar PDF**, when TeX Live or MiKTeX is installed.

## Documentation and GitHub

The portal discovers Markdown files from the local repository. It detects the
GitHub repository from `git remote origin`, or you can configure it explicitly:

```bash
python -m automatizando_latex.cli docs . \
  --github-repo owner/repository \
  --github-branch main
```

For private repositories, set a read-only `GITHUB_TOKEN` in the environment.
Never commit tokens to the repository.

## Development

```bash
python -m unittest discover -v
```

See the Portuguese [README](../README.md), [roadmap](ROADMAP.md), and
[contribution guide](../CONTRIBUTING.md) for the complete workflow.