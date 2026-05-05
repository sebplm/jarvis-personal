# Configuration de Jarvis Personnel

Ce guide couvre l'installation complète avec Claude Sonnet 4.6, Google Calendar multi-comptes, Gmail, Slack, WhatsApp et iMessage.

---

## 1. Prérequis

```bash
# Python 3.10+
python3 --version

# uv (gestionnaire de paquets rapide)
curl -LsSf https://astral.sh/uv/install.sh | sh

# Rust (pour la compilation du composant natif)
curl --proto '=https' --tlsv1.2 -sSf https://sh.rustup.rs | sh
```

---

## 2. Installation

```bash
cd jarvis-personal
uv sync
uv run maturin develop -m rust/crates/openjarvis-python/Cargo.toml

# Copier la config personnalisée
cp configs/openjarvis/config.personal.toml ~/.openjarvis/config.toml

# Copier le fichier de variables d'environnement
cp .env.example .env
```

---

## 3. Clé API Anthropic (Claude)

1. Aller sur [console.anthropic.com/settings/keys](https://console.anthropic.com/settings/keys)
2. Créer une nouvelle clé API
3. Renseigner dans `.env` :
   ```
   ANTHROPIC_API_KEY=sk-ant-...
   ```

---

## 4. Google Calendar & Gmail (multi-comptes)

### 4a. Créer le projet Google Cloud

1. Aller sur [console.cloud.google.com](https://console.cloud.google.com)
2. Créer un nouveau projet (ex: "Jarvis Personnel")
3. Activer les APIs suivantes :
   - **Google Calendar API**
   - **Gmail API**
4. Dans "Identifiants" → "Créer des identifiants" → "ID client OAuth 2.0"
   - Type d'application : **Application de bureau**
   - Télécharger le JSON

### 4b. Autoriser chaque compte

Pour chaque adresse mail (perso, mentorshow, etc.) :

```bash
# Compte perso
source .env
uv run jarvis connect gcalendar --account perso \
  --client-id $GOOGLE_CLIENT_ID_PERSO \
  --client-secret $GOOGLE_CLIENT_SECRET_PERSO

# Compte MentorShow
uv run jarvis connect gcalendar --account mentorshow \
  --client-id $GOOGLE_CLIENT_ID_MENTORSHOW \
  --client-secret $GOOGLE_CLIENT_SECRET_MENTORSHOW
```

> Un navigateur s'ouvre pour chaque compte → autoriser l'accès → les tokens sont sauvegardés dans `~/.openjarvis/connectors/gcalendar_<compte>.json`

---

## 5. Slack

1. Aller sur [api.slack.com/apps](https://api.slack.com/apps) → "Create New App"
2. Choisir "From scratch" → donner un nom (ex: "Jarvis") → sélectionner ton workspace
3. Dans "OAuth & Permissions" → ajouter ces **Bot Token Scopes** :
   - `channels:history`, `channels:read`, `chat:write`
   - `im:history`, `im:read`, `users:read`
4. Installer l'app dans le workspace → copier le **Bot User OAuth Token**
5. Activer "Socket Mode" → créer un App-Level Token avec scope `connections:write`
6. Renseigner dans `.env` :
   ```
   SLACK_BOT_TOKEN=xoxb-...
   SLACK_APP_TOKEN=xapp-...
   ```

---

## 6. WhatsApp

> Nécessite un compte **WhatsApp Business** et un numéro dédié.

1. Aller sur [developers.facebook.com](https://developers.facebook.com) → créer une app "Business"
2. Ajouter le produit **WhatsApp**
3. Dans "API Setup" → copier le token d'accès temporaire (ou créer un token permanent)
4. Renseigner dans `.env` :
   ```
   WHATSAPP_API_TOKEN=EAA...
   WHATSAPP_PHONE_NUMBER_ID=...
   WHATSAPP_VERIFY_TOKEN=mon_token_secret
   ```

---

## 7. iMessage & SMS (iPhone via Mac)

Aucune configuration d'API requise — Jarvis lit directement la base de données de l'app Messages sur ton Mac.

**Deux étapes obligatoires :**

1. **Activer la synchronisation iMessage sur Mac** :
   Messages.app → Préférences → iMessage → cocher "Activer Messages dans iCloud"

2. **Donner l'accès disque complet à Terminal** (ou à l'app Jarvis) :
   Préférences Système → Confidentialité & Sécurité → Accès complet au disque → ajouter Terminal.app

Tester :
```bash
uv run jarvis ask "Montre-moi mes derniers messages iMessage"
```

---

## 8. Lancer Jarvis

```bash
# Charger les variables d'environnement
source .env

# Test rapide
uv run jarvis ask "Bonjour, quels sont mes rendez-vous aujourd'hui ?"

# Mode interactif
uv run jarvis chat

# Serveur API (pour desktop app ou frontend web)
uv run jarvis serve
```

---

## 9. Ajouter d'autres comptes Google

Éditer `~/.openjarvis/config.toml` → section `[connectors.gcalendar_multi]` :

```toml
accounts = [
  { label = "perso",      credentials = "~/.openjarvis/connectors/gcalendar_perso.json" },
  { label = "mentorshow", credentials = "~/.openjarvis/connectors/gcalendar_mentorshow.json" },
  { label = "nouveau",    credentials = "~/.openjarvis/connectors/gcalendar_nouveau.json" },
]
```

Puis relancer l'OAuth pour le nouveau compte :
```bash
uv run jarvis connect gcalendar --account nouveau \
  --client-id $GOOGLE_CLIENT_ID_NOUVEAU \
  --client-secret $GOOGLE_CLIENT_SECRET_NOUVEAU
```

---

## Résumé des fichiers importants

| Fichier | Rôle |
|---|---|
| `~/.openjarvis/config.toml` | Configuration principale |
| `.env` | Clés API (ne jamais committer) |
| `~/.openjarvis/connectors/gcalendar_<compte>.json` | Tokens OAuth Google Calendar |
| `~/.openjarvis/connectors/gmail_<compte>.json` | Tokens OAuth Gmail |
| `~/.openjarvis/connectors/slack.json` | Token Slack |
| `~/.openjarvis/memory.db` | Mémoire locale de Jarvis |
