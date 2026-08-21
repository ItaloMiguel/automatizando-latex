FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PROJECT_DIR=/workspace/rascunhos/artigo-abnt

WORKDIR /app

COPY pyproject.toml README.md LICENSE ./
COPY automatizando_latex ./automatizando_latex
COPY docs ./docs
COPY CONTRIBUTING.md ./CONTRIBUTING.md
COPY __init__.py ./__init__.py
COPY docker/start.sh /usr/local/bin/start-automatizando-latex

RUN python -m pip install --no-cache-dir --upgrade pip \
    && python -m pip install --no-cache-dir . \
    && apt-get update \
    && apt-get install -y --no-install-recommends \
        texlive-latex-base \
        texlive-latex-extra \
        texlive-lang-portuguese \
        texlive-publishers \
        texlive-binaries \
    && rm -rf /var/lib/apt/lists/* \
    && chmod +x /usr/local/bin/start-automatizando-latex \
    && useradd --create-home --shell /usr/sbin/nologin appuser \
    && mkdir -p /workspace \
    && chown -R appuser:appuser /app /workspace

USER appuser
EXPOSE 8000 8765 8766

CMD ["start-automatizando-latex"]
