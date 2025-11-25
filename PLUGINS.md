# FlexCore Plugin Development Guide

Guida completa alla creazione di plugin per FlexCore Discord Bot.

---

## 📋 Struttura di un Plugin

Ogni plugin è un file `.py` nella cartella `plugins/` e deve seguire questa struttura base:

```python
import discord
from discord.ext import commands
from discord import app_commands

class NomePluginCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        # Inizializzazione qui
    
async def setup(bot):
    await bot.add_cog(NomePluginCog(bot))
```

### Convenzione dei Nomi
- **File**: `nome_plugin.py` (snake_case)
- **Classe**: `NomePluginCog` (PascalCase + suffisso "Cog")
- Esempio: `example.py` → `ExampleCog`

---

## ⚙️ Sistema di Configurazione (Auto-Create & Validate)

### Struttura Raccomandata

```python
import json
import os

class MioPluginCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.config_path = os.path.join("config", "mio_plugin.json")
        
        # Configurazione di default
        self.default_config = {
            "enabled": True,
            "admin_role_id": 0,
            "message": "Hello World"
        }
        
        # Carica e valida
        self.config = self._load_and_validate_config()
    
    def _load_and_validate_config(self):
        """Auto-crea, carica e ripara la configurazione"""
        
        # 1. Auto-Create
        if not os.path.exists(self.config_path):
            print(f"⚙️ [MioPlugin] Creazione config in {self.config_path}")
            os.makedirs(os.path.dirname(self.config_path), exist_ok=True)
            self._save_config(self.default_config)
            return self.default_config
        
        # 2. Load
        try:
            with open(self.config_path, 'r') as f:
                config = json.load(f)
        except Exception as e:
            print(f"❌ [MioPlugin] Errore caricamento config: {e}")
            return self.default_config
        
        # 3. Validate & Repair
        valid = True
        
        # Check chiavi mancanti
        for key, default_val in self.default_config.items():
            if key not in config:
                print(f"⚠️ [MioPlugin] Chiave '{key}' mancante, aggiunta.")
                config[key] = default_val
                valid = False
        
        # Check types
        if not isinstance(config.get("enabled"), bool):
            config["enabled"] = True
            valid = False
        
        # Salva se modificato
        if not valid:
            print(f"🔧 [MioPlugin] Config riparata.")
            self._save_config(config)
        else:
            print(f"✅ [MioPlugin] Config caricata.")
        
        return config
    
    def _save_config(self, config):
        """Salva la configurazione"""
        with open(self.config_path, 'w') as f:
            json.dump(config, f, indent=4)
```

---

## 📝 Text Commands (Prefix Commands)

I text commands usano il prefix del bot (es. `!comando`).

### Comando Base

```python
@commands.command(name="ping")
async def ping_command(self, ctx):
    """Risponde con Pong!"""
    await ctx.send("🏓 Pong!")
```

### Con Argomenti

```python
@commands.command(name="say")
async def say_command(self, ctx, *, message: str):
    """Ripete un messaggio
    
    Args:
        ctx: Contesto del comando
        message: Il messaggio da ripetere
    """
    await ctx.send(message)
```

### Con Permessi

```python
@commands.command(name="kick")
@commands.has_permissions(kick_members=True)
async def kick_command(self, ctx, member: discord.Member, *, reason: str = None):
    """Espelle un membro (richiede permessi)"""
    await member.kick(reason=reason)
    await ctx.send(f"✅ {member.mention} è stato espulso!")
```

### Error Handling per Text Commands

```python
@kick_command.error
async def kick_error(self, ctx, error):
    if isinstance(error, commands.MissingPermissions):
        await ctx.send("❌ Non hai i permessi necessari!")
    elif isinstance(error, commands.MemberNotFound):
        await ctx.send("❌ Membro non trovato!")
```

---

## ⚡ Slash Commands (Application Commands)

Gli slash commands sono i moderni comandi di Discord (`/comando`).

### Comando Base

```python
@app_commands.command(name="hello", description="Saluta l'utente")
async def hello_slash(self, interaction: discord.Interaction):
    """Comando slash base"""
    await interaction.response.send_message(f"👋 Ciao {interaction.user.mention}!")
```

### Con Parametri

```python
@app_commands.command(name="userinfo", description="Mostra info su un utente")
@app_commands.describe(user="L'utente di cui vedere le info")
async def userinfo_slash(self, interaction: discord.Interaction, user: discord.Member):
    """Slash command con parametro"""
    embed = discord.Embed(title=f"Info su {user.name}", color=discord.Color.blue())
    embed.add_field(name="ID", value=user.id)
    embed.add_field(name="Creato il", value=user.created_at.strftime("%d/%m/%Y"))
    await interaction.response.send_message(embed=embed)
```

### Con Choices (Dropdown)

```python
@app_commands.command(name="color", description="Scegli un colore")
@app_commands.describe(color="Il colore preferito")
@app_commands.choices(color=[
    app_commands.Choice(name="Rosso", value="red"),
    app_commands.Choice(name="Verde", value="green"),
    app_commands.Choice(name="Blu", value="blue")
])
async def color_slash(self, interaction: discord.Interaction, color: app_commands.Choice[str]):
    """Slash command con choices"""
    await interaction.response.send_message(f"Hai scelto: {color.name} ({color.value})")
```

