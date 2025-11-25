# FlexCore Plugin Development Guide

Complete guide to creating plugins for FlexCore Discord Bot.

---

## 📋 Plugin Structure

Each plugin is a `.py` file in the `plugins/` folder and must follow this basic structure:

```python
import discord
from discord.ext import commands
from discord import app_commands

class PluginNameCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        # Initialize here
    
async def setup(bot):
    await bot.add_cog(PluginNameCog(bot))
```

### Naming Convention
- **File**: `plugin_name.py` (snake_case)
- **Class**: `PluginNameCog` (PascalCase + "Cog" suffix)
- Example: `example.py` → `ExampleCog`

---

## ⚙️ Configuration System (Auto-Create & Validate)

### Recommended Structure

```python
import json
import os

class MyPluginCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.config_path = os.path.join("config", "my_plugin.json")
        
        # Default configuration
        self.default_config = {
            "enabled": True,
            "admin_role_id": 0,
            "message": "Hello World"
        }
        
        # Load and validate
        self.config = self._load_and_validate_config()
    
    def _load_and_validate_config(self):
        """Auto-create, load and repair configuration"""
        
        # 1. Auto-Create
        if not os.path.exists(self.config_path):
            print(f"⚙️ [MyPlugin] Creating config at {self.config_path}")
            os.makedirs(os.path.dirname(self.config_path), exist_ok=True)
            self._save_config(self.default_config)
            return self.default_config
        
        # 2. Load
        try:
            with open(self.config_path, 'r') as f:
                config = json.load(f)
        except Exception as e:
            print(f"❌ [MyPlugin] Error loading config: {e}")
            return self.default_config
        
        # 3. Validate & Repair
        valid = True
        
        # Check missing keys
        for key, default_val in self.default_config.items():
            if key not in config:
                print(f"⚠️ [MyPlugin] Missing key '{key}', added.")
                config[key] = default_val
                valid = False
        
        # Check types
        if not isinstance(config.get("enabled"), bool):
            config["enabled"] = True
            valid = False
        
        # Save if modified
        if not valid:
            print(f"🔧 [MyPlugin] Config repaired.")
            self._save_config(config)
        else:
            print(f"✅ [MyPlugin] Config loaded.")
        
        return config
    
    def _save_config(self, config):
        """Save configuration"""
        with open(self.config_path, 'w') as f:
            json.dump(config, f, indent=4)
```

---

## 📝 Text Commands (Prefix Commands)

Text commands use the bot's prefix (e.g., `!command`).

### Basic Command

```python
@commands.command(name="ping")
async def ping_command(self, ctx):
    """Responds with Pong!"""
    await ctx.send("🏓 Pong!")
```

### With Arguments

```python
@commands.command(name="say")
async def say_command(self, ctx, *, message: str):
    """Repeats a message
    
    Args:
        ctx: Command context
        message: The message to repeat
    """
    await ctx.send(message)
```

### With Permissions

```python
@commands.command(name="kick")
@commands.has_permissions(kick_members=True)
async def kick_command(self, ctx, member: discord.Member, *, reason: str = None):
    """Kicks a member (requires permissions)"""
    await member.kick(reason=reason)
    await ctx.send(f"✅ {member.mention} has been kicked!")
```

### Error Handling for Text Commands

```python
@kick_command.error
async def kick_error(self, ctx, error):
    if isinstance(error, commands.MissingPermissions):
        await ctx.send("❌ You don't have the necessary permissions!")
    elif isinstance(error, commands.MemberNotFound):
        await ctx.send("❌ Member not found!")
```

---

## ⚡ Slash Commands (Application Commands)

Slash commands are Discord's modern commands (`/command`).

### Basic Command

```python
@app_commands.command(name="hello", description="Greets the user")
async def hello_slash(self, interaction: discord.Interaction):
    """Basic slash command"""
    await interaction.response.send_message(f"👋 Hello {interaction.user.mention}!")
```

### With Parameters

```python
@app_commands.command(name="userinfo", description="Show user information")
@app_commands.describe(user="The user to get info about")
async def userinfo_slash(self, interaction: discord.Interaction, user: discord.Member):
    """Slash command with parameter"""
    embed = discord.Embed(title=f"Info about {user.name}", color=discord.Color.blue())
    embed.add_field(name="ID", value=user.id)
    embed.add_field(name="Created on", value=user.created_at.strftime("%m/%d/%Y"))
    await interaction.response.send_message(embed=embed)
```

