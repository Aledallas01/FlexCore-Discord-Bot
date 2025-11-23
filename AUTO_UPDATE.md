# 🔄 Sistema Auto-Update

Il bot include un sistema di auto-aggiornamento intelligente che sincronizza automaticamente con la repository GitHub.

## Come Abilitarlo

Aggiungi al tuo `config/config.json`:

```json
{
  "token": "YOUR_BOT_TOKEN",
  "prefix": "!",
  "owner_id": "YOUR_DISCORD_ID",
  "startscreen_type": "ui",
  "auto_update": true
}
```

## Comportamento

### Quando si Aggiorna
- **All'avvio del bot**: Se `auto_update: true`, controlla aggiornamenti prima di inizializzare

### Cosa Aggiorna

#### ✅ File Aggiornati Automaticamente
- **File `.py`** (Python): Sovrascritti completamente con la versione GitHub
- **File `.json` NON protetti**: Merge intelligente (nuovi campi aggiunti, valori esistenti mantenuti)
- **Nuovi file**: Scaricati se non presenti

#### 🛡️ File **MAI**Toccati (Protetti)
- `config/config.json` - La tua configurazione personale
- `data/` - Database e dati utente
- `logs/` - File di log
- `.env` - Variabili d'ambiente
- `.venv/` - Virtual environment
- `.git/` - Repository git locale

### Smart JSON Merge

Per file come `config/moderation.json`:
- **Nuovi campi** dalla repository → Aggiunti automaticamente
- **Campi esistenti** locali → Mantenuti con i tuoi valori
- **Campi rimossi** dalla repository → Mantenuti localmente (non cancellati)

**Esempio:**
```json
// GitHub aggiunge nuovo campo "backup_enabled"
// TUO FILE LOCALE:
{
  "staff_roles": ["123456"],
  "log_channel_id": "789012"
}

// DOPO L'UPDATE:
{
  "staff_roles": ["123456"],      // ✅ Mantenuto
  "log_channel_id": "789012",     // ✅ Mantenuto
  "backup_enabled": true           // ✅ Aggiunto automaticamente
}
```

## Sicurezza

- Repository hardcoded: `Aledallas01/FlexCore-Discord-Bot`
- Branch hardcoded: `main`
- **NON modificabili** dall'utente per sicurezza

## Backup

Prima di ogni aggiornamento, i file modificati vengono backuppati in `.update_backups/`

## Disabilitare

Rimuovi o imposta `"auto_update": false` in `config.json`

## Problemi

Se l'auto-update fallisce:
- Il bot continua normalmente
- Messaggio di errore visualizzato in console
- Controlla connessione internet
- Verifica permessi file

## File Tracciamento

- `.last_update_check` - Salva ultimo commit GitHub per confronto
