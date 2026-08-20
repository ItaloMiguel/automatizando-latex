# Automatizando LaTeX

Ferramenta para iniciar artigos científicos em LaTeX usando a classe `abntex2`,
com fontes simples de editar e versionar no Git.

## Fluxo rápido

```bash
git clone URL_DO_REPOSITORIO
cd automatizando-latex
python3 -m venv .venv
source .venv/bin/activate
python -m pip install -e .
python -m automatizando_latex.cli init meu-artigo --title "Meu artigo" --author "Seu Nome"
python3 __init__.py
```

Abra `http://127.0.0.1:8766` no navegador. O portal visualiza a documentação
do projeto e a seção `GitHub Documents` carrega arquivos Markdown do repositório
GitHub configurado no `origin`. Para editar um artigo, use o editor separado:

No WSL, o servidor imprime a URL e pode não abrir o navegador automaticamente.
Nesse caso, abra o endereço no navegador do Windows.

```bash
python -m automatizando_latex.cli serve projetos/meu-artigo
```

O projeto mantém os fontes em arquivos de texto para que cada mudança possa ser
revisada e versionada com Git. Consulte [CONTRIBUTING.md](CONTRIBUTING.md) para
commits e Pull Requests, [docs/HISTORICO.md](docs/HISTORICO.md) para o histórico
recente e [docs/ROADMAP.md](docs/ROADMAP.md) para ideias futuras.

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

Os comandos disponíveis são `init`, `serve`, `build`, `check`, `section`,
`table`, `reference` e `docs`. Veja todos os argumentos com:

```bash
python -m automatizando_latex.cli --help
```

## Portal visual da documentação

Para navegar pela documentação Markdown do projeto em uma interface visual:

```bash
python -m automatizando_latex.cli docs .
```

O mesmo portal é iniciado diretamente pela raiz com:

```bash
python3 __init__.py
```

O portal abre em `http://127.0.0.1:8766` e encontra automaticamente arquivos
`.md` na raiz informada, incluindo `README.md`, `CONTRIBUTING.md` e a pasta
`docs/`. Ele oferece navegação lateral, busca por nome, renderização de títulos,
listas, tabelas, links, citações e blocos de código, além de layout responsivo.

O comando `serve` continua dedicado ao editor de um artigo individual. Essa
separação mantém a documentação do projeto independente do conteúdo LaTeX de
cada artigo.

O portal também exibe `docs/README.en.md`, uma tradução em inglês, e
`docs/LICENSE.md`, uma cópia documental da licença MIT. A fonte legal da licença
continua sendo o arquivo `LICENSE` na raiz.

### Documentação do GitHub

O portal tenta descobrir automaticamente o repositório a partir de:

```bash
git remote get-url origin
```

Para informar o repositório manualmente:

```bash
python -m automatizando_latex.cli docs . \
	--github-repo italo/automatizando-latex \
	--github-branch main
```

A API usa a árvore pública do GitHub e o conteúdo bruto dos arquivos Markdown.
Para repositórios privados, configure um token com acesso de leitura antes de
iniciar o servidor:

```bash
export GITHUB_TOKEN=seu_token_de_leitura
python3 __init__.py
```

O token nunca é exibido na página. Não o commite nem o inclua em arquivos do
projeto.

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

## Comandos de edição

Valide um projeto antes de compilá-lo:

```bash
python -m automatizando_latex.cli check projetos/meu-artigo
```

Insira uma seção no `main.tex`. Por padrão, ela é adicionada antes de
`\\postextual`:

```bash
python -m automatizando_latex.cli section projetos/meu-artigo "Metodologia" \
	--level section \
	--content "Descreva aqui os métodos utilizados."
```

Adicione uma tabela. As colunas e linhas usam vírgulas como separador; repita
`--row` para incluir mais linhas:

```bash
python -m automatizando_latex.cli table projetos/meu-artigo "Resultados" \
	--columns "Indicador,Valor" \
	--row "Amostra,120" \
	--row "Respostas,98"
```

Adicione uma referência de artigo ao `referencias.bib`:

```bash
python -m automatizando_latex.cli reference projetos/meu-artigo silva2026 \
	--author "Silva, Ana" \
	--title "Um estudo sobre o tema" \
	--year 2026 \
	--journal "Revista Científica"
```

Depois cite a chave no texto com `\\cite{silva2026}` e compile:

```bash
python -m automatizando_latex.cli build projetos/meu-artigo
```

## Interface de edição

Abra o editor local apontando para um projeto:

```bash
python -m automatizando_latex.cli serve projetos/meu-artigo
```

O navegador abrirá em `http://127.0.0.1:8765`. A interface oferece:

- tela de recepção antes do editor;
- tradução visível entre Português e English;
- edição de `main.tex`, `configuracao.tex` e `referencias.bib`;
- salvamento automático após uma pausa na digitação;
- botão para salvar manualmente;
- compilação completa com LaTeX e BibTeX;
- prévia HTML em tempo real do arquivo `.tex`;
- visualização do `main.pdf` em uma aba ao lado, quando compilado.

O salvamento e a prévia HTML são em tempo real, mas a geração do PDF acontece
ao clicar em `Compilar PDF`, pois compilar LaTeX a cada tecla seria lento. Para escolher
outra porta ou evitar a abertura automática do navegador:

```bash
python -m automatizando_latex.cli serve projetos/meu-artigo \
	--port 9000 \
	--no-browser
```

Instale TeX Live ou MiKTeX para habilitar a visualização do PDF. Sem LaTeX, o
editor e o salvamento continuam disponíveis.

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

- adicionar histórico visual de versões e comparação entre commits;
- incluir suporte a imagens e upload de arquivos do projeto;
- criar uma fila de compilação para trabalhos longos.