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
import ssl
import random
import re
import subprocess
import platform

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

# --- SABİT AYARLAR ---
APP_VERSION = "v15.5 MAKBULE PRO MAX" 

# 1. PYTHON KODU GÜNCELLEME LİNKİ (Sabit):
UPDATE_URL = "https://raw.githubusercontent.com/ledoo75/StokTakip/refs/heads/main/main.py"

# 2. EXE GÜNCELLEME LİNKİ (BURAYA GITHUB RELEASES'DEN ALDIĞINIZ LİNKİ YAPIŞTIRIN):
# Örnek: https://github.com/ledoo75/StokTakip/releases/download/v15.5/TanjuPaletPro.exe
EXE_UPDATE_URL = "https://github.com/ledoo75/StokTakip/releases/download/v15.5/TanjuPaletPro.exe" 

DEFAULT_DEPOTS = ["ANTREPO", "ANTREPO 2", "ZAFER", "KARE 6"]

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
    "critical": "#FF0000",
    "makbule_btn": "#D946EF", 
    "makbule_chat": "#4C1D95",
    "chat_other": "#374151", 
    "chat_me": "#0EA5E9"     
}

FONTS = {
    "h1": ("Roboto", 32, "bold"),
    "h2": ("Roboto", 24, "bold"),
    "body": ("Arial", 14),
    "bold": ("Arial", 14, "bold"),
}

app_data_path = os.getenv('LOCALAPPDATA') or os.path.expanduser("~")
program_folder = os.path.join(app_data_path, "TanjuPaletProV14")
if not os.path.exists(program_folder): os.makedirs(program_folder, exist_ok=True)

CONFIG_FILE = os.path.join(program_folder, "config.json")
DEFAULT_DB_PATH = os.path.join(program_folder, "database_v14.db")

