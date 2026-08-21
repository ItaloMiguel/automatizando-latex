#!/bin/sh
set -eu

project_dir="${PROJECT_DIR:-/workspace/rascunhos/artigo-abnt}"
host="${HOST:-0.0.0.0}"

if [ ! -d "$project_dir" ]; then
  echo "Aviso: projeto não encontrado em $project_dir" >&2
  echo "Crie um projeto com o comando init ou ajuste PROJECT_DIR." >&2
fi

python -m automatizando_latex.cli docs /app --host "$host" --port 8766 --no-browser &
docs_pid=$!
python -m automatizando_latex.cli serve "$project_dir" --host "$host" --port 8765 --no-browser &
editor_pid=$!
python -c "from automatizando_latex.web_home import serve_home; serve_home('$host', 8000, False)" &
home_pid=$!

trap 'kill "$docs_pid" "$editor_pid" "$home_pid" 2>/dev/null || true' INT TERM EXIT
wait "$docs_pid" "$editor_pid" "$home_pid"
