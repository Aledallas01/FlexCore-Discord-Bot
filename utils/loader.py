import discord
from discord.ext import commands
import json
import os
import importlib
import sys
from pathlib import Path


from utils.config_validator import ConfigValidator


class PluginLoader:
    """Gestisce il caricamento dinamico dei plugin con auto-discovery"""
    
    def __init__(self, bot: commands.Bot):
        self.bot = bot
        self.plugins_dir = "plugins"
        self.config_path = os.path.join("config", "plugins.json")
        self.plugins_config = {}
    
    def discover_plugins(self):
        """
        Scansiona la cartella plugins/ e trova tutti i file .py
        Ritorna una lista di nomi plugin (senza estensione)
        """
        plugins_path = Path(self.plugins_dir)
        
        if not plugins_path.exists():
            print(f"⚠️  Cartella {self.plugins_dir}/ non trovata!")
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
                print(f"  ➕ Nuovo plugin '{plugin_name}' aggiunto (abilitato di default)")
                updated = True
        
        # Rimuovi plugin che non esistono più (opzionale)
        plugins_to_remove = [
            name for name in self.plugins_config.keys() 
            if name not in discovered_plugins
        ]
        
        for plugin_name in plugins_to_remove:
            del self.plugins_config[plugin_name]
            print(f"  ➖ Plugin '{plugin_name}' rimosso (file non trovato)")
            updated = True
        
        if updated:
            self.save_plugins_config()
        
        return updated
    
    async def load_plugins(self):
        """
        Carica tutti i plugin abilitati
        Supporta sia comandi text che slash commands
        """
        print("🔌 Sistema di caricamento plugin avviato")
        print("━" * 50)
        
        # 1. Carica configurazione esistente
        self.load_plugins_config()
        
        # 2. Scopri plugin nella cartella
        print("🔍 Scansione cartella plugins/...")
        discovered_plugins = self.discover_plugins()
        print(f"   Trovati {len(discovered_plugins)} plugin: {', '.join(discovered_plugins)}")
        print()
        
        # 3. Aggiorna configurazione con nuovi plugin
        print("📝 Aggiornamento configurazione...")
        self.update_plugins_config(discovered_plugins)
        print()
        
        # 4. Carica i plugin abilitati
        print("⚙️  Caricamento plugin abilitati...")
        print("━" * 50)
        
        loaded_count = 0
        disabled_count = 0
        error_count = 0
        
        for plugin_name, enabled in self.plugins_config.items():
            if enabled:
                # Valida configurazione plugin
                if not ConfigValidator.validate_plugin(plugin_name):
                    print(f"  ❌ Plugin '{plugin_name}' saltato: Configurazione invalida")
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
                        print(f"  ✅ Plugin '{plugin_name}' caricato")
                        loaded_count += 1
                    else:
                        print(f"  ⚠️  Plugin '{plugin_name}': classe {class_name} non trovata")
                        error_count += 1
                        
                except ModuleNotFoundError:
                    print(f"  ❌ Plugin '{plugin_name}': file non trovato")
                    error_count += 1
                except Exception as e:
                    print(f"  ❌ Errore caricamento '{plugin_name}': {e}")
                    error_count += 1
            else:
                print(f"  ⏭️  Plugin '{plugin_name}' disabilitato")
                disabled_count += 1
        
        print("━" * 50)
        print(f"📊 Riepilogo: {loaded_count} caricati, {disabled_count} disabilitati, {error_count} errori")
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
