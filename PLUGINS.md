# 📚 Plugin Moderazione - Documentazione Essenziale

Sistema avanzato di moderazione con database SQLite, logging automatico, ban/mute temporanei e controllo permessi.

## 📖 Indice

1. [Installazione e Configurazione](#installazione)
2. [Comandi Disponibili](#comandi)
3. [Database SQLite](#database)

---

## 🔧 Installazione {#installazione}

### Step 1: Configurazione Base

Modifica `config/moderation.json`. **Nota: I valori numerici vanno inseriti come stringhe.**

```json
{
  "staff_roles": [],           // ID ruoli staff (es: [123456789])
  "admin_roles": [],           // ID ruoli admin
  "log_channel_id": null,      // ID canale log (o "123456789")
  "mute_role_id": null,        // ID ruolo mute (null = auto-creazione)
  "mute_role_name": "Muted",
  "embed_colors": {
    "warn": "#FFA500",
    "ban": "#DC143C",
    "mute": "#FFD700",
    "success": "#00FF00",
    "error": "#FF0000"
  },
  "rate_limit": {
    "enabled": true,
    "max_commands": "5",       // Stringa!
    "per_seconds": "60"        // Stringa!
  },
  "auto_actions": {
    "enabled": true,
    "auto_ban_warns": "5",     // Stringa!
    "auto_mute_warns": "3"     // Stringa!
  },
  "dm_users": true,
  "log_file_enabled": true     // Abilita log su file
}
```

### Step 2: Abilita Plugin

In `config/plugins.json`:
```json
{
  "moderation": true
}
```

### Step 3: Riavvia Bot
```bash
python bot.py
```

---

## 🎮 Comandi Disponibili {#comandi}

Tutti i comandi supportano sia prefix (`!`) che slash (`/`).

### 🛡️ Moderazione Base

| Comando | Sintassi | Descrizione | Permessi |
|---------|----------|-------------|----------|
| **Warn** | `/warn @user [motivo]` | Assegna un avvertimento | Staff |
| **Unwarn** | `/unwarn @user [id]` | Rimuove un avvertimento | Admin |
| **Kick** | `/kick @user [motivo]` | Espelle un utente | Staff |
| **Clear** | `/clear [n]` | Cancella messaggi | Staff |

### 🔨 Ban & Mute (Temporanei)

Supportano durata flessibile: `30s`, `10m`, `1h`, `7d`, `4w`.

| Comando | Sintassi | Descrizione | Permessi |
|---------|----------|-------------|----------|
| **Ban** | `/ban @user [durata] [motivo]` | Banna (temp/perm) | Admin |
| **Unban** | `/unban <id> [motivo]` | Rimuove ban | Admin |
| **Mute** | `/mute @user [durata] [motivo]` | Silenzia (temp/perm) | Staff |
| **Unmute** | `/unmute @user` | Rimuove silenziamento | Staff |

**Esempi:**
- `/ban @User 1h Spam` (Ban per 1 ora)
- `/mute @User 30m Insulti` (Mute per 30 minuti)

---

## 🗄️ Database SQLite {#database}

Il database è in `data/moderation.db`.

### Tabelle Principali
- **warns**: Storico avvertimenti
- **bans**: Storico ban (attivi e passati)
- **mutes**: Storico mute
- **mod_log**: Audit log completo di tutte le azioni

### Backup
Il sistema esegue backup automatici se configurato in `moderation.json`.

---

## 📜 Licenza

Plugin open source per FlexCore Discord Bot.
