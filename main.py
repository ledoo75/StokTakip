import customtkinter as ctk
from tkinter import ttk, filedialog, messagebox
import sqlite3
from datetime import datetime, timedelta
import os
import sys
import time
import math
import json
import threading
import shutil
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
import webbrowser
import urllib.request

# --- Kütüphane Kontrolleri ---
try:
    import pandas as pd
    HAS_PANDAS = True
except ImportError: HAS_PANDAS = False

try:
    import matplotlib.pyplot as plt
    from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
    from matplotlib.figure import Figure
    HAS_MATPLOTLIB = True
except ImportError: HAS_MATPLOTLIB = False

# ================== AYARLAR & TEMA ==================
ctk.set_appearance_mode("Dark")
ctk.set_default_color_theme("dark-blue")

# --- GÜNCELLEME AYARLARI ---
APP_VERSION = "v14.1 FIX"
UPDATE_URL = "https://raw.githubusercontent.com/SizinKullaniciAdiniz/ProjeAdiniz/main/main.py"

# Varsayılanlar
DEFAULT_DEPOTS = ["ANTREPO", "ANTREPO 2", "ZAFER", "KARE 6"]

# Renk Paleti
COLORS = {
    "bg": "#0B1121",           
    "sidebar": "#111827",      
    "card": "#1F2937",         
    "accent": "#38BDF8",       
    "success": "#34D399",      
    "danger": "#F87171",       
    "warning": "#FBBF24",      
    "text_h1": "#F9FAFB",      
    "text_body": "#E5E7EB",    
    "text_muted": "#9CA3AF",   
    "border": "#374151",
    "critical": "#FF0000"
}

FONTS = {
    "h1": ("Roboto", 32, "bold"),
    "h2": ("Roboto", 24, "bold"),
    "body": ("Arial", 14),
    "bold": ("Arial", 14, "bold"),
}

# Yollar
app_data_path = os.getenv('LOCALAPPDATA') or os.path.expanduser("~")
program_folder = os.path.join(app_data_path, "TanjuPaletProV14")
if not os.path.exists(program_folder): os.makedirs(program_folder, exist_ok=True)

CONFIG_FILE = os.path.join(program_folder, "config.json")
DEFAULT_DB_PATH = os.path.join(program_folder, "database_v14.db")

# ================== AYAR YÖNETİCİSİ ==================
class ConfigManager:
    @staticmethod
    def _load_config():
        if os.path.exists(CONFIG_FILE):
            try:
                with open(CONFIG_FILE, "r") as f:
                    return json.load(f)
            except: return {}
        return {}

    @staticmethod
    def _save_config(data):
        try:
            with open(CONFIG_FILE, "w") as f: json.dump(data, f)
            return True
        except: return False

    @staticmethod
    def get_db_path():
        data = ConfigManager._load_config()
        return data.get("db_path", DEFAULT_DB_PATH)

    @staticmethod
    def set_db_path(path):
        data = ConfigManager._load_config()
        data["db_path"] = path
        return ConfigManager._save_config(data)

    @staticmethod
    def get_creds():
        data = ConfigManager._load_config()
        return data.get("saved_user", ""), data.get("saved_pass", "")

    @staticmethod
    def save_creds(user, password, remember):
        data = ConfigManager._load_config()
        if remember:
            data["saved_user"] = user
            data["saved_pass"] = password
        else:
            data.pop("saved_user", None)
            data.pop("saved_pass", None)
        ConfigManager._save_config(data)
    
    # --- MAIL AYARLARI ---
    @staticmethod
    def get_email_config():
        data = ConfigManager._load_config()
        return {
            "sender": data.get("email_sender", ""),
            "password": data.get("email_password", ""),
            "receivers": data.get("email_receivers", ""),
            "time_h": data.get("email_time_h", "18"),
            "time_m": data.get("email_time_m", "00")
        }

    @staticmethod
    def save_email_config(sender, password, receivers, time_h, time_m):
        data = ConfigManager._load_config()
        data["email_sender"] = sender
        data["email_password"] = password
        data["email_receivers"] = receivers
        data["email_time_h"] = time_h
        data["email_time_m"] = time_m
        ConfigManager._save_config(data)

CURRENT_DB_PATH = ConfigManager.get_db_path()

# ================== VERİTABANI ==================
class DB:
    @staticmethod
    def init():
        try:
            conn = sqlite3.connect(CURRENT_DB_PATH)
            c = conn.cursor()
            c.execute("CREATE TABLE IF NOT EXISTS depots (name TEXT PRIMARY KEY, count INTEGER DEFAULT 0)")
            c.execute("CREATE TABLE IF NOT EXISTS logs (id INTEGER PRIMARY KEY, date TEXT, action TEXT, depot TEXT, qty INTEGER, user TEXT)")
            c.execute("CREATE TABLE IF NOT EXISTS users (name TEXT PRIMARY KEY, pass TEXT, role TEXT DEFAULT 'personel')")
            
            # --- YENİ EKLENEN: SİSTEM DEĞİŞKENLERİ (Mail Kontrolü İçin) ---
            c.execute("CREATE TABLE IF NOT EXISTS system_vars (key TEXT PRIMARY KEY, value TEXT)")
            
            for d in DEFAULT_DEPOTS:
                c.execute("INSERT OR IGNORE INTO depots (name, count) VALUES (?, 0)", (d,))
            
            if c.execute("SELECT count(*) FROM users").fetchone()[0] == 0:
                c.execute("INSERT INTO users (name, pass, role) VALUES (?,?,?)", ("admin", "admin", "admin"))
            
            conn.commit(); conn.close()
            return True
        except Exception as e:
            print(f"DB Init Error: {e}")
            return False

    @staticmethod
    def get_conn(): return sqlite3.connect(CURRENT_DB_PATH)
    
    @staticmethod
    def get_all_depots():
        try:
            conn = DB.get_conn()
            deps = [r[0] for r in conn.cursor().execute("SELECT name FROM depots ORDER BY name").fetchall()]
            conn.close()
            return deps if deps else DEFAULT_DEPOTS
        except: return DEFAULT_DEPOTS

# ================== BİLDİRİM & SPLASH ==================
class ToastNotification(ctk.CTkFrame):
    def __init__(self, master, message, color):
        try:
            if not master.winfo_exists(): return
        except: return
        super().__init__(master, fg_color=color, corner_radius=15, border_width=2, border_color="white")
        self.place(relx=0.98, rely=0.95, anchor="se")
        ctk.CTkLabel(self, text=message, text_color="white", font=("Arial", 15, "bold"), padx=25, pady=15).pack()
        self.after(3000, self.destroy)

