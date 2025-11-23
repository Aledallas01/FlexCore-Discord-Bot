# 📚 Plugin Moderazione - Documentazione Completa

Sistema avanzato di moderazione con database SQLite, logging automatico, ban/mute temporanei e controllo permessi.

## 📖 Indice

1. [Installazione e Configurazione](#installazione)
2. [Comandi Disponibili](#comandi)
3. [Database SQLite](#database)
4. [Testing](#testing)
5. [Estensioni Future](#estensioni)

---

## 🔧 Installazione {#installazione}

### Step 1: Configurazione Base

Modifica `config/moderation.json`:

```json
{
  "staff_roles": [1234567890, 9876543210],  // ← Aggiungi ID ruoli staff
  "admin_roles": [1112223334],               // ← Aggiungi ID ruoli admin
  "log_channel_id": 555666777888,            // ← ID canale log
  "mute_role_id": null,                      // ← null = auto-creazione
  "mute_role_name": "Muted",
  "embed_colors": {
    "warn": "#FFA500"  // Arancione
    // ... altri colori
  },
  "rate_limit": {
    "enabled": true,
    "max_commands": 5,
    "per_seconds": 60
  },
  "auto_actions": {
    "enabled": true,
    "auto_ban_warns": 5,    // Ban automatico a 5 warn
    "auto_mute_warns": 3     // Mute automatico a 3 warn
  },
  "dm_users": true
}
```

### Step 2: Abilita Plugin

In `config/plugins.json`, assicurati che moderation sia `true`:

```json
{
  "moderation": true
}
```

### Step 3: Permessi Bot Discord

Il bot necessita dei seguenti permessi:
- ✅ Manage Roles (per mute)
- ✅ Kick Members
- ✅ Ban Members
- ✅ Send Messages (canale log)
- ✅ Embed Links
- ✅ Manage Channels (per permessi ruolo mute)

### Step 4: Riavvia Bot

```bash
python bot.py
```

Output atteso:
```
✅ Configurazione moderazione caricata da config/moderation.json
✅ Plugin 'moderation' caricato
```

---

## 🎮 Comandi Disponibili {#comandi}

### 1. `/warn`  - Avvertimento Utente

**Sintassi:** `/warn @utente [motivo]`

**Descrizione:** Assigns a warning to a user and saves it in the database

**Permessi:** Staff roles

**Parametri:**
- `user` (required): Discord Member to warn
- `reason` (optional): Reason for the warning

**Comportamento:**
1. Verifica permessi staff
2. Applica rate limiting
3. Salva warn in DB con timestamp
4. Invia DM all'utente (se abilitato)
5. Log in canale configurato
6. Mostra conteggio warn totali
7. Trigger auto-actions se soglie raggiunte (auto-mute a 3, auto-ban a 5)

**Esempio:**
```
/warn @Utente#1234 Spam in chat generale
```

**Output:**
```
🚨 Warn Assegnato
━━━━━━━━━━━━━━━━
⚠️ Warn #15

Utente: @Utente#1234 (123456789)
Moderatore: @Mod#5678
Motivo: Spam in chat generale
Warn Totali: 2
```

**Test:**
```python
# Test 1: Warn base
/warn @TestUser Motivo di test

# Test 2: Warn senza motivo
/warn @TestUser

# Test 3: Verifica auto-actions
/warn @TestUser Prima warn
/warn @TestUser Seconda warn
/warn @TestUser Terza warn  # ← Dovrebbe auto-mutare
```

---

### 2. `/unwarn` - Rimozione Warn

**Sintassi:** `/unwarn @utente [warn_id]`

**Permessi:** Admin roles

**Parametri:**
- `user` (required): Utente da cui rimuovere warn
- `warn_id` (optional): ID specifico del warn. Se omesso, rimuove l'ultimo

**Comportamento:**
1. Verifica permessi admin
2. Rimuove warn dal DB (per ID o ultimo)
3. Mostra warn rimanenti
4. Log in canale

**Esempio:**
```
# Rimuovi ultimo warn
/unwarn @Utente#1234

# Rimuovi warn specifico
/unwarn @Utente#1234 15
```

---

### 3. `/kick` - Espulsione

**Sintassi:** `/kick @utente [motivo]`

**Permessi:** Staff roles

**Parametri:**
- `user` (required): Utente da espellere
- `reason` (optional): Motivo del kick

**Comportamento:**
1. Verifica permessi e gerarchia ruoli
2. Invia DM all'utente prima del kick
3. Esegue kick
4. Salva in DB
5. Log in canale

**Sicurezza:**
- Non può kickare se stesso
- Non può kickare il bot
- Non può kickare ruoli superiori

**Test:**
```
/kick @TestUser Comportamento inappropriato
```

---

### 4. `/ban` - Bandimento

**Sintassi:** `/ban @utente [duration] [motivo]`

**Permessi:** Admin roles

**Parametri:**
- `user` (required): Utente da bannare
- `duration` (optional): Durata ban. **Formato flessibile `Nt`:**
  - `s` = secondi (es: `30s`)
  - `m` = minuti (es: `45m`)
  - `h` = ore (es: `2h`)
  - `d` = giorni (es: `7d`)
  - `w` = settimane (es: `2w`)
  - `M` = mesi (es: `3M`)
  - `y` = anni (es: `1y`)
  - Se omesso = **permanente**
- `reason` (optional): Motivo del ban

**Comportamento:**
1. Verifica permessi admin
2. Parse durata (con validazione formato)
3. Invia DM all'utente
4. Esegue ban
5. Salva in DB con expiry timestamp
6. Se temporaneo, crea task asyncio per auto-unban
7. Task ripristinati dopo restart bot
8. Log in canale

**Esempi:**
```
# Ban permanente
/ban @Hacker#666 Cheating

# Ban 30 minuti
/ban @Spammer#123 30m Spam ripetuto

# Ban 7 giorni
/ban @Troll#999 7d Comportamento tossico

# Ban 2 settimane
/ban @User#111 2w Violazione regole gravi

# Ban 3 mesi
/ban @User#222 3M Recidivo

# Ban 1 anno
/ban @User#333 1y Ban esteso
```

**Task Manager:**
- All'avvio bot, carica ban attivi da DB
- Ripristina task per ban non ancora scaduti
- Auto-unban alla scadenza con log automatico

**Test Tempor anei:**
```python
# Test ban 1 minuto
/ban @TestUser 1m Test ban temporaneo

# Attendi 1 minuto → Verifica auto-unban nel log channel
# Verifica che il ban sia stato rimosso dal server
```

---

### 5. `/unban` - Rimozione Ban

**Sintassi:** `/unban <user_id> [motivo]`

**Permessi:** Admin roles

**Parametri:**
- `user_id` (required): ID Discord dell'utente (stringa)
- `reason` (optional): Motivo dell'unban

**Comportamento:**
1. Converti e valida ID
2. Fetch utente da Discord
3. Rimuovi ban dal server
4. Aggiorna DB
5. Log in canale

**Esempio:**
```
/unban 123456789012345678 Appeal accettato
```

**Nota:** Usa ID numerico, non @mention (utente non è nel server)

---

### 6. `/mute` - Silenziamento

**Sintassi:** `/mute @utente [duration] [motivo]`

**Permessi:** Staff roles

**Parametri:**
- `user` (required): Utente da silenziare
- `duration` (optional): Durata mute (formato `Nt`, stesso di ban)
- `reason` (optional): Motivo del mute

**Comportamento:**
1. Ottiene/crea ruolo "Muted"
2. Auto-configura permessi canali (no speak/write)
3. Applica ruolo all'utente
4. Salva in DB con expiry
5. Se temporaneo, crea task per auto-unmute
6. DM all'utente
7. Log in canale

**Esempi:**
```
# Mute permanente
/mute @Disturbatore#123 Spam vocale

# Mute 1 ora
/mute @Flame#456 1h Insulti in chat

# Mute 30 minuti
/mute @Caps#789 30m All caps spam
```

**Auto-creazione Ruolo:**
- Se `mute_role_id` non configurato, crea ruolo "Muted"
- Imposta permessi su tutti i canali:
  - ❌ Send Messages
  - ❌ Speak
  - ❌ Add Reactions
  - ❌ Create Threads

---

### 7. `/unmute` - Rimozione Mute

**Sintassi:** `/unmute @utente [motivo]`

**Permessi:** Staff roles

**Parametri:**
- `user` (required): Utente da smutare
- `reason` (optional): Motivo dell'unmute

**Comportamento:**
1. Verifica che utente abbia ruolo mute
2. Rimuovi ruolo
3. Aggiorna DB
4. Log in canale

**Esempio:**
```
/unmute @Utente#123 Comportamento migliorato
```

---

## 🗄️ Database SQLite {#database}

### Schema Tabelle

Il database è salvato in `data/moderation.db` e contiene 5 tabelle:

#### 1. `warns`
```sql
CREATE TABLE warns (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER NOT NULL,
    moderator_id INTEGER NOT NULL,
    guild_id INTEGER NOT NULL,
    reason TEXT,
    timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
);
```

#### 2. `bans`
```sql
CREATE TABLE bans (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER NOT NULL,
    moderator_id INTEGER NOT NULL,
    guild_id INTEGER NOT NULL,
    reason TEXT,
    duration INTEGER,        -- secondi, NULL = permanente
    expires_at DATETIME,
    timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
    active BOOLEAN DEFAULT 1
);
```

#### 3. `mutes`
```sql
CREATE TABLE mutes (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER NOT NULL,
    moderator_id INTEGER NOT NULL,
    guild_id INTEGER NOT NULL,
    reason TEXT,
    duration INTEGER,
    expires_at DATETIME,
    timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
    active BOOLEAN DEFAULT 1
);
```

#### 4. `kicks`
```sql
CREATE TABLE kicks (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER NOT NULL,
    moderator_id INTEGER NOT NULL,
    guild_id INTEGER NOT NULL,
    reason TEXT,
    timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
);
```

#### 5. `mod_log` (Audit)
```sql
CREATE TABLE mod_log (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    action_type TEXT NOT NULL,  -- WARN, KICK, BAN, MUTE
    user_id INTEGER NOT NULL,
    moderator_id INTEGER NOT NULL,
    guild_id INTEGER NOT NULL,
    details TEXT,
    timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
);
```

### Query di Esempio

```sql
-- Conta warn di un utente
SELECT COUNT(*) FROM warns WHERE user_id = ? AND guild_id = ?;

-- Ottieni ban attivi
SELECT * FROM bans WHERE active = 1 AND guild_id = ?;

-- Storico completo utente
SELECT * FROM mod_log WHERE user_id = ? ORDER BY timestamp DESC;

-- Ban in scadenza nelle prossime 24h
SELECT * FROM bans 
WHERE active = 1 
  AND expires_at IS NOT NULL 
  AND expires_at BETWEEN datetime('now') AND datetime('now', '+1 day');
```

### Backup Database

Il database è auto-creato all'avvio. Per backup manuale:

```bash
# Copia file database
cp data/moderation.db data/backups/moderation_backup_2025-11-23.db
```

---

## 🧪 Testing Completo {#testing}

### Test Suite Base

```python
# 1. TEST WARN SYSTEM
/warn @TestUser Prima infrazione
# Verifica: warn salvato in DB, DM inviato, conteggio = 1

/warn @TestUser Seconda infrazione
# Verifica: conteggio = 2

/warn @TestUser Terza infrazione
# Verifica: Se auto_actions abilitato → auto-mute 1h

# 2. TEST UNWARN
/unwarn @TestUser
# Verifica: ultimo warn rimosso, conteggio = 2

# 3. TEST KICK
/kick @TestUser Comportamento spam
# Verifica: utente kickato, salvato in DB, log generato

# 4. TEST BAN TEMPORANEO
/ban @TestUser 2m Test ban 2 minuti
# Attendi 2 minuti
# Verifica: auto-unban, log generato, ban_active = 0 in DB

# 5. TEST BAN PERMANENTE
/ban @TestUser Cheating permanente
# Verifica: ban applicato, no expiry in DB

# 6. TEST MUTE
/mute @TestUser 5m Test mute 5 minuti
# Verifica: ruolo Muted applicato, DM inviato
# Attendi 5 minuti → auto-unmute

# 7. TEST RATE LIMITING
# Esegui 6 comandi rapidi
/warn @User1
/warn @User2
/warn @User3
/warn @User4
/warn @User5
/warn @User6  # ← Dovrebbe fallire con rate limit

# 8. TEST PERMESSI
# Con utente non-staff:
/warn @TestUser  # ← Dovrebbe fallire

# 9. TEST GERARCHIA RUOLI
# Staff prova a bannare Admin:
/ban @AdminUser  # ← Dovrebbe fallire

#10. TEST RESTART PERSISTENZA
# Crea mute 10m
/mute @TestUser 10m
# Riavvia bot
# Verifica: mute ancora attivo, task ripristinato
```

### Test Database

```python
# Verifica integrità database
import sqlite3
conn = sqlite3.connect('data/moderation.db')
cursor = conn.cursor()

# Test query
cursor.execute("SELECT COUNT(*) FROM warns")
print(f"Totale warn: {cursor.fetchone()[0]}")

cursor.execute("SELECT COUNT(*) FROM bans WHERE active = 1")
print(f"Ban attivi: {cursor.fetchone()[0]}")

conn.close()
```

---

## 🚀 Estensioni Future {#estensioni}

### 1. Dashboard Web  
Visualizza statistiche moderazione con grafici

```python
# Possibili metriche:
# - Warn per giorno/settimana/mese
# - Top moderatori
# - Utenti più moderati
# - Tempo medio risposta staff
```

### 2. Case System 
Numeri caso progressivi per ogni azione

```sql
ALTER TABLE mod_log ADD COLUMN case_number INTEGER;
```

### 3. Appeal System
Utenti possono contestare warn/ban

```python
# Comandi nuovi:
# /appeal <case_number> <motivo>
# /review <case_number>  # Staff only
# /approve <case_number>  # Admin only
```

### 4. Auto-Moderation
Filtri automatici per spam, insulti, link

```python
@bot.event
async def on_message(message):
    # Spam detection
    if len(message.content) > 1000:
        await auto_warn(message.author, "Spam")
    
    # Bad words filter
    if contains_profanity(message.content):
        await message.delete()
        await auto_warn(message.author, "Linguaggio inappropriato")
```

### 5. Reports
Sistema report utenti

```python
/report @Utente Motivo
# Crea ticket report per staff
```

### 6. Temporary Roles
Assegna ruoli temporanei

```python
/temprole @Utente @Role 7d
# Auto-rimuove dopo 7 giorni
```

### 7. Multi-Guild Sync
Condividi ban tra server

```python
# DB globale per ban multi-server
# /globalban @Utente
# Banna da tutti i server del network
```

### 8. Scheduled Actions
Azioni programmate

```python
/schedule ban @Utente 2025-12-25 Natale ban
# Esegue ban automaticamente alla data specificata
```

### 9. Moderation Notes
Note private su utenti

```python
/note @Utente Sospettato multi-account
# Solo staff può vedere
```

### 10. Warnings Decay
Warn che scadono dopo tempo

```python
# Config:
"warn_expiry_days": 90

# Auto-rimuovi warn > 90 giorni
```

---

## 📊 Statistiche e Metriche

### Query Utili

```sql
-- Top 10 utenti più warnati
SELECT user_id, COUNT(*) as warn_count 
FROM warns 
WHERE guild_id = ?
GROUP BY user_id 
ORDER BY warn_count DESC 
LIMIT 10;

-- Moderatore più attivo
SELECT moderator_id, COUNT(*) as action_count
FROM mod_log
WHERE guild_id = ?
GROUP BY moderator_id
ORDER BY action_count DESC;

-- Azioni per tipo (ultimi 30 giorni)
SELECT action_type, COUNT(*) as count
FROM mod_log
WHERE guild_id = ? AND timestamp >= datetime('now', '-30 days')
GROUP BY action_type;
```

---

## ⚠️ Troubleshooting

### Problema: Plugin non carica
**Soluzione:** Verifica `config/plugins.json` abbia `"moderation": true`

### Problema: Comandi non sincronizzati
**Soluzione:** In `bot.py`, `on_ready`, decomenta:
```python
await self.loader.sync_commands(guild_id=YOUR_GUILD_ID)
```

### Problema: Mute non funziona
**Soluzione:** 
1. Verifica permessi bot (Man age Roles)
2. Verifica gerarchia ruoli (ruolo bot > ruolo Muted)

### Problema: Rate limiting troppo aggressivo
**Soluzione:** Modifica `config/moderation.json`:
```json
"rate_limit": {
  "enabled": false  // Disabilita completamente
  // oppure
  "max_commands": 10,  // Aumenta limite
  "per_seconds": 30    // Riduci finestra temporale
}
```

### Problema: Auto-actions non funzionano
**Soluzione:** Verifica config:
```json
"auto_actions": {
  "enabled": true  // ← Deve essere true
}
```

---

## 📜 Licenza & Crediti

Plugin creato per Discord Bot con sistema modulare.
Libero uso e modifica. Contributi benvenuti!

---

**🎉 Happy Moderating!** 🎉
