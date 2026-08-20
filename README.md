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
cd projetos/meu-artigo
python -m automatizando_latex.cli build .
```

O comando `build` executa a sequência completa:

```text
pdflatex -> bibtex -> pdflatex -> pdflatex
```

As três passagens do LaTeX resolvem referências cruzadas, sumário e citações
depois que o BibTeX gera a bibliografia. O PDF será criado em
`projetos/meu-artigo/main.pdf`.

Por padrão, todo projeto novo é criado em `projetos/`. Essa pasta está no
`.gitignore`, portanto os artigos e PDFs gerados nela não serão enviados ao
GitHub. Para usar outra pasta, informe `--output-dir`:

```bash
python -m automatizando_latex.cli init meu-artigo --output-dir rascunhos
```

O tipo padrão é `artigo`. Também é possível criar `tcc`, `monografia`,
`dissertacao` ou `tese`:

```bash
python -m automatizando_latex.cli init meu-tcc \
	--type tcc \
	--title "Meu trabalho de conclusão" \
	--author "Seu Nome"
```

Cada tipo ajusta `\\tipotrabalho` e `\\preambulo` em `configuracao.tex`. Os
campos comuns, como instituição, cidade e orientador, continuam editáveis no
arquivo gerado.

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
python -m automatizando_latex.cli init abnt --type artigo --title "Paul_Dirac" --author "ItaloMiguel"
```

Isso cria a pasta `projetos/abnt`. Para gerar o PDF, a máquina também
precisa ter TeX Live e a classe `abntex2` instalados. Em uma instância Linux
EC2, por exemplo, instale-os antes da compilação:

```bash
sudo apt update
sudo apt install -y texlive-latex-base texlive-lang-portuguese texlive-publishers texlive-binaries
cd projetos/abnt
python -m automatizando_latex.cli build .
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

O workflow `CI` do GitHub Actions roda automaticamente em cada `push` para
`main`/`master` e em cada Pull Request. Ele testa Python 3.10 a 3.13 e faz um
smoke test da CLI. A segunda job compila um artigo ABNT completo com BibTeX e
publica o PDF como artefato da execução. Consulte [CONTRIBUTING.md](CONTRIBUTING.md)
para o padrão de commits e o checklist de Pull Requests.

O PDF e os arquivos auxiliares de compilação ficam fora do versionamento. O
texto-fonte continua disponível para comparar qualquer mudança ao longo do
tempo.

## Testes

```powershell
python -m pytest
```

## Próximos passos

- criar comandos para inserir seções, tabelas e referências;
- adicionar uma interface de edição e visualização em tempo real.