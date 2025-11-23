"""
🔄 AUTO-UPDATE SYSTEM
Sistema intelligente di aggiornamento automatico dal repository GitHub
"""

import os
import json
import requests
import shutil
from datetime import datetime
from typing import Dict, List, Optional, Tuple
from pathlib import Path

# CONFIGURAZIONE HARDCODED (NON MODIFICABILE)
GITHUB_REPO = "Aledallas01/FlexCore-Discord-Bot"
GITHUB_BRANCH = "main"
GITHUB_API_BASE = f"https://api.github.com/repos/{GITHUB_REPO}"

# File da NON aggiornare MAI
PROTECTED_FILES = {
    "config/config.json",  # Configurazione utente
    ".env",                # Variabili ambiente
    ".git",                # Repository git locale
    ".venv",               # Virtual environment
    "__pycache__",         # Cache Python
    "data/",               # Database e dati utente
    "logs/",               # Log files
}

# ANSI Colors
class Colors:
    RESET = "\033[0m"
    BOLD = "\033[1m"
    GREEN = "\033[92m"
    YELLOW = "\033[93m"
    BLUE = "\033[94m"
    CYAN = "\033[96m"
    MAGENTA = "\033[95m"
    RED = "\033[91m"


class AutoUpdater:
    """Gestisce aggiornamenti automatici da GitHub"""
    
    def __init__(self):
        self.last_check_file = ".last_update_check"
        self.backup_dir = ".update_backups"
        
    def is_protected(self, file_path: str) -> bool:
        """Controlla se un file è protetto dall'aggiornamento"""
        for protected in PROTECTED_FILES:
            if file_path.startswith(protected) or protected in file_path:
                return True
        return False
    
    def get_remote_commit(self) -> Optional[str]:
        """Ottieni l'ultimo commit SHA dalla repository GitHub"""
        try:
            url = f"{GITHUB_API_BASE}/commits/{GITHUB_BRANCH}"
            response = requests.get(url, timeout=10)
            response.raise_for_status()
            return response.json()["sha"]
        except Exception as e:
            print(f"{Colors.RED}❌ Errore nel controllare GitHub: {e}{Colors.RESET}")
            return None
    
    def get_local_commit(self) -> Optional[str]:
        """Leggi l'ultimo commit SHA salvato localmente"""
        if os.path.exists(self.last_check_file):
            try:
                with open(self.last_check_file, 'r') as f:
                    data = json.load(f)
                    return data.get("last_commit")
            except:
                pass
        return None
    
    def save_local_commit(self, commit_sha: str):
        """Salva l'ultimo commit SHA localmente"""
        data = {
            "last_commit": commit_sha,
            "last_check": datetime.now().isoformat()
        }
        with open(self.last_check_file, 'w') as f:
            json.dump(data, f, indent=2)
    
    def smart_json_merge(self, local_data: dict, remote_data: dict) -> dict:
        """
        Merge intelligente di JSON:
        - Mantiene valori locali esistenti
        - Aggiunge nuovi campi da remoto
        - Non rimuove campi locali
        """
        result = local_data.copy()
        
        for key, remote_value in remote_data.items():
            if key not in result:
                # Nuovo campo: aggiungi
                result[key] = remote_value
            elif isinstance(remote_value, dict) and isinstance(result[key], dict):
                # Entrambi dict: merge ricorsivo
                result[key] = self.smart_json_merge(result[key], remote_value)
            # Altrimenti mantieni valore locale
        
        return result
    
    def download_file(self, file_path: str) -> Optional[bytes]:
        """Scarica un file dalla repository GitHub"""
        try:
            url = f"https://raw.githubusercontent.com/{GITHUB_REPO}/{GITHUB_BRANCH}/{file_path}"
            response = requests.get(url, timeout=15)
            response.raise_for_status()
            return response.content
        except Exception as e:
            print(f"{Colors.YELLOW}   ⚠️  Impossibile scaricare {file_path}: {e}{Colors.RESET}")
            return None
    
    def get_changed_files(self, old_commit: Optional[str], new_commit: str) -> List[str]:
        """Ottieni lista di file modificati tra due commit"""
        try:
            if not old_commit:
                # Prima volta: scarica tutto (tranne protected)
                url = f"{GITHUB_API_BASE}/git/trees/{new_commit}?recursive=1"
                response = requests.get(url, timeout=10)
                response.raise_for_status()
                tree = response.json()["tree"]
                return [item["path"] for item in tree if item["type"] == "blob"]
            else:
                # Confronto tra commit
                url = f"{GITHUB_API_BASE}/compare/{old_commit}...{new_commit}"
                response = requests.get(url, timeout=10)
                response.raise_for_status()
                files = response.json()["files"]
                return [f["filename"] for f in files]
        except Exception as e:
            print(f"{Colors.RED}❌ Errore nel recuperare file modificati: {e}{Colors.RESET}")
            return []
    
    def backup_file(self, file_path: str):
        """Crea backup di un file prima di aggiornarlo"""
        if not os.path.exists(file_path):
            return
        
        os.makedirs(self.backup_dir, exist_ok=True)
        backup_path = os.path.join(self.backup_dir, file_path.replace("/", "_").replace("\\", "_"))
        shutil.copy2(file_path, backup_path)
    
    def apply_update(self, file_path: str, content: bytes) -> bool:
        """Applica un aggiornamento a un file"""
        try:
            # Crea directory se necessaria
            os.makedirs(os.path.dirname(file_path) if os.path.dirname(file_path) else ".", exist_ok=True)
            
            # Gestione speciale per JSON
            if file_path.endswith(".json"):
                # Smart merge per JSON
                local_data = {}
                if os.path.exists(file_path):
                    with open(file_path, 'r', encoding='utf-8') as f:
                        local_data = json.load(f)
                
                remote_data = json.loads(content.decode('utf-8'))
                merged_data = self.smart_json_merge(local_data, remote_data)
                
                with open(file_path, 'w', encoding='utf-8') as f:
                    json.dump(merged_data, f, indent=2, ensure_ascii=False)
                
                print(f"{Colors.GREEN}   ✅ Merged: {file_path}{Colors.RESET}")
            else:
                # Sovrascrivi file Python e altri
                self.backup_file(file_path)
                
                with open(file_path, 'wb') as f:
                    f.write(content)
                
                print(f"{Colors.GREEN}   ✅ Updated: {file_path}{Colors.RESET}")
            
            return True
        except Exception as e:
            print(f"{Colors.RED}   ❌ Errore aggiornando {file_path}: {e}{Colors.RESET}")
            return False
    
    def check_and_apply(self) -> bool:
        """
        Controlla e applica aggiornamenti se disponibili.
        Ritorna True se aggiornamenti sono stati applicati.
        """
        print(f"\n{Colors.CYAN}{Colors.BOLD}{'='*70}{Colors.RESET}")
        print(f"{Colors.CYAN}{Colors.BOLD}🔄 AUTO-UPDATE SYSTEM{Colors.RESET}")
        print(f"{Colors.CYAN}{'='*70}{Colors.RESET}")
        print(f"{Colors.BLUE}📡 Repository:{Colors.RESET} {GITHUB_REPO}")
        print(f"{Colors.BLUE}🌿 Branch:{Colors.RESET} {GITHUB_BRANCH}\n")
        
        # Controlla commit remoto
        print(f"{Colors.YELLOW}⏳ Controllo aggiornamenti...{Colors.RESET}")
        remote_commit = self.get_remote_commit()
        
        if not remote_commit:
            print(f"{Colors.RED}❌ Impossibile verificare aggiornamenti (GitHub non raggiungibile){Colors.RESET}\n")
            return False
        
        local_commit = self.get_local_commit()
        
        if local_commit == remote_commit:
            print(f"{Colors.GREEN}✅ Bot già aggiornato all'ultima versione!{Colors.RESET}")
            print(f"{Colors.CYAN}{'='*70}{Colors.RESET}\n")
            return False
        
        # Ci sono aggiornamenti
        if local_commit:
            print(f"{Colors.YELLOW}🆕 Nuovi aggiornamenti disponibili!{Colors.RESET}")
            print(f"{Colors.BLUE}   Locale:{Colors.RESET}  {local_commit[:8]}")
            print(f"{Colors.BLUE}   Remoto:{Colors.RESET}  {remote_commit[:8]}\n")
        else:
            print(f"{Colors.YELLOW}🆕 Prima sincronizzazione con GitHub{Colors.RESET}\n")
        
        # Scarica lista file modificati
        print(f"{Colors.YELLOW}📥 Scaricamento file modificati...{Colors.RESET}")
        changed_files = self.get_changed_files(local_commit, remote_commit)
        
        if not changed_files:
            print(f"{Colors.RED}❌ Nessun file da aggiornare{Colors.RESET}\n")
            return False
        
        # Filtra file protetti
        files_to_update = [f for f in changed_files if not self.is_protected(f)]
        
        if not files_to_update:
            print(f"{Colors.YELLOW}⚠️  Tutti i file modificati sono protetti{Colors.RESET}\n")
            self.save_local_commit(remote_commit)
            return False
        
        print(f"{Colors.GREEN}   Trovati {len(files_to_update)} file da aggiornare{Colors.RESET}\n")
        
        # Applica aggiornamenti
        updated_count = 0
        for file_path in files_to_update:
            content = self.download_file(file_path)
            if content and self.apply_update(file_path, content):
                updated_count += 1
        
        # Salva nuovo commit
        self.save_local_commit(remote_commit)
        
        print(f"\n{Colors.GREEN}{Colors.BOLD}✅ Aggiornamento completato!{Colors.RESET}")
        print(f"{Colors.GREEN}   {updated_count}/{len(files_to_update)} file aggiornati con successo{Colors.RESET}")
        print(f"{Colors.CYAN}{'='*70}{Colors.RESET}\n")
        
        return True
