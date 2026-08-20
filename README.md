# Automatizando LaTeX

Ferramenta para iniciar artigos científicos em LaTeX usando a classe `abntex2`,
com fontes simples de editar e versionar no Git.

## Requisitos

- Python 3.10 ou superior;
- uma distribuição LaTeX com a classe `abntex2` instalada, como TeX Live ou MiKTeX;
- Git para acompanhar a evolução do texto.

## Uso

Na raiz deste repositório, crie um ambiente virtual e instale o projeto em modo editável:

```bash
python3 -m venv .venv
source .venv/bin/activate
python -m pip install -e .
```

Crie um artigo:

```powershell
python -m automatizando_latex.cli init meu-artigo --title "Meu primeiro artigo" --author "Seu Nome"
cd meu-artigo
pdflatex main.tex
```

Para consultar a ajuda, execute o comando separadamente:

```powershell
python -m automatizando_latex.cli init -h
```

## Executar na AWS

Como o projeto é uma CLI, a forma mais simples de testá-lo na AWS é pelo
**AWS CloudShell**. No terminal da AWS, clone o repositório e instale o pacote:

```bash
git clone URL_DO_SEU_REPOSITORIO
cd automatizando-latex
sudo apt update
sudo apt install -y python3-venv
python3 -m venv .venv
source .venv/bin/activate
python -m pip install -e .
python -m automatizando_latex.cli init abnt --title "Paul_Dirac" --author "ItaloMiguel"
```

Isso cria a pasta `abnt` no diretório atual. Para gerar o PDF, a máquina também
precisa ter TeX Live e a classe `abntex2` instalados. Em uma instância Linux
EC2, por exemplo, instale-os antes da compilação:

```bash
sudo apt update
sudo apt install -y texlive-latex-base texlive-lang-portuguese texlive-publishers
cd abnt
pdflatex main.tex
```

O CloudShell e o EC2 servem para executar a ferramenta. Para armazenar os
artigos e PDFs entre sessões, use GitHub ou S3. Lambda não é a melhor primeira
opção para este projeto, pois exige empacotar uma distribuição LaTeX grande e
um mecanismo adicional para devolver os arquivos gerados.

Edite `main.tex`, `configuracao.tex` e `referencias.bib`. Registre cada etapa
com commits pequenos e descritivos:

```powershell
git add .
git commit -m "Escreve introducao do artigo"
```

O PDF e os arquivos auxiliares de compilação ficam fora do versionamento. O
texto-fonte continua disponível para comparar qualquer mudança ao longo do
tempo.

## Testes

```powershell
python -m pytest
```

## Próximos passos

- adicionar suporte a múltiplos tipos de publicação;
- incluir uma rotina de compilação completa com BibTeX;
- criar comandos para inserir seções, tabelas e referências;
- adicionar uma interface de edição e visualização em tempo real.