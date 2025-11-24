import customtkinter as ctk
import threading
import time
import psutil
from datetime import datetime
import sys
import queue
import os
import json
from utils.language_manager import get_text

# Configurazione Colori - Palette "Super Figa" (Cyberpunk/Modern Dark)
COLORS = {
    "bg_dark": "#0f0f14",       # Background ultra dark
    "bg_sidebar": "#16161e",    # Sidebar
    "card_bg": "#1a1b26",       # Sfondo card
    "card_hover": "#24283b",    # Hover card
    "accent": "#7aa2f7",        # Accento principale (blu neon)
    "text_main": "#c0caf5",     # Testo principale
    "text_dim": "#565f89",      # Testo secondario
    "success": "#9ece6a",       # Verde neon
    "warning": "#e0af68",       # Giallo/Arancio
    "error": "#f7768e",         # Rosso neon
    "disabled": "#414868",      # Grigio disabilitato
    "terminal_bg": "#0c0c0f",   # Sfondo terminale
    "border": "#292e42"         # Bordi sottili
}

class PluginRow(ctk.CTkFrame):
    """Riga compatta per visualizzare lo stato di un plugin nella sidebar"""
    def __init__(self, parent, name, status="disabled", **kwargs):
        super().__init__(parent, fg_color="transparent", **kwargs)
        
        self.status = status
        self.name = name
        
        # Layout interno
        self.grid_columnconfigure(1, weight=1)
        
        # Indicatore di stato (Pallino colorato)
        self.status_indicator = ctk.CTkLabel(
            self,
            text="●",
            font=("Arial", 16),
            text_color=self.get_status_color(status),
            width=20
        )
        self.status_indicator.grid(row=0, column=0, padx=(5, 5), pady=2)
        
        # Nome Plugin
        self.name_lbl = ctk.CTkLabel(
            self,
            text=name.capitalize(),
            font=("Roboto", 12),
            text_color=COLORS["text_main"]
        )
        self.name_lbl.grid(row=0, column=1, sticky="w", padx=0, pady=2)
        
    def get_status_color(self, status):
        if status == "active": return COLORS["success"]
        if status == "error": return COLORS["error"]
        return COLORS["disabled"]

    def update_status(self, status):
        self.status = status
        color = self.get_status_color(status)
        self.status_indicator.configure(text_color=color)

