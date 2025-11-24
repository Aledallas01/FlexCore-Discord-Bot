import requests
import os
import json
from typing import List, Dict, Optional

class PluginInstaller:
    """Gestisce il download e l'installazione dei plugin da GitHub"""
    
    REPO_API_URL = "https://api.github.com/repos/Aledallas01/FlexCore-Plugins/plugins/"
    PLUGINS_DIR = "plugins"

    @staticmethod
    def get_available_plugins() -> List[Dict]:
        """
        Recupera la lista dei plugin disponibili dalla repo GitHub.
        Ritorna una lista di dizionari con 'name', 'download_url', 'size'.
        """
        try:
            response = requests.get(PluginInstaller.REPO_API_URL, timeout=10)
            response.raise_for_status()
            data = response.json()
            
            plugins = []
            for item in data:
                # Filtra solo i file .py che non sono file di sistema
                if item['type'] == 'file' and item['name'].endswith('.py') and not item['name'].startswith('.'):
                    plugins.append({
                        'name': item['name'],
                        'download_url': item['download_url'],
                        'size': item['size'],
                        'sha': item['sha']
                    })
            return plugins
        except Exception as e:
            print(f"Error fetching plugins: {e}")
            return []

    @staticmethod
    def install_plugin(plugin_data: Dict) -> bool:
        """
        Scarica e installa un plugin.
        """
        try:
            if not os.path.exists(PluginInstaller.PLUGINS_DIR):
                os.makedirs(PluginInstaller.PLUGINS_DIR)
                
            response = requests.get(plugin_data['download_url'], timeout=15)
            response.raise_for_status()
            
            file_path = os.path.join(PluginInstaller.PLUGINS_DIR, plugin_data['name'])
            
            with open(file_path, 'wb') as f:
                f.write(response.content)
                
            return True
        except Exception as e:
            print(f"Error installing plugin {plugin_data.get('name')}: {e}")
            return False

    @staticmethod
    def is_installed(plugin_name: str) -> bool:
        """Controlla se un plugin è già installato localmente"""
        return os.path.exists(os.path.join(PluginInstaller.PLUGINS_DIR, plugin_name))
