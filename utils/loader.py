import discord
from discord.ext import commands
import json
import os
import importlib
import sys
from pathlib import Path


from utils.config_validator import ConfigValidator
from utils.language_manager import get_text


class PluginLoader:
    """Gestisce il caricamento dinamico dei plugin con auto-discovery"""
    
    def __init__(self, bot: commands.Bot):
        self.bot = bot
        self.plugins_dir = "plugins"
        self.config_path = os.path.join("config", "plugins.json")
        self.plugins_config = {}
        self.plugin_status = {} # Tracks status: "active", "disabled", "error"
    
    def discover_plugins(self):
        """
        Scansiona la cartella plugins/ e trova tutti i file .py
        Ritorna una lista di nomi plugin (senza estensione)
        """
        plugins_path = Path(self.plugins_dir)
        
        if not plugins_path.exists():
            print(f"⚠️  {get_text('general.folder_not_found', folder=self.plugins_dir)}")
            return []
        
        # Trova tutti i file .py eccetto __init__.py
        plugin_files = [
            f.stem for f in plugins_path.glob("*.py") 
            if f.name != "__init__.py"
        ]
        
        return plugin_files
    
    def load_plugins_config(self):
        """Carica la configurazione dei plugin da plugins.json"""
        try:
            with open(self.config_path, 'r', encoding='utf-8') as f:
                self.plugins_config = json.load(f)
        except FileNotFoundError:
            print(f"⚠️  {self.config_path} non trovato, verrà creato")
            self.plugins_config = {}
        except json.JSONDecodeError as e:
            print(f"❌ Errore nel parsing di {self.config_path}: {e}")
            sys.exit(1)
    
    def save_plugins_config(self):
        """Salva la configurazione dei plugin in plugins.json"""
        try:
            # Crea la directory config se non esiste
            os.makedirs(os.path.dirname(self.config_path), exist_ok=True)
            
            with open(self.config_path, 'w', encoding='utf-8') as f:
                json.dump(self.plugins_config, f, indent=2, ensure_ascii=False)
        except Exception as e:
            print(f"❌ Errore nel salvataggio di {self.config_path}: {e}")
    
    def update_plugins_config(self, discovered_plugins):
        """
        Aggiorna plugins.json con i plugin scoperti
        I nuovi plugin vengono aggiunti con valore 'true' di default
        I plugin esistenti mantengono il loro valore
        """
        updated = False
        
        for plugin_name in discovered_plugins:
            if plugin_name not in self.plugins_config:
                self.plugins_config[plugin_name] = True
                print(f"  ➕ {get_text('plugins.loading.new_added', name=plugin_name)}")
                updated = True
        
        # Rimuovi plugin che non esistono più (opzionale)
        plugins_to_remove = [
            name for name in self.plugins_config.keys() 
            if name not in discovered_plugins
        ]
        
        for plugin_name in plugins_to_remove:
            del self.plugins_config[plugin_name]
            print(f"  ➖ {get_text('plugins.loading.removed', name=plugin_name)}")
            updated = True
        
        if updated:
            self.save_plugins_config()
        
        return updated
    
    async def load_plugins(self):
        """
        Carica tutti i plugin abilitati
        Supporta sia comandi text che slash commands
        """
        print(f"🔌 {get_text('plugins.loading.title')}")
        print("━" * 50)
        
        # 1. Carica configurazione esistente
        self.load_plugins_config()
        
        # 2. Scopri plugin nella cartella
        print(f"🔍 {get_text('plugins.loading.scanning')}")
        discovered_plugins = self.discover_plugins()
        print(f"   {get_text('plugins.loading.found', count=len(discovered_plugins), names=', '.join(discovered_plugins))}")
        print()
        
        # 3. Aggiorna configurazione con nuovi plugin
        print(f"📝 {get_text('plugins.loading.updating_config')}")
        self.update_plugins_config(discovered_plugins)
        print()
        
        # 4. Carica i plugin abilitati
        print(f"⚙️  {get_text('plugins.loading.loading_enabled')}")
        print("━" * 50)
        
        loaded_count = 0
        disabled_count = 0
        error_count = 0
        
        # Reset status
        self.plugin_status = {}
        
        for plugin_name, enabled in self.plugins_config.items():
            if enabled:
                # Valida configurazione plugin
                if not ConfigValidator.validate_plugin(plugin_name):
                    print(f"  ❌ {get_text('plugins.loading.error_config', name=plugin_name)}")
                    self.plugin_status[plugin_name] = "error"
                    error_count += 1
                    continue

                try:
                    # Importa dinamicamente il modulo
                    module = importlib.import_module(f'{self.plugins_dir}.{plugin_name}')
                    
                    # Cerca la classe Cog (naming convention: PluginNameCog)
                    class_name = ''.join(word.capitalize() for word in plugin_name.split('_')) + 'Cog'
                    
                    if hasattr(module, class_name):
                        cog_class = getattr(module, class_name)
                        await self.bot.add_cog(cog_class(self.bot))
                        print(f"  ✅ {get_text('plugins.loading.loaded', name=plugin_name)}")
                        self.plugin_status[plugin_name] = "active"
                        loaded_count += 1
                    else:
                        print(f"  ⚠️  {get_text('plugins.loading.error_class', name=plugin_name, class_name=class_name)}")
                        self.plugin_status[plugin_name] = "error"
                        error_count += 1
                        
                except ModuleNotFoundError:
                    print(f"  ❌ {get_text('plugins.loading.error_file', name=plugin_name)}")
                    self.plugin_status[plugin_name] = "error"
                    error_count += 1
                except Exception as e:
                    print(f"  ❌ {get_text('plugins.loading.error_loading', name=plugin_name, error=e)}")
                    self.plugin_status[plugin_name] = "error"
                    error_count += 1
            else:
                print(f"  ⏭️  {get_text('plugins.loading.disabled', name=plugin_name)}")
                self.plugin_status[plugin_name] = "disabled"
                disabled_count += 1
        
        print("━" * 50)
        print(f"📊 {get_text('plugins.loading.summary', loaded=loaded_count, disabled=disabled_count, errors=error_count)}")
        print("━" * 50)
        
        return loaded_count, disabled_count, error_count
    
    async def sync_commands(self, guild_id=None):
        """
        Sincronizza gli slash commands con Discord
        
        Args:
            guild_id: Se specificato, sincronizza solo per quel server (più veloce per testing)
                     Se None, sincronizza globalmente (può richiedere fino a 1 ora)
        """
        try:
            if guild_id:
                guild = discord.Object(id=guild_id)
                self.bot.tree.copy_global_to(guild=guild)
                synced = await self.bot.tree.sync(guild=guild)
                print(f"✅ Sincronizzati {len(synced)} slash commands per il server {guild_id}")
            else:
                synced = await self.bot.tree.sync()
                print(f"✅ Sincronizzati {len(synced)} slash commands globalmente")
                print("   ⏱️  Nota: I comandi globali possono richiedere fino a 1 ora per propagarsi")
        except Exception as e:
            print(f"❌ Errore nella sincronizzazione slash commands: {e}")
    
    def reload_plugin(self, plugin_name: str):
        """
        Ricarica un plugin specifico (per hot-reload)
        Nota: Richiede il riavvio del bot per funzionare completamente
        """
        try:
            module = importlib.import_module(f'{self.plugins_dir}.{plugin_name}')
            importlib.reload(module)
            print(f"🔄 Plugin '{plugin_name}' ricaricato")
            return True
        except Exception as e:
            print(f"❌ Errore ricaricamento '{plugin_name}': {e}")
            return False