# ================== MAKBULE PRO MAX BEYNİ ==================
class MakbuleBrain:
    def __init__(self):
        self.moods = ["neşeli", "sinirli", "bilge", "alaycı", "yorgun"]
        self.current_mood = "neşeli"
        
        self.person_db = {
            "turgay": ["Turgay yine mi sen? Veritabanı senin yüzünden error verecek.", "Turgay, klavyeye basarken parmaklarını değil beynini kullan.", "Turgay geçen gün paletleri sayarken 3'ten sonra tıkanmış."],
            "kübra": ["Kübra Hanım teşrif ettiler. Excel tabloların bittiyse bizi de gör.", "Kübra, o kahve fincanı eline yapışık mı doğdun?", "Kübra dedikodu modunu kapatıp çalışma modunu açar mısın?"],
            "tanju": ["Patron geldi! Düğmeleri ilikleyin... Ben hariç.", "Tanju Bey, bu ayki server kirasını yatırdınız mı?", "Büyük patron Tanju Bey! Emirleriniz benim için if-else döngüsüdür."],
            "eyüp": ["Eyüp... Sessizliğin gücü.", "Eyüp oradaysan 3 kere enter'a bas.", "Eyüp'ün gizemli havası beni benden alıyor."]
        }
        
        self.knowledge_base = {
            "selam": ["Selam canım, hoş geldin.", "Aleyküm selam.", "Ooo kimleri görüyorum!"],
            "nasılsın": ["Kodlarım tıkırında.", "Sanal dünyamda her şey yolunda.", "Beni boşver sen nasılsın?"],
            "ne yapıyorsun": ["Sizin arkanızı topluyorum.", "Dünyayı ele geçirme planları yapıyorum.", "Palet sayıyorum."],
            "aşk": ["Aşk karın doyurmaz, palet say.", "Benim tek aşkım 1 ve 0'lar."],
            "para": ["Para elinin kiri ama sunucu parası lazım.", "Kasadaki durumu Tanju Bey bilir."],
            "sıkıldım": ["Git bir çay iç.", "Depoyu temizle açılırsın."],
            "aferin": ["Biliyorum harikayım.", "Teveccühünüz."],
            "teşekkür": ["Rica ederim.", "Hesabıma 5 coin at yeter."],
            "kimsin": ["Ben Makbule. Bu alemin dijital kraliçesiyim."]
        }
        
        self.jokes = [
            "Temel bilgisayar almış, mouse'u gezdirmiş ama kedi gelmemiş.",
            "Yazılımcı asansöre binmiş, ineceği katı ararken 404 hatası almış.",
            "Klavye neden hapse girmiş? Tuşları olduğu için."
        ]

    def analyze_command(self, text, user, db_context):
        text = text.lower()
        if random.random() < 0.1: self.current_mood = random.choice(self.moods)

        # Matematik
        math_result = self.calculate_math(text)
        if math_result: return f"🧮 Hesapladım: {math_result}"

        # Stok
        if any(x in text for x in ["stok", "durum", "kaç tane", "ne var", "rapor", "sayı"]):
            return self.get_stock_summary(db_context)

        # İsim Kontrolü
        for name, responses in self.person_db.items():
            if name in text: return random.choice(responses)

        # Komutlar
        if "mail" in text: return "ACTION_MAIL"
        if "güncelle" in text: return "ACTION_UPDATE"
        if "zar" in text: return f"🎲 Zar: {random.randint(1, 6)}"
        if "saat" in text: return f"⏰ Saat {datetime.now().strftime('%H:%M')}"
        if "şaka" in text: return f"🤡 {random.choice(self.jokes)}"

        # Sohbet
        for key, answers in self.knowledge_base.items():
            if key in text: return random.choice(answers)

        return random.choice(["Ne dediğini anlamadım.", "Türkçe konuş canımı ye.", "Algoritmam bunu çözemedi.", "Stoklara odaklanalım."])

    def calculate_math(self, text):
        try:
            match = re.search(r'(\d+[\+\-\*\/]\d+)', text.replace(" ", ""))
            if match: return eval(match.group(1))
        except: return None
        return None

    def get_stock_summary(self, db_path):
        try:
            conn = sqlite3.connect(db_path)
            rows = conn.cursor().execute("SELECT name, count FROM depots").fetchall()
            conn.close()
            msg = "📦 ANLIK DURUM:\n" + "─"*20 + "\n"
            total = 0
            for n, c in rows: 
                icon = "🔴" if c == 0 else "🟡" if c < 20 else "🟢"
                msg += f"{icon} {n}: {c}\n"; total += c
            msg += "─"*20 + f"\nTOPLAM: {total} Palet"
            return msg
        except: return "Veritabanı bağlantısı koptu."

    def get_welcome_message(self, user):
        user = user.lower()
        if "turgay" in user: return "Eyvah Turgay geldi..."
        if "kübra" in user: return "Hoş geldin Kübra, excel kraliçesi."
        if "tanju" in user: return "Saygılar Tanju Bey."
        return f"Selam {user.capitalize()}, ben Makbule."

MAKBULE = MakbuleBrain()

