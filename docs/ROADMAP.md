# Roadmap

Ideias que podem melhorar a experiência sem aumentar muito a complexidade.

## Curto prazo

- adicionar um botão para criar seções, tabelas e referências pela interface;
- mostrar o erro de compilação em um painel com destaque da linha;
- incluir um comando `clean` para remover arquivos auxiliares do LaTeX;
- permitir escolher o arquivo `.tex` principal na interface.

## Médio prazo

- mostrar o diff da última alteração antes de salvar;
- criar snapshots locais nomeados, além do histórico do Git;
- adicionar upload de imagens e uma galeria de figuras do projeto;
- oferecer modelos de referência para livros, sites e trabalhos acadêmicos.

## Longo prazo

- criar autenticação e armazenamento remoto para uso em equipe;
- adicionar colaboração simultânea com controle de conflitos;
- integrar revisão textual e validações específicas das normas ABNT;
- publicar uma imagem Docker com TeX Live e dependências fixadas.

## Critérios para priorizar

Priorize funcionalidades que reduzam edição manual, tenham baixo risco de
perder conteúdo e possam ser cobertas por testes automatizados. Toda nova
operação de escrita deve recusar sobrescritas silenciosas e gerar uma mensagem
de erro clara.