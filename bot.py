"""
🤖 DISCORD BOT - Sistema Plugin Modulare Avanzato
Sistema completo con auto-discovery, dual commands, monitoring e statistiche in tempo reale
"""

import discord
from discord.ext import commands, tasks
import json
import os
import sys
import platform
import psutil
import asyncio
from datetime import datetime, timedelta
from typing import Optional, Dict
from collections import defaultdict
from utils.loader import PluginLoader
from utils.config_validator import ConfigValidator
from utils.language_manager import init_language, get_text


class DiscordBot:
    """Bot Discord Super Potente con sistema di plugin modulare e monitoring avanzato"""
    
    def __init__(self):
        # Carica configurazione (prima per ottenere la lingua)
        self.config = self.load_config()
        
        # Inizializza sistema lingue PRIMA della validazione
        lang_code = self.config.get('language', 'ita')
        init_language(lang_code)
        
        # Valida configurazione core (ora con messaggi tradotti)
        if not ConfigValidator.validate_core():
            print(f"❌ {get_text('bot.config.invalid')}")
            sys.exit(1)
        
        # Statistiche bot
        self.stats = {
            "start_time": datetime.now(),
            "commands_executed": 0,
            "messages_seen": 0,
            "errors": 0,
            "guilds_joined": 0,
            "guilds_left": 0
        }
        
        # Performance tracking
        self.command_timings = defaultdict(list)
        
        # Configura intents (TUTTI per massima compatibilità)
        intents = discord.Intents.all()
        
        # Crea il bot con configurazioni avanzate
        self.bot = commands.Bot(
            command_prefix=self._dynamic_prefix,  # Prefix dinamico
            intents=intents,
            help_command=commands.DefaultHelpCommand(),
            case_insensitive=True,  # Comandi case-insensitive
            strip_after_prefix=True,
            owner_id=self._get_owner_id()
        )
        
        # Inizializza il loader
        self.loader = PluginLoader(self.bot)
        
        # Registra eventi
        self.setup_events()
        
        # I task in background verranno avviati in on_ready per evitare errori di loop
    
    def _dynamic_prefix(self, bot, message):
        """Prefix dinamico che supporta menzioni e prefix custom"""
        prefixes = [self.config.get('prefix', '!')]
        
        # Aggiungi menzione come prefix
        return commands.when_mentioned_or(*prefixes)(bot, message)
    
    def _get_owner_id(self) -> Optional[int]:
        """Recupera e converte owner_id in int"""
        oid = self.config.get('owner_id')
        if not oid:
            return None
        try:
            return int(oid)
        except ValueError:
            print(f"⚠️  Warning: owner_id '{oid}' non valido (deve essere numerico).")
            return None

    def load_config(self) -> Dict:
        """Carica il file di configurazione principale"""
        config_path = os.path.join('config', 'config.json')
        try:
            with open(config_path, 'r', encoding='utf-8') as f:
                return json.load(f)
        except FileNotFoundError:
            # NOTE: Hardcoded perché viene chiamato prima di init_language()
            print(f"❌ Error: File {config_path} not found!")
            sys.exit(1)
        except json.JSONDecodeError as e:
            # NOTE: Hardcoded perché viene chiamato prima di init_language()
            print(f"❌ Error parsing {config_path}: {e}")
            sys.exit(1)
    
    def start_background_tasks(self):
        """Avvia task in background per monitoring"""
        self.status_rotation.start()
        self.stats_logger.start()
    
    @tasks.loop(minutes=5)
    async def status_rotation(self):
        """Rotazione automatica dello status del bot"""
        await self.bot.wait_until_ready()
        
        statuses = [
            discord.Game(name=f"{self.config.get('prefix', '!')}help | {len(self.bot.guilds)} servers"),
            discord.Activity(type=discord.ActivityType.watching, name=f"{len(set(self.bot.get_all_members()))} users"),
            discord.Activity(type=discord.ActivityType.listening, name="/help"),
            discord.Game(name=f"Uptime: {self._get_uptime()}")
        ]
        
        # Rotazione status
        import random
        await self.bot.change_presence(activity=random.choice(statuses))
    
    @tasks.loop(hours=1)
    async def stats_logger(self):
        """Log periodico delle statistiche"""
        await self.bot.wait_until_ready()
        
        uptime = self._get_uptime()
        print(f"\n📊 {get_text('stats.title')} ({datetime.now().strftime('%H:%M:%S')})")
        print(f"├─ {get_text('stats.uptime')}: {uptime}")
        print(f"├─ {get_text('stats.servers_count')}: {len(self.bot.guilds)}")
        print(f"├─ {get_text('stats.users_count')}: {len(set(self.bot.get_all_members()))}")
        print(f"├─ {get_text('stats.commands_executed')}: {self.stats['commands_executed']}")
        print(f"├─ {get_text('stats.messages_seen')}: {self.stats['messages_seen']}")
        print(f"├─ {get_text('stats.errors_count')}: {self.stats['errors']}")
        print(f"└─ {get_text('stats.latency')}: {round(self.bot.latency * 1000)}ms\n")
    
    def _get_uptime(self) -> str:
        """Calcola uptime del bot"""
        delta = datetime.now() - self.stats["start_time"]
        hours, remainder = divmod(int(delta.total_seconds()), 3600)
        minutes, seconds = divmod(remainder, 60)
        days, hours = divmod(hours, 24)
        
        if days > 0:
            return f"{days}d {hours}h {minutes}m"
        elif hours > 0:
            return f"{hours}h {minutes}m"
        else:
            return f"{minutes}m {seconds}s"
    
    def _get_system_info(self) -> Dict:
        """Ottieni informazioni di sistema"""
        cpu_percent = psutil.cpu_percent(interval=1)
        memory = psutil.virtual_memory()
        
        return {
            "cpu": f"{cpu_percent}%",
            "ram": f"{memory.percent}%",
            "ram_used": f"{memory.used / (1024**3):.1f}GB",
            "ram_total": f"{memory.total / (1024**3):.1f}GB"
        }
    
    def setup_events(self):
        """Configura tutti gli eventi del bot"""
        
        @self.bot.event
        async def on_ready():
            # Avvia task background (se non già avviati)
            if not self.status_rotation.is_running():
                self.start_background_tasks()

            # ANSI Colors
            RESET = "\033[0m"
            BOLD = "\033[1m"
            GREEN = "\033[92m"
            CYAN = "\033[96m"
            YELLOW = "\033[93m"
            MAGENTA = "\033[95m"
            BLUE = "\033[94m"
            
            print()
            print(f"{MAGENTA}{BOLD}{'═' * 88}{RESET}")
            print(f"{GREEN}{BOLD}{get_text('bot.startup.connected')}{RESET}".center(88 + len(RESET) + len(GREEN) + len(BOLD)))
            print(f"{MAGENTA}{BOLD}{'═' * 88}{RESET}\n")
            
            # Bot Info
            print(f"{CYAN}{BOLD}{get_text('system.bot_info.title')}{RESET}")
            print(f"{YELLOW}├─{RESET} {get_text('system.bot_info.username')}: {GREEN}{BOLD}{self.bot.user.name}#{self.bot.user.discriminator}{RESET}")
            print(f"{YELLOW}├─{RESET} {get_text('system.bot_info.id')}: {GREEN}{self.bot.user.id}{RESET}")
            print(f"{YELLOW}├─{RESET} {get_text('system.bot_info.servers')}: {GREEN}{BOLD}{len(self.bot.guilds)}{RESET}")
            print(f"{YELLOW}├─{RESET} {get_text('system.bot_info.users')}: {GREEN}{BOLD}{len(set(self.bot.get_all_members()))}{RESET}")
            print(f"{YELLOW}├─{RESET} {get_text('system.bot_info.plugins')}: {GREEN}{BOLD}{len(self.bot.cogs)}{RESET}")
            print(f"{YELLOW}├─{RESET} {get_text('system.bot_info.text_commands')}: {GREEN}{BOLD}{len([c for c in self.bot.commands])}{RESET}")
            print(f"{YELLOW}├─{RESET} {get_text('system.bot_info.slash_commands')}: {GREEN}{BOLD}{len(self.bot.tree.get_commands())}{RESET}")
            print(f"{YELLOW}└─{RESET} {get_text('system.bot_info.latency')}: {GREEN}{BOLD}{round(self.bot.latency * 1000)}ms{RESET}\n")
            
            # System Info
            sys_info = self._get_system_info()
            print(f"{CYAN}{BOLD}{get_text('system.resources.title')}{RESET}")
            print(f"{BLUE}├─{RESET} CPU: {YELLOW}{sys_info['cpu']}{RESET}")
            print(f"{BLUE}├─{RESET} RAM: {YELLOW}{sys_info['ram']}{RESET} ({sys_info['ram_used']}/{sys_info['ram_total']})")
            print(f"{BLUE}└─{RESET} {get_text('system.info.processes')}: {YELLOW}{len(psutil.pids())}{RESET}\n")
            
            # Server List
            if len(self.bot.guilds) > 0:
                print(f"{CYAN}{BOLD}{get_text('servers.title')}{RESET}")
                for i, guild in enumerate(self.bot.guilds[:5], 1):  # Max 5 per evitare spam
                    symbol = "└─" if i == min(5, len(self.bot.guilds)) else "├─"
                    print(f"{YELLOW}{symbol}{RESET} 🏰 {guild.name} ({guild.member_count} {get_text('servers.members')})")
                if len(self.bot.guilds) > 5:
                    print(f"{YELLOW}└─{RESET} {get_text('servers.and_more', count=len(self.bot.guilds) - 5)}")
                print()
            
            # Plugin List
            if len(self.bot.cogs) > 0:
                print(f"{CYAN}{BOLD}{get_text('plugins.list.title')}{RESET}")
                for i, (name, cog) in enumerate(self.bot.cogs.items(), 1):
                    symbol = "└─" if i == len(self.bot.cogs) else "├─"
                    # Conta comandi text
                    text_commands = [c for c in self.bot.commands if c.cog_name == name]
                    # Conta slash commands
                    slash_commands = cog.get_app_commands() if hasattr(cog, 'get_app_commands') else []
                    
                    cmd_info = []
                    if len(text_commands) > 0:
                        cmd_info.append(f"{len(text_commands)} text")
                    if len(slash_commands) > 0:
                        cmd_info.append(f"{len(slash_commands)} slash")
                    
                    info_str = ", ".join(cmd_info) if cmd_info else "0 comandi"
                    print(f"{YELLOW}{symbol}{RESET} 📦 {name} ({info_str})")
                print()
            
            # Imposta status iniziale
            await self.bot.change_presence(
                activity=discord.Game(name=f"{self.config.get('prefix', '!')}help | /help"),
                status=discord.Status.online
            )
            
            # 🔥 SINCRONIZZAZIONE SLASH COMMANDS (Fix Duplicati) 🔥
            print(f"{YELLOW}⚙️  {get_text('commands.sync.syncing')}{RESET}")
            
            try:
                # 1. Pulisci comandi locali dei server (rimuove i duplicati)
                print(f"{YELLOW}   {get_text('commands.sync.cleaning')}{RESET}")
                for guild in self.bot.guilds:
                    self.bot.tree.clear_commands(guild=guild)
                    await self.bot.tree.sync(guild=guild)
                
                # 2. Sync Globale (Unica fonte di verità)
                synced = await self.bot.tree.sync()
                print(f"{GREEN}✅ {get_text('commands.sync.synced_global', count=len(synced))}{RESET}")
                print(f"{GREEN}   {get_text('commands.sync.unique_available')}{RESET}\n")
                    
            except Exception as e:
                RED = "\033[91m"
                print(f"{RED}❌ {get_text('commands.sync.error', error=e)}{RESET}")
            
            print(f"{GREEN}{BOLD}{'─' * 88}{RESET}")
            print(f"{GREEN}{BOLD}{get_text('bot.startup.ready')}{RESET}".center(88 + len(RESET) + len(GREEN) + len(BOLD)))
            print(f"{GREEN}{BOLD}{'─' * 88}{RESET}\n")
        
        @self.bot.event
        async def on_message(message):
            """Evento per ogni messaggio (tracking e processing)"""
            # Ignora messaggi del bot stesso
            if message.author.bot:
                return
            
            # Incrementa counter
            self.stats["messages_seen"] += 1
            
            # Processa comandi
            await self.bot.process_commands(message)
        
        @self.bot.event
        async def on_command(ctx):
            """Evento quando un comando viene invocato"""
            self.stats["commands_executed"] += 1
            
            # Log comando
            print(f"💬 {ctx.author} {get_text('commands.executed', command=ctx.command, location=ctx.guild.name if ctx.guild else 'DM')}")
        
        @self.bot.event
        async def on_command_completion(ctx):
            """Evento quando un comando completa con successo"""
            # Tracking performance
            if hasattr(ctx, 'command_start_time'):
                elapsed = (datetime.now() - ctx.command_start_time).total_seconds()
                self.command_timings[ctx.command.name].append(elapsed)
        
        @self.bot.event
        async def on_command_error(ctx, error):
            """Gestione errori globale per comandi text"""
            self.stats["errors"] += 1
            
            if isinstance(error, commands.CommandNotFound):
                return  # Ignora comandi non trovati
            
            elif isinstance(error, commands.MissingPermissions):
                await ctx.send(f"❌ Non hai i permessi necessari: `{', '.join(error.missing_permissions)}`")
            
            elif isinstance(error, commands.MissingRequiredArgument):
                await ctx.send(
                    f"❌ Argomento mancante: `{error.param.name}`\n"
                    f"💡 Usa `{ctx.prefix}help {ctx.command}` per vedere la sintassi corretta"
                )
            
            elif isinstance(error, commands.BadArgument):
                await ctx.send(
                    f"❌ Argomento non valido!\n"
                    f"💡 Usa `{ctx.prefix}help {ctx.command}` per maggiori informazioni"
                )
            
            elif isinstance(error, commands.CommandOnCooldown):
                await ctx.send(f"⏱️ Comando in cooldown! Riprova tra {error.retry_after:.1f} secondi")
            
            elif isinstance(error, commands.BotMissingPermissions):
                await ctx.send(
                    f"❌ Il bot non ha i permessi necessari: `{', '.join(error.missing_permissions)}`"
                )
            
            else:
                print(f"❌ Errore non gestito nel comando '{ctx.command}': {error}")
                await ctx.send(f"❌ Si è verificato un errore imprevisto. L'errore è stato registrato.")
        
        @self.bot.tree.error
        async def on_app_command_error(interaction: discord.Interaction, error: discord.app_commands.AppCommandError):
            """Gestione errori globale per slash commands"""
            self.stats["errors"] += 1
            
            if isinstance(error, discord.app_commands.MissingPermissions):
                await interaction.response.send_message(
                    "❌ Non hai i permessi necessari per usare questo comando!",
                    ephemeral=True
                )
            
            elif isinstance(error, discord.app_commands.CommandOnCooldown):
                await interaction.response.send_message(
                    f"⏱️ Comando in cooldown! Riprova tra {error.retry_after:.1f} secondi",
                    ephemeral=True
                )
            
            elif isinstance(error, discord.app_commands.BotMissingPermissions):
                await interaction.response.send_message(
                    f"❌ Il bot non ha i permessi necessari!",
                    ephemeral=True
                )
            
            else:
                print(f"❌ Errore non gestito nello slash command: {error}")
                if not interaction.response.is_done():
                    await interaction.response.send_message(
                        "❌ Si è verificato un errore! L'errore è stato registrato.",
                        ephemeral=True
                    )
        
        @self.bot.event
        async def on_guild_join(guild):
            """Evento quando il bot entra in un server"""
            self.stats["guilds_joined"] += 1
            print(f"➕ {get_text('servers.joined', name=guild.name, id=guild.id, members=guild.member_count)}")
        
        @self.bot.event
        async def on_guild_remove(guild):
            """Evento quando il bot viene rimosso da un server"""
            self.stats["guilds_left"] += 1
            print(f"➖ {get_text('servers.left', name=guild.name, id=guild.id)}")
        
        @self.bot.event
        async def on_member_join(member):
            """Evento quando un membro si unisce a un server"""
            # Log (può essere esteso con auto-role, welcome messages, etc)
            print(f"👋 {get_text('members.joined', member=member, guild=member.guild.name)}")
        
        @self.bot.event
        async def on_member_remove(member):
            """Evento quando un membro lascia un server"""
            print(f"👋 {get_text('members.left', member=member, guild=member.guild.name)}")
    
    async def start(self):
        """Avvia il bot e carica i plugin"""
        # Carica i plugin prima di avviare il bot
        await self.loader.load_plugins()
        
        # Verifica token
        token = self.config.get('token')
        if not token or token == "YOUR_BOT_TOKEN_HERE":
            print()
            print("❌ Errore: Token non configurato!")
            print("💡 Configura il token in config/config.json")
            print()
            sys.exit(1)
        
        # Avvia il bot
        try:
            await self.bot.start(token)
        except discord.LoginFailure:
            print()
            print("❌ Errore: Token non valido!")
            print()
            sys.exit(1)
        except Exception as e:
            print()
            print(f"❌ Errore durante l'avvio del bot: {e}")
            print()
            sys.exit(1)


    async def ui_updater_task(self, bot_queue):
        """Task per inviare aggiornamenti alla UI"""
        while not self.bot.is_closed():
            try:
                stats = {
                    "ping": round(self.bot.latency * 1000),
                    "uptime": self._get_uptime()
                }
                bot_queue.put(("stats", stats))
                
                # Invia stato plugin
                if hasattr(self, "plugin_loader"):
                    bot_queue.put(("plugins_status", self.plugin_loader.plugin_status))
                
                # Info statiche (una tantum)
                if not hasattr(self, "_ui_info_sent"):
                    info = {
                        "name": f"{self.bot.user.name}#{self.bot.user.discriminator}",
                        "id": self.bot.user.id,
                        "servers": len(self.bot.guilds)
                    }
                    bot_queue.put(("info", info))
                    # Invia status online quando il bot è pronto
                    bot_queue.put(("status", "online"))
                    self._ui_info_sent = True
                    
            except Exception:
                pass
            await asyncio.sleep(2) # Rallenta leggermente per non spammare la queue