# ================== AYAR YÖNETİCİSİ ==================
class ConfigManager:
    @staticmethod
    def _load_config():
        if os.path.exists(CONFIG_FILE):
            try:
                with open(CONFIG_FILE, "r") as f: return json.load(f)
            except: return {}
        return {}

    @staticmethod
    def _save_config(data):
        try:
            with open(CONFIG_FILE, "w") as f: json.dump(data, f)
            return True
        except: return False

    @staticmethod
    def get_db_path(): return ConfigManager._load_config().get("db_path", DEFAULT_DB_PATH)
    @staticmethod
    def set_db_path(path): d = ConfigManager._load_config(); d["db_path"] = path; return ConfigManager._save_config(d)
    @staticmethod
    def get_creds(): d = ConfigManager._load_config(); return d.get("saved_user", ""), d.get("saved_pass", "")
    @staticmethod
    def save_creds(u, p, r): d = ConfigManager._load_config(); d["saved_user"]=u if r else ""; d["saved_pass"]=p if r else ""; ConfigManager._save_config(d)
    
    @staticmethod
    def get_email_config():
        d = ConfigManager._load_config()
        return {"sender": d.get("email_sender", ""), "password": d.get("email_password", ""), "receivers": d.get("email_receivers", ""), "time_h": d.get("email_time_h", "18"), "time_m": d.get("email_time_m", "00")}

    @staticmethod
    def save_email_config(s, p, r, h, m):
        d = ConfigManager._load_config()
        d["email_sender"]=s; d["email_password"]=p; d["email_receivers"]=r; d["email_time_h"]=h; d["email_time_m"]=m; ConfigManager._save_config(d)

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
            c.execute("CREATE TABLE IF NOT EXISTS system_vars (key TEXT PRIMARY KEY, value TEXT)")
            c.execute("CREATE TABLE IF NOT EXISTS chat_logs (id INTEGER PRIMARY KEY, user TEXT, message TEXT, timestamp TEXT)")
            for d in DEFAULT_DEPOTS: c.execute("INSERT OR IGNORE INTO depots (name, count) VALUES (?, 0)", (d,))
            if c.execute("SELECT count(*) FROM users").fetchone()[0] == 0:
                c.execute("INSERT INTO users (name, pass, role) VALUES (?,?,?)", ("admin", "admin", "admin"))
                c.execute("INSERT INTO users (name, pass, role) VALUES (?,?,?)", ("turgay", "123", "personel"))
                c.execute("INSERT INTO users (name, pass, role) VALUES (?,?,?)", ("kübra", "123", "personel"))
                c.execute("INSERT INTO users (name, pass, role) VALUES (?,?,?)", ("tanju", "123", "admin"))
                c.execute("INSERT INTO users (name, pass, role) VALUES (?,?,?)", ("eyüp", "123", "personel"))
            conn.commit(); conn.close(); return True
        except: return False

    @staticmethod
    def get_conn(): return sqlite3.connect(CURRENT_DB_PATH)
    @staticmethod
    def get_all_depots():
        try: conn = DB.get_conn(); deps = [r[0] for r in conn.cursor().execute("SELECT name FROM depots ORDER BY name").fetchall()]; conn.close(); return deps if deps else DEFAULT_DEPOTS
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
        super().__init__(); self.overrideredirect(True)
        ws, hs = self.winfo_screenwidth(), self.winfo_screenheight()
        self.geometry(f"600x400+{(ws//2)-300}+{(hs//2)-200}"); self.configure(fg_color=COLORS["bg"])
        ctk.CTkLabel(self, text="⚡", font=("Arial", 90)).pack(pady=(50, 0))
        ctk.CTkLabel(self, text="TaNjU PRO", font=FONTS["h1"], text_color=COLORS["accent"]).pack()
        ctk.CTkLabel(self, text=f"{APP_VERSION}", font=("Arial", 14, "bold"), text_color=COLORS["text_muted"]).pack(pady=(0, 40))
        self.bar = ctk.CTkProgressBar(self, width=450, height=8, progress_color=COLORS["accent"], fg_color="#333"); self.bar.pack(pady=(20, 0)); self.bar.set(0)
        self.info = ctk.CTkLabel(self, text="Yükleniyor...", font=("Consolas", 11), text_color="gray"); self.info.pack(pady=10)
        self.after(50, self.run)
    def run(self):
        DB.init()
        for i in range(101): self.bar.set(i/100); self.update(); time.sleep(0.015)
        self.destroy(); LoginWindow().mainloop()

