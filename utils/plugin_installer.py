"""
FlexCore Plugin Store - Enhanced Version

Advanced plugin management system with:
- Auto-fetch plugin metadata from README.md
- Version checking and updates
- Search and filtering
- One-click install/update/uninstall
- Automatic plugin.json registration
"""

import requests
import os
import json
import re
from typing import List, Dict, Optional
from datetime import datetime

class PluginInstaller:
    """Enhanced plugin installer with metadata support"""
    
    REPO_OWNER = "Aledallas01"
    REPO_NAME = "FlexCore-Plugins"
    REPO_API_URL = f"https://api.github.com/repos/{REPO_OWNER}/{REPO_NAME}/contents/"
    PLUGINS_DIR = "plugins"
    PLUGINS_CONFIG = "config/plugins.json"
    REPO_API_URL2 = f"https://api.github.com/repos/{REPO_OWNER}/{REPO_NAME}/contents/{PLUGINS_DIR}"
    
    @staticmethod
    def get_available_plugins() -> List[Dict]:
        """
        Fetch available plugins from GitHub with enhanced metadata.
        Returns list with: name, description, author, version, download_url, size, sha
        """
        try:
            # Fetch plugins directory
            response = requests.get(PluginInstaller.REPO_API_URL2, timeout=10)
            response.raise_for_status()
            data = response.json()
            
            plugins = []
            for item in data:
                # Filter .py files (exclude system files and __init__)
                if (item['type'] == 'file' and 
                    item['name'].endswith('.py') and 
                    not item['name'].startswith('_')):
                    
                    plugin_info = {
                        'name': item['name'],
                        'display_name': item['name'].replace('.py', '').replace('_', ' ').title(),
                        'download_url': item['download_url'],
                        'size': item['size'],
                        'sha': item['sha'],
                        'description': 'No description available',
                        'author': 'Unknown',
                        'version': '1.0.0',
                        'tags': []
                    }
                    
                    # Try to fetch metadata from plugin file
                    metadata = PluginInstaller._fetch_plugin_metadata(item['download_url'])
                    if metadata:
                        plugin_info.update(metadata)
                    
                    plugins.append(plugin_info)
            
            return sorted(plugins, key=lambda x: x['display_name'])
            
        except Exception as e:
            print(f"❌ Error fetching plugins: {e}")
            return []
    
    @staticmethod
    def _fetch_plugin_metadata(download_url: str) -> Optional[Dict]:
        """Extract metadata from plugin file docstring"""
        try:
            response = requests.get(download_url, timeout=10)
            response.raise_for_status()
            content = response.text
            
            metadata = {}
            
            # Extract docstring
            docstring_match = re.search(r'"""(.*?)"""', content, re.DOTALL)
            if docstring_match:
                docstring = docstring_match.group(1).strip()
                
                # Parse metadata from docstring
                lines = docstring.split('\n')
                description_lines = []
                
                for line in lines:
                    line = line.strip()
                    
                    # Check for metadata tags
                    if line.lower().startswith('author:'):
                        metadata['author'] = line.split(':', 1)[1].strip()
                    elif line.lower().startswith('version:'):
                        metadata['version'] = line.split(':', 1)[1].strip()
                    elif line.lower().startswith('tags:'):
                        tags_str = line.split(':', 1)[1].strip()
                        metadata['tags'] = [t.strip() for t in tags_str.split(',')]
                    elif line and not any(line.lower().startswith(x) for x in ['author:', 'version:', 'tags:']):
                        description_lines.append(line)
                
                # Set description (first non-empty lines)
                if description_lines:
                    metadata['description'] = ' '.join(description_lines[:3])[:150]
            
            return metadata if metadata else None
            
        except Exception as e:
            print(f"⚠️ Could not fetch metadata: {e}")
            return None
    
    @staticmethod
    def install_plugin(plugin_data: Dict) -> bool:
        """
        Download and install a plugin.
        Automatically registers it in plugins.json.
        """
        try:
            if not os.path.exists(PluginInstaller.PLUGINS_DIR):
                os.makedirs(PluginInstaller.PLUGINS_DIR)
            
            # Download plugin file
            response = requests.get(plugin_data['download_url'], timeout=15)
            response.raise_for_status()
            
            file_path = os.path.join(PluginInstaller.PLUGINS_DIR, plugin_data['name'])
            
            # Write file
            with open(file_path, 'wb') as f:
                f.write(response.content)
            
            # Register in plugins.json
            plugin_name = plugin_data['name'].replace('.py', '')
            PluginInstaller._register_plugin(plugin_name, enabled=True)
            
            print(f"✅ Plugin '{plugin_name}' installed successfully!")
            return True
            
        except Exception as e:
            print(f"❌ Error installing plugin {plugin_data.get('name')}: {e}")
            return False
    
    @staticmethod
    def uninstall_plugin(plugin_name: str) -> bool:
        """
        Uninstall a plugin.
        Removes file and plugins.json entry.
        """
        try:
            file_path = os.path.join(PluginInstaller.PLUGINS_DIR, plugin_name)
            
            if os.path.exists(file_path):
                os.remove(file_path)
                print(f"✅ File deleted: {file_path}")
            
            # Remove from plugins.json
            plugin_key = plugin_name.replace('.py', '')
            PluginInstaller._unregister_plugin(plugin_key)
            
            print(f"✅ Plugin '{plugin_key}' uninstalled!")
            return True
            
        except Exception as e:
            print(f"❌ Error uninstalling plugin: {e}")
            return False
    
    @staticmethod
    def is_installed(plugin_name: str) -> bool:
        """Check if plugin is installed locally"""
        return os.path.exists(os.path.join(PluginInstaller.PLUGINS_DIR, plugin_name))
    
    @staticmethod
    def get_installed_version(plugin_name: str) -> Optional[str]:
        """Get version of installed plugin (from file hash)"""
        try:
            file_path = os.path.join(PluginInstaller.PLUGINS_DIR, plugin_name)
            if not os.path.exists(file_path):
                return None
            
            # Return file modification date as pseudo-version
            mtime = os.path.getmtime(file_path)
            return datetime.fromtimestamp(mtime).strftime("%Y%m%d")
            
        except:
            return None
    
    @staticmethod
    def _register_plugin(plugin_name: str, enabled: bool = True):
        """Register plugin in plugins.json"""
        try:
            # Ensure config directory exists
            os.makedirs(os.path.dirname(PluginInstaller.PLUGINS_CONFIG), exist_ok=True)
            
            # Load existing config
            if os.path.exists(PluginInstaller.PLUGINS_CONFIG):
                with open(PluginInstaller.PLUGINS_CONFIG, 'r') as f:
                    config = json.load(f)
            else:
                config = {}
            
            # Add/update plugin
            config[plugin_name] = enabled
            
            # Save
            with open(PluginInstaller.PLUGINS_CONFIG, 'w') as f:
                json.dump(config, f, indent=2)
                
        except Exception as e:
            print(f"⚠️ Could not register plugin in config: {e}")
    
    @staticmethod
    def _unregister_plugin(plugin_name: str):
        """Remove plugin from plugins.json"""
        try:
            if not os.path.exists(PluginInstaller.PLUGINS_CONFIG):
                return
            
            with open(PluginInstaller.PLUGINS_CONFIG, 'r') as f:
                config = json.load(f)
            
            if plugin_name in config:
                del config[plugin_name]
                
                with open(PluginInstaller.PLUGINS_CONFIG, 'w') as f:
                    json.dump(config, f, indent=2)
                    
        except Exception as e:
            print(f"⚠️ Could not unregister plugin: {e}")
    
    @staticmethod
    def search_plugins(query: str, plugins: List[Dict]) -> List[Dict]:
        """Search plugins by name, description, or tags"""
        query = query.lower()
        results = []
        
        for plugin in plugins:
            # Search in name
            if query in plugin['display_name'].lower():
                results.append(plugin)
                continue
            
            # Search in description
            if query in plugin.get('description', '').lower():
                results.append(plugin)
                continue
            
            # Search in tags
            if any(query in tag.lower() for tag in plugin.get('tags', [])):
                results.append(plugin)
                continue
        
        return results