class StreamRedirector:
    """Reindirizza stdout/stderr alla queue della UI"""
    def __init__(self, queue, original_stream):
        self.queue = queue
        self.original_stream = original_stream
        
    def write(self, text):
        self.original_stream.write(text)
        if text.strip():  # Ignora righe vuote
            self.queue.put(("log", text.strip()))
            
    def flush(self):
        self.original_stream.flush()

def run_bot_thread(bot_instance, loop):
    """Esegue il bot in un thread separato"""
    asyncio.set_event_loop(loop)
    loop.run_until_complete(bot_instance.start())

def main():
    """Funzione principale"""
    
    # 🌍 INIT LANGUAGE FIRST 🌍
    # Carica la lingua prima di tutto il resto per avere messaggi tradotti anche nell'updater
    try:
        config_path = os.path.join('config', 'config.json')
        if os.path.exists(config_path):
            with open(config_path, 'r') as f:
                temp_config = json.load(f)
                lang_code = temp_config.get('language', 'ita')
        else:
            lang_code = 'ita'
    except:
        lang_code = 'ita'
        
    init_language(lang_code)
    
    # 🔥 AUTO-UPDATE PRIORITY - PRIMA DI TUTTO 🔥
    # Esegue SEMPRE il check aggiornamenti come prima cosa
    # Se ci sono bug nel codice corrente, vengono risolti prima di causare problemi
    
    # Check per force update mode
    force_update_mode = "-forceupdate" in sys.argv
    
    if force_update_mode:
        print("\n" + "="*70)
        print(f"🔄 {get_text('auto_updater.title')} - FORCE MODE")
        print("="*70)
        print(f"{get_text('auto_updater.force_mode_warning')}\n")
    else:
        print("\n" + "="*70)
        print(f"🔄 {get_text('auto_updater.title')}")
        print("="*70)
    
    try:
        from utils.auto_updater import AutoUpdater
        updater = AutoUpdater()
        update_applied = updater.check_and_apply()
        
        if force_update_mode:
            # Modalità force update: esci sempre dopo il check
            if update_applied:
                print("\n" + "="*70)
                print(f"✅ {get_text('auto_updater.force_success')}")
                print("="*70)
                print(f"\n{get_text('auto_updater.force_restart_hint')}\n")
            else:
                print("\n" + "="*70)
                print(f"ℹ️  {get_text('auto_updater.no_updates_title')}")
                print("="*70)
                print(f"\n{get_text('auto_updater.no_updates_message')}\n")
            sys.exit(0)
        
        if update_applied:
            print("\n" + "="*70)
            print(f"✅ {get_text('auto_updater.restart_required')}")
            print("="*70)
            print(f"\n⚠️  {get_text('auto_updater.restart_warning')}")
            print(f"\n{get_text('auto_updater.restart_countdown')}")
            
            import time
            import subprocess
            time.sleep(3)
            
            # Riavvio automatico
            print(f"🔄 {get_text('auto_updater.auto_restart')}")
            
            # Ottieni path assoluto dello script
            script_path = os.path.abspath(__file__)
            args = [sys.executable, script_path]
            
            # Aggiungi eventuali argomenti passati all'avvio originale
            if len(sys.argv) > 1:
                args.extend(sys.argv[1:])
                
            # Lancia nuovo processo
            if os.name == 'nt':
                subprocess.Popen(args, creationflags=subprocess.CREATE_NEW_CONSOLE)
            else:
                subprocess.Popen(args)
            
            sys.exit(0)
            
    except Exception as e:
        print(f"⚠️  Auto-update non disponibile: {e}")
        if force_update_mode:
            print("\nImpossibile completare l'update. Controlla la connessione o i permessi.\n")
            sys.exit(1)
        print("Continuo con l'avvio normale...\n")
    
    # Carica config per decidere modalità
    try:
        with open(os.path.join('config', 'config.json'), 'r') as f:
            config = json.load(f)
    except:
        config = {}
    
    startscreen_type = config.get("startscreen_type", "prompt")
    
    if startscreen_type == "UI" or startscreen_type == "ui":
        # Modalità UI
        import queue
        import threading
        from ui.startscreen import run_ui
        
        bot_queue = queue.Queue()
        stop_event = threading.Event()
        
        # Reindirizza stdout
        sys.stdout = StreamRedirector(bot_queue, sys.stdout)
        # sys.stderr = StreamRedirector(bot_queue, sys.stderr) # Opzionale
        
        # Inizializza bot
        bot_instance = DiscordBot()
        
        # Crea loop per il thread del bot
        loop = asyncio.new_event_loop()
        
        # Aggiungi task updater
        loop.create_task(bot_instance.ui_updater_task(bot_queue))
        
        # Avvia bot in thread background
        bot_thread = threading.Thread(target=run_bot_thread, args=(bot_instance, loop))
        bot_thread.daemon = True
        bot_thread.start()
        
        # Avvia UI nel main thread (bloccante)
        try:
            run_ui(bot_queue, stop_event)
        except KeyboardInterrupt:
            pass
        finally:
            stop_event.set()
            
    else:
        # Modalità Prompt (Classica)
        # ANSI Color Codes
        RESET = "\033[0m"
        BOLD = "\033[1m"
        CYAN = "\033[96m"
        MAGENTA = "\033[95m"
        YELLOW = "\033[93m"
        GREEN = "\033[92m"
        BLUE = "\033[94m"
        RED = "\033[91m"
        
        # Clear screen
        os.system('cls' if os.name == 'nt' else 'clear')
        
        # ASCII Art Logo EPICO
        logo = f"""
{CYAN}{BOLD}
    ██████╗ ██╗███████╗ ██████╗ ██████╗ ██████╗ ██████╗     ██████╗  ██████╗ ████████╗
    ██╔══██╗██║██╔════╝██╔════╝██╔═══██╗██╔══██╗██╔══██╗    ██╔══██╗██╔═══██╗╚══██╔══╝
    ██║  ██║██║███████╗██║     ██║   ██║██████╔╝██║  ██║    ██████╔╝██║   ██║   ██║   
    ██║  ██║██║╚════██║██║     ██║   ██║██╔══██╗██║  ██║    ██╔══██╗██║   ██║   ██║   
    ██████╔╝██║███████║╚██████╗╚██████╔╝██║  ██║██████╔╝    ██████╔╝╚██████╔╝   ██║   
    ╚═════╝ ╚═╝╚══════╝ ╚═════╝ ╚═════╝ ╚═╝  ╚═╝╚═════╝     ╚═════╝  ╚═════╝    ╚═╝   
{RESET}"""
        
        print(logo)
        print(f"{MAGENTA}{BOLD}{'═' * 88}{RESET}")
        print(f"{YELLOW}{BOLD}                    {get_text('bot.startup.logo_title')}{RESET}")
        print(f"{MAGENTA}{BOLD}{'═' * 88}{RESET}\n")
        
        # System Information
        print(f"{CYAN}{BOLD}{get_text('system.info.title')}{RESET}")
        print(f"{BLUE}├─{RESET} {get_text('system.info.os')}: {YELLOW}{platform.system()} {platform.release()} ({platform.machine()}){RESET}")
        print(f"{BLUE}├─{RESET} {get_text('system.info.python')}: {YELLOW}{platform.python_version()}{RESET}")
        print(f"{BLUE}├─{RESET} {get_text('system.info.discord_py')}: {YELLOW}{discord.__version__}{RESET}")
        
        # System Resources
        cpu_percent = psutil.cpu_percent(interval=0.5)
        memory = psutil.virtual_memory()
        print(f"{BLUE}├─{RESET} {get_text('system.info.cpu')}: {YELLOW}{cpu_percent}%{RESET}")
        print(f"{BLUE}├─{RESET} {get_text('system.info.ram')}: {YELLOW}{memory.percent}% ({memory.used / (1024**3):.1f}GB / {memory.total / (1024**3):.1f}GB){RESET}")
        
        print(f"{BLUE}├─{RESET} {get_text('system.info.date')}: {YELLOW}{datetime.now().strftime('%d/%m/%Y %H:%M:%S')}{RESET}")
        print(f"{BLUE}└─{RESET} {get_text('system.info.directory')}: {YELLOW}{os.getcwd()}{RESET}\n")
        
        # Features SUPER POTENTI
        print(f"{CYAN}{BOLD}✨ CARATTERISTICHE SUPER POTENTI{RESET}")
        print(f"{GREEN}├─{RESET} ✅ Auto-Discovery Plugin con Hot-Reload")
        print(f"{GREEN}├─{RESET} ✅ Dual Commands (Text + Slash) Sincronizzati")
        print(f"{GREEN}├─{RESET} ✅ Monitoring Sistema in Tempo Reale")
        print(f"{GREEN}├─{RESET} ✅ Statistiche & Performance Tracking")
        print(f"{GREEN}├─{RESET} ✅ Error Handling Avanzato Multi-Layer")
        print(f"{GREEN}├─{RESET} ✅ Dynamic Prefix con Menzioni")
        print(f"{GREEN}├─{RESET} ✅ Status Rotation Automatica")
        print(f"{GREEN}├─{RESET} ✅ Event Logging Completo")
        print(f"{GREEN}├─{RESET} ✅ Configurazione Dinamica JSON")
        print(f"{GREEN}└─{RESET} ✅ Background Tasks per Automazione\n")
        
        # Loading message
        print(f"{YELLOW}{BOLD}⚙️  {get_text('bot.startup.initializing')}{RESET}\n")
        print(f"{MAGENTA}{'─' * 88}{RESET}\n")
        
        # Start bot
        bot_instance = DiscordBot()
        asyncio.run(bot_instance.start())

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print(f"\n\n⏹️  {get_text('general.stopped_by_user')}\n")
    except Exception as e:
        print(f"\n\n❌ {get_text('general.critical_error', error=e)}\n")
        sys.exit(1)
