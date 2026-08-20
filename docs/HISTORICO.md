# Histórico recente

Este documento resume os três commits mais recentes do projeto. A fonte de
verdade continua sendo o histórico do Git.

## 2026-08-20

### `7cc6c9d` feat(web): adiciona editor local com visualizacao PDF

- adiciona o comando `serve`;
- cria editor local para `main.tex`, `configuracao.tex` e `referencias.bib`;
- salva alterações automaticamente;
- permite compilar LaTeX/BibTeX e visualizar `main.pdf` no navegador;
- restringe a API aos arquivos permitidos do projeto.

### `8dd3f88` feat(cli): adiciona comandos de edicao de artigos

- adiciona `section`, `table`, `reference` e `check`;
- escapa valores básicos para LaTeX e BibTeX;
- evita referências BibTeX duplicadas;
- cobre os comandos com testes automatizados.

### `4b895d1` ci: automatiza validacao e compilacao ABNT

- cria o workflow do GitHub Actions;
- testa múltiplas versões do Python;
- compila um artigo ABNT com BibTeX no CI;
- publica o PDF como artefato;
- adiciona checklist de Pull Request e guia de contribuição.

## Como atualizar

Ao adicionar uma funcionalidade relevante, atualize o README e acrescente uma
entrada nesta página com o commit correspondente. Não substitua este resumo:
adicione o item mais recente no topo.