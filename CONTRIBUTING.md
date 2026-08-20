# Contribuindo

## Fluxo recomendado

1. Crie uma branch curta a partir de `main`.
2. Faça uma mudança pequena e executável.
3. Rode `python -m unittest discover -v`.
4. Registre um commit com uma única intenção.
5. Abra um Pull Request e aguarde o workflow `CI`.

## Commits

Use o formato [Conventional Commits](https://www.conventionalcommits.org/):

```text
tipo(escopo): descrição no imperativo
```

Tipos comuns: `feat`, `fix`, `test`, `docs`, `refactor`, `ci` e `chore`.

Exemplos:

```text
feat(cli): adiciona compilação com BibTeX
ci: valida a CLI em múltiplas versões do Python
docs: documenta o fluxo de publicação
```

Não inclua credenciais, PDFs ou artefatos de compilação. Projetos criados em
`projetos/` já são ignorados pelo Git.