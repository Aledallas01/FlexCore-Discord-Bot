import customtkinter as ctk
import threading
import time
import psutil
from datetime import datetime
import sys
import queue
import os

# Configurazione Colori
COLORS = {
    "bg_dark": "#1a1b26",       # Background principale
    "bg_sidebar": "#16161e",    # Sidebar
    "card_bg": "#24283b",       # Sfondo card
    "accent": "#7aa2f7",        # Accento principale (blu)
    "text_main": "#c0caf5",     # Testo principale
    "text_dim": "#565f89",      # Testo secondario
    "success": "#9ece6a",       # Verde
    "warning": "#e0af68",       # Giallo/Arancio
    "error": "#f7768e",         # Rosso
    "terminal_bg": "#0f0f14"    # Sfondo terminale
}

class StatCard(ctk.CTkFrame):
    """Card personalizzata per le statistiche"""
    def __init__(self, parent, title, icon, color, **kwargs):
        super().__init__(parent, fg_color=COLORS["card_bg"], corner_radius=15, border_width=1, border_color=COLORS["bg_sidebar"], **kwargs)
        
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(1, weight=1)
        
        # Header con Icona e Titolo
        header = ctk.CTkFrame(self, fg_color="transparent")
        header.grid(row=0, column=0, sticky="ew", padx=15, pady=(15, 5))
        
        # Icona colorata
        icon_lbl = ctk.CTkLabel(
            header, 
            text=icon, 
            font=("Segoe UI Emoji", 24),
            text_color=color
        )
        icon_lbl.pack(side="left")
        
        # Titolo
        title_lbl = ctk.CTkLabel(
            header, 
            text=title.upper(), 
            font=("Roboto Medium", 11),
            text_color=COLORS["text_dim"]
        )
        title_lbl.pack(side="left", padx=10)
        
        # Valore
        self.value_lbl = ctk.CTkLabel(
            self, 
            text="...", 
            font=("Roboto", 28, "bold"),
            text_color=COLORS["text_main"]
        )
        self.value_lbl.grid(row=1, column=0, sticky="w", padx=20, pady=(0, 15))
        
        # Progress Bar decorativa (opzionale)
        self.progress = ctk.CTkProgressBar(self, height=4, progress_color=color)
        self.progress.grid(row=2, column=0, sticky="ew", padx=20, pady=(0, 20))
        self.progress.set(0)

    def update_value(self, value, progress=None):
        self.value_lbl.configure(text=value)
        if progress is not None:
            self.progress.set(progress)

