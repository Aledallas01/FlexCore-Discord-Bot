# Discord Bot con Sistema Plugin

Bot Discord modulare in Python con sistema di caricamento dinamico dei plugin e supporto dual-command (text + slash).

## 🚀 Caratteristiche

- **Sistema Plugin Modulare**: Architettura separata con `bot.py` (core) e `loader.py` (gestione plugin)
- **Auto-Discovery**: Scansione automatica della cartella `plugins/` e registrazione in `plugins.json`
- **Dual Commands**: Supporto sia per comandi text (`!comando`) che slash (`/comando`)
- **Configurazione Dinamica**: Nuovi plugin aggiunti automaticamente con `true` di default
- **Configurazione Semplice**: File JSON per gestire token e abilitazione plugin
- **Plugin Inclusi**:
  - 🎫 **Tickets**: Sistema di supporto con ticket
  - 🛡️ **Moderation**: Comandi di moderazione (kick, ban, timeout, clear)
  - 🎮 **Funny**: Comandi divertenti e giochi

## 📁 Struttura del Progetto

```
DiscordBot/
├── bot.py                 # Core del bot (inizializzazione, eventi)
├── loader.py              # Sistema auto-discovery e caricamento plugin
├── config/                # Configurazioni
│   ├── config.json       # Configurazione bot
│   └── plugins.json      # Abilitazione plugin (auto-generato)
├── plugins/              # Plugin
│   ├── __init__.py
│   ├── tickets.py        # Plugin ticket
│   ├── moderation.py     # Plugin moderazione
│   └── funny.py          # Plugin divertenti
├── requirements.txt      # Dipendenze
└── README.md            # Questo file
```

## 🔧 Installazione

1. **Clona o scarica il repository**

2. **Installa le dipendenze**:
```bash
pip install -r requirements.txt
```

3. **Configura il bot**:
   - Apri `config/config.json`
   - Inserisci il tuo token Discord
   - (Opzionale) Modifica il prefix e altri parametri

4. **Configura i plugin**:
   - Apri `config/plugins.json`
   - Imposta `true` per i plugin da caricare, `false` per quelli da disabilitare

## ▶️ Avvio

```bash
python bot.py
```

## 🎮 Comandi

> **Nota**: Tutti i comandi sono disponibili sia come comandi text (con prefix `!`) che come slash commands (con `/`)

### Plugin Tickets (🎫)
| Text Command | Slash Command | Descrizione | Permessi |
|--------------|---------------|-------------|----------|
| `!ticket` | `/ticket` | Crea un nuovo ticket di supporto | Tutti |
| `!closeticket` | `/closeticket` | Chiude il ticket corrente | Manage Channels |
| `!ticketstats` | `/ticketstats` | Mostra statistiche sui ticket | Manage Guild |

### Plugin Moderation (🛡️)
> **Nota**: Il plugin moderation è **disabilitato di default**. Abilitalo in `config/plugins.json`

- `!kick @utente [motivo]` - Espelle un membro
- `!ban @utente [motivo]` - Banna un membro
- `!unban <user_id>` - Sbanna un utente
- `!clear <numero>` - Elimina messaggi (max 100)
- `!timeout @utente <minuti> [motivo]` - Mette in timeout un membro
- `!untimeout @utente` - Rimuove il timeout

### Plugin Funny (🎮)
| Text Command | Slash Command | Descrizione |
|--------------|---------------|-------------|
| `!8ball <domanda>` | `/8ball <domanda>` | Chiedi alla palla magica |
| `!dado [facce]` | `/dado [facce]` | Lancia un dado |
| `!moneta` | `/moneta` | Lancia una moneta |
| `!complimento [@utente]` | `/complimento [membro]` | Fa un complimento |
| `!choose opz1, opz2, opz3` | - | Sceglie casualmente |
| `!meme` | - | Invia un meme casuale |
| `!indovina` | - | Gioca a indovina il numero |

## 🔌 Auto-Discovery dei Plugin

Il bot scansiona automaticamente la cartella `plugins/` all'avvio:
- **Nuovi plugin** vengono aggiunti automaticamente a `plugins.json` con valore `true`
- **Plugin rimossi** vengono eliminati da `plugins.json`
- **Plugin esistenti** mantengono il loro stato (enabled/disabled)

**Esempio**: Aggiungi `plugins/welcome.py` → Riavvia il bot → Il plugin viene auto-registrato e caricato!

## 🔌 Creare un Nuovo Plugin

1. Crea un nuovo file in `plugins/nome_plugin.py`
2. Crea una classe che eredita da `commands.Cog`:

```python
import discord
from discord.ext import commands
from discord import app_commands

class NomePluginCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
    
    # Text Command
    @commands.command(name='comando')
    async def mio_comando(self, ctx, argomento: str = None):
        await ctx.send(f"Text: Ciao {argomento}!")
    
    # Slash Command
    @app_commands.command(name="comando", description="Descrizione del comando")
    @app_commands.describe(argomento="Descrizione dell'argomento")
    async def comando_slash(self, interaction: discord.Interaction, argomento: str = None):
        await interaction.response.send_message(f"Slash: Ciao {argomento}!")

async def setup(bot):
    await bot.add_cog(NomePluginCog(bot))
```

3. **Non serve modificare `plugins.json`!** Il loader lo farà automaticamente all'avvio
4. Riavvia il bot e il plugin verrà caricato automaticamente

## ⚙️ Sincronizzazione Slash Commands

Gli slash commands devono essere sincronizzati con Discord:

### Opzione 1: Sincronizzazione per Server (Rapida)
Modifica `bot.py` dopo `await self.loader.load_plugins()`:
```python
# Sincronizza per un server specifico (immediato)
await self.loader.sync_commands(guild_id=YOUR_GUILD_ID)
```

### Opzione 2: Sincronizzazione Globale (Lenta)
```python
# Sincronizza globalmente (può richiedere fino a 1 ora)
await self.loader.sync_commands()
```

> **Consiglio**: Usa sincronizzazione per server durante lo sviluppo, poi passa a globale per produzione

## 📝 Configurazione

### config/config.json
```json
{
  "token": "YOUR_BOT_TOKEN_HERE",
  "prefix": "!",
  "owner_id": "YOUR_DISCORD_USER_ID"
}
```

### config/plugins.json
```json
{
  "tickets": true,
  "moderation": false,
  "funny": true
}
```

## 🔑 Ottenere un Token Discord

1. Vai su [Discord Developer Portal](https://discord.com/developers/applications)
2. Crea una nuova applicazione
3. Vai su "Bot" e clicca "Add Bot"
4. Copia il token e inseriscilo in `config/config.json`
5. Abilita "Message Content Intent" in Bot → Privileged Gateway Intents
6. Invita il bot al tuo server usando OAuth2 URL Generator

## ⚠️ Note Importanti

- **Non condividere mai il tuo token!**
- Aggiungi `config/config.json` al `.gitignore` se usi Git
- Il bot necessita dei permessi appropriati nel server Discord
- Per la moderazione, il bot deve avere ruoli superiori agli utenti da moderare

## 📦 Dipendenze

- `discord.py` >= 2.3.0
- `python-dotenv` >= 1.0.0

## 🐛 Troubleshooting

**Il bot non si avvia**: Verifica che il token sia corretto in `config/config.json`

**Plugin non caricato**: Controlla che il nome in `plugins.json` corrisponda al nome del file

**Comandi non funzionano**: Verifica che il bot abbia i permessi necessari

**Errori di permessi**: Assicurati che il bot abbia i ruoli appropriati nel server

## 📄 Licenza

Progetto libero e open source. Usalo e modificalo come preferisci!