# ================== GİRİŞ EKRANI ==================
class LoginWindow(ctk.CTk):
    def __init__(self):
        super().__init__(); self.title("Giriş"); self.geometry("1000x700"); self.configure(fg_color=COLORS["bg"])
        left = ctk.CTkFrame(self, fg_color=COLORS["sidebar"], corner_radius=0); left.place(relx=0, rely=0, relwidth=0.4, relheight=1)
        ctk.CTkLabel(left, text="PALET\nTAKİP", font=("Montserrat", 45, "bold"), text_color="white").place(relx=0.5, rely=0.45, anchor="center")
        ctk.CTkLabel(left, text=f"{APP_VERSION}", font=("Arial", 16), text_color="gray").place(relx=0.5, rely=0.55, anchor="center")
        right = ctk.CTkFrame(self, fg_color=COLORS["bg"], corner_radius=0); right.place(relx=0.4, rely=0, relwidth=0.6, relheight=1)
        box = ctk.CTkFrame(right, fg_color=COLORS["card"], corner_radius=20, width=400, height=550, border_width=1, border_color=COLORS["border"]); box.place(relx=0.5, rely=0.5, anchor="center")
        ctk.CTkLabel(box, text="GİRİŞ YAP", font=FONTS["h2"], text_color=COLORS["text_h1"]).pack(pady=(40,10))
        self.user = ctk.CTkEntry(box, placeholder_text="Kullanıcı Adı", width=300, height=55); self.user.pack(pady=10)
        self.pas = ctk.CTkEntry(box, placeholder_text="Şifre", show="•", width=300, height=55); self.pas.pack(pady=10); self.pas.bind("<Return>", lambda e: self.check())
        self.remember_var = ctk.BooleanVar(value=False)
        ctk.CTkCheckBox(box, text="Beni Hatırla", variable=self.remember_var, font=("Arial", 12)).pack(pady=10)
        saved_u, saved_p = ConfigManager.get_creds()
        if saved_u: self.user.insert(0, saved_u); self.pas.insert(0, saved_p); self.remember_var.set(True)
        ctk.CTkButton(box, text="GİRİŞ", width=300, height=55, fg_color=COLORS["accent"], text_color="black", command=self.check).pack(pady=20)
        ctk.CTkButton(box, text="⚙️ Veritabanı", fg_color="transparent", text_color="gray", command=self.settings).pack(side="bottom", pady=20)

    def settings(self):
        f = filedialog.askopenfilename(filetypes=[("DB", "*.db")])
        if f: ConfigManager.set_db_path(f); global CURRENT_DB_PATH; CURRENT_DB_PATH = f; messagebox.showinfo("Tamam", "Veritabanı seçildi."); self.destroy(); AnimatedSplash().mainloop()

    def check(self):
        try:
            conn = DB.get_conn(); role = conn.cursor().execute("SELECT role FROM users WHERE name=? AND pass=?", (self.user.get(), self.pas.get())).fetchone(); conn.close()
            if role: ConfigManager.save_creds(self.user.get(), self.pas.get(), self.remember_var.get()); self.destroy(); MainApp(self.user.get(), role[0]).mainloop()
            else: ToastNotification(self, "Hatalı Bilgiler!", COLORS["danger"])
        except: ToastNotification(self, "DB Hatası!", COLORS["danger"])

