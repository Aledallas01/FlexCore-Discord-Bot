"""
═══════════════════════════════════════════════════════════════════════════
Language Manager - Multilingual Support System
═══════════════════════════════════════════════════════════════════════════

Gestisce il caricamento e l'accesso alle traduzioni per il bot.
Supporta lingue multiple tramite file JSON in utils/language/

Supported Languages:
- ita (Italiano)
- eng (English)
"""

import json
import os
from typing import Dict, Any, Optional


class LanguageManager:
    """
    Gestore del sistema multilingua.
    
    Carica le traduzioni da file JSON e fornisce un'interfaccia
    semplice per accedere ai testi tradotti.
    
    Usage:
        lang = LanguageManager("ita")
        print(lang.get("bot.startup.connected"))
        # Output: "🎉 BOT CONNESSO CON SUCCESSO! 🎉"
        
        # Con parametri
        print(lang.get("bot.config.file_not_found", path="config.json"))
        # Output: "Errore: File config.json non trovato!"
    """
    
    # Lingue supportate
    SUPPORTED_LANGUAGES = ["ita", "eng"]
    DEFAULT_LANGUAGE = "ita"
    
    def __init__(self, language: str = "ita"):
        """
        Inizializza il Language Manager.
        
        Args:
            language: Codice lingua (ita, eng, etc.)
        """
        self.language = language if language in self.SUPPORTED_LANGUAGES else self.DEFAULT_LANGUAGE
        self.translations: Dict[str, Any] = {}
        self._load_translations()
    
    def _load_translations(self):
        """Carica le traduzioni dal file JSON della lingua selezionata."""
        lang_file = os.path.join("utils", "language", f"{self.language}.json")
        
        try:
            with open(lang_file, 'r', encoding='utf-8') as f:
                self.translations = json.load(f)
        except FileNotFoundError:
            print(f"⚠️ Warning: Language file '{lang_file}' not found, falling back to {self.DEFAULT_LANGUAGE}")
            # Fallback to default language
            if self.language != self.DEFAULT_LANGUAGE:
                self.language = self.DEFAULT_LANGUAGE
                self._load_translations()
            else:
                self.translations = {}
        except json.JSONDecodeError as e:
            print(f"❌ Error parsing '{lang_file}': {e}")
            self.translations = {}
    
    def get(self, key: str, **kwargs) -> str:
        """
        Ottiene una traduzione dato il suo path separato da punti.
        
        Args:
            key: Chiave della traduzione (es: "bot.startup.connected")
            **kwargs: Parametri opzionali per formattazione stringa
            
        Returns:
            str: Testo tradotto (o la chiave stessa se non trovata)
            
        Examples:
            >>> lang.get("bot.startup.connected")
            "🎉 BOT CONNESSO CON SUCCESSO! 🎉"
            
            >>> lang.get("plugins.loading.found", count=3, names="mod1, mod2, mod3")
            "Trovati 3 plugin: mod1, mod2, mod3"
        """
        keys = key.split('.')
        value = self.translations
        
        # Naviga attraverso le chiavi annidate
        for k in keys:
            if isinstance(value, dict) and k in value:
                value = value[k]
            else:
                # Chiave non trovata, ritorna la chiave stessa come fallback
                return key
        
        # Se il valore è una stringa, formatta con i parametri
        if isinstance(value, str):
            try:
                return value.format(**kwargs)
            except KeyError as e:
                print(f"⚠️ Warning: Missing parameter {e} for translation key '{key}'")
                return value
        
        # Se il valore non è una stringa, ritorna la chiave
        return key
    
    def change_language(self, language: str):
        """
        Cambia la lingua corrente.
        
        Args:
            language: Nuovo codice lingua
        """
        if language in self.SUPPORTED_LANGUAGES:
            self.language = language
            self._load_translations()
        else:
            print(f"⚠️ Warning: Language '{language}' not supported. Available: {', '.join(self.SUPPORTED_LANGUAGES)}")
    
    def get_current_language(self) -> str:
        """Ritorna il codice della lingua corrente."""
        return self.language
    
    @classmethod
    def get_supported_languages(cls) -> list:
        """Ritorna la lista delle lingue supportate."""
        return cls.SUPPORTED_LANGUAGES


# Istanza globale (sarà inizializzata dal bot)
_lang_instance: Optional[LanguageManager] = None


def init_language(language: str = "ita"):
    """
    Inizializza l'istanza globale del Language Manager.
    
    Args:
        language: Codice lingua da usare
    """
    global _lang_instance
    _lang_instance = LanguageManager(language)


def get_text(key: str, **kwargs) -> str:
    """
    Funzione helper per ottenere testi tradotti dall'istanza globale.
    
    Args:
        key: Chiave traduzione
        **kwargs: Parametri formattazione
        
    Returns:
        str: Testo tradotto
    """
    if _lang_instance is None:
        # Se non inizializzato, usa lingua default
        init_language()
    
    return _lang_instance.get(key, **kwargs)


def change_language(language: str):
    """
    Cambia la lingua dell'istanza globale.
    
    Args:
        language: Nuovo codice lingua
    """
    if _lang_instance is None:
        init_language(language)
    else:
        _lang_instance.change_language(language)