class StatCard(ctk.CTkFrame):
    """Card personalizzata per le statistiche"""
    def __init__(self, parent, title, icon, color, **kwargs):
        super().__init__(parent, fg_color=COLORS["card_bg"], corner_radius=15, border_width=1, border_color=COLORS["border"], **kwargs)
        
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
        
        # Progress Bar decorativa
        self.progress = ctk.CTkProgressBar(self, height=4, progress_color=color, fg_color=COLORS["bg_dark"])
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
        self.plugin_rows = {}
        
        # Configurazione Finestra
        self.title("🚀 Discord Bot Manager Pro")
        self.geometry("1200x800")
        ctk.set_appearance_mode("Dark")
        
        # Layout Principale
        self.grid_columnconfigure(1, weight=1)
        self.grid_rowconfigure(0, weight=1)
        
        # --- SIDEBAR ---
        self.sidebar = ctk.CTkFrame(self, width=260, corner_radius=0, fg_color=COLORS["bg_sidebar"])
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
        
        # Carica stato iniziale plugin
        self.load_initial_plugins()
        
    def setup_sidebar(self):
        # Logo Area
        logo_frame = ctk.CTkFrame(self.sidebar, fg_color="transparent")
        logo_frame.pack(pady=(30, 10), padx=20, fill="x")
        
        ctk.CTkLabel(logo_frame, text="⚡ FLEXCORE", font=("Roboto", 20, "bold"), text_color=COLORS["accent"]).pack()
        ctk.CTkLabel(logo_frame, text="MANAGER v2.0", font=("Roboto", 10, "bold"), text_color=COLORS["text_dim"]).pack()
        
        # Separatore
        ctk.CTkFrame(self.sidebar, height=1, fg_color=COLORS["border"]).pack(fill="x", padx=20, pady=15)
        
        # Info Bot Compresse
        self.info_container = ctk.CTkFrame(self.sidebar, fg_color="transparent")
        self.info_container.pack(padx=20, fill="x")
        
        self.lbl_bot_name = self.create_compact_info("🤖", "Bot", "Loading...")
        self.lbl_bot_id = self.create_compact_info("🆔", "ID", "...")
        self.lbl_servers = self.create_compact_info("🏰", "Servers", "...")
        
        # Separatore Plugin
        ctk.CTkFrame(self.sidebar, height=1, fg_color=COLORS["border"]).pack(fill="x", padx=20, pady=15)
        
        # Plugin List Header
        ctk.CTkLabel(
            self.sidebar, 
            text="PLUGINS", 
            font=("Roboto", 11, "bold"),
            text_color=COLORS["text_dim"]
        ).pack(anchor="w", padx=25, pady=(0, 5))
        
        # Plugin List Container (Scrollable)
        self.plugin_scroll = ctk.CTkScrollableFrame(
            self.sidebar, 
            fg_color="transparent",
            height=300
        )
        self.plugin_scroll.pack(fill="both", expand=True, padx=10, pady=(0, 10))
        
        # Pulsanti Footer
        footer = ctk.CTkFrame(self.sidebar, fg_color="transparent")
        footer.pack(side="bottom", fill="x", padx=20, pady=20)
        
        self.btn_store = ctk.CTkButton(
            footer, 
            text=f"🛒 {get_text('ui.store.title')}",
            font=("Roboto", 12, "bold"),
            fg_color=COLORS["accent"], 
            hover_color="#5a82d8",
            height=35,
            corner_radius=6,
            command=self.open_store
        )
        self.btn_store.pack(fill="x", pady=(0, 8))
        
        self.btn_restart = ctk.CTkButton(
            footer, 
            text="RIAVVIA",
            font=("Roboto", 12, "bold"),
            fg_color=COLORS["warning"], 
            hover_color="#d35400",
            height=35,
            corner_radius=6,
            command=self.restart_bot_action
        )
        self.btn_restart.pack(fill="x", pady=(0, 8))
        
        self.btn_stop = ctk.CTkButton(
            footer, 
            text="ARRESTA",
            font=("Roboto", 12, "bold"),
            fg_color=COLORS["error"], 
            hover_color="#c0392b",
            height=35,
            corner_radius=6,
            command=self.on_close
        )
        self.btn_stop.pack(fill="x")

    def create_compact_info(self, icon, label, value):
        row = ctk.CTkFrame(self.info_container, fg_color="transparent")
        row.pack(fill="x", pady=2)
        
        ctk.CTkLabel(row, text=icon, font=("Segoe UI Emoji", 14), width=25).pack(side="left")
        ctk.CTkLabel(row, text=label, font=("Roboto", 11, "bold"), text_color=COLORS["text_dim"], width=50, anchor="w").pack(side="left")
        
        lbl = ctk.CTkLabel(row, text=value, font=("Roboto", 11), text_color=COLORS["text_main"], anchor="w")
        lbl.pack(side="left", fill="x", expand=True)
        return lbl

    def setup_main_content(self):
        # Header
        header = ctk.CTkFrame(self.main_frame, fg_color="transparent")
        header.grid(row=0, column=0, sticky="ew", padx=30, pady=(20, 10))
        
        ctk.CTkLabel(
            header, 
            text="Dashboard", 
            font=("Roboto", 24, "bold"),
            text_color=COLORS["text_main"]
        ).pack(side="left")
        
        self.status_badge = ctk.CTkLabel(
            header,
            text=f"● {get_text('ui.status.starting')}",
            font=("Roboto", 12, "bold"),
            text_color=COLORS["warning"],
            fg_color=COLORS["card_bg"],
            corner_radius=20,
            width=120,
            height=28
        )
        self.status_badge.pack(side="right")
        
        # Stats Grid
        stats_grid = ctk.CTkFrame(self.main_frame, fg_color="transparent")
        stats_grid.grid(row=1, column=0, sticky="ew", padx=30, pady=(10, 20))
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
        log_container = ctk.CTkFrame(self.main_frame, fg_color=COLORS["terminal_bg"], corner_radius=10, border_width=1, border_color=COLORS["border"])
        log_container.grid(row=2, column=0, sticky="nsew", padx=30, pady=(0, 30))
        log_container.grid_rowconfigure(1, weight=1)
        log_container.grid_columnconfigure(0, weight=1)
        
        # Log Header
        log_header = ctk.CTkFrame(log_container, fg_color="#1e1e2e", corner_radius=10, height=30)
        log_header.grid(row=0, column=0, sticky="ew", padx=1, pady=1)
        
        ctk.CTkLabel(
            log_header, 
            text=" TERMINAL ", 
            font=("Consolas", 10, "bold"),
            text_color=COLORS["text_dim"],
            fg_color="transparent"
        ).pack(side="left", padx=10)
        
        # Log Box
        self.log_box = ctk.CTkTextbox(
            log_container, 
            font=("Consolas", 11),
            fg_color=COLORS["terminal_bg"],
            text_color="#dcdfe4", # Colore base console più chiaro
            corner_radius=0,
            activate_scrollbars=True,
            border_width=0
        )
        self.log_box.grid(row=1, column=0, sticky="nsew", padx=5, pady=5)
        self.log_box.configure(state="disabled")

    def load_initial_plugins(self):
        """Carica i plugin dal file config per mostrare lo stato iniziale"""
        try:
            config_path = os.path.join("config", "plugins.json")
            if os.path.exists(config_path):
                with open(config_path, 'r') as f:
                    plugins_config = json.load(f)
                for name, enabled in plugins_config.items():
                    status = "disabled" if not enabled else "active"
                    self.add_plugin_row(name, status)
        except Exception as e:
            print(f"Error loading initial plugins: {e}")

    def add_plugin_row(self, name, status):
        row = PluginRow(self.plugin_scroll, name, status)
        row.pack(fill="x", padx=5, pady=2)
        self.plugin_rows[name] = row

    def update_plugins_view(self, plugins_data):
        """Aggiorna lo stato dei plugin ricevuto dal bot"""
        for name, status in plugins_data.items():
            if name in self.plugin_rows:
                self.plugin_rows[name].update_status(status)
            else:
                self.add_plugin_row(name, status)

    def update_stats(self):
        if self.stop_event.is_set(): return
        cpu = psutil.cpu_percent()
        ram = psutil.virtual_memory().percent
        self.card_cpu.update_value(f"{cpu}%", cpu/100)
        self.card_ram.update_value(f"{ram}%", ram/100)
        self.after(1000, self.update_stats)

    def check_queue(self):
        try:
            while True:
                msg_type, data = self.bot_queue.get_nowait()
                if msg_type == "log": self.append_log(data)
                elif msg_type == "stats": self.update_bot_stats(data)
                elif msg_type == "info": self.update_bot_info(data)
                elif msg_type == "plugins_status": self.update_plugins_view(data)
                elif msg_type == "status":
                    if data == "online": self.status_badge.configure(text=f"● {get_text('ui.status.online')}", text_color=COLORS["success"])
                    elif data == "offline": self.status_badge.configure(text=f"● {get_text('ui.status.offline')}", text_color=COLORS["error"])
        except queue.Empty: pass
        if not self.stop_event.is_set(): self.after(100, self.check_queue)

    def append_log(self, text):
        self.log_box.configure(state="normal")
        
        # Mappa colori ANSI -> Colori Hex Console-Like
        ansi_colors = {
            "\033[0m": "reset",
            "\033[1m": "bold",
            "\033[91m": "#ff5555", # Rosso acceso
            "\033[92m": "#50fa7b", # Verde acceso
            "\033[93m": "#f1fa8c", # Giallo acceso
            "\033[94m": "#bd93f9", # Viola/Blu (Dracula theme style)
            "\033[95m": "#ff79c6", # Rosa
            "\033[96m": "#8be9fd", # Ciano
            "\033[90m": "#6272a4", # Grigio commento
        }
        
        for code, color in ansi_colors.items():
            if color != "reset" and color != "bold":
                self.log_box.tag_config(color, foreground=color)
        
        parts = text.split("\033[")
        if parts[0]: self.log_box.insert("end", parts[0] + "\n")
            
        current_tag = None
        for part in parts[1:]:
            if "m" in part:
                code_suffix, content = part.split("m", 1)
                full_code = f"\033[{code_suffix}m"
                color = ansi_colors.get(full_code)
                if color == "reset": current_tag = None
                elif color == "bold": pass
                elif color: current_tag = color
                if content:
                    if current_tag: self.log_box.insert("end", content, current_tag)
                    else: self.log_box.insert("end", content)
            else: self.log_box.insert("end", part)
        
        self.log_box.insert("end", "\n")
        self.log_box.see("end")
        self.log_box.configure(state="disabled")

    def update_bot_stats(self, stats):
        if "ping" in stats: self.card_ping.update_value(f"{stats['ping']}ms", min(stats['ping']/500, 1))
        if "uptime" in stats: self.card_uptime.update_value(stats['uptime'], 1)

    def update_bot_info(self, info):
        if "name" in info: self.lbl_bot_name.configure(text=info['name'])
        if "id" in info: self.lbl_bot_id.configure(text=str(info['id']))
        if "servers" in info: self.lbl_servers.configure(text=str(info['servers']))
    
    def open_store(self):
        PluginStoreWindow(self)

    def show_error_popup(self, title, message):
        error_window = ctk.CTkToplevel(self)
        error_window.title(f"❌ {title}")
        error_window.geometry("600x500")
        error_window.resizable(False, False)
        error_window.lift()
        error_window.focus_force()
        error_window.grab_set()
        
        header = ctk.CTkFrame(error_window, fg_color=COLORS["error"], height=80)
        header.pack(fill="x", padx=0, pady=0)
        header.pack_propagate(False)
        ctk.CTkLabel(header, text="⚠️", font=("Segoe UI Emoji", 48)).pack(pady=15)
        
        title_frame = ctk.CTkFrame(error_window, fg_color="transparent")
        title_frame.pack(fill="x", padx=30, pady=(20, 10))
        ctk.CTkLabel(title_frame, text=title, font=("Roboto", 20, "bold"), text_color=COLORS["error"]).pack()
        
        msg_frame = ctk.CTkFrame(error_window, fg_color=COLORS["card_bg"], corner_radius=10)
        msg_frame.pack(fill="both", expand=True, padx=30, pady=(0, 20))
        msg_box = ctk.CTkTextbox(msg_frame, font=("Roboto", 12), fg_color=COLORS["card_bg"], text_color=COLORS["text_main"], wrap="word", activate_scrollbars=True)
        msg_box.pack(fill="both", expand=True, padx=15, pady=15)
        msg_box.insert("1.0", message)
        msg_box.configure(state="disabled")
        
        btn_frame = ctk.CTkFrame(error_window, fg_color="transparent")
        btn_frame.pack(fill="x", padx=30, pady=(0, 20))
        ctk.CTkButton(btn_frame, text=get_text('ui.error_popup.button'), font=("Roboto", 14, "bold"), fg_color=COLORS["error"], hover_color="#c0392b", height=50, command=lambda: [error_window.destroy(), self.on_close()]).pack(fill="x")

    def restart_bot_action(self):
        self.append_log("🔄 Riavvio del sistema in corso...")
        self.btn_restart.configure(state="disabled")
        self.after(1000, self._perform_restart)

    def _perform_restart(self):
        self.stop_event.set()
        self.destroy()
        import os
        import subprocess
        script_path = os.path.abspath("bot.py")
        args = [sys.executable, script_path]
        if len(sys.argv) > 1: args.extend(sys.argv[1:])
        if os.name == 'nt': subprocess.Popen(args, creationflags=subprocess.CREATE_NEW_CONSOLE)
        else: subprocess.Popen(args)
        sys.exit(0)

    def on_close(self):
        self.stop_event.set()
        self.destroy()
        sys.exit(0)