### With Choices (Dropdown)

```python
@app_commands.command(name="color", description="Choose a color")
@app_commands.describe(color="Your favorite color")
@app_commands.choices(color=[
    app_commands.Choice(name="Red", value="red"),
    app_commands.Choice(name="Green", value="green"),
    app_commands.Choice(name="Blue", value="blue")
])
async def color_slash(self, interaction: discord.Interaction, color: app_commands.Choice[str]):
    """Slash command with choices"""
    await interaction.response.send_message(f"You chose: {color.name} ({color.value})")
```

### With Permissions

```python
@app_commands.command(name="ban", description="Ban a user")
@app_commands.default_permissions(ban_members=True)
@app_commands.describe(user="User to ban", reason="Ban reason")
async def ban_slash(self, interaction: discord.Interaction, user: discord.Member, reason: str = None):
    """Slash command with permissions"""
    await user.ban(reason=reason)
    await interaction.response.send_message(f"🔨 {user.mention} has been banned!")
```

### Ephemeral Responses (Only Visible to User)

```python
@app_commands.command(name="secret", description="Secret message")
async def secret_slash(self, interaction: discord.Interaction):
    """Response visible only to user"""
    await interaction.response.send_message("🤫 This message is only for you!", ephemeral=True)
```

---

## 🎯 Event Listeners

Events allow plugins to react to Discord events.

### Event: Member Join

```python
@commands.Cog.listener()
async def on_member_join(self, member: discord.Member):
    """Triggered when a member joins the server"""
    channel = member.guild.system_channel
    if channel:
        await channel.send(f"👋 Welcome {member.mention}!")
```

### Event: Message Sent

```python
@commands.Cog.listener()
async def on_message(self, message: discord.Message):
    """Triggered for every message"""
    # Ignore bots
    if message.author.bot:
        return
    
    # Example: responds to "hello"
    if "hello" in message.content.lower():
        await message.channel.send(f"Hello {message.author.mention}!")
```

### Event: Reaction Added

```python
@commands.Cog.listener()
async def on_reaction_add(self, reaction: discord.Reaction, user: discord.User):
    """Triggered when a reaction is added"""
    if user.bot:
        return
    
    if str(reaction.emoji) == "👍":
        await reaction.message.channel.send(f"{user.mention} liked this!")
```

---

## 🗄️ Database Integration (Optional)

### SQLite Example

```python
import sqlite3

class DatabasePluginCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.db_path = "data/my_plugin.db"
        self._init_database()
    
    def _init_database(self):
        """Initialize database"""
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
        """Add points to a user"""
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

### 1. Error Handling
Always handle exceptions to avoid crashes:

```python
@commands.command()
async def risky_command(self, ctx):
    try:
        # Risky operation
        result = await some_api_call()
        await ctx.send(f"Result: {result}")
    except Exception as e:
        print(f"Error: {e}")
        await ctx.send("❌ An error occurred!")
```

### 2. Logging
Use print or logging for debugging:

```python
print(f"[MyPlugin] Command executed by {ctx.author}")
```

### 3. Modular Configuration
Separate settings from code logic using JSON config files.

### 4. Documentation
Document commands with docstrings:

```python
@commands.command()
async def help_me(self, ctx):
    """Shows plugin help
    
    This command provides useful information
    on how to use the plugin.
    """
    await ctx.send("📖 Here's the help...")
```

### 5. Permissions
Always check permissions before sensitive actions:

```python
if not ctx.author.guild_permissions.administrator:
    await ctx.send("❌ Only admins can use this command!")
    return
```

---

## 📦 Complete Example

See `plugins/example.py` for a working example that includes:
- ✅ Auto-create/validate configuration system
- ✅ Text commands
- ✅ Slash commands
- ✅ Event listeners
- ✅ Error handling
- ✅ Complete documentation

---

## 🚀 Testing the Plugin

1. Save the file in `plugins/`
2. Restart the bot or use reload command (if implemented)
3. Check that the plugin is loaded in the log
4. Test commands in Discord server

---

## 🔧 Troubleshooting

### Plugin won't load
- Check that class name ends with "Cog"
- Verify that `async def setup(bot)` is present
- Check for syntax errors in the log

### Slash commands don't appear
- Slash commands must be synced: `/sync` (if you have the command)
- May take a few minutes to appear

### Config won't create
- Verify that `config/` folder exists
- Check file system write permissions

---

**Happy Coding! 🎉**