### Con Permessi

```python
@app_commands.command(name="ban", description="Banna un utente")
@app_commands.default_permissions(ban_members=True)
@app_commands.describe(user="Utente da bannare", reason="Motivo del ban")
async def ban_slash(self, interaction: discord.Interaction, user: discord.Member, reason: str = None):
    """Slash command con permessi"""
    await user.ban(reason=reason)
    await interaction.response.send_message(f"🔨 {user.mention} è stato bannato!")
```

### Risposte Ephemeral (Solo Visibili all'Utente)

```python
@app_commands.command(name="secret", description="Messaggio segreto")
async def secret_slash(self, interaction: discord.Interaction):
    """Risposta visibile solo all'utente"""
    await interaction.response.send_message("🤫 Questo messaggio è solo per te!", ephemeral=True)
```

---

## 🎯 Event Listeners

Gli eventi permettono al plugin di reagire a eventi Discord.

### Evento: Membro Entra

```python
@commands.Cog.listener()
async def on_member_join(self, member: discord.Member):
    """Si attiva quando un membro entra nel server"""
    channel = member.guild.system_channel
    if channel:
        await channel.send(f"👋 Benvenuto {member.mention}!")
```

### Evento: Messaggio Inviato

```python
@commands.Cog.listener()
async def on_message(self, message: discord.Message):
    """Si attiva per ogni messaggio"""
    # Ignora bot
    if message.author.bot:
        return
    
    # Esempio: risponde a "ciao"
    if "ciao" in message.content.lower():
        await message.channel.send(f"Ciao {message.author.mention}!")
```

### Evento: Reazione Aggiunta

```python
@commands.Cog.listener()
async def on_reaction_add(self, reaction: discord.Reaction, user: discord.User):
    """Si attiva quando viene aggiunta una reazione"""
    if user.bot:
        return
    
    if str(reaction.emoji) == "👍":
        await reaction.message.channel.send(f"{user.mention} ha messo like!")
```

---

## 🗄️ Database Integration (Opzionale)

### Esempio con SQLite

```python
import sqlite3

class DatabasePluginCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.db_path = "data/mio_plugin.db"
        self._init_database()
    
    def _init_database(self):
        """Inizializza il database"""
        os.makedirs(os.path.dirname(self.db_path), exist_ok=True)
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS users (
                user_id INTEGER PRIMARY KEY,
                points INTEGER DEFAULT 0
            )
        """)
        
        conn.commit()
        conn.close()
    
    def add_points(self, user_id: int, points: int):
        """Aggiunge punti a un utente"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute("""
            INSERT INTO users (user_id, points) VALUES (?, ?)
            ON CONFLICT(user_id) DO UPDATE SET points = points + ?
        """, (user_id, points, points))
        
        conn.commit()
        conn.close()
```

---

## ✅ Best Practices

### 1. Gestione Errori
Gestisci sempre le eccezioni per evitare crash:

```python
@commands.command()
async def risky_command(self, ctx):
    try:
        # Operazione rischiosa
        result = await some_api_call()
        await ctx.send(f"Risultato: {result}")
    except Exception as e:
        print(f"Errore: {e}")
        await ctx.send("❌ Si è verificato un errore!")
```

### 2. Logging
Usa print o logging per debug:

```python
print(f"[MioPlugin] Comando eseguito da {ctx.author}")
```

### 3. Configurazione Modulare
Separa le impostazioni dal code logic usando i config file JSON.

### 4. Documentazione
Documenta i comandi con docstring:

```python
@commands.command()
async def help_me(self, ctx):
    """Mostra l'aiuto del plugin
    
    Questo comando fornisce informazioni utili
    su come usare il plugin.
    """
    await ctx.send("📖 Ecco l'aiuto...")
```

### 5. Permessi
Controlla sempre i permessi prima di azioni sensibili:

```python
if not ctx.author.guild_permissions.administrator:
    await ctx.send("❌ Solo gli admin possono usare questo comando!")
    return
```

---

## 📦 Esempio Completo

Vedi `plugins/example.py` per un esempio funzionante che include:
- ✅ Sistema di configurazione auto-create/validate
- ✅ Text commands
- ✅ Slash commands
- ✅ Event listeners
- ✅ Error handling
- ✅ Documentazione completa

---

## 🚀 Testing del Plugin

1. Salva il file in `plugins/`
2. Riavvia il bot o usa il comando reload (se implementato)
3. Verifica che il plugin sia caricato nel log
4. Testa i comandi nel server Discord

---

## 🔧 Troubleshooting

### Plugin non si carica
- Controlla che il nome della classe finisca con "Cog"
- Verifica che `async def setup(bot)` sia presente
- Controlla errori di sintassi nel log

### Slash commands non compaiono
- I slash commands devono essere sincronizzati: `/sync` (se hai il comando)
- Potrebbero volerci alcuni minuti prima che appaiano

### Config non si crea
- Verifica che la cartella `config/` esista
- Controlla i permessi di scrittura del file system

---

**Buon Coding! 🎉**