class PluginStoreWindow(ctk.CTkToplevel):
    def __init__(self, parent):
        super().__init__(parent)
        self.title(f"🛒 {get_text('ui.store.title')}")
        self.geometry("800x600")
        self.resizable(False, False)
        self.lift()
        self.focus_force()
        self.grab_set()
        
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(1, weight=1)
        
        # Header
        header = ctk.CTkFrame(self, fg_color="transparent")
        header.grid(row=0, column=0, sticky="ew", padx=20, pady=20)
        
        ctk.CTkLabel(
            header, 
            text=get_text('ui.store.browse'), 
            font=("Roboto", 24, "bold"),
            text_color=COLORS["text_main"]
        ).pack(side="left")
        
        self.status_lbl = ctk.CTkLabel(header, text="", font=("Roboto", 12), text_color=COLORS["text_dim"])
        self.status_lbl.pack(side="right")
        
        # List Container
        self.scroll_frame = ctk.CTkScrollableFrame(self, fg_color="transparent")
        self.scroll_frame.grid(row=1, column=0, sticky="nsew", padx=20, pady=(0, 20))
        self.scroll_frame.grid_columnconfigure(0, weight=1)
        
        # Loading
        self.loading_lbl = ctk.CTkLabel(self.scroll_frame, text="Loading...", font=("Roboto", 16))
        self.loading_lbl.pack(pady=50)
        
        # Start fetch in thread
        threading.Thread(target=self.fetch_plugins, daemon=True).start()
        
    def fetch_plugins(self):
        from utils.plugin_installer import PluginInstaller
        plugins = PluginInstaller.get_available_plugins()
        self.after(0, lambda: self.show_plugins(plugins))
        
    def show_plugins(self, plugins):
        self.loading_lbl.destroy()
        
        if not plugins:
            ctk.CTkLabel(self.scroll_frame, text=get_text('ui.store.empty'), font=("Roboto", 16)).pack(pady=50)
            return
            
        from utils.plugin_installer import PluginInstaller
        
        for p in plugins:
            self.create_plugin_row(p, PluginInstaller.is_installed(p['name']))
            
    def create_plugin_row(self, plugin_data, is_installed):
        row = ctk.CTkFrame(self.scroll_frame, fg_color=COLORS["card_bg"], corner_radius=10)
        row.pack(fill="x", pady=5)
        
        # Icon & Name
        info_frame = ctk.CTkFrame(row, fg_color="transparent")
        info_frame.pack(side="left", padx=15, pady=15)
        
        ctk.CTkLabel(info_frame, text="📦", font=("Segoe UI Emoji", 24)).pack(side="left", padx=(0, 10))
        
        text_frame = ctk.CTkFrame(info_frame, fg_color="transparent")
        text_frame.pack(side="left")
        
        name = plugin_data['name'].replace('.py', '').capitalize()
        ctk.CTkLabel(text_frame, text=name, font=("Roboto", 16, "bold"), text_color=COLORS["text_main"]).pack(anchor="w")
        ctk.CTkLabel(text_frame, text=f"{plugin_data['size']} bytes", font=("Roboto", 11), text_color=COLORS["text_dim"]).pack(anchor="w")
        
        # Action Button
        btn_text = get_text('ui.store.installed') if is_installed else get_text('ui.store.install')
        btn_color = COLORS["success"] if is_installed else COLORS["accent"]
        btn_state = "disabled" if is_installed else "normal"
        
        # Se installato, permetti aggiornamento (opzionale, per ora disabilitato se installato)
        if is_installed:
             btn_text = get_text('ui.store.reinstall')
             btn_color = COLORS["warning"]
             btn_state = "normal"
        
        btn = ctk.CTkButton(
            row,
            text=btn_text,
            font=("Roboto", 12, "bold"),
            fg_color=btn_color,
            width=100,
            height=35,
            state=btn_state
        )
        btn.configure(command=lambda b=btn, p=plugin_data: self.install_action(b, p))
        btn.pack(side="right", padx=15)

    def install_action(self, btn, plugin_data):
        btn.configure(state="disabled", text=get_text('ui.store.downloading'))
        threading.Thread(target=self._run_install, args=(btn, plugin_data), daemon=True).start()
        
    def _run_install(self, btn, plugin_data):
        from utils.plugin_installer import PluginInstaller
        success = PluginInstaller.install_plugin(plugin_data)
        self.after(0, lambda: self._post_install(btn, success))
        
    def _post_install(self, btn, success):
        if success:
            btn.configure(text=get_text('ui.store.success'), fg_color=COLORS["success"])
        else:
            btn.configure(text=get_text('ui.store.error'), fg_color=COLORS["error"], state="normal")

def run_ui(bot_queue, stop_event):
    from utils.config_validator import ConfigValidator
    app = BotDashboard(bot_queue, stop_event)
    if ConfigValidator.last_error:
        app.after(100, lambda: app.show_error_popup(ConfigValidator.last_error["title"], ConfigValidator.last_error["message"]))
    app.mainloop()
