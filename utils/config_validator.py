import json
import os
import sys
from typing import Dict, List, Any, Optional
from utils.language_manager import get_text

# ANSI Color Codes per output leggibile
class Colors:
    RESET = "\033[0m"
    BOLD = "\033[1m"
    GRAY = "\033[90m"
    RED = "\033[91m"
    GREEN = "\033[92m"
    YELLOW = "\033[93m"
    BLUE = "\033[94m"
    MAGENTA = "\033[95m"
    CYAN = "\033[96m"

class ConfigValidator:
    """Valida le configurazioni del bot e dei plugin"""

    REQUIRED_CORE = ["token", "prefix", "owner_id"]
    
    # Store last error for UI popup
    last_error = None
    
    # Schemi per i plugin (campi obbligatori)
    PLUGIN_SCHEMAS = {
        "moderation": [
            "staff_roles", 
            "admin_roles", 
            "rate_limit", 
            "auto_actions"
        ],
        "tickets": [
            "category_id",
            "support_role_id"
        ]
    }

    @staticmethod
    def _load_json(path: str) -> Optional[Dict[str, Any]]:
        """Carica un file JSON in modo sicuro"""
        if not os.path.exists(path):
            return None
        try:
            with open(path, 'r', encoding='utf-8') as f:
                return json.load(f)
        except Exception as e:
            print(f"❌ {get_text('general.json_read_error', path=path, error=e)}")
            return None

    @classmethod
    def validate_core(cls) -> bool:
        """
        Valida la configurazione principale (config.json).
        Ritorna True se valida, altrimenti stampa errore e ritorna False.
        """
        config_path = os.path.join("config", "config.json")
        config = cls._load_json(config_path)

        if config is None:
            error_msg = (
                f"{get_text('validation.core.title')}\n\n"
                f"File: {config_path}\n\n"
                f"{get_text('validation.core.file_missing')}\n\n"
                f"{get_text('validation.core.how_to_fix')}\n"
                f"1. {get_text('validation.core.step1', path=config_path)}\n"
                f"2. {get_text('validation.core.step2')}"
            )
            cls.last_error = {"title": "Config Core Invalido", "message": error_msg}
            
            print(f"\n{Colors.RED}{Colors.BOLD}{'='*70}{Colors.RESET}")
            print(f"{Colors.RED}{Colors.BOLD}❌ {get_text('validation.core.title')}{Colors.RESET}")
            print(f"{Colors.RED}{'='*70}{Colors.RESET}")
            print(f"{Colors.YELLOW}📁 File:{Colors.RESET} {config_path}")
            print(f"{Colors.RED}   {get_text('validation.core.file_missing')}{Colors.RESET}")
            print(f"\n{Colors.CYAN}💡 {get_text('validation.core.how_to_fix')}:{Colors.RESET}")
            print(f"   1. {get_text('validation.core.step1', path=config_path)}")
            print(f"   2. {get_text('validation.core.step2')}")
            print(f"{Colors.RED}{'='*70}{Colors.RESET}\n")
            return False

        missing = [key for key in cls.REQUIRED_CORE if key not in config]
        
        if missing:
            fields_list = "\n".join([get_text('validation.core.field', field=field) for field in missing])
            error_msg = (
                f"{get_text('validation.core.title')}\n\n"
                f"File: {config_path}\n\n"
                f"{get_text('validation.core.missing_fields')}\n"
                f"{fields_list}\n\n"
                f"{get_text('validation.core.how_to_fix')}\n"
                "Aggiungi i campi mancanti al file di configurazione:\n"
                '{\n  "token": "YOUR_BOT_TOKEN",\n  "prefix": "!",\n  "owner_id": "YOUR_DISCORD_ID"\n}'
            )
            cls.last_error = {"title": "Config Core Incompleto", "message": error_msg}
            
            print(f"\n{Colors.RED}{Colors.BOLD}{'='*70}{Colors.RESET}")
            print(f"{Colors.RED}{Colors.BOLD}❌ {get_text('validation.core.title')}{Colors.RESET}")
            print(f"{Colors.RED}{'='*70}{Colors.RESET}")
            print(f"{Colors.YELLOW}📁 File:{Colors.RESET} {config_path}")
            print(f"{Colors.RED}   {get_text('validation.core.missing_fields')}:{Colors.RESET}")
            for field in missing:
                print(f"      {Colors.RED}•{Colors.RESET} {Colors.BOLD}{field}{Colors.RESET}")
            print(f"\n{Colors.CYAN}💡 {get_text('validation.core.how_to_fix')}:{Colors.RESET}")
            print(f"   Aggiungi i campi mancanti al file di configurazione:")
            print(f'{Colors.GRAY}   {{\n     "token": "YOUR_BOT_TOKEN",\n     "prefix": "!",\n     "owner_id": "YOUR_DISCORD_ID"\n   }}{Colors.RESET}')
            print(f"{Colors.RED}{'='*70}{Colors.RESET}\n")
            return False
            
        # Verifica valori vuoti
        empty = [key for key in cls.REQUIRED_CORE if not config[key] and not isinstance(config[key], (int, bool))]
        if empty:
            print(f"{Colors.YELLOW}⚠️  ATTENZIONE:{Colors.RESET} Campi core vuoti: {', '.join(empty)}")

        print(f"{Colors.GREEN}✅ {get_text('validation.core.title')} valida{Colors.RESET}")
        return True

    @classmethod
    def validate_plugin(cls, plugin_name: str) -> bool:
        """
        Valida la configurazione di un plugin.
        Ritorna True se valida (o se non c'è schema), False se invalida.
        """
        # Se non c'è uno schema definito per questo plugin, assumiamo sia ok
        if plugin_name not in cls.PLUGIN_SCHEMAS:
            return True

        config_path = os.path.join("config", f"{plugin_name}.json")
        
        # Se il file non esiste, il plugin userà i default
        if not os.path.exists(config_path):
            return True

        config = cls._load_json(config_path)
        if config is None:
            print(f"\n{Colors.RED}{Colors.BOLD}{'='*70}{Colors.RESET}")
            print(f"{Colors.RED}{Colors.BOLD}❌ {get_text('validation.plugin.error_corrupted')}{Colors.RESET}")
            print(f"{Colors.RED}{'='*70}{Colors.RESET}")
            print(f"{Colors.YELLOW}🔌 Plugin:{Colors.RESET} {Colors.BOLD}{plugin_name}{Colors.RESET}")
            print(f"{Colors.YELLOW}📁 File:{Colors.RESET} {config_path}")
            print(f"{Colors.RED}   {get_text('validation.plugin.file_corrupted')}{Colors.RESET}")
            print(f"\n{Colors.CYAN}💡 {get_text('validation.core.how_to_fix')}:{Colors.RESET}")
            print(f"   1. Controlla la sintassi JSON del file")
            print(f"   2. Assicurati che non ci siano virgole extra o parentesi non chiuse")
            print(f"{Colors.RED}{'='*70}{Colors.RESET}\n")
            return False

        required_keys = cls.PLUGIN_SCHEMAS[plugin_name]
        missing = [key for key in required_keys if key not in config]

        if missing:
            print(f"\n{Colors.RED}{Colors.BOLD}{'='*70}{Colors.RESET}")
            print(f"{Colors.RED}{Colors.BOLD}❌ {get_text('validation.plugin.error_incomplete')}{Colors.RESET}")
            print(f"{Colors.RED}{'='*70}{Colors.RESET}")
            print(f"{Colors.YELLOW}🔌 Plugin:{Colors.RESET} {Colors.BOLD}{plugin_name}{Colors.RESET}")
            print(f"{Colors.YELLOW}📁 File:{Colors.RESET} {config_path}")
            print(f"{Colors.RED}   {get_text('validation.plugin.missing_fields')}:{Colors.RESET}")
            for field in missing:
                print(f"      {Colors.RED}•{Colors.RESET} {Colors.BOLD}{field}{Colors.RESET}")
            print(f"{Colors.RED}{'='*70}{Colors.RESET}\n")
            return False

        # Validazione specifica valori per moderation
        if plugin_name == "moderation":
            staff_roles = config.get("staff_roles")
            if not staff_roles or not isinstance(staff_roles, list) or len(staff_roles) == 0:
                print(f"\n{Colors.RED}{Colors.BOLD}{'='*70}{Colors.RESET}")
                print(f"{Colors.RED}{Colors.BOLD}❌ ERRORE PLUGIN MODERATION - STAFF_ROLES VUOTO{Colors.RESET}")
                print(f"{Colors.RED}{'='*70}{Colors.RESET}")
                print(f"{Colors.YELLOW}🔌 Plugin:{Colors.RESET} {Colors.BOLD}moderation{Colors.RESET}")
                print(f"{Colors.YELLOW}📁 File:{Colors.RESET} {config_path}")
                print(f"{Colors.RED}   Il campo 'staff_roles' è vuoto o non è una lista!{Colors.RESET}")
                print(f"\n{Colors.CYAN}💡 Come risolvere:{Colors.RESET}")
                print(f"   1. Vai sul tuo server Discord")
                print(f"   2. Impostazioni Server → Ruoli → Click destro sul ruolo staff → Copia ID")
                print(f"   3. Aggiungi l'ID a 'staff_roles' in {config_path}:")
                print(f'{Colors.GRAY}      "staff_roles": [123456789012345678]{Colors.RESET}')
                print(f"\n{Colors.YELLOW}   🔍 Nota:{Colors.RESET} Devi abilitare 'Modalità Sviluppatore' in Discord:")
                print(f"      Impostazioni Utente → Avanzate → Modalità Sviluppatore")
                print(f"{Colors.RED}{'='*70}{Colors.RESET}\n")
                return False
                
            # Controllo validità ID Discord
            for key in ["log_channel_id", "mute_role_id"]:
                val = config.get(key)
                if val is not None and val != "":
                    if isinstance(val, str):
                        try:
                            int(val)
                        except ValueError:
                            print(f"\n{Colors.RED}{Colors.BOLD}{'='*70}{Colors.RESET}")
                            print(f"{Colors.RED}{Colors.BOLD}❌ {get_text('validation.plugin.error_values')}{Colors.RESET}")
                            print(f"{Colors.RED}{'='*70}{Colors.RESET}")
                            print(f"{Colors.YELLOW}🔌 Plugin:{Colors.RESET} {Colors.BOLD}moderation{Colors.RESET}")
                            print(f"{Colors.YELLOW}📁 File:{Colors.RESET} {config_path}")
                            print(f"{Colors.RED}   {get_text('validation.plugin.invalid_value', field=key, value=val, hint='Deve essere un ID Discord numerico')}{Colors.RESET}")
                            print(f"\n{Colors.CYAN}💡 {get_text('validation.core.how_to_fix')}:{Colors.RESET}")
                            print(f"   Opzione 1: Usa un ID Discord numerico valido")
                            print(f'{Colors.GRAY}      "{key}": "123456789012345678"{Colors.RESET}')
                            print(f"   Opzione 2: Imposta a null se vuoi disabilitare")
                            print(f'{Colors.GRAY}      "{key}": null{Colors.RESET}')
                            print(f"\n{Colors.YELLOW}   🔍 Come copiare ID:{Colors.RESET}")
                            print(f"      1. Abilita Modalità Sviluppatore in Discord")
                            print(f"      2. Click destro su canale/ruolo → Copia ID")
                            print(f"{Colors.RED}{'='*70}{Colors.RESET}\n")
                            return False

        return True