class BotDashboard(ctk.CTk):
    def __init__(self, bot_queue, stop_event):
        super().__init__()
        
        self.bot_queue = bot_queue
        self.stop_event = stop_event
        
        # Configurazione Finestra
        self.title("🚀 Discord Bot Manager Pro")
        self.geometry("1100x750")
        ctk.set_appearance_mode("Dark")
        
        # Layout Principale
        self.grid_columnconfigure(1, weight=1)
        self.grid_rowconfigure(0, weight=1)
        
        # --- SIDEBAR ---
        self.sidebar = ctk.CTkFrame(self, width=280, corner_radius=0, fg_color=COLORS["bg_sidebar"])
        self.sidebar.grid(row=0, column=0, sticky="nsew")
        self.sidebar.grid_propagate(False)
        self.setup_sidebar()
        
        # --- MAIN CONTENT ---
        self.main_frame = ctk.CTkFrame(self, corner_radius=0, fg_color=COLORS["bg_dark"])
        self.main_frame.grid(row=0, column=1, sticky="nsew")
        self.main_frame.grid_columnconfigure(0, weight=1)
        self.main_frame.grid_rowconfigure(2, weight=1) # Log espandibile
        self.setup_main_content()
        
        # Start Loop
        self.update_stats()
        self.check_queue()
        self.protocol("WM_DELETE_WINDOW", self.on_close)
        
    def setup_sidebar(self):
        # Logo Area
        logo_frame = ctk.CTkFrame(self.sidebar, fg_color="transparent")
        logo_frame.pack(pady=(40, 20), padx=20, fill="x")
        
        ctk.CTkLabel(
            logo_frame, 
            text="⚡", 
            font=("Segoe UI Emoji", 48)
        ).pack()
        
        ctk.CTkLabel(
            logo_frame, 
            text="BOT MANAGER", 
            font=("Roboto", 20, "bold"),
            text_color=COLORS["text_main"]
        ).pack(pady=(10, 0))
        
        ctk.CTkLabel(
            logo_frame, 
            text="v1.0", 
            font=("Roboto", 12),
            text_color=COLORS["text_dim"]
        ).pack()
        
        # Separatore
        ctk.CTkFrame(self.sidebar, height=2, fg_color=COLORS["card_bg"]).pack(fill="x", padx=30, pady=20)
        
        # Info Bot Container
        self.info_container = ctk.CTkFrame(self.sidebar, fg_color=COLORS["card_bg"], corner_radius=10)
        self.info_container.pack(padx=20, fill="x")
        
        self.lbl_bot_name = self.create_sidebar_info("🤖", "Bot Name", "Loading...")
        self.lbl_bot_id = self.create_sidebar_info("🆔", "Bot ID", "...")
        self.lbl_servers = self.create_sidebar_info("🏰", "Servers", "...")
        
        # Pulsanti Footer
        footer = ctk.CTkFrame(self.sidebar, fg_color="transparent")
        footer.pack(side="bottom", fill="x", padx=20, pady=30)
        
        self.btn_restart = ctk.CTkButton(
            footer, 
            text="RIAVVIA SISTEMA",
            font=("Roboto", 12, "bold"),
            fg_color=COLORS["warning"], 
            hover_color="#d35400",
            height=40,
            corner_radius=8,
            command=self.restart_bot_action
        )
        self.btn_restart.pack(fill="x", pady=(0, 10))
        
        self.btn_stop = ctk.CTkButton(
            footer, 
            text="ARRESTA TUTTO",
            font=("Roboto", 12, "bold"),
            fg_color=COLORS["error"], 
            hover_color="#c0392b",
            height=40,
            corner_radius=8,
            command=self.on_close
        )
        self.btn_stop.pack(fill="x")

    def create_sidebar_info(self, icon, label, value):
        row = ctk.CTkFrame(self.info_container, fg_color="transparent")
        row.pack(fill="x", padx=15, pady=12)
        
        ctk.CTkLabel(row, text=icon, font=("Segoe UI Emoji", 16)).pack(side="left")
        
        text_frame = ctk.CTkFrame(row, fg_color="transparent")
        text_frame.pack(side="left", padx=10)
        
        ctk.CTkLabel(
            text_frame, 
            text=label.upper(), 
            font=("Roboto", 9, "bold"), 
            text_color=COLORS["text_dim"]
        ).pack(anchor="w")
        
        lbl = ctk.CTkLabel(
            text_frame, 
            text=value, 
            font=("Roboto", 13), 
            text_color=COLORS["text_main"]
        )
        lbl.pack(anchor="w")
        return lbl

    def setup_main_content(self):
        # Header
        header = ctk.CTkFrame(self.main_frame, fg_color="transparent")
        header.grid(row=0, column=0, sticky="ew", padx=30, pady=(30, 20))
        
        ctk.CTkLabel(
            header, 
            text="Dashboard Monitoraggio", 
            font=("Roboto", 24, "bold"),
            text_color=COLORS["text_main"]
        ).pack(side="left")
        
        self.status_badge = ctk.CTkLabel(
            header,
            text="● ONLINE",
            font=("Roboto", 12, "bold"),
            text_color=COLORS["success"],
            fg_color=COLORS["card_bg"],
            corner_radius=20,
            width=100,
            height=30
        )
        self.status_badge.pack(side="right")
        
        # Stats Grid
        stats_grid = ctk.CTkFrame(self.main_frame, fg_color="transparent")
        stats_grid.grid(row=1, column=0, sticky="ew", padx=30, pady=(0, 30))
        stats_grid.grid_columnconfigure((0,1,2,3), weight=1)
        
        self.card_cpu = StatCard(stats_grid, "CPU Load", "🔥", COLORS["error"])
        self.card_cpu.grid(row=0, column=0, padx=(0, 10), sticky="ew")
        
        self.card_ram = StatCard(stats_grid, "RAM Usage", "💾", COLORS["accent"])
        self.card_ram.grid(row=0, column=1, padx=10, sticky="ew")
        
        self.card_ping = StatCard(stats_grid, "Latency", "⚡", COLORS["success"])
        self.card_ping.grid(row=0, column=2, padx=10, sticky="ew")
        
        self.card_uptime = StatCard(stats_grid, "Uptime", "⏱️", COLORS["warning"])
        self.card_uptime.grid(row=0, column=3, padx=(10, 0), sticky="ew")
        
        # Console Log Area
        log_container = ctk.CTkFrame(self.main_frame, fg_color=COLORS["card_bg"], corner_radius=15)
        log_container.grid(row=2, column=0, sticky="nsew", padx=30, pady=(0, 30))
        log_container.grid_rowconfigure(1, weight=1)
        log_container.grid_columnconfigure(0, weight=1)
        
        # Log Header
        log_header = ctk.CTkFrame(log_container, fg_color="transparent")
        log_header.grid(row=0, column=0, sticky="ew", padx=20, pady=15)
        
        ctk.CTkLabel(
            log_header, 
            text="TERMINAL LOGS", 
            font=("Roboto Mono", 12, "bold"),
            text_color=COLORS["text_dim"]
        ).pack(side="left")
        
        # Log Box
        self.log_box = ctk.CTkTextbox(
            log_container, 
            font=("Consolas", 12),
            fg_color=COLORS["terminal_bg"],
            text_color=COLORS["text_main"],
            corner_radius=10,
            activate_scrollbars=True
        )
        self.log_box.grid(row=1, column=0, sticky="nsew", padx=20, pady=(0, 20))
        self.log_box.configure(state="disabled")

    def update_stats(self):
        if self.stop_event.is_set():
            return
            
        # CPU & RAM
        cpu = psutil.cpu_percent()
        ram = psutil.virtual_memory().percent
        
        self.card_cpu.update_value(f"{cpu}%", cpu/100)
        self.card_ram.update_value(f"{ram}%", ram/100)
        
        self.after(1000, self.update_stats)

    def check_queue(self):
        try:
            while True:
                msg_type, data = self.bot_queue.get_nowait()
                
                if msg_type == "log":
                    self.append_log(data)
                elif msg_type == "stats":
                    self.update_bot_stats(data)
                elif msg_type == "info":
                    self.update_bot_info(data)
                    
        except queue.Empty:
            pass
        
        if not self.stop_event.is_set():
            self.after(100, self.check_queue)

    def append_log(self, text):
        self.log_box.configure(state="normal")
        
        # Mappa colori ANSI -> Colori Hex
        ansi_colors = {
            "\033[0m": "reset",
            "\033[1m": "bold",
            "\033[91m": "#f7768e", # Rosso
            "\033[92m": "#9ece6a", # Verde
            "\033[93m": "#e0af68", # Giallo
            "\033[94m": "#7aa2f7", # Blu
            "\033[95m": "#bb9af7", # Magenta
            "\033[96m": "#7dcfff", # Ciano
            "\033[90m": "#565f89", # Grigio
        }
        
        # Configura tag per i colori
        for code, color in ansi_colors.items():
            if color != "reset" and color != "bold":
                self.log_box.tag_config(color, foreground=color)
        
        # Parsing testo
        parts = text.split("\033[")
        
        # Prima parte (senza codice colore iniziale)
        if parts[0]:
            self.log_box.insert("end", parts[0] + "\n")
            
        current_tag = None
        
        for part in parts[1:]:
            # Separa codice e testo (es: "92mTesto")
            if "m" in part:
                code_suffix, content = part.split("m", 1)
                full_code = f"\033[{code_suffix}m"
                
                color = ansi_colors.get(full_code)
                
                if color == "reset":
                    current_tag = None
                elif color == "bold":
                    pass # Ignora bold per ora
                elif color:
                    current_tag = color
                
                if content:
                    if current_tag:
                        self.log_box.insert("end", content, current_tag)
                    else:
                        self.log_box.insert("end", content)
            else:
                self.log_box.insert("end", part)
        
        self.log_box.insert("end", "\n")
        self.log_box.see("end")
        self.log_box.configure(state="disabled")

    def update_bot_stats(self, stats):
        if "ping" in stats:
            self.card_ping.update_value(f"{stats['ping']}ms", min(stats['ping']/500, 1))
        if "uptime" in stats:
            self.card_uptime.update_value(stats['uptime'], 1)

    def update_bot_info(self, info):
        if "name" in info:
            self.lbl_bot_name.configure(text=info['name'])
        if "id" in info:
             self.lbl_bot_id.configure(text=str(info['id']))
        if "servers" in info:
             self.lbl_servers.configure(text=str(info['servers']))
    
    def show_error_popup(self, title, message):
        """Mostra popup di errore con messaggio dettagliato"""
        # Crea toplevel window
        error_window = ctk.CTkToplevel(self)
        error_window.title(f"❌ {title}")
        error_window.geometry("600x500")
        error_window.resizable(False, False)
        
        # Porta in primo piano
        error_window.lift()
        error_window.focus_force()
        error_window.grab_set()
        
        # Header
        header = ctk.CTkFrame(error_window, fg_color=COLORS["error"], height=80)
        header.pack(fill="x", padx=0, pady=0)
        header.pack_propagate(False)
        
        ctk.CTkLabel(
            header,
            text="⚠️",
            font=("Segoe UI Emoji", 48)
        ).pack(pady=15)
        
        # Titolo
        title_frame = ctk.CTkFrame(error_window, fg_color="transparent")
        title_frame.pack(fill="x", padx=30, pady=(20, 10))
        
        ctk.CTkLabel(
            title_frame,
            text=title,
            font=("Roboto", 20, "bold"),
            text_color=COLORS["error"]
        ).pack()
        
        # Messaggio
        msg_frame = ctk.CTkFrame(error_window, fg_color=COLORS["card_bg"], corner_radius=10)
        msg_frame.pack(fill="both", expand=True, padx=30, pady=(0, 20))
        
        msg_box = ctk.CTkTextbox(
            msg_frame,
            font=("Roboto", 12),
            fg_color=COLORS["card_bg"],
            text_color=COLORS["text_main"],
            wrap="word",
            activate_scrollbars=True
        )
        msg_box.pack(fill="both", expand=True, padx=15, pady=15)
        msg_box.insert("1.0", message)
        msg_box.configure(state="disabled")
        
        # Pulsante Chiudi
        btn_frame = ctk.CTkFrame(error_window, fg_color="transparent")
        btn_frame.pack(fill="x", padx=30, pady=(0, 20))
        
        ctk.CTkButton(
            btn_frame,
            text="CHIUDI E CORREGGI CONFIG",
            font=("Roboto", 14, "bold"),
            fg_color=COLORS["error"],
            hover_color="#c0392b",
            height=50,
            command=lambda: [error_window.destroy(), self.on_close()]
        ).pack(fill="x")

    def restart_bot_action(self):
        self.append_log("🔄 Riavvio del sistema in corso...")
        self.btn_restart.configure(state="disabled")
        self.after(1000, self._perform_restart)

    def _perform_restart(self):
        self.stop_event.set()
        self.destroy()
        
        # Ottieni path assoluto dello script
        import os
        import subprocess
        
        # Determina lo script da lanciare (bot.py)
        # Se siamo in un eseguibile compilato (es. pyinstaller), sys.argv[0] è l'exe
        # Altrimenti cerchiamo bot.py nella directory corrente
        script_path = os.path.abspath("bot.py")
        
        args = [sys.executable, script_path]
        
        # Aggiungi eventuali argomenti passati all'avvio originale
        if len(sys.argv) > 1:
            args.extend(sys.argv[1:])
            
        # Lancia nuovo processo
        if os.name == 'nt':
            # CREATE_NEW_CONSOLE (0x10) per staccare il processo dal debugger/terminale che sta chiudendo
            subprocess.Popen(args, creationflags=subprocess.CREATE_NEW_CONSOLE)
        else:
            subprocess.Popen(args)
        
        # Chiude il processo corrente
        sys.exit(0)

    def on_close(self):
        self.stop_event.set()
        self.destroy()
        sys.exit(0)

def run_ui(bot_queue, stop_event):
    """Avvia l'interfaccia UI con controllo errori configurazione"""
    from config_validator import ConfigValidator
    
    app = BotDashboard(bot_queue, stop_event)
    
    # Controlla se c'è un errore di validazione da mostrare
    if ConfigValidator.last_error:
        # Schedule error popup after UI is ready
        app.after(100, lambda: app.show_error_popup(
            ConfigValidator.last_error["title"],
            ConfigValidator.last_error["message"]
        ))
    
    app.mainloop()