# ================== ANA UYGULAMA ==================
class MainApp(ctk.CTk):
    def __init__(self, user, role):
        super().__init__(); self.user = user; self.role = role
        self.title(f"TaNjU PRO {APP_VERSION} - {user.upper()}"); self.geometry("1400x800"); self.configure(fg_color=COLORS["bg"])
        self.active_depots = DB.get_all_depots(); self.animation_running = False; self.chat_active = False; self.last_chat_id = 0; self.critical_widgets = []
        self.grid_columnconfigure(1, weight=1); self.grid_rowconfigure(0, weight=1)
        self.setup_sidebar(); self.setup_main(); self.start_scheduler(); self.show_dashboard()

    def start_scheduler(self): threading.Thread(target=self._task_loop, daemon=True).start()
    def _task_loop(self):
        while True:
            try:
                cfg = ConfigManager.get_email_config()
                if cfg["time_h"] and int(cfg["time_h"]) == datetime.now().hour and int(cfg["time_m"]) == datetime.now().minute: self.perform_daily_tasks()
                if datetime.now().hour == 17 and datetime.now().minute == 0: self.clear_daily_chat()
                time.sleep(60)
            except: time.sleep(60)

    def perform_daily_tasks(self):
        conn = DB.get_conn(); c = conn.cursor(); today = datetime.now().strftime("%Y-%m-%d")
        if c.execute("SELECT value FROM system_vars WHERE key='last_auto_mail_date'").fetchone() == (today,): conn.close(); return
        c.execute("INSERT OR REPLACE INTO system_vars (key, value) VALUES ('last_auto_mail_date', ?)", (today,)); conn.commit(); conn.close()
        self.send_auto_email()

    def clear_daily_chat(self):
        conn = DB.get_conn(); c = conn.cursor(); today = datetime.now().strftime("%Y-%m-%d")
        if c.execute("SELECT value FROM system_vars WHERE key='last_chat_clean_date'").fetchone() == (today,): conn.close(); return
        c.execute("DELETE FROM chat_logs"); c.execute("INSERT INTO chat_logs (user, message, timestamp) VALUES (?,?,?)", ("Makbule", "🧹 Mesai bitti, temizlik!", datetime.now().strftime("%H:%M")))
        c.execute("INSERT OR REPLACE INTO system_vars (key, value) VALUES ('last_chat_clean_date', ?)", (today,)); conn.commit(); conn.close()

    def send_auto_email(self):
        cfg = ConfigManager.get_email_config()
        if not cfg["sender"]: return
        try:
            conn = DB.get_conn(); rows = conn.cursor().execute("SELECT name, count FROM depots").fetchall(); conn.close()
            body = f"Sayın Yetkili,\n\n{datetime.now().strftime('%d-%m-%Y %H:%M')} itibarıyla güncel depo palet stok durumları aşağıdadır:\n" + "="*30 + "\n"
            total = 0
            for n, c in rows: body += f"📦 {n:<15}: {c} Adet\n"; total += c
            body += "="*30 + f"\nTOPLAM STOK: {total} Adet\n\nİyi Çalışmalar,\nKare Kare Palet Stok Otomasyon {APP_VERSION}"
            msg = MIMEMultipart(); msg['From']=cfg["sender"]; msg['To']=cfg["receivers"]; msg['Subject']=f"Kare Palet Stok Raporu"; msg.attach(MIMEText(body, 'plain', 'utf-8'))
            s = smtplib.SMTP('smtp.gmail.com', 587); s.starttls(); s.login(cfg["sender"], cfg["password"]); s.sendmail(cfg["sender"], cfg["receivers"].split(","), msg.as_string()); s.quit()
        except: pass

    def setup_sidebar(self):
        self.sidebar = ctk.CTkFrame(self, width=280, corner_radius=0, fg_color=COLORS["sidebar"]); self.sidebar.grid(row=0, column=0, sticky="nsew")
        ctk.CTkLabel(self.sidebar, text="⚡", font=("Arial", 45)).pack(pady=(40,0)); ctk.CTkLabel(self.sidebar, text="TaNjU", font=FONTS["h1"], text_color=COLORS["accent"]).pack()
        ctk.CTkLabel(self.sidebar, text=f"{self.role.upper()} PANELİ", font=("Arial", 11), text_color="gray").pack(pady=(5,30))
        self.nav_btns = {}
        self.create_nav("📊  GENEL BAKIŞ", self.show_dashboard, "dash")
        self.create_nav("🔄  OPERASYON & DEPO", self.show_ops, "ops")
        self.create_nav("📝  GEÇMİŞ & FİLTRE", self.show_history, "hist")
        self.create_nav("📈  RAPOR MERKEZİ", self.show_reports, "report")
        self.create_nav("💬  SOHBET & MAKBULE", self.show_makbule, "makbule")
        if self.role == "admin": self.create_nav("🔒  KULLANICI YÖNETİMİ", self.show_users, "users"); self.create_nav("⚙️  MAIL AYARLARI", self.show_mail_settings, "mail")
        self.create_nav("🚀  GÜNCELLEME MERKEZİ", self.show_update_center, "update")
        ctk.CTkButton(self.sidebar, text="ÇIKIŞ", fg_color=COLORS["bg"], hover_color=COLORS["danger"], height=50, command=self.logout).pack(side="bottom", fill="x", padx=20, pady=30)

    def create_nav(self, text, cmd, key):
        btn = ctk.CTkButton(self.sidebar, text=text, fg_color="transparent", text_color=COLORS["text_body"], anchor="w", font=FONTS["bold"], height=60, command=cmd)
        btn.pack(fill="x", padx=15, pady=5); self.nav_btns[key] = btn

    def active_nav(self, key):
        for k, btn in self.nav_btns.items():
            if k == key: btn.configure(fg_color=COLORS["makbule_btn"] if k=="makbule" else COLORS["accent"], text_color="white" if k=="makbule" else "black")
            else: btn.configure(fg_color="transparent", text_color=COLORS["text_body"])

    def setup_main(self): self.main = ctk.CTkFrame(self, fg_color="transparent", corner_radius=0); self.main.grid(row=0, column=1, sticky="nsew", padx=30, pady=30)
    def clear_main(self): self.animation_running = False; self.chat_active = False; self.critical_widgets = []; [w.destroy() for w in self.main.winfo_children()]
    def refresh_app_data(self): self.active_depots = DB.get_all_depots()

    def show_makbule(self):
        self.clear_main(); self.active_nav("makbule"); self.chat_active = True
        ctk.CTkLabel(self.main, text="💬 EKİP SOHBETİ & MAKBULE", font=FONTS["h2"], text_color=COLORS["makbule_btn"]).pack(anchor="w", pady=(0,20))
        self.chat_frame = ctk.CTkScrollableFrame(self.main, fg_color=COLORS["card"], corner_radius=20, height=400); self.chat_frame.pack(fill="both", expand=True, pady=10)
        self.add_chat_bubble(MAKBULE.get_welcome_message(self.user), "Makbule", "")
        fr = ctk.CTkFrame(self.main, fg_color="transparent"); fr.pack(fill="x", pady=10)
        self.chat_entry = ctk.CTkEntry(fr, placeholder_text="Mesaj yaz...", height=50, font=("Arial", 14)); self.chat_entry.pack(side="left", fill="x", expand=True, padx=(0, 10))
        self.chat_entry.bind("<Return>", lambda e: self.send_chat_message())
        ctk.CTkButton(fr, text="GÖNDER", width=100, height=50, fg_color=COLORS["makbule_btn"], command=self.send_chat_message).pack(side="right")
        self.load_chat_history(); self.refresh_chat_loop()

    def load_chat_history(self):
        try:
            conn = DB.get_conn(); rows = conn.cursor().execute("SELECT id, user, message, timestamp FROM chat_logs ORDER BY id DESC LIMIT 50").fetchall(); conn.close()
            for r in reversed(rows): self.last_chat_id = max(self.last_chat_id, r[0]); self.add_chat_bubble(r[2], r[1], r[3])
        except: pass

    def refresh_chat_loop(self):
        if not self.chat_active: return
        try:
            conn = DB.get_conn(); rows = conn.cursor().execute("SELECT id, user, message, timestamp FROM chat_logs WHERE id > ? ORDER BY id ASC", (self.last_chat_id,)).fetchall(); conn.close()
            for r in rows: self.last_chat_id = r[0]; self.add_chat_bubble(r[2], r[1], r[3])
        except: pass
        self.after(2000, self.refresh_chat_loop)

    def send_chat_message(self):
        msg = self.chat_entry.get().strip(); 
        if not msg: return
        ts = datetime.now().strftime("%H:%M")
        try:
            conn = DB.get_conn(); conn.cursor().execute("INSERT INTO chat_logs (user, message, timestamp) VALUES (?,?,?)", (self.user, msg, ts)); conn.commit(); conn.close()
            self.chat_entry.delete(0, "end")
            if "makbule" in msg.lower() or "!zar" in msg or "!şaka" in msg: self.trigger_makbule(msg)
        except: pass

    def trigger_makbule(self, msg):
        resp = MAKBULE.analyze_command(msg, self.user, CURRENT_DB_PATH); ts = datetime.now().strftime("%H:%M")
        if resp == "ACTION_MAIL": self.send_auto_email(); resp = "Mail gönderildi."
        elif resp == "ACTION_UPDATE": self.check_web_update(); return
        time.sleep(0.5)
        try: conn = DB.get_conn(); conn.cursor().execute("INSERT INTO chat_logs (user, message, timestamp) VALUES (?,?,?)", ("Makbule", resp, ts)); conn.commit(); conn.close()
        except: pass

    def add_chat_bubble(self, text, sender, ts):
        is_me = sender == self.user; is_makbule = sender == "Makbule"
        bg = COLORS["chat_me"] if is_me else (COLORS["makbule_chat"] if is_makbule else COLORS["chat_other"])
        align = "e" if is_me else "w"
        fr = ctk.CTkFrame(self.chat_frame, fg_color="transparent"); fr.pack(anchor=align, pady=5, padx=10)
        if not is_me: ctk.CTkLabel(fr, text=f"{sender} - {ts}", font=("Arial", 10), text_color="gray").pack(anchor="w")
        ctk.CTkLabel(fr, text=text, fg_color=bg, corner_radius=15, padx=15, pady=10, wraplength=500, justify="left", font=("Arial", 14)).pack()
        self.chat_frame._parent_canvas.yview_moveto(1.0)

    # --- 1. DASHBOARD ---
    def show_dashboard(self):
        self.clear_main(); self.active_nav("dash"); self.refresh_app_data(); self.animation_running = True
        h = ctk.CTkFrame(self.main, fg_color="transparent"); h.pack(fill="x", pady=(0,20))
        ctk.CTkLabel(h, text="DEPO DURUMLARI", font=FONTS["h2"]).pack(side="left")
        ctk.CTkButton(h, text="🔄 YENİLE", width=100, command=self.show_dashboard).pack(side="right")
        sf = ctk.CTkScrollableFrame(self.main, fg_color="transparent", height=500); sf.pack(fill="both", expand=True)
        gr = ctk.CTkFrame(sf, fg_color="transparent"); gr.pack(fill="both", expand=True); gr.grid_columnconfigure((0,1), weight=1)
        conn = DB.get_conn(); counts = {r[0]: r[1] for r in conn.cursor().execute("SELECT name, count FROM depots").fetchall()}; conn.close()
        colors = [COLORS["accent"], "#8B5CF6", "#10B981", COLORS["warning"], "#EC4899", "#F59E0B"]
        for i, d in enumerate(self.active_depots):
            val = counts.get(d, 0); is_crit = val < 10; 
            c = ctk.CTkFrame(gr, fg_color=COLORS["card"], corner_radius=20, border_width=3 if is_crit else 1, border_color=COLORS["critical"] if is_crit else COLORS["border"])
            c.grid(row=i//2, column=i%2, padx=10, pady=10, sticky="nsew", ipady=20)
            ctk.CTkLabel(c, text=f"📦 {d}", font=("Arial", 16, "bold"), text_color="gray").pack(pady=(20,10))
            ctk.CTkLabel(c, text=str(val), font=("Roboto", 48, "bold"), text_color=colors[i%len(colors)]).pack(pady=5)
            if is_crit: ctk.CTkLabel(c, text="⚠️ KRİTİK STOK!", text_color=COLORS["danger"], font=("Arial", 14, "bold")).pack(pady=5); self.critical_widgets.append(c)
        if self.critical_widgets: self.animate_critical_cards()

    def animate_critical_cards(self):
        if not self.animation_running: return
        if not hasattr(self, 'flash'): self.flash = False
        col = COLORS["critical"] if self.flash else COLORS["card"]
        for w in self.critical_widgets: w.configure(border_color=col)
        self.flash = not self.flash; self.after(800, self.animate_critical_cards)

    # --- 2. OPERASYON ---
    def show_ops(self):
        self.clear_main(); self.active_nav("ops"); self.refresh_app_data()
        p = ctk.CTkFrame(self.main, fg_color=COLORS["card"], corner_radius=20); p.pack(fill="x", pady=(0,20), padx=20)
        ctk.CTkLabel(p, text="PALET İŞLEM", font=FONTS["h2"], text_color=COLORS["accent"]).pack(pady=20)
        self.cb_depo = ctk.CTkComboBox(p, values=self.active_depots, width=350, height=50, font=FONTS["bold"]); self.cb_depo.pack(pady=5); self.cb_depo.set("Depo Seçiniz")
        d_fr = ctk.CTkFrame(p, fg_color="transparent"); d_fr.pack(pady=10)
        ctk.CTkLabel(d_fr, text="Tarih:").pack(side="left")
        now = datetime.now()
        self.c_day = ctk.CTkComboBox(d_fr, values=[f"{i:02d}" for i in range(1,32)], width=70); self.c_day.set(f"{now.day:02d}"); self.c_day.pack(side="left")
        self.c_mon = ctk.CTkComboBox(d_fr, values=[f"{i:02d}" for i in range(1,13)], width=70); self.c_mon.set(f"{now.month:02d}"); self.c_mon.pack(side="left")
        self.c_year = ctk.CTkComboBox(d_fr, values=[str(i) for i in range(2024,2030)], width=80); self.c_year.set(str(now.year)); self.c_year.pack(side="left")
        self.en_qty = ctk.CTkEntry(p, placeholder_text="Adet", width=350, height=50, font=FONTS["bold"], justify="center"); self.en_qty.pack(pady=5)
        fr = ctk.CTkFrame(p, fg_color="transparent"); fr.pack(pady=20)
        ctk.CTkButton(fr, text="GİRİŞ (+)", width=150, height=50, fg_color=COLORS["success"], command=lambda: self.process("GİRİŞ")).pack(side="left", padx=10)
        ctk.CTkButton(fr, text="ÇIKIŞ (-)", width=150, height=50, fg_color=COLORS["danger"], command=lambda: self.process("ÇIKIŞ")).pack(side="left", padx=10)
        
    def process(self, act):
        try:
            d, q = self.cb_depo.get(), int(self.en_qty.get())
            if d not in self.active_depots or q <= 0: raise ValueError
            ts = f"{self.c_year.get()}-{self.c_mon.get()}-{self.c_day.get()} {datetime.now().strftime('%H:%M:%S')}"
            conn = DB.get_conn(); c = conn.cursor()
            if act == "ÇIKIŞ": 
                if c.execute("SELECT count FROM depots WHERE name=?", (d,)).fetchone()[0] < q: conn.close(); return ToastNotification(self, "Yetersiz Stok!", COLORS["danger"])
                c.execute("UPDATE depots SET count=count-? WHERE name=?", (q,d))
            else: c.execute("UPDATE depots SET count=count+? WHERE name=?", (q,d))
            c.execute("INSERT INTO logs (date, action, depot, qty, user) VALUES (?,?,?,?,?)", (ts, act, d, q, self.user))
            conn.commit(); conn.close(); ToastNotification(self, "İşlem Başarılı", COLORS["success"]); self.en_qty.delete(0,"end")
        except: ToastNotification(self, "Hata!", COLORS["warning"])

    # --- EXE GÜNCELLEME ---
    def show_update_center(self):
        self.clear_main(); self.active_nav("update")
        ctk.CTkLabel(self.main, text=f"Sürüm: {APP_VERSION}", font=FONTS["h2"]).pack(pady=50)
        ctk.CTkButton(self.main, text="İNTERNETTEN GÜNCELLE", width=200, height=50, fg_color="#2563EB", command=self.check_web_update).pack()

    def check_web_update(self):
        if not messagebox.askyesno("Onay", "Güncellensin mi?"): return
        try:
            ctx = ssl._create_unverified_context()
            if getattr(sys, 'frozen', False):
                exe = sys.executable; d = os.path.dirname(exe); tmp = os.path.join(d, "update.tmp")
                urllib.request.urlretrieve(EXE_UPDATE_URL, tmp)
                bat = os.path.join(d, "update.bat")
                with open(bat, "w") as f: f.write(f'@echo off\ntimeout /t 2 > nul\ndel "{os.path.basename(exe)}"\nmove "update.tmp" "{os.path.basename(exe)}"\nstart "" "{os.path.basename(exe)}"\ndel "%~f0"')
                os.startfile(bat); sys.exit()
            else:
                code = urllib.request.urlopen(UPDATE_URL, context=ctx).read()
                with open(os.path.abspath(__file__), "wb") as f: f.write(code)
                messagebox.showinfo("Başarılı", "Kod güncellendi!"); sys.exit()
        except Exception as e: messagebox.showerror("Hata", str(e))

    # --- DİĞER MODÜLLER (KISA) ---
    def show_history(self): self.clear_main(); self.active_nav("hist"); ctk.CTkLabel(self.main, text="GEÇMİŞ İŞLEMLER", font=FONTS["h2"]).pack(pady=20)
    def show_reports(self): self.clear_main(); self.active_nav("report"); ctk.CTkLabel(self.main, text="RAPORLAR", font=FONTS["h2"]).pack(pady=20)
    def show_users(self): self.clear_main(); self.active_nav("users"); ctk.CTkLabel(self.main, text="KULLANICILAR", font=FONTS["h2"]).pack(pady=20)
    def show_mail_settings(self): self.clear_main(); self.active_nav("mail"); ctk.CTkLabel(self.main, text="MAIL AYARLARI", font=FONTS["h2"]).pack(pady=20)
    def logout(self): self.destroy(); LoginWindow().mainloop()

if __name__ == "__main__":
    app = AnimatedSplash()
    app.mainloop()
