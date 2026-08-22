# 001 Arquitetura Híbrida CLI e Servidor Web Nativo

* **status:** Proposto
* **Contexto:** 2026-08-22
* **Author:** Ítalo Miguel

## Contexto e Problema

O projeto atual consiste em uma CLI em Python para automação de documenttos LateX no padrão ABNT. Identifiquei a necessidade de expandir a experiência do usuário adicionando uma interface gráfica web que permita:
1. Edição de texto em tempo real (Markdown/Latex/PDF)
2. Visualização dinâmica do PDF compilado ao lado do editor.
3. Sincronização e salvamento dos arquivos compilados diretamente no Google Drive do usuário. 

# Decisão

Refatorar o componente `web.py`para atuar como um **servidor híbrido nativo**, utilizando estrututamente as bibliotecas padrão do python (`http.server`, `urllib` e `threading`).

A arquitetura seguirá os seguinte pilares:

* **Front-end Desacoplado:** Toda a interface visual será escrita em HTML5, CSS3 e JavaScrip assíncrono (Fetch API) puros, embutido na resposta do servidor ou servidos estaticamente.
* **API Rest Nativa:** O `web.py`estenderá o `BaseHTTPRequestHandler`para expor endipoint JSON (ex: `api/compile`), processando requisições `POST`sem bloquear o CLI através de `ThreadingHTTPServer`.
* **Autenticação Descentralizada (OAuth 2.0):** O Front-end obterá o token de acesso do Google Drive diretamente no navegador via *Google Identity Services*. Este token será repassado para a API Python via cabeçalho `Authorization: Bearer <token>`.
* **Upload Multipart Puro:** O servidor Python fará o upload do PDF para o Google Drive através de requisições HTTP construídas manualmente com `urllib.request`.

## Consequências

### Positivas
* **Dependência Zero:** O projeto continua extremamente leve e fácil de instalar, exigindo apenas o Python padrão e o compilador LaTeX da máquina (`pdflatex`).
* **Segurança:** O token do Google Drive fica na memória do navegador e transita apenas para o endpoint local, evitando armazenamento de chaves secretas no backend.
* **Experiência Visual:** A visualização em tempo real via Iframe melhora drasticamente o fluxo de escrita do usuário.

### Negativas / Desafios
* **Manutenção Manual:** Sem frameworks, a validação de rotas HTTP, tratamento de erros de API e montagem de pacotes Multipart precisam ser controlados manualmente no código Python.
