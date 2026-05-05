#!/bin/zsh
# Lance Jarvis — double-clic ou ./start.sh dans le terminal

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
cd "$SCRIPT_DIR"

# Ajouter uv au PATH si nécessaire
export PATH="$HOME/.local/bin:$PATH"

# Charger les clés API
if [ -f "$SCRIPT_DIR/.env" ]; then
  set -a
  source "$SCRIPT_DIR/.env"
  set +a
else
  echo "❌  Fichier .env introuvable dans $SCRIPT_DIR"
  exit 1
fi

# Vérifier que la clé Anthropic est bien là
if [ -z "$ANTHROPIC_API_KEY" ]; then
  echo "❌  ANTHROPIC_API_KEY manquante dans .env"
  exit 1
fi

echo "✅  Jarvis prêt (Claude Sonnet 4.6)"
echo "───────────────────────────────────"

uv run jarvis chat