class AnimatedSplash(ctk.CTk):
    def __init__(self):
        super().__init__()
        self.overrideredirect(True)
        ws, hs = self.winfo_screenwidth(), self.winfo_screenheight()
        self.geometry(f"600x400+{(ws//2)-300}+{(hs//2)-200}")
        self.configure(fg_color=COLORS["bg"])

        ctk.CTkLabel(self, text="⚡", font=("Arial", 90)).pack(pady=(50, 0))
        ctk.CTkLabel(self, text="TaNjU PRO", font=FONTS["h1"], text_color=COLORS["accent"]).pack()
        ctk.CTkLabel(self, text=f"{APP_VERSION}", font=("Arial", 14, "bold"), text_color=COLORS["text_muted"]).pack(pady=(0, 40))

        self.bar = ctk.CTkProgressBar(self, width=450, height=8, progress_color=COLORS["accent"], fg_color="#333")
        self.bar.pack()
        self.bar.set(0)
        self.info = ctk.CTkLabel(self, text="Sistem başlatılıyor...", font=("Consolas", 11), text_color="gray")
        self.info.pack(pady=10)
        self.after(50, self.run)

    def run(self):
        DB.init()
        steps = ["Veritabanı bağlanıyor...", "Depo listesi güncelleniyor...", "Arayüz oluşturuluyor...", "Hazır!"]
        for i in range(101):
            self.bar.set(i/100)
            if i % 25 == 0 and i < 100: self.info.configure(text=steps[int(i/25)])
            self.update()
            time.sleep(0.015)
        self.destroy()
        LoginWindow().mainloop()

# ================== GİRİŞ EKRANI ==================
class LoginWindow(ctk.CTk):
    def __init__(self):
        super().__init__()
        self.title("Giriş")
        self.geometry("1000x700")
        self.configure(fg_color=COLORS["bg"])
        
        left = ctk.CTkFrame(self, fg_color=COLORS["sidebar"], corner_radius=0)
        left.place(relx=0, rely=0, relwidth=0.4, relheight=1)
        ctk.CTkLabel(left, text="PALET\nTAKİP", font=("Montserrat", 45, "bold"), text_color="white").place(relx=0.5, rely=0.45, anchor="center")
        ctk.CTkLabel(left, text=f"{APP_VERSION}", font=("Arial", 16), text_color="gray").place(relx=0.5, rely=0.55, anchor="center")

        right = ctk.CTkFrame(self, fg_color=COLORS["bg"], corner_radius=0)
        right.place(relx=0.4, rely=0, relwidth=0.6, relheight=1)
        
        box = ctk.CTkFrame(right, fg_color=COLORS["card"], corner_radius=20, width=400, height=550, border_width=1, border_color=COLORS["border"])
        box.place(relx=0.5, rely=0.5, anchor="center")
        
        ctk.CTkLabel(box, text="GİRİŞ YAP", font=FONTS["h2"], text_color=COLORS["text_h1"]).pack(pady=(40,10))
        ctk.CTkLabel(box, text="TJ", font=("Arial Black", 16), text_color=COLORS["accent"]).pack(pady=(0,20))

        self.user = ctk.CTkEntry(box, placeholder_text="Kullanıcı Adı", width=300, height=55, font=FONTS["body"])
        self.user.pack(pady=10)
        
        self.pas = ctk.CTkEntry(box, placeholder_text="Şifre", show="•", width=300, height=55, font=FONTS["body"])
        self.pas.pack(pady=10)
        self.pas.bind("<Return>", lambda e: self.check())

        self.remember_var = ctk.BooleanVar(value=False)
        self.chk_remember = ctk.CTkCheckBox(box, text="Beni Hatırla", variable=self.remember_var, 
                                            font=("Arial", 12), text_color="gray", hover_color=COLORS["accent"], fg_color=COLORS["accent"])
        self.chk_remember.pack(pady=10)

        saved_u, saved_p = ConfigManager.get_creds()
        if saved_u and saved_p:
            self.user.insert(0, saved_u)
            self.pas.insert(0, saved_p)
            self.remember_var.set(True)

        ctk.CTkButton(box, text="GİRİŞ", width=300, height=55, fg_color=COLORS["accent"], text_color="black",
                      font=FONTS["bold"], hover_color="white", command=self.check).pack(pady=20)
        
        ctk.CTkButton(box, text="⚙️ Veritabanı Seç", fg_color="transparent", text_color="gray", command=self.settings).pack(side="bottom", pady=20)

    def settings(self):
        f = filedialog.askopenfilename(filetypes=[("DB", "*.db")])
        if f:
            ConfigManager.set_db_path(f)
            global CURRENT_DB_PATH
            CURRENT_DB_PATH = f
            messagebox.showinfo("Tamam", "Veritabanı güncellendi. Yeniden başlatılıyor...")
            self.destroy()
            AnimatedSplash().mainloop()

    def check(self):
        u_name = self.user.get()
        p_word = self.pas.get()
        try:
            conn = DB.get_conn()
            data = conn.cursor().execute("SELECT role FROM users WHERE name=? AND pass=?", (u_name, p_word)).fetchone()
            conn.close()
            if data:
                u_role = data[0]
                ConfigManager.save_creds(u_name, p_word, self.remember_var.get())
                self.destroy()
                MainApp(u_name, u_role).mainloop()
            else: ToastNotification(self, "Hatalı Bilgiler!", COLORS["danger"])
        except: ToastNotification(self, "DB Hatası!", COLORS["danger"])

