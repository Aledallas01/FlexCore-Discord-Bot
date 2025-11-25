# 🔄 Auto-Update System

The bot includes an intelligent auto-update system that automatically synchronizes with the GitHub repository.

## How to Enable

Add to your `config/config.json`:

```json
{
  "token": "YOUR_BOT_TOKEN",
  "prefix": "!",
  "owner_id": "YOUR_DISCORD_ID",
  "startscreen_type": "TEXT or UI",
  "auto_update": true
}
```

## Behavior

### When It Updates
- **On bot startup**: If `auto_update: true`, checks for updates before initialization

### What Gets Updated

#### ✅ Automatically Updated Files
- **`.py` files** (Python): Completely overwritten with GitHub version
- **`.json` files NOT protected**: Smart merge (new fields added, existing values kept)
- **New files**: Downloaded if not present

#### 🛡️ Files **NEVER** Touched (Protected)
- `config/config.json` - Your personal configuration
- `data/` - Database and user data
- `logs/` - Log files
- `.env` - Environment variables
- `.venv/` - Virtual environment
- `.git/` - Local git repository

### Smart JSON Merge

For files like `config/moderation.json`:
- **New fields** from repository → Added automatically
- **Existing local fields** → Kept with your values
- **Fields removed** from repository → Kept locally (not deleted)

**Example:**
```json
// GitHub adds new field "backup_enabled"
// YOUR LOCAL FILE:
{
  "staff_roles": ["123456"],
  "log_channel_id": "789012"
}

// AFTER UPDATE:
{
  "staff_roles": ["123456"],      // ✅ Kept
  "log_channel_id": "789012",     // ✅ Kept
  "backup_enabled": true           // ✅ Added automatically
}
```

## Security

- Repository hardcoded: `Aledallas01/FlexCore-Discord-Bot`
- Branch hardcoded: `main`
- **NOT modifiable** by user for security

## Backup

Before each update, modified files are backed up in `.update_backups/`

## Disable

Set `"auto_update": false` in `config.json`

## Issues

If auto-update fails:
- Bot continues normally
- Error message displayed in console
- Check internet connection
- Verify file permissions

## Tracking File

- `.last_update_check` - Saves last GitHub commit for comparison
