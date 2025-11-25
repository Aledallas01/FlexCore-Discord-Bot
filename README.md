# Discord Bot with Plugin System

Modular Discord bot in Python with dynamic plugin loading system, dual-command support (text + slash) and **Dashboard UI**.

## 🚀 Features

- **Modular Plugin System**: Separated architecture with `bot.py` (core) and `loader.py` (plugin management)
- **Dashboard UI**: Modern graphical interface with real-time statistics (CPU, RAM, Ping) and colored logs
- **Advanced Logging**: File logging (`logs/moderation.log`) and aesthetic embeds with avatar and footer
- **Auto-Discovery**: Automatic scanning of `plugins/` folder and registration in `plugins.json`
- **Dual Commands**: Support for both text commands (`!command`) and slash commands (`/command`)
- **Dynamic Configuration**: New plugins added automatically with `true` by default
- **Simple Configuration**: JSON files to manage token and plugin enabling (numeric values as strings)

## 📁 Project Structure

```
DiscordBot/
├── bot.py                 # Bot core (initialization, events)
├── loader.py              # Auto-discovery and plugin loading system
├── ui/                    # Graphical Interface
│   └── startscreen.py    # Dashboard UI
├── config/                # Configurations
│   ├── config.json       # Bot configuration
│   ├── moderation.json   # Moderation configuration
│   └── plugins.json      # Plugin enabling (auto-generated)
├── plugins/              # Plugins
│   ├── __init__.py
│   └── moderation.py     # Moderation plugin
├── logs/                 # Log files
├── data/                 # SQLite databases
├── requirements.txt      # Dependencies
└── README.md            # This file
```

## 🔧 Installation

1. **Clone or download the repository**

2. **Install dependencies**:
```bash
pip install -r requirements.txt
```

3. **Configure the bot**:
   - Open `config/config.json`
   - Insert your Discord token
   - (Optional) Modify prefix and other parameters

4. **Configure plugins**:
   - Open `config/plugins.json`
   - Set `true` for plugins to load, `false` to disable

## ▶️ Startup

```bash
python bot.py
```
The **Dashboard UI** will automatically open to monitor the bot.

## 🎮 Commands

> **Note**: All commands are available both as text commands (with prefix) and slash commands (with `/`)

### Moderation Plugin (🛡️)
| Text Command | Slash Command | Description | Permissions |
|--------------|---------------|-------------|------------|
| `!kick @user [reason]` | `/kick @user [reason]` | Kick a member | Kick Members |
| `!ban @user [duration] [reason]` | `/ban @user [duration] [reason]` | Ban a member (e.g.: `!ban @User 1h Spam`) | Ban Members |
| `!unban <user_id>` | `/unban <user_id>` | Unban a user | Ban Members |
| `!mute @user [duration] [reason]` | `/mute @user [duration] [reason]` | Mute a user (e.g.: `!mute @User 30m`) | Manage Roles |
| `!unmute @user` | `/unmute @user` | Remove mute | Manage Roles |
| `!warn @user [reason]` | `/warn @user [reason]` | Warn a user | Manage Roles |
| `!unwarn @user [id]` | `/unwarn @user [id]` | Remove a warning | Manage Roles |


## 🔌 Plugin Auto-Discovery

The bot automatically scans the `plugins/` folder at startup:
- **New plugins** are automatically added to `plugins.json` with value `true`
- **Removed plugins** are deleted from `plugins.json`
- **Existing plugins** keep their state (enabled/disabled)

**Example**: Add `plugins/welcome.py` → Restart bot → Plugin is auto-registered and loaded!

## 🔌 Creating a New Plugin

1. Create a new file in `plugins/plugin_name.py`
2. Create a class that inherits from `commands.Cog`:

```python
import discord
from discord.ext import commands
from discord import app_commands

class PluginNameCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
    
    # Text Command
    @commands.command(name='command')
    async def my_command(self, ctx, argument: str = None):
        await ctx.send(f"Text: Hello {argument}!")
    
    # Slash Command
    @app_commands.command(name="command", description="Command description")
    @app_commands.describe(argument="Argument description")
    async def command_slash(self, interaction: discord.Interaction, argument: str = None):
        await interaction.response.send_message(f"Slash: Hello {argument}!")

async def setup(bot):
    await bot.add_cog(PluginNameCog(bot))
```

3. **No need to modify `plugins.json`!** The loader will do it automatically on startup
4. Restart the bot and the plugin will be loaded automatically

## ⚙️ Slash Command Sync

The bot automatically performs a **global sync** on startup.
Slash commands may take up to 1 hour to appear everywhere, but are usually instant if the bot is in few servers.

## 📝 Configuration

### config/config.json
```json
{
  "token": "YOUR_BOT_TOKEN_HERE",
  "prefix": "!",
  "owner_id": "YOUR_DISCORD_USER_ID",
  "startscreen_type": "TEXT or UI",
  "auto_update": true
}
```

### config/plugins.json
```json
{
  "example": false,
  "moderation": true
}
```

## 🔑 Getting a Discord Token

1. Visit [Discord Developer Portal](https://discord.com/developers/applications)
2. Create a new application
3. Go to "Bot" and click "Add Bot"
4. Copy the token and paste it in `config/config.json`
5. Enable "Message Content Intent" in Bot → Privileged Gateway Intents
6. Invite the bot to your server using OAuth2 URL Generator

## ⚠️ Important Notes

- **Never share your token!**
- Bot needs appropriate permissions in Discord server
- For moderation, bot must have roles higher than users to moderate

## 📦 Dependencies

- `discord.py` >= 2.3.0
- `customtkinter` >= 5.2.0 (for UI)
- `Pillow` >= 10.0.0 (for UI images)
- `psutil` (for system statistics)

## 🐛 Troubleshooting

**Bot won't start**: Verify token is correct in `config/config.json`

**Plugin not loaded**: Check that name in `plugins.json` matches file name

**Commands don't work**: Try to restart Discord and Verify bot has necessary permissions

**Permission errors**: Make sure bot has appropriate roles in server

## 📄 License

Free and open source project. Use and modify as you prefer!