# ================== ANA UYGULAMA ==================
class MainApp(ctk.CTk):
    def __init__(self, user, role):
        super().__init__()
        self.user = user
        self.role = role
        self.title(f"TaNjU PRO {APP_VERSION} - {user.upper()}")
        self.geometry("1400x800")
        self.configure(fg_color=COLORS["bg"])

        self.active_depots = DB.get_all_depots()
        self.animation_running = False
        self.critical_widgets = []

        self.grid_columnconfigure(1, weight=1)
        self.grid_rowconfigure(0, weight=1)
        self.setup_sidebar()
        self.setup_main()
        
        # --- OTOMATİK GÖREVLER BAŞLAT ---
        self.start_scheduler()
        
        self.show_dashboard()

    def start_scheduler(self):
        task_thread = threading.Thread(target=self._task_loop, daemon=True)
        task_thread.start()

    def _task_loop(self):
        while True:
            try:
                cfg = ConfigManager.get_email_config()
                if not cfg["time_h"] or not cfg["time_m"]:
                    time.sleep(30); continue
                    
                target_h = int(cfg["time_h"])
                target_m = int(cfg["time_m"])

                now = datetime.now()
                if now.hour == target_h and now.minute == target_m:
                    self.perform_daily_tasks()
                    time.sleep(61)
                else:
                    time.sleep(10)
            except: time.sleep(60)

    # --- YENİLENMİŞ OTOMATİK GÖREV FONKSİYONU ---
    def perform_daily_tasks(self):
        # ÖNCE KONTROL ET: Bugün mail atıldı mı?
        today_str = datetime.now().strftime("%Y-%m-%d")
        conn = DB.get_conn()
        c = conn.cursor()
        
        try:
            # Veritabanından son mail tarihini çek
            c.execute("SELECT value FROM system_vars WHERE key='last_auto_mail_date'")
            row = c.fetchone()
            last_date = row[0] if row else ""

            # Eğer veritabanındaki tarih BUGÜN ise, başka bir kullanıcı maili atmış demektir.
            if last_date == today_str:
                print("Bugünün otomatik görevi zaten yapılmış. Atlanıyor.")
                conn.close()
                return # Fonksiyondan çık, işlem yapma.

            # Eğer yapılmadıysa, hemen tarihi güncelle ki diğer kullanıcılar da yapmasın
            c.execute("INSERT OR REPLACE INTO system_vars (key, value) VALUES ('last_auto_mail_date', ?)", (today_str,))
            conn.commit()
            
        except Exception as e:
            print(f"DB Kontrol Hatası: {e}")
            conn.close()
            return

        conn.close()

        # --- BURADAN AŞAĞISI GÖREVİ GERÇEKLEŞTİRİR ---
        try:
            backup_dir = os.path.join(program_folder, "Yedekler")
            if not os.path.exists(backup_dir): os.makedirs(backup_dir)
            
            timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
            backup_filename = f"OtoYedek_{timestamp}.db"
            backup_path = os.path.join(backup_dir, backup_filename)
            shutil.copy2(CURRENT_DB_PATH, backup_path)
            
            # Sadece işlemi yapan kişiye bildirim ver
            self.after(0, lambda: ToastNotification(self, "Otomatik Mail Gönderiliyor...", COLORS["accent"]))
            
            self.send_auto_email()

        except Exception as e:
            print(f"Otomatik Görev Hatası: {e}")

    def send_auto_email(self):
        cfg = ConfigManager.get_email_config()
        if not cfg["sender"] or not cfg["password"] or not cfg["receivers"]:
            print("Mail ayarları eksik.")
            return

        try:
            conn = DB.get_conn()
            rows = conn.cursor().execute("SELECT name, count FROM depots ORDER BY name").fetchall()
            conn.close()

            if not rows: return

            timestamp = datetime.now().strftime("%d-%m-%Y %H:%M")
            
            body = f"Sayın Yetkili,\n\n{timestamp} itibarıyla güncel depo stok durumları aşağıdadır:\n\n"
            body += "="*30 + "\n"
            
            total_stock = 0
            for name, count in rows:
                body += f"📦 {name:<15}: {count} Adet\n"
                total_stock += count
            
            body += "="*30 + "\n"
            body += f"TOPLAM STOK      : {total_stock} Adet\n\n"
            body += f"İyi Çalışmalar,\nKare Palet Stok Otomasyon {APP_VERSION}"

            msg = MIMEMultipart()
            msg['From'] = cfg["sender"]
            msg['To'] = cfg["receivers"]
            msg['Subject'] = f"Kare Palet Stok Otomasyon - {timestamp}"
            
            msg.attach(MIMEText(body, 'plain', 'utf-8'))

            server = smtplib.SMTP('smtp.gmail.com', 587)
            server.starttls()
            server.login(cfg["sender"], cfg["password"])
            
            recipients = cfg["receivers"].split(",") 
            server.sendmail(cfg["sender"], recipients, msg.as_string())
            server.quit()

            self.after(0, lambda: ToastNotification(self, "Stok Durumu Mail Atıldı!", COLORS["success"]))

        except Exception as e:
            print(f"Mail Hatası: {e}")
            self.after(0, lambda: ToastNotification(self, "Mail Gönderilemedi!", COLORS["danger"]))

    def setup_sidebar(self):
        self.sidebar = ctk.CTkFrame(self, width=280, corner_radius=0, fg_color=COLORS["sidebar"])
        self.sidebar.grid(row=0, column=0, sticky="nsew")
        
        ctk.CTkLabel(self.sidebar, text="⚡", font=("Arial", 45)).pack(pady=(40,0))
        ctk.CTkLabel(self.sidebar, text="TaNjU", font=FONTS["h1"], text_color=COLORS["accent"]).pack()
        ctk.CTkLabel(self.sidebar, text=f"{self.role.upper()} PANELİ", font=("Arial", 11, "bold"), text_color="gray").pack(pady=(5,50))

        self.nav_btns = {}
        self.create_nav("📊  GENEL BAKIŞ", self.show_dashboard, "dash")
        self.create_nav("🔄  OPERASYON & DEPO", self.show_ops, "ops")
        self.create_nav("📝  GEÇMİŞ & FİLTRE", self.show_history, "hist")
        self.create_nav("📈  RAPOR MERKEZİ", self.show_reports, "report")
        
        if self.role == "admin":
            self.create_nav("🔒  KULLANICI YÖNETİMİ", self.show_users, "users")
            self.create_nav("⚙️  MAIL AYARLARI", self.show_mail_settings, "mail")
        
        self.create_nav("🚀  GÜNCELLEME MERKEZİ", self.show_update_center, "update")

        ctk.CTkButton(self.sidebar, text="ÇIKIŞ", fg_color=COLORS["bg"], hover_color=COLORS["danger"], 
                      height=50, font=FONTS["bold"], command=self.logout).pack(side="bottom", fill="x", padx=20, pady=30)

    def create_nav(self, text, cmd, key):
        btn = ctk.CTkButton(self.sidebar, text=text, fg_color="transparent", text_color=COLORS["text_body"], 
                            hover_color="#334155", anchor="w", font=FONTS["bold"], height=60, command=cmd)
        btn.pack(fill="x", padx=15, pady=5)
        self.nav_btns[key] = btn

    def active_nav(self, key):
        for k, btn in self.nav_btns.items():
            if k == key: btn.configure(fg_color=COLORS["accent"], text_color="black")
            else: btn.configure(fg_color="transparent", text_color=COLORS["text_body"])

    def setup_main(self):
        self.main = ctk.CTkFrame(self, fg_color="transparent", corner_radius=0)
        self.main.grid(row=0, column=1, sticky="nsew", padx=30, pady=30)

    def clear_main(self):
        self.animation_running = False
        self.critical_widgets = []
        for w in self.main.winfo_children(): w.destroy()

    def refresh_app_data(self):
        self.active_depots = DB.get_all_depots()

    # --- 1. DASHBOARD ---
    def show_dashboard(self):
        self.clear_main(); self.active_nav("dash")
        self.refresh_app_data()
        self.animation_running = True 
        
        ctk.CTkLabel(self.main, text="DEPO DURUMLARI", font=FONTS["h2"], text_color="white").pack(anchor="w", pady=(0, 20))

        scroll_frame = ctk.CTkScrollableFrame(self.main, fg_color="transparent", height=500)
        scroll_frame.pack(fill="both", expand=True)

        grid = ctk.CTkFrame(scroll_frame, fg_color="transparent")
        grid.pack(fill="both", expand=True)

        conn = DB.get_conn()
        cur = conn.cursor()
        cur.execute("SELECT name, count FROM depots")
        data = {row[0]: row[1] for row in cur.fetchall()}
        conn.close()

        colors = [COLORS["accent"], "#8B5CF6", "#10B981", COLORS["warning"], "#EC4899", "#F59E0B"]
        row_idx = 0; col_idx = 0
        grid.grid_columnconfigure(0, weight=1); grid.grid_columnconfigure(1, weight=1)

        for i, depot in enumerate(self.active_depots):
            val = data.get(depot, 0)
            col = colors[i % len(colors)]
            
            is_critical = val < 10
            
            card = self.create_depot_card(grid, depot, val, col, row_idx, col_idx, is_critical)
            
            if is_critical:
                self.critical_widgets.append(card)

            col_idx += 1
            if col_idx > 1:
                col_idx = 0; row_idx += 1

        bottom = ctk.CTkFrame(self.main, fg_color="transparent")
        bottom.pack(fill="x", pady=20)
        conn = DB.get_conn()
        today = datetime.now().strftime("%Y-%m-%d")
        t_in = conn.cursor().execute(f"SELECT SUM(qty) FROM logs WHERE action='GİRİŞ' AND date LIKE '{today}%'").fetchone()[0] or 0
        t_out = conn.cursor().execute(f"SELECT SUM(qty) FROM logs WHERE action='ÇIKIŞ' AND date LIKE '{today}%'").fetchone()[0] or 0
        conn.close()
        self.create_mini_kpi(bottom, "BUGÜN GİREN", f"+{t_in}", COLORS["success"])
        self.create_mini_kpi(bottom, "BUGÜN ÇIKAN", f"-{t_out}", COLORS["danger"])

        if self.critical_widgets:
            self.animate_critical_cards()

    def create_depot_card(self, parent, name, val, color, r, c, is_critical=False):
        border_col = COLORS["critical"] if is_critical else COLORS["border"]
        border_w = 3 if is_critical else 1
        
        card = ctk.CTkFrame(parent, fg_color=COLORS["card"], corner_radius=20, border_width=border_w, border_color=border_col)
        card.grid(row=r, column=c, padx=10, pady=10, sticky="nsew", ipady=20)
        
        ctk.CTkLabel(card, text="📦 " + name, font=("Arial", 16, "bold"), text_color="gray").pack(pady=(20, 10))
        ctk.CTkLabel(card, text=str(val), font=("Roboto", 48, "bold"), text_color=color).pack(pady=5)
        ctk.CTkLabel(card, text="Palet Mevcut", font=("Arial", 12), text_color="gray").pack()
        
        if is_critical:
            ctk.CTkLabel(card, text="⚠️ KRİTİK STOK!", font=("Arial", 14, "bold"), text_color=COLORS["danger"]).pack(pady=5)
            
        return card

    def animate_critical_cards(self):
        if not self.animation_running: return
        if not hasattr(self, 'flash_state'): self.flash_state = False
        current_color = COLORS["critical"] if self.flash_state else COLORS["card"]
        for widget in self.critical_widgets:
            try: widget.configure(border_color=current_color)
            except: pass
        self.flash_state = not self.flash_state
        self.after(800, self.animate_critical_cards)

    def create_mini_kpi(self, parent, title, val, color):
        f = ctk.CTkFrame(parent, fg_color=COLORS["card"], corner_radius=15, height=80)
        f.pack(side="left", fill="x", expand=True, padx=10)
        ctk.CTkLabel(f, text=title, font=("Arial", 12, "bold"), text_color="gray").pack(side="left", padx=20)
        ctk.CTkLabel(f, text=val, font=("Arial", 24, "bold"), text_color=color).pack(side="right", padx=20)

    # --- 2. OPERASYON ---
    def show_ops(self):
        self.clear_main(); self.active_nav("ops")
        self.refresh_app_data()

        p = ctk.CTkFrame(self.main, fg_color=COLORS["card"], corner_radius=20, border_width=1, border_color=COLORS["border"])
        p.pack(fill="x", pady=(0, 20), padx=20)
        
        ctk.CTkLabel(p, text="PALET İŞLEM", font=FONTS["h2"], text_color=COLORS["accent"]).pack(pady=(20,10))
        
        self.cb_depo = ctk.CTkComboBox(p, values=self.active_depots, width=350, height=50, font=FONTS["bold"])
        self.cb_depo.pack(pady=5); self.cb_depo.set("Depo Seçiniz")
        
        d_frame = ctk.CTkFrame(p, fg_color="transparent")
        d_frame.pack(pady=10)
        ctk.CTkLabel(d_frame, text="Tarih:", font=("Arial", 14, "bold"), text_color="gray").pack(side="left", padx=10)
        
        now = datetime.now()
        self.c_day = ctk.CTkComboBox(d_frame, values=[f"{d:02d}" for d in range(1, 32)], width=70, font=("Arial", 12))
        self.c_day.set(f"{now.day:02d}"); self.c_day.pack(side="left", padx=2)
        self.c_month = ctk.CTkComboBox(d_frame, values=[f"{m:02d}" for m in range(1, 13)], width=70, font=("Arial", 12))
        self.c_month.set(f"{now.month:02d}"); self.c_month.pack(side="left", padx=2)
        self.c_year = ctk.CTkComboBox(d_frame, values=[str(y) for y in range(2024, 2030)], width=80, font=("Arial", 12))
        self.c_year.set(str(now.year)); self.c_year.pack(side="left", padx=2)

        self.en_qty = ctk.CTkEntry(p, placeholder_text="Adet Giriniz", width=350, height=50, font=FONTS["bold"], justify="center")
        self.en_qty.pack(pady=5)
        
        fr = ctk.CTkFrame(p, fg_color="transparent"); fr.pack(pady=20)
        ctk.CTkButton(fr, text="GİRİŞ (+)", width=150, height=50, fg_color=COLORS["success"], font=FONTS["bold"], command=lambda: self.process("GİRİŞ")).pack(side="left", padx=10)
        ctk.CTkButton(fr, text="ÇIKIŞ (-)", width=150, height=50, fg_color=COLORS["danger"], font=FONTS["bold"], command=lambda: self.process("ÇIKIŞ")).pack(side="left", padx=10)

        admin_frame = ctk.CTkFrame(self.main, fg_color="transparent")
        admin_frame.pack(fill="x", padx=20)
        
        ctk.CTkLabel(admin_frame, text="Depo Yönetimi", font=FONTS["h2"], text_color="white").pack(anchor="w", pady=10)
        
        af = ctk.CTkFrame(admin_frame, fg_color=COLORS["card"], corner_radius=20)
        af.pack(fill="x")
        
        self.entry_new_depot = ctk.CTkEntry(af, placeholder_text="Yeni Depo Adı...", width=300, height=40)
        self.entry_new_depot.pack(side="left", padx=20, pady=20)
        
        ctk.CTkButton(af, text="DEPO EKLE", fg_color=COLORS["accent"], text_color="black", width=120, command=self.add_new_depot).pack(side="left", padx=10)
        
        ctk.CTkFrame(af, width=2, height=40, fg_color="gray").pack(side="left", padx=20)
        
        ctk.CTkLabel(af, text="Seçili Olanı:", text_color="gray").pack(side="left")
        ctk.CTkButton(af, text="SİL", fg_color=COLORS["danger"], width=100, command=self.delete_selected_depot).pack(side="left", padx=10)

    def process(self, act):
        try:
            d = self.cb_depo.get()
            q_str = self.en_qty.get()
            if not q_str: raise ValueError
            q = int(q_str)

            if d not in self.active_depots or q <= 0: raise ValueError
            
            sel_d, sel_m, sel_y = self.c_day.get(), self.c_month.get(), self.c_year.get()
            try:
                valid_date = datetime(int(sel_y), int(sel_m), int(sel_d))
            except ValueError:
                ToastNotification(self, "Geçersiz Tarih!", COLORS["danger"])
                return

            current_time = datetime.now().strftime("%H:%M:%S")
            final_date_str = f"{sel_y}-{sel_m}-{sel_d} {current_time}"

            conn = DB.get_conn(); c = conn.cursor()
            if act == "ÇIKIŞ":
                curr = c.execute("SELECT count FROM depots WHERE name=?", (d,)).fetchone()[0]
                if curr < q: conn.close(); return ToastNotification(self, f"Yetersiz Stok! ({curr})", COLORS["danger"])
                c.execute("UPDATE depots SET count = count - ? WHERE name=?", (q, d))
            else: c.execute("UPDATE depots SET count = count + ? WHERE name=?", (q, d))
            
            c.execute("INSERT INTO logs (date, action, depot, qty, user) VALUES (?,?,?,?,?)", (final_date_str, act, d, q, self.user))
            conn.commit(); conn.close()
            ToastNotification(self, "İşlem Başarılı", COLORS["success"]); self.en_qty.delete(0, "end")
        except ValueError: ToastNotification(self, "Hatalı Giriş!", COLORS["warning"])
        except Exception as e: ToastNotification(self, f"Hata: {e}", COLORS["danger"])

    def add_new_depot(self):
        name = self.entry_new_depot.get().strip().upper()
        if not name: return ToastNotification(self, "İsim Giriniz", COLORS["warning"])
        try:
            conn = DB.get_conn()
            conn.cursor().execute("INSERT INTO depots (name, count) VALUES (?, 0)", (name,))
            conn.commit(); conn.close()
            ToastNotification(self, "Depo Eklendi", COLORS["success"])
            self.entry_new_depot.delete(0, "end")
            self.refresh_app_data()
            self.cb_depo.configure(values=self.active_depots)
        except sqlite3.IntegrityError:
            ToastNotification(self, "Bu depo zaten var!", COLORS["danger"])

    def delete_selected_depot(self):
        name = self.cb_depo.get()
        if name not in self.active_depots: return ToastNotification(self, "Depo Seçiniz", COLORS["warning"])
        
        if not messagebox.askyesno("Onay", f"'{name}' deposunu silmek istediğinize emin misiniz?\nİçindeki stok verisi kaybolacaktır!"): return
        conn = DB.get_conn()
        count = conn.cursor().execute("SELECT count FROM depots WHERE name=?", (name,)).fetchone()[0]
        if count > 0:
            if not messagebox.askyesno("Dikkat", f"Bu depoda {count} adet stok var! Yine de silinsin mi?"):
                conn.close(); return

        conn.cursor().execute("DELETE FROM depots WHERE name=?", (name,))
        conn.commit(); conn.close()
        ToastNotification(self, "Depo Silindi", COLORS["success"])
        self.refresh_app_data()
        self.cb_depo.configure(values=self.active_depots)
        self.cb_depo.set("Depo Seçiniz")

    # --- 3. GEÇMİŞ ---
    def show_history(self):
        self.clear_main(); self.active_nav("hist")
        self.refresh_app_data()
        
        top = ctk.CTkFrame(self.main, fg_color="transparent"); top.pack(fill="x", pady=(0, 10))
        ctk.CTkLabel(top, text="GEÇMİŞ & DÜZENLEME", font=FONTS["h2"]).pack(side="left")
        
        flt = ctk.CTkFrame(self.main, fg_color=COLORS["card"], corner_radius=10)
        flt.pack(fill="x", pady=10, padx=5)
        ctk.CTkLabel(flt, text="Filtrele:", font=("Arial", 12, "bold"), text_color=COLORS["accent"]).pack(side="left", padx=15)

        self.cb_y = ctk.CTkComboBox(flt, values=["Yıl"] + [str(y) for y in range(2024, 2030)], width=80); self.cb_y.pack(side="left", padx=5)
        self.cb_m = ctk.CTkComboBox(flt, values=["Ay"] + [f"{m:02d}" for m in range(1, 13)], width=70); self.cb_m.pack(side="left", padx=5)
        self.cb_d = ctk.CTkComboBox(flt, values=["Gün"] + [f"{d:02d}" for d in range(1, 32)], width=70); self.cb_d.pack(side="left", padx=5)
        
        conn = DB.get_conn()
        users = [u[0] for u in conn.cursor().execute("SELECT name FROM users").fetchall()]
        conn.close()
        self.cb_u = ctk.CTkComboBox(flt, values=["Kullanıcı"] + users, width=120); self.cb_u.pack(side="left", padx=5)
        
        self.ent_search = ctk.CTkEntry(flt, placeholder_text="Serbest Arama...", width=150); self.ent_search.pack(side="left", padx=15)

        ctk.CTkButton(flt, text="UYGULA", width=80, fg_color=COLORS["accent"], text_color="black", command=self.load_history_combined).pack(side="left", padx=10)
        ctk.CTkButton(flt, text="TEMİZLE", width=80, fg_color=COLORS["sidebar"], command=self.reset_filter).pack(side="left", padx=5)

        cols = ("ID", "TARİH", "SAAT", "GÜN", "İŞLEM", "DEPO", "ADET", "KULLANICI")
        style = ttk.Style(); style.theme_use("clam")
        style.configure("Treeview", background=COLORS["card"], foreground="white", fieldbackground=COLORS["card"], rowheight=40, borderwidth=0, font=("Arial", 12))
        style.configure("Treeview.Heading", background="#111827", foreground=COLORS["accent"], font=("Arial", 12, "bold"))
        style.map("Treeview", background=[('selected', COLORS["accent"])], foreground=[('selected', 'black')])
        
        self.tree = ttk.Treeview(self.main, columns=cols, show="headings")
        self.tree.heading("ID", text="#"); self.tree.column("ID", width=40, anchor="center")
        
        self.tree.heading("TARİH", text="TARİH"); self.tree.column("TARİH", width=100, anchor="center")
        self.tree.heading("SAAT", text="SAAT"); self.tree.column("SAAT", width=80, anchor="center")
        self.tree.heading("GÜN", text="GÜN"); self.tree.column("GÜN", width=100, anchor="center")
        
        for c in cols[4:]: self.tree.heading(c, text=c); self.tree.column(c, anchor="center")
        
        self.tree.tag_configure("IN", foreground=COLORS["success"])
        self.tree.tag_configure("OUT", foreground=COLORS["danger"])
        self.tree.pack(fill="both", expand=True, pady=10)

        btn_fr = ctk.CTkFrame(self.main, fg_color="transparent"); btn_fr.pack(fill="x", pady=5)
        ctk.CTkButton(btn_fr, text="✏️ DÜZELT", fg_color=COLORS["warning"], text_color="black", width=150, command=self.edit_transaction).pack(side="left", padx=5)
        ctk.CTkButton(btn_fr, text="🗑️ SİL", fg_color=COLORS["danger"], width=150, command=self.delete_transaction).pack(side="left", padx=5)
        
        self.load_history_combined()

    def reset_filter(self):
        self.cb_y.set("Yıl"); self.cb_m.set("Ay"); self.cb_d.set("Gün"); self.cb_u.set("Kullanıcı"); self.ent_search.delete(0, "end")
        self.load_history_combined()

    def load_history_combined(self):
        for i in self.tree.get_children(): self.tree.delete(i)
        y, m, d, u = self.cb_y.get(), self.cb_m.get(), self.cb_d.get(), self.cb_u.get()
        search_term = self.ent_search.get().strip()
        query = "SELECT * FROM logs WHERE 1=1"
        params = []
        
        if y != "Yıl": query += " AND strftime('%Y', date) = ?"; params.append(y)
        if m != "Ay": query += " AND strftime('%m', date) = ?"; params.append(m)
        if d != "Gün": query += " AND strftime('%d', date) = ?"; params.append(d)
        if u != "Kullanıcı": query += " AND user = ?"; params.append(u)
        if search_term:
            query += " AND (depot LIKE ? OR user LIKE ? OR action LIKE ?)"
            params.extend([f"%{search_term}%", f"%{search_term}%", f"%{search_term}%"])
        
        query += " ORDER BY id DESC LIMIT 500"
        
        tr_days = {"Monday": "Pazartesi", "Tuesday": "Salı", "Wednesday": "Çarşamba", "Thursday": "Perşembe", "Friday": "Cuma", "Saturday": "Cumartesi", "Sunday": "Pazar"}

        conn = DB.get_conn()
        try:
            rows = conn.cursor().execute(query, params).fetchall()
            for r in rows:
                raw_date = r[1]
                try:
                    dt_obj = datetime.strptime(raw_date, "%Y-%m-%d %H:%M:%S")
                    d_str = dt_obj.strftime("%Y-%m-%d")
                    t_str = dt_obj.strftime("%H:%M")
                    day_eng = dt_obj.strftime("%A")
                    day_tr = tr_days.get(day_eng, day_eng)
                except: d_str, t_str, day_tr = raw_date, "-", "-"
                new_row = (r[0], d_str, t_str, day_tr, r[2], r[3], r[4], r[5])
                tag = "IN" if r[2] == "GİRİŞ" else "OUT"
                self.tree.insert("", "end", values=new_row, tags=(tag,))
        except Exception as e: print(e)
        finally: conn.close()

    def delete_transaction(self):
        sel = self.tree.selection()
        if not sel: return ToastNotification(self, "Seçim Yapın!", COLORS["warning"])
        item = self.tree.item(sel)['values']
        log_id, action, depot, qty = item[0], item[4], item[5], int(item[6])
        
        if not messagebox.askyesno("Onay", "Kayıt silinsin mi? Stok düzeltilecek."): return
        conn = DB.get_conn(); c = conn.cursor()
        try:
            if action == "GİRİŞ": c.execute("UPDATE depots SET count=count-? WHERE name=?", (qty, depot))
            else: c.execute("UPDATE depots SET count=count+? WHERE name=?", (qty, depot))
            c.execute("DELETE FROM logs WHERE id=?", (log_id,))
            conn.commit(); 
            ToastNotification(self, "Silindi", COLORS["success"])
            self.load_history_combined()
        except: ToastNotification(self, "Hata", COLORS["danger"])
        finally: conn.close()

    def edit_transaction(self):
        sel = self.tree.selection()
        if not sel: return ToastNotification(self, "Seçim Yapın!", COLORS["warning"])
        item = self.tree.item(sel)['values']
        old_id, old_date_str, old_time_str, _, old_act, old_dep, old_qty, _ = item

        try:
            dt = datetime.strptime(old_date_str, "%Y-%m-%d")
            def_d, def_m, def_y = f"{dt.day:02d}", f"{dt.month:02d}", str(dt.year)
        except:
            now = datetime.now()
            def_d, def_m, def_y = f"{now.day:02d}", f"{now.month:02d}", str(now.year)

        top = ctk.CTkToplevel(self); top.geometry("350x550"); top.title("Düzenle"); top.attributes("-topmost", True)
        ctk.CTkLabel(top, text="KAYIT DÜZENLE", font=FONTS["h2"]).pack(pady=20)
        
        d_frame = ctk.CTkFrame(top, fg_color="transparent"); d_frame.pack(pady=5)
        ctk.CTkLabel(d_frame, text="Tarih:", font=("Arial", 12, "bold")).pack(anchor="w", padx=5)
        
        c_day = ctk.CTkComboBox(d_frame, values=[f"{d:02d}" for d in range(1, 32)], width=70); c_day.set(def_d); c_day.pack(side="left", padx=2)
        c_month = ctk.CTkComboBox(d_frame, values=[f"{m:02d}" for m in range(1, 13)], width=70); c_month.set(def_m); c_month.pack(side="left", padx=2)
        c_year = ctk.CTkComboBox(d_frame, values=[str(y) for y in range(2024, 2030)], width=80); c_year.set(def_y); c_year.pack(side="left", padx=2)

        ctk.CTkLabel(top, text="İşlem Tipi:", font=("Arial", 12)).pack(pady=(10,0))
        c_act = ctk.CTkComboBox(top, values=["GİRİŞ", "ÇIKIŞ"], height=40); c_act.set(old_act); c_act.pack(pady=5)
        
        ctk.CTkLabel(top, text="Depo:", font=("Arial", 12)).pack(pady=(10,0))
        c_dep = ctk.CTkComboBox(top, values=self.active_depots, height=40); c_dep.set(old_dep); c_dep.pack(pady=5)
        
        ctk.CTkLabel(top, text="Adet:", font=("Arial", 12)).pack(pady=(10,0))
        e_qty = ctk.CTkEntry(top, height=40); e_qty.insert(0, str(old_qty)); e_qty.pack(pady=5)

        def save():
            try:
                na, nd, nq = c_act.get(), c_dep.get(), int(e_qty.get())
                if nq <= 0: raise ValueError
                
                sel_d, sel_m, sel_y = c_day.get(), c_month.get(), c_year.get()
                try: datetime(int(sel_y), int(sel_m), int(sel_d))
                except ValueError: return messagebox.showerror("Hata", "Geçersiz Tarih!")

                final_time = "00:00:00"
                if old_time_str and old_time_str != "-":
                    if len(old_time_str) == 5: final_time = f"{old_time_str}:00"
                    else: final_time = old_time_str
                
                new_date_iso = f"{sel_y}-{sel_m}-{sel_d} {final_time}"

                conn = DB.get_conn(); c = conn.cursor()
                if old_act=="GİRİŞ": c.execute("UPDATE depots SET count=count-? WHERE name=?", (old_qty, old_dep))
                else: c.execute("UPDATE depots SET count=count+? WHERE name=?", (old_qty, old_dep))
                
                if na=="GİRİŞ": c.execute("UPDATE depots SET count=count+? WHERE name=?", (nq, nd))
                else: c.execute("UPDATE depots SET count=count-? WHERE name=?", (nq, nd))
                
                c.execute("UPDATE logs SET date=?, action=?, depot=?, qty=?, user=? WHERE id=?", (new_date_iso, na, nd, nq, f"{self.user}*", old_id))
                conn.commit(); conn.close()
                top.destroy(); self.load_history_combined()
                ToastNotification(self, "Güncellendi", COLORS["success"])
            except Exception as e: messagebox.showerror("Hata", f"İşlem Başarısız: {e}")
        ctk.CTkButton(top, text="KAYDET", height=50, fg_color=COLORS["success"], command=save).pack(pady=20)

    # --- 4. RAPORLAR ---
    def show_reports(self):
        self.clear_main(); self.active_nav("report")
        ctk.CTkLabel(self.main, text="RAPOR MERKEZİ", font=FONTS["h2"]).pack(anchor="w", pady=20)
        fr = ctk.CTkFrame(self.main, fg_color=COLORS["card"]); fr.pack(fill="x", padx=10, pady=10)
        ctk.CTkLabel(fr, text="Hızlı Raporlar", font=("Arial", 14, "bold"), text_color="gray").pack(anchor="w", padx=20, pady=10)
        r1 = ctk.CTkFrame(fr, fg_color="transparent"); r1.pack(fill="x", padx=10, pady=10)
        
        ctk.CTkButton(r1, text="TÜM GEÇMİŞ (EXCEL)", height=50, command=lambda: self.export_adv("ALL")).pack(side="left", fill="x", expand=True, padx=5)
        ctk.CTkButton(r1, text="BU AYIN RAPORU", height=50, command=lambda: self.export_adv("MONTH")).pack(side="left", fill="x", expand=True, padx=5)

    def export_adv(self, mode):
        if not HAS_PANDAS: return ToastNotification(self, "Pandas Modülü Eksik!", COLORS["danger"])
        report_dir = os.path.join(program_folder, "Raporlar")
        if not os.path.exists(report_dir): os.makedirs(report_dir)
        timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
        prefix = "TJ-RAPOR TUM" if mode == "ALL" else "TJ-RAPOR AYLIK"
        filename = f"{prefix}_{timestamp}.xlsx"
        filepath = os.path.join(report_dir, filename)

        conn = DB.get_conn()
        q = "SELECT * FROM logs"
        if mode == "MONTH": m = datetime.now().strftime("%Y-%m"); q += f" WHERE date LIKE '{m}%'"
        df = pd.read_sql(q, conn); conn.close()

        if df.empty: return ToastNotification(self, "Veri Bulunamadı", COLORS["warning"])
        try:
            with pd.ExcelWriter(filepath, engine='openpyxl') as writer: df.to_excel(writer, sheet_name="Rapor", index=False)
            ToastNotification(self, "Rapor Kaydedildi!", COLORS["success"])
            if os.name == 'nt': os.startfile(report_dir)
            else: os.system(f"open '{report_dir}'")
        except Exception as e: ToastNotification(self, f"Hata: {e}", COLORS["danger"])

    # --- 5. MAIL AYARLARI EKRANI ---
    def show_mail_settings(self):
        self.clear_main(); self.active_nav("mail")
        ctk.CTkLabel(self.main, text="OTOMATİK MAIL AYARLARI", font=FONTS["h2"]).pack(pady=20)
        
        box = ctk.CTkFrame(self.main, fg_color=COLORS["card"], corner_radius=15, width=600)
        box.pack(pady=10, padx=50)

        cfg = ConfigManager.get_email_config()

        ctk.CTkLabel(box, text="Gönderen Mail (Gmail):", font=FONTS["bold"]).pack(anchor="w", padx=30, pady=(20,5))
        e_sender = ctk.CTkEntry(box, width=400); e_sender.pack(padx=30, pady=5); e_sender.insert(0, cfg["sender"])

        ctk.CTkLabel(box, text="Uygulama Şifresi:", font=FONTS["bold"]).pack(anchor="w", padx=30, pady=(10,5))
        e_pass = ctk.CTkEntry(box, width=400, show="*"); e_pass.pack(padx=30, pady=5); e_pass.insert(0, cfg["password"])

        ctk.CTkLabel(box, text="Alıcı Mailler:", font=FONTS["bold"]).pack(anchor="w", padx=30, pady=(10,5))
        e_recv = ctk.CTkEntry(box, width=400); e_recv.pack(padx=30, pady=5); e_recv.insert(0, cfg["receivers"])

        ctk.CTkLabel(box, text="Otomatik Gönderim Saati:", font=FONTS["bold"]).pack(anchor="w", padx=30, pady=(15,5))
        time_fr = ctk.CTkFrame(box, fg_color="transparent")
        time_fr.pack(anchor="w", padx=30, pady=5)
        
        hours = [f"{i:02d}" for i in range(24)]
        mins = [f"{i:02d}" for i in range(60)]
        
        c_h = ctk.CTkComboBox(time_fr, values=hours, width=70)
        c_h.pack(side="left", padx=5)
        c_h.set(cfg["time_h"])
        
        ctk.CTkLabel(time_fr, text=":").pack(side="left")
        
        c_m = ctk.CTkComboBox(time_fr, values=mins, width=70)
        c_m.pack(side="left", padx=5)
        c_m.set(cfg["time_m"])

        def save_mail():
            ConfigManager.save_email_config(e_sender.get(), e_pass.get(), e_recv.get(), c_h.get(), c_m.get())
            ToastNotification(self, "Mail Ayarları Kaydedildi", COLORS["success"])

        def test_mail():
            save_mail()
            ToastNotification(self, "Test Maili Gönderiliyor...", COLORS["accent"])
            threading.Thread(target=self.send_auto_email, daemon=True).start()

        btn_fr = ctk.CTkFrame(box, fg_color="transparent")
        btn_fr.pack(pady=30)
        ctk.CTkButton(btn_fr, text="KAYDET", fg_color=COLORS["success"], width=150, command=save_mail).pack(side="left", padx=10)
        ctk.CTkButton(btn_fr, text="TEST ET", fg_color=COLORS["warning"], text_color="black", width=150, command=test_mail).pack(side="left", padx=10)
    
    # ================== GÜNCELLEME SİSTEMİ (SADECE WEB) ==================
    def show_update_center(self):
        self.clear_main()
        self.active_nav("update")
        
        ctk.CTkLabel(self.main, text="SİSTEM GÜNCELLEME", font=FONTS["h2"], text_color=COLORS["text_h1"]).pack(pady=(30, 10))
        
        card = ctk.CTkFrame(self.main, fg_color=COLORS["card"], corner_radius=20, border_width=1, border_color=COLORS["border"])
        card.pack(fill="x", padx=50, pady=20)
        
        ctk.CTkLabel(card, text=f"Mevcut Sürüm: {APP_VERSION}", font=("Arial", 24, "bold"), text_color=COLORS["accent"]).pack(pady=(30, 10))
        ctk.CTkLabel(card, text="Sunucudaki en son sürümü indirip kurabilirsiniz.", font=("Arial", 14), text_color="gray").pack(pady=(0, 30))

        # Butonlar Alanı
        btn_frame = ctk.CTkFrame(card, fg_color="transparent")
        btn_frame.pack(pady=20)

        web_btn = ctk.CTkButton(btn_frame, 
                              text="🌐 WEB'DEN GÜNCELLE (OTOMATİK)", 
                              width=300, 
                              height=50, 
                              fg_color="#3B82F6", 
                              font=FONTS["bold"],
                              command=self.check_web_update)
        web_btn.pack(pady=10)

        info_box = ctk.CTkFrame(self.main, fg_color="transparent")
        info_box.pack(pady=20, padx=50, fill="x")
        
        info_text = """
        GÜNCELLEME NASIL ÇALIŞIR?
        
        1. Bu işlem internet bağlantısı gerektirir.
        2. Sistem, sunucudaki en güncel yazılım dosyasını indirir.
        3. Mevcut yazılımın yedeği (.bak uzantılı) otomatik olarak alınır.
        4. Yeni sürüm kurulur ve uygulama kapatılır.
        5. Uygulamayı tekrar açtığınızda yeni sürümle çalışacaktır.
        """
        ctk.CTkLabel(info_box, text=info_text, font=("Consolas", 12), justify="left", anchor="w", text_color="gray").pack(fill="x")

    def check_web_update(self):
        if not messagebox.askyesno("Onay", "İnternetten en son sürüm indirilip kurulacak.\nDevam etmek istiyor musunuz?"):
            return

        try:
            ToastNotification(self, "Güncelleme indiriliyor...", COLORS["warning"])
            self.update() 
            
            with urllib.request.urlopen(UPDATE_URL) as response:
                new_code = response.read()
            
            if not new_code:
                raise ValueError("Sunucudan boş veri geldi.")

            current_file = os.path.abspath(__file__)
            shutil.copy2(current_file, current_file + ".bak")
            
            with open(current_file, "wb") as f:
                f.write(new_code)
                
            messagebox.showinfo("BAŞARILI", "Güncelleme başarıyla tamamlandı!\n\nUygulama şimdi kapanacak.\nLütfen tekrar çalıştırın.")
            self.destroy()
            sys.exit()

        except Exception as e:
            messagebox.showerror("GÜNCELLEME HATASI", f"Hata oluştu:\n{e}\n\nLütfen internet bağlantınızı veya linki kontrol edin.")

    # --- KULLANICI YÖNETİMİ ---
    def show_users(self):
        self.clear_main(); self.active_nav("users")
        ctk.CTkLabel(self.main, text="Kullanıcı Yönetimi", font=FONTS["h2"]).pack(pady=20)
        fr = ctk.CTkFrame(self.main, fg_color=COLORS["card"]); fr.pack(fill="both", expand=True, padx=20, pady=20)
        cols = ("KULLANICI", "ROL")
        self.u_tree = ttk.Treeview(fr, columns=cols, show="headings"); self.u_tree.pack(side="left", fill="both", expand=True, padx=15, pady=15)
        self.u_tree.heading("KULLANICI", text="KULLANICI ADI"); self.u_tree.heading("ROL", text="YETKİ ROLÜ")
        self.u_tree.bind("<<TreeviewSelect>>", self.fill_user_form)

        pnl = ctk.CTkFrame(fr, fg_color="transparent", width=300); pnl.pack(side="right", fill="y", padx=15, pady=15)
        self.u_name = ctk.CTkEntry(pnl, placeholder_text="Kullanıcı Adı"); self.u_name.pack(pady=10)
        self.u_pass = ctk.CTkEntry(pnl, placeholder_text="Şifre", show="•"); self.u_pass.pack(pady=10)
        self.show_pass_var = ctk.BooleanVar(value=False)
        ctk.CTkCheckBox(pnl, text="Şifreyi Göster", variable=self.show_pass_var, command=self.toggle_password).pack(pady=5)
        self.u_role = ctk.CTkComboBox(pnl, values=["personel", "admin"]); self.u_role.pack(pady=15); self.u_role.set("personel")

        ctk.CTkButton(pnl, text="KAYDET", fg_color=COLORS["success"], command=self.save_user).pack(pady=10)
        ctk.CTkButton(pnl, text="SİL", fg_color=COLORS["danger"], command=self.del_user).pack(pady=5)
        ctk.CTkButton(pnl, text="TEMİZLE", fg_color=COLORS["border"], command=self.clear_user_form).pack(pady=20)
        self.refresh_users()

    def toggle_password(self):
        if self.show_pass_var.get(): self.u_pass.configure(show="")
        else: self.u_pass.configure(show="•")

    def refresh_users(self):
        for i in self.u_tree.get_children(): self.u_tree.delete(i)
        conn = DB.get_conn()
        for r in conn.cursor().execute("SELECT name, role FROM users").fetchall(): self.u_tree.insert("", "end", values=r)
        conn.close()

    def fill_user_form(self, event):
        sel = self.u_tree.selection()
        if not sel: return
        u_name_val = self.u_tree.item(sel)['values'][0]
        conn = DB.get_conn()
        data = conn.cursor().execute("SELECT name, pass, role FROM users WHERE name=?", (u_name_val,)).fetchone()
        conn.close()
        if data:
            self.clear_user_form()
            self.u_name.insert(0, data[0])
            self.u_pass.insert(0, data[1])
            self.u_role.set(data[2])

    def clear_user_form(self):
        self.u_name.delete(0, "end"); self.u_pass.delete(0, "end"); self.u_role.set("personel")
        self.u_tree.selection_remove(self.u_tree.selection())

    def save_user(self):
        n, p, r = self.u_name.get(), self.u_pass.get(), self.u_role.get()
        if not n or not p: return ToastNotification(self, "Eksik Bilgi!", COLORS["warning"])
        try:
            conn = DB.get_conn()
            conn.cursor().execute("INSERT OR REPLACE INTO users (name, pass, role) VALUES (?,?,?)", (n,p,r))
            conn.commit(); conn.close()
            self.refresh_users(); self.clear_user_form()
            ToastNotification(self, "Kaydedildi", COLORS["success"])
        except Exception as e: ToastNotification(self, f"Hata: {e}", COLORS["danger"])

    def del_user(self):
        n = self.u_name.get()
        if not n: return ToastNotification(self, "Seçim Yapın", COLORS["warning"])
        if n == "admin": return ToastNotification(self, "Admin Silinemez!", COLORS["danger"])
        if messagebox.askyesno("Onay", "Silinsin mi?"):
            conn = DB.get_conn(); conn.cursor().execute("DELETE FROM users WHERE name=?", (n,)); conn.commit(); conn.close()
            self.refresh_users(); self.clear_user_form()
            ToastNotification(self, "Silindi", COLORS["success"])

    def logout(self): self.destroy(); LoginWindow().mainloop()

if __name__ == "__main__":
    app = AnimatedSplash()
    app.mainloop()
