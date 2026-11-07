#!/usr/bin/env bash
# Instalador de uma linha para o Termux (tablet Android).
# Prepara tudo e abre o Claude ja com a tarefa de otimizar o projetor HY320.
set -e
BASE="https://raw.githubusercontent.com/josejhsn/painel-rj-2026/claude/otimizar-tablet-projetor-xrp9kf/projetor"
DIR="$HOME/hy320"

echo "== 1/4 Instalando pacotes (pode levar alguns minutos) =="
pkg update -y >/dev/null 2>&1 || true
pkg install -y nodejs-lts android-tools curl

echo "== 2/4 Instalando o Claude Code =="
command -v claude >/dev/null 2>&1 || npm install -g @anthropic-ai/claude-code

echo "== 3/4 Baixando os arquivos do projetor =="
mkdir -p "$DIR"
curl -fsSL "$BASE/otimizar_hy320.sh" -o "$DIR/otimizar_hy320.sh"
curl -fsSL "$BASE/instrucoes_claude_local.md" -o "$DIR/instrucoes_claude_local.md"
chmod +x "$DIR/otimizar_hy320.sh"

echo "== 4/4 Abrindo o Claude =="
echo "Se pedir login, entre com a mesma conta do app do Claude."
cd "$DIR"
exec claude "Leia instrucoes_claude_local.md e execute tudo"
