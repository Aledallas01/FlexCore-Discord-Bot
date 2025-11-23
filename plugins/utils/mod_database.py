"""
Database manager for moderation plugin
Handles all SQLite operations for warns, bans, mutes, kicks, and audit logging
"""

import sqlite3
import os
from datetime import datetime, timedelta
from typing import Optional, List, Dict, Any
import json


class ModerationDatabase:
    """Gestisce il database SQLite per il sistema di moderazione"""
    
    def __init__(self, db_path: str = "data/moderation.db"):
        self.db_path = db_path
        self._ensure_data_directory()
        self._initialize_database()
    
    def _ensure_data_directory(self):
        """Crea la directory data se non esiste"""
        os.makedirs(os.path.dirname(self.db_path), exist_ok=True)
    
    def _get_connection(self) -> sqlite3.Connection:
        """Ottiene una connessione al database"""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row  # Accesso per nome colonna
        return conn
    
    def _initialize_database(self):
        """Inizializza il database con le tabelle necessarie"""
        conn = self._get_connection()
        cursor = conn.cursor()
        
        # Tabella warns
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS warns (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                moderator_id INTEGER NOT NULL,
                guild_id INTEGER NOT NULL,
                reason TEXT,
                timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        # Tabella bans
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS bans (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                moderator_id INTEGER NOT NULL,
                guild_id INTEGER NOT NULL,
                reason TEXT,
                duration INTEGER,
                expires_at DATETIME,
                timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
                active BOOLEAN DEFAULT 1
            )
        """)
        
        # Tabella mutes
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS mutes (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                moderator_id INTEGER NOT NULL,
                guild_id INTEGER NOT NULL,
                reason TEXT,
                duration INTEGER,
                expires_at DATETIME,
                timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
                active BOOLEAN DEFAULT 1
            )
        """)
        
        # Tabella kicks
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS kicks (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                moderator_id INTEGER NOT NULL,
                guild_id INTEGER NOT NULL,
                reason TEXT,
                timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        # Tabella mod_log (audit generale)
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS mod_log (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                action_type TEXT NOT NULL,
                user_id INTEGER NOT NULL,
                moderator_id INTEGER NOT NULL,
                guild_id INTEGER NOT NULL,
                details TEXT,
                timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        conn.commit()
        conn.close()
    
    # ===== WARNS =====
    
    def add_warn(self, user_id: int, moderator_id: int, guild_id: int, reason: Optional[str] = None) -> int:
        """Aggiunge un warn e ritorna l'ID"""
        conn = self._get_connection()
        cursor = conn.cursor()
        
        cursor.execute("""
            INSERT INTO warns (user_id, moderator_id, guild_id, reason)
            VALUES (?, ?, ?, ?)
        """, (user_id, moderator_id, guild_id, reason))
        
        warn_id = cursor.lastrowid
        
        # Log nell'audit
        self._add_log(cursor, "WARN", user_id, moderator_id, guild_id, 
                     f"Warn #{warn_id}: {reason or 'Nessun motivo'}")
        
        conn.commit()
        conn.close()
        return warn_id
    
    def remove_warn(self, warn_id: Optional[int] = None, user_id: Optional[int] = None, 
                    guild_id: Optional[int] = None) -> bool:
        """Rimuove un warn specifico o l'ultimo warn di un utente"""
        conn = self._get_connection()
        cursor = conn.cursor()
        
        if warn_id:
            cursor.execute("DELETE FROM warns WHERE id = ?", (warn_id,))
        elif user_id and guild_id:
            # Rimuovi l'ultimo warn
            cursor.execute("""
                DELETE FROM warns WHERE id = (
                    SELECT id FROM warns 
                    WHERE user_id = ? AND guild_id = ?
                    ORDER BY timestamp DESC LIMIT 1
                )
            """, (user_id, guild_id))
        else:
            conn.close()
            return False
        
        removed = cursor.rowcount > 0
        conn.commit()
        conn.close()
        return removed
    
    def get_user_warns(self, user_id: int, guild_id: int) -> List[Dict]:
        """Ottiene tutti i warn di un utente"""
        conn = self._get_connection()
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT * FROM warns 
            WHERE user_id = ? AND guild_id = ?
            ORDER BY timestamp DESC
        """, (user_id, guild_id))
        
        warns = [dict(row) for row in cursor.fetchall()]
        conn.close()
        return warns
    
    def get_warn_count(self, user_id: int, guild_id: int) -> int:
        """Conta i warn di un utente"""
        conn = self._get_connection()
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT COUNT(*) as count FROM warns 
            WHERE user_id = ? AND guild_id = ?
        """, (user_id, guild_id))
        
        count = cursor.fetchone()['count']
        conn.close()
        return count
    
    # ===== BANS =====
    
    def add_ban(self, user_id: int, moderator_id: int, guild_id: int, 
                reason: Optional[str] = None, duration: Optional[int] = None) -> int:
        """Aggiunge un ban (duration in secondi, None = permanente)"""
        conn = self._get_connection()
        cursor = conn.cursor()
        
        expires_at = None
        if duration:
            expires_at = datetime.now() + timedelta(seconds=duration)
        
        cursor.execute("""
            INSERT INTO bans (user_id, moderator_id, guild_id, reason, duration, expires_at)
            VALUES (?, ?, ?, ?, ?, ?)
        """, (user_id, moderator_id, guild_id, reason, duration, expires_at))
        
        ban_id = cursor.lastrowid
        
        # Log
        ban_type = "temporaneo" if duration else "permanente"
        self._add_log(cursor, "BAN", user_id, moderator_id, guild_id,
                     f"Ban {ban_type}: {reason or 'Nessun motivo'}")
        
        conn.commit()
        conn.close()
        return ban_id
    
    def remove_ban(self, user_id: int, guild_id: int) -> bool:
        """Rimuove un ban (setta active = 0)"""
        conn = self._get_connection()
        cursor = conn.cursor()
        
        cursor.execute("""
            UPDATE bans SET active = 0 
            WHERE user_id = ? AND guild_id = ? AND active = 1
        """, (user_id, guild_id))
        
        removed = cursor.rowcount > 0
        conn.commit()
        conn.close()
        return removed
    
    def get_active_bans(self, guild_id: Optional[int] = None) -> List[Dict]:
        """Ottiene tutti i ban attivi (opzionalmente filtrati per guild)"""
        conn = self._get_connection()
        cursor = conn.cursor()
        
        if guild_id:
            cursor.execute("""
                SELECT * FROM bans 
                WHERE guild_id = ? AND active = 1
                ORDER BY timestamp DESC
            """, (guild_id,))
        else:
            cursor.execute("""
                SELECT * FROM bans 
                WHERE active = 1
                ORDER BY timestamp DESC
            """)
        
        bans = [dict(row) for row in cursor.fetchall()]
        conn.close()
        return bans
    
    # ===== MUTES =====
    
    def add_mute(self, user_id: int, moderator_id: int, guild_id: int,
                 reason: Optional[str] = None, duration: Optional[int] = None) -> int:
        """Aggiunge un mute (duration in secondi, None = permanente)"""
        conn = self._get_connection()
        cursor = conn.cursor()
        
        expires_at = None
        if duration:
            expires_at = datetime.now() + timedelta(seconds=duration)
        
        cursor.execute("""
            INSERT INTO mutes (user_id, moderator_id, guild_id, reason, duration, expires_at)
            VALUES (?, ?, ?, ?, ?, ?)
        """, (user_id, moderator_id, guild_id, reason, duration, expires_at))
        
        mute_id = cursor.lastrowid
        
        # Log
        mute_type = "temporaneo" if duration else "permanente"
        self._add_log(cursor, "MUTE", user_id, moderator_id, guild_id,
                     f"Mute {mute_type}: {reason or 'Nessun motivo'}")
        
        conn.commit()
        conn.close()
        return mute_id
    
    def remove_mute(self, user_id: int, guild_id: int) -> bool:
        """Rimuove un mute (setta active = 0)"""
        conn = self._get_connection()
        cursor = conn.cursor()
        
        cursor.execute("""
            UPDATE mutes SET active = 0 
            WHERE user_id = ? AND guild_id = ? AND active = 1
        """, (user_id, guild_id))
        
        removed = cursor.rowcount > 0
        conn.commit()
        conn.close()
        return removed
    
    def get_active_mutes(self, guild_id: Optional[int] = None) -> List[Dict]:
        """Ottiene tutti i mute attivi"""
        conn = self._get_connection()
        cursor = conn.cursor()
        
        if guild_id:
            cursor.execute("""
                SELECT * FROM mutes 
                WHERE guild_id = ? AND active = 1
                ORDER BY timestamp DESC
            """, (guild_id,))
        else:
            cursor.execute("""
                SELECT * FROM mutes 
                WHERE active = 1
                ORDER BY timestamp DESC
            """)
        
        mutes = [dict(row) for row in cursor.fetchall()]
        conn.close()
        return mutes
    
    # ===== KICKS =====
    
    def add_kick(self, user_id: int, moderator_id: int, guild_id: int, 
                 reason: Optional[str] = None) -> int:
        """Aggiunge un kick"""
        conn = self._get_connection()
        cursor = conn.cursor()
        
        cursor.execute("""
            INSERT INTO kicks (user_id, moderator_id, guild_id, reason)
            VALUES (?, ?, ?, ?)
        """, (user_id, moderator_id, guild_id, reason))
        
        kick_id = cursor.lastrowid
        
        # Log
        self._add_log(cursor, "KICK", user_id, moderator_id, guild_id,
                     f"Kick: {reason or 'Nessun motivo'}")
        
        conn.commit()
        conn.close()
        return kick_id
    
    # ===== UTILITIES =====
    
    def _add_log(self, cursor: sqlite3.Cursor, action_type: str, user_id: int, 
                 moderator_id: int, guild_id: int, details: str):
        """Aggiunge un entry nel log di moderazione"""
        cursor.execute("""
            INSERT INTO mod_log (action_type, user_id, moderator_id, guild_id, details)
            VALUES (?, ?, ?, ?, ?)
        """, (action_type, user_id, moderator_id, guild_id, details))
    
    def cleanup_expired(self) -> Dict[str, int]:
        """Rimuove ban e mute scaduti, ritorna conteggi"""
        conn = self._get_connection()
        cursor = conn.cursor()
        now = datetime.now()
        
        # Conta ban scaduti
        cursor.execute("""
            SELECT COUNT(*) as count FROM bans 
            WHERE active = 1 AND expires_at IS NOT NULL AND expires_at <= ?
        """, (now,))
        expired_bans = cursor.fetchone()['count']
        
        # Rimuovi ban scaduti
        cursor.execute("""
            UPDATE bans SET active = 0 
            WHERE active = 1 AND expires_at IS NOT NULL AND expires_at <= ?
        """, (now,))
        
        # Conta mute scaduti
        cursor.execute("""
            SELECT COUNT(*) as count FROM mutes 
            WHERE active = 1 AND expires_at IS NOT NULL AND expires_at <= ?
        """, (now,))
        expired_mutes = cursor.fetchone()['count']
        
        # Rimuovi mute scaduti
        cursor.execute("""
            UPDATE mutes SET active = 0 
            WHERE active = 1 AND expires_at IS NOT NULL AND expires_at <= ?
        """, (now,))
        
        conn.commit()
        conn.close()
        
        return {"bans": expired_bans, "mutes": expired_mutes}
    
    def get_user_history(self, user_id: int, guild_id: int) -> Dict[str, Any]:
        """Ottiene tutto lo storico di moderazione di un utente"""
        return {
            "warns": self.get_user_warns(user_id, guild_id),
            "bans": self._get_user_bans(user_id, guild_id),
            "mutes": self._get_user_mutes(user_id, guild_id),
            "kicks": self._get_user_kicks(user_id, guild_id)
        }
    
    def _get_user_bans(self, user_id: int, guild_id: int) -> List[Dict]:
        """Ottiene tutti i ban di un utente"""
        conn = self._get_connection()
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT * FROM bans 
            WHERE user_id = ? AND guild_id = ?
            ORDER BY timestamp DESC
        """, (user_id, guild_id))
        
        bans = [dict(row) for row in cursor.fetchall()]
        conn.close()
        return bans
    
    def _get_user_mutes(self, user_id: int, guild_id: int) -> List[Dict]:
        """Ottiene tutti i mute di un utente"""
        conn = self._get_connection()
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT * FROM mutes 
            WHERE user_id = ? AND guild_id = ?
            ORDER BY timestamp DESC
        """, (user_id, guild_id))
        
        mutes = [dict(row) for row in cursor.fetchall()]
        conn.close()
        return mutes
    
    def _get_user_kicks(self, user_id: int, guild_id: int) -> List[Dict]:
        """Ottiene tutti i kick di un utente"""
        conn = self._get_connection()
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT * FROM kicks 
            WHERE user_id = ? AND guild_id = ?
            ORDER BY timestamp DESC
        """, (user_id, guild_id))
        
        kicks = [dict(row) for row in cursor.fetchall()]
        conn.close()
        return kicks
