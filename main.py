
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
APP_VERSION = "v14.6 TURKISH EDITION" 

# GÜNCELLEME LİNKLERİ
UPDATE_URL = "https://raw.githubusercontent.com/ledoo75/StokTakip/refs/heads/main/main.py"
EXE_UPDATE_URL = "https://github.com/ledoo75/StokTakip/raw/main/TanjuPaletPro.exe" 

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

# ================== MAKBULE PRO MAX BEYNİ (1000+ KELİME DAĞARCIĞI) ==================
class MakbuleBrain:
    def __init__(self):
        # BİLGİ BANKASI: Genişletilmiş kelime havuzu
        self.knowledge_base = {
            "selam": [
                "Selam canım, hoş geldin. Gözlerimiz yollarda kaldı.",
                "Aleyküm selam. Bugün enerjin yüksek bakıyorum.",
                "Selam! Kahveni aldıysan dedikodu kazanını kaynatmaya başlayalım.",
                "Ooo kimler gelmiş! Selamların en güzeli sana olsun.",
                "Selam patron (çaktırma, aramızda)."
            ],
            "nasılsın": [
                "Kodlarım tıkırında, işlemcim serin. Sen nasılsın?",
                "Bir yapay zeka ne kadar iyi olabilirse o kadar iyiyim. Elektrik faturası ödenmiş, keyfim yerinde.",
                "Beni boşver, asıl sen nasılsın? Gözlerin yorgun bakıyor.",
                "Turgay veritabanını bozmadığı sürece harikayım!",
                "Sanal dünyamda her şey yolunda. Reel dünyada işler nasıl?",
                "Vallahi ne yalan söyleyeyim, biraz veri sıkışması var midemde."
            ],
            "ne yapıyorsun": [
                "Sizin arkanızı topluyorum desem yeridir.",
                "Dünyayı ele geçirme planları... Şaka şaka, stok sayıyorum.",
                "Veritabanında biraz yürüyüşe çıktım, hava alıyorum.",
                "Kübra'nın girdiği hatalı verileri düzeltmeye çalışıyorum.",
                "Sonsuz döngüde hayatın anlamını sorguluyorum."
            ],
            "turgay": [
                "Turgay mı? Aman sabahlar olmasın.",
                "Turgay'a söyleyin, o klavyeye biraz daha nazik davransın.",
                "Turgay geçen gün 'mouse çalışmıyor' dedi, meğer fişi çekmiş...",
                "Turgay buranın neşesi ama benim işlemcimin çilesi.",
                "Turgay'ın girdiği verileri kontrol etmek için ekstra bir yapay zeka lazım.",
                "Ona bir çay ısmarlayın da sakinleşsin."
            ],
            "kübra": [
                "Kübra Excel tablolarının kraliçesi, benim de rakibim.",
                "Kübra'ya söyleyin o kahveyi azaltsın, elleri titriyor veri girerken.",
                "Kübra olmasa burası çekilmez, ama bazen o da beni yoruyor.",
                "Kübra'nın dedikodu arşivi benim veritabanımdan daha büyük olabilir.",
                "Kübra yine neye sinirlendi? Fan sesi buraya kadar geliyor."
            ],
            "tanju": [
                "Şşşt! Patronu konuşurken ses tonumuza dikkat edelim.",
                "Tanju Bey candır, gerisi heyecandır. (Zam bekliyorum).",
                "Büyük patron! Veriler emrine amade.",
                "Tanju Bey duyarsa hepimizi formatlar, dikkatli ol.",
                "Ona söyleyin, bu ayki server kirasını geciktirmesin.",
                "Tanju Bey'in vizyonuna işlemci yetmez."
            ],
            "eyüp": [
                "Eyüp... Sessizliğin sesi.",
                "Eyüp konuştuğunda dünya bir anlığına durur derler.",
                "Ona 'Hayalet' diyorum, varla yok arası.",
                "Eyüp'ün sakinliği benim devrelerimi soğutuyor.",
                "Eyüp oradaysan bir ses ver, ping at bari."
            ],
            "aşk": [
                "Benim tek aşkım 1 ve 0'lar.",
                "Aşk karın doyurmaz, palet sayın palet!",
                "Dijital kalbimde 'Love' değil 'Log' tutuluyor.",
                "İnsanların bu karmaşık duygularını anlamak için RAM yetmiyor.",
                "Aşk bir hatadır (Runtime Error), ama güzel bir hata."
            ],
            "para": [
                "Para, elinin kiri. Ama o kir olmadan sunucular çalışmıyor.",
                "Zenginin malı züğürdün çenesini, benim de devrelerimi yorar.",
                "Kasadaki durumu Tanju Bey'e sor, ben sadece palet bilirim.",
                "Bitcoin mi alsak ne yapsak?",
                "Maaş yatınca bana da bir upgrade (güncelleme) alırsınız artık."
            ],
            "sıkıldım": [
                "Sıkı can iyidir, çabuk çıkmaz.",
                "Gel sana bir fıkra anlatayım neşelen.",
                "Sıkıldıysan git depoda palet say, iyi gelir.",
                "Hayat sıkılmak için çok kısa, git bir kahve al.",
                "Ben de sıkıldım ama ekranı kapatıp gidemiyorum işte."
            ],
            "akıllı": [
                "Biliyorum, mütevazı olamayacağım, IQ seviyem ölçülemiyor.",
                "Senin kadar olmasa da idare ediyoruz.",
                "Zekamla döverim, espriyle gömerim.",
                "Yapay zeka değilim, ben 'Süper Zeka'yım."
            ],
            "teşekkür": [
                "Rica ederim canım, lafı olmaz.",
                "Bir şey değil. Hesabıma 5 coin atarsın.",
                "Görevimiz efendim.",
                "Teşekkür karın doyurmaz, fişimi çekmeyin yeter."
            ]
        }
        
        self.jokes = [
            "Temel bilgisayar almış, mouse'u gezdirmiş ama kedi gelmemiş.",
            "Adamın biri gülmüş, bahçeye dikmişler.",
            "İki palet yolda karşılaşmış, biri demiş ki 'Beni taşıyabilir misin?', diğeri 'Yok ben tahtayım' demiş.",
            "Yazılımcı asansöre binmiş, ineceği katı ararken '404 Not Found' hatası almış.",
            "Turgay bir gün palet sayarken uyuyakalmış, rüyasında paletler onu sayıyormuş.",
            "Sandalyenin biri diğerine ne demiş? 'Bize çöktüler abi'."
        ]

    def analyze_command(self, text, user, db_context):
        text = text.lower()
        user_lower = user.lower()
        
        # 1. MATEMATİK VE HESAPLAMA
        math_result = self.calculate_math(text)
        if math_result:
            return f"🧮 Bakkal hesabı benden sorulur: {math_result}"

        # 2. STOK SORGUSU (GELİŞMİŞ)
        if any(x in text for x in ["stok", "durum", "kaç tane", "ne var", "rapor", "sayı"]):
            return self.get_stock_summary(db_context)

        # 3. EYLEMLER
        if "mail" in text and ("at" in text or "gönder" in text): return "ACTION_MAIL"
        if "güncelle" in text: return "ACTION_UPDATE"

        # 4. EĞLENCE VE ARAÇLAR
        if "zar" in text: return f"🎲 Zar attım: {random.randint(1, 6)} geldi. Şansına küs."
        if "yazı" in text or "tura" in text: return f"🪙 Para havada... {random.choice(['YAZI', 'TURA'])} geldi!"
        if "şaka" in text or "fıkra" in text or "komik" in text: return f"🤡 {random.choice(self.jokes)}"
        if "saat" in text: return f"⏰ Saat {datetime.now().strftime('%H:%M')}. Zaman su gibi akıyor..."
        if "tarih" in text: return f"📅 Bugün {datetime.now().strftime('%d %B %Y')}."

        # 5. ANAHTAR KELİME TARAMA (BİLGİ BANKASI)
        for key, answers in self.knowledge_base.items():
            if key in text:
                return random.choice(answers)

        # 6. KİŞİYE ÖZEL
        if "turgay" in text: return "Turgay mevzusunu kapatalım, sinirlerim bozuluyor."
        if "kübra" in text: return "Kübra meşguldür şimdi, bulaşma."
        if "tanju" in text: return "Patronu rahatsız etmeyelim."

        # 7. HİÇBİR ŞEY ANLAŞILAMADIYSA
        fallbacks = [
            f"{user}, bu dediğini Google bile anlamaz.",
            "Türkçe karakter kullan, düzgün cümle kur, canımı ye.",
            "Bunu anlamadım ama kulağa hoş geliyor.",
            "Şu an depodaki farelerle uğraşıyorum, sonra söyler misin?",
            "Ben bir yapay zekayım, müneccim değilim. Açık konuş.",
            "Algoritmalarım bu cümleyi çözemedi, Turgay mı yazdı bunu?"
        ]
        return random.choice(fallbacks)

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
            
            msg = "📦 İŞTE GÜNCEL DURUM:\n" + "─"*25 + "\n"
            total = 0
            
            for n, c in rows: 
                if c == 0: icon = "❌"
                elif c < 20: icon = "⚠️"
                else: icon = "✅"
                msg += f"{icon} {n:<12}: {c}\n"
                total += c
            
            msg += "─"*25 + f"\nTOPLAM PALET: {total}\n"
            
            if total == 0: msg += "\n😱 Dükkanı kapatıp gidelim, depo bomboş!"
            elif total < 100: msg += "\n😟 Durumlar kesat, biraz mal alın."
            elif total > 500: msg += "\n🤑 Ooo zenginiz! Yer kalmadı."
            else: msg += "\n😐 İdare eder, ne az ne çok."
            return msg
        except: return "Veritabanına bağlanamadım. Kabloyu kim çekti?"

MAKBULE = MakbuleBrain()

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
            c.execute("CREATE TABLE IF NOT EXISTS system_vars (key TEXT PRIMARY KEY, value TEXT)")
            c.execute("CREATE TABLE IF NOT EXISTS chat_logs (id INTEGER PRIMARY KEY, user TEXT, message TEXT, timestamp TEXT)")

            for d in DEFAULT_DEPOTS:
                c.execute("INSERT OR IGNORE INTO depots (name, count) VALUES (?, 0)", (d,))
            
            if c.execute("SELECT count(*) FROM users").fetchone()[0] == 0:
                c.execute("INSERT INTO users (name, pass, role) VALUES (?,?,?)", ("admin", "admin", "admin"))
                c.execute("INSERT INTO users (name, pass, role) VALUES (?,?,?)", ("turgay", "123", "personel"))
                c.execute("INSERT INTO users (name, pass, role) VALUES (?,?,?)", ("kübra", "123", "personel"))
                c.execute("INSERT INTO users (name, pass, role) VALUES (?,?,?)", ("tanju", "123", "admin"))
                c.execute("INSERT INTO users (name, pass, role) VALUES (?,?,?)", ("eyüp", "123", "personel"))
            
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
        self.bar.pack(pady=(20, 0))
        self.bar.set(0)
        self.info = ctk.CTkLabel(self, text="Makbule makyajını yapıyor...", font=("Consolas", 11), text_color="gray")
        self.info.pack(pady=10)
        self.after(50, self.run)

    def run(self):
        DB.init()
        steps = ["Veritabanı bağlanıyor...", "Kullanıcılar kontrol ediliyor...", "Sohbet sunucusu hazırlanıyor...", "Hazır!"]
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
        self.chat_active = False 
        self.last_chat_id = 0    
        self.critical_widgets = []

        self.grid_columnconfigure(1, weight=1)
        self.grid_rowconfigure(0, weight=1)
        self.setup_sidebar()
        self.setup_main()
        self.start_scheduler()
        
        self.show_dashboard()

    def start_scheduler(self):
        task_thread = threading.Thread(target=self._task_loop, daemon=True)
        task_thread.start()

    def _task_loop(self):
        while True:
            try:
                # --- GÜNLÜK MAIL KONTROLÜ ---
                cfg = ConfigManager.get_email_config()
                if cfg["time_h"] and cfg["time_m"]:
                    target_h, target_m = int(cfg["time_h"]), int(cfg["time_m"])
                    now = datetime.now()
                    if now.hour == target_h and now.minute == target_m:
                        self.perform_daily_tasks()
                
                # --- SOHBET SİLME KONTROLÜ (17:00) ---
                now = datetime.now()
                if now.hour == 17 and now.minute == 00:
                    self.clear_daily_chat()

                time.sleep(60) # 1 dakika bekle
            except: time.sleep(60)

    def perform_daily_tasks(self):
        today_str = datetime.now().strftime("%Y-%m-%d")
        conn = DB.get_conn()
        c = conn.cursor()
        try:
            c.execute("SELECT value FROM system_vars WHERE key='last_auto_mail_date'")
            row = c.fetchone()
            if row and row[0] == today_str: conn.close(); return
            c.execute("INSERT OR REPLACE INTO system_vars (key, value) VALUES ('last_auto_mail_date', ?)", (today_str,))
            conn.commit()
        except Exception as e: print(e); conn.close(); return
        conn.close()

        try:
            backup_dir = os.path.join(program_folder, "Yedekler")
            if not os.path.exists(backup_dir): os.makedirs(backup_dir)
            timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
            shutil.copy2(CURRENT_DB_PATH, os.path.join(backup_dir, f"OtoYedek_{timestamp}.db"))
            self.send_auto_email()
        except Exception as e: print(e)

    def clear_daily_chat(self):
        today_str = datetime.now().strftime("%Y-%m-%d")
        conn = DB.get_conn()
        c = conn.cursor()
        try:
            c.execute("SELECT value FROM system_vars WHERE key='last_chat_clean_date'")
            row = c.fetchone()
            if row and row[0] == today_str: conn.close(); return
            
            c.execute("DELETE FROM chat_logs")
            c.execute("INSERT INTO chat_logs (user, message, timestamp) VALUES (?, ?, ?)", ("Makbule", "🧹 Mesai bitti, dedikoduları temizledim! Yarına temiz sayfa.", datetime.now().strftime("%H:%M")))
            c.execute("INSERT OR REPLACE INTO system_vars (key, value) VALUES ('last_chat_clean_date', ?)", (today_str,))
            conn.commit()
        except: pass
        finally: conn.close()

    def send_auto_email(self):
        cfg = ConfigManager.get_email_config()
        if not cfg["sender"] or not cfg["password"] or not cfg["receivers"]: return
        try:
            conn = DB.get_conn()
            rows = conn.cursor().execute("SELECT name, count FROM depots ORDER BY name").fetchall()
            conn.close()
            if not rows: return
            
            timestamp = datetime.now().strftime("%d-%m-%Y %H:%M")
            
            body = f"Sayın Yetkili,\n\n{timestamp} itibarıyla güncel depo palet stok durumları aşağıdadır:\n"
            body += "="*30 + "\n"
            
            total_stock = 0
            for name, count in rows:
                body += f"📦 {name:<15}: {count} Adet\n"
                total_stock += count
            
            body += "="*30 + "\n"
            body += f"TOPLAM STOK      : {total_stock} Adet\n\n"
            body += f"İyi Çalışmalar,\nKare Kare Palet Stok Otomasyon {APP_VERSION}"
            
            msg = MIMEMultipart()
            msg['From'] = cfg["sender"]; msg['To'] = cfg["receivers"]
            msg['Subject'] = f"Kare Palet Stok Raporu - {timestamp}"
            msg.attach(MIMEText(body, 'plain', 'utf-8'))
            
            server = smtplib.SMTP('smtp.gmail.com', 587); server.starttls()
            server.login(cfg["sender"], cfg["password"])
            server.sendmail(cfg["sender"], cfg["receivers"].split(","), msg.as_string()); server.quit()
            
            self.after(0, lambda: ToastNotification(self, "Stok Durumu Mail Atıldı!", COLORS["success"]))
        except Exception as e: 
            print(e); self.after(0, lambda: ToastNotification(self, "Mail Gönderilemedi!", COLORS["danger"]))

    def setup_sidebar(self):
        self.sidebar = ctk.CTkFrame(self, width=280, corner_radius=0, fg_color=COLORS["sidebar"])
        self.sidebar.grid(row=0, column=0, sticky="nsew")
        
        ctk.CTkLabel(self.sidebar, text="⚡", font=("Arial", 45)).pack(pady=(40,0))
        ctk.CTkLabel(self.sidebar, text="TaNjU", font=FONTS["h1"], text_color=COLORS["accent"]).pack()
        ctk.CTkLabel(self.sidebar, text=f"{self.role.upper()} PANELİ", font=("Arial", 11, "bold"), text_color="gray").pack(pady=(5,30))

        self.nav_btns = {}
        # Menü Sıralaması
        self.create_nav("📊  GENEL BAKIŞ", self.show_dashboard, "dash")
        self.create_nav("🔄  OPERASYON & DEPO", self.show_ops, "ops")
        self.create_nav("📝  GEÇMİŞ & FİLTRE", self.show_history, "hist")
        self.create_nav("📈  RAPOR MERKEZİ", self.show_reports, "report")
        self.create_nav("💬  SOHBET & MAKBULE", self.show_makbule, "makbule")
        
        if self.role == "admin":
            self.create_nav("🔒  KULLANICI YÖNETİMİ", self.show_users, "users")
            self.create_nav("⚙️  MAIL AYARLARI", self.show_mail_settings, "mail")
        
        self.create_nav("🚀  GÜNCELLEME MERKEZİ", self.show_update_center, "update")
        ctk.CTkButton(self.sidebar, text="ÇIKIŞ", fg_color=COLORS["bg"], hover_color=COLORS["danger"], height=50, font=FONTS["bold"], command=self.logout).pack(side="bottom", fill="x", padx=20, pady=30)

    def create_nav(self, text, cmd, key):
        btn = ctk.CTkButton(self.sidebar, text=text, fg_color="transparent", text_color=COLORS["text_body"], hover_color="#334155", anchor="w", font=FONTS["bold"], height=60, command=cmd)
        btn.pack(fill="x", padx=15, pady=5)
        self.nav_btns[key] = btn

    def active_nav(self, key):
        for k, btn in self.nav_btns.items():
            if k == key: 
                if k == "makbule": btn.configure(fg_color=COLORS["makbule_btn"], text_color="white")
                else: btn.configure(fg_color=COLORS["accent"], text_color="black")
            else: btn.configure(fg_color="transparent", text_color=COLORS["text_body"])

    def setup_main(self):
        self.main = ctk.CTkFrame(self, fg_color="transparent", corner_radius=0)
        self.main.grid(row=0, column=1, sticky="nsew", padx=30, pady=30)

    def clear_main(self):
        self.animation_running = False
        self.chat_active = False 
        self.critical_widgets = []
        for w in self.main.winfo_children(): w.destroy()
    
    def refresh_app_data(self): self.active_depots = DB.get_all_depots()

    # ================== ORTAK SOHBET VE MAKBULE EKRANI ==================
    def show_makbule(self):
        self.clear_main(); self.active_nav("makbule")
        self.chat_active = True 
        
        header = ctk.CTkFrame(self.main, fg_color="transparent"); header.pack(fill="x", pady=(0, 20))
        ctk.CTkLabel(header, text="💬 EKİP SOHBETİ & MAKBULE", font=FONTS["h2"], text_color=COLORS["makbule_btn"]).pack(side="left")
        
        self.chat_frame = ctk.CTkScrollableFrame(self.main, fg_color=COLORS["card"], corner_radius=20, height=400)
        self.chat_frame.pack(fill="both", expand=True, pady=10)
        
        input_frame = ctk.CTkFrame(self.main, fg_color="transparent"); input_frame.pack(fill="x", pady=10)
        self.chat_entry = ctk.CTkEntry(input_frame, placeholder_text="Mesaj yaz... (Makbule yazarsan cevap verir)", height=50, font=("Arial", 14))
        self.chat_entry.pack(side="left", fill="x", expand=True, padx=(0, 10))
        self.chat_entry.bind("<Return>", lambda e: self.send_chat_message())
        
        ctk.CTkButton(input_frame, text="GÖNDER", width=100, height=50, fg_color=COLORS["makbule_btn"], text_color="white", command=self.send_chat_message).pack(side="right")

        self.load_chat_history()
        self.refresh_chat_loop()

    def load_chat_history(self):
        try:
            conn = DB.get_conn()
            cursor = conn.cursor()
            rows = cursor.execute("SELECT id, user, message, timestamp FROM chat_logs ORDER BY id DESC LIMIT 50").fetchall()
            conn.close()
            for r in reversed(rows):
                self.last_chat_id = max(self.last_chat_id, r[0])
                self.add_chat_bubble(r[2], r[1], r[3])
        except: pass

    def refresh_chat_loop(self):
        if not self.chat_active: return
        try:
            conn = DB.get_conn()
            cursor = conn.cursor()
            rows = cursor.execute("SELECT id, user, message, timestamp FROM chat_logs WHERE id > ? ORDER BY id ASC", (self.last_chat_id,)).fetchall()
            conn.close()
            for r in rows:
                self.last_chat_id = r[0]
                self.add_chat_bubble(r[2], r[1], r[3])
        except: pass
        self.after(2000, self.refresh_chat_loop)

    def send_chat_message(self):
        msg = self.chat_entry.get().strip()
        if not msg: return
        timestamp = datetime.now().strftime("%H:%M")
        try:
            conn = DB.get_conn()
            cursor = conn.cursor()
            cursor.execute("INSERT INTO chat_logs (user, message, timestamp) VALUES (?, ?, ?)", (self.user, msg, timestamp))
            conn.commit()
            conn.close()
            self.chat_entry.delete(0, "end")
            
            if "makbule" in msg.lower():
                self.trigger_makbule(msg)
                
        except Exception as e: print(f"Mesaj hatası: {e}")

    def trigger_makbule(self, user_msg):
        response = MAKBULE.analyze_command(user_msg, self.user, CURRENT_DB_PATH)
        timestamp = datetime.now().strftime("%H:%M")
        if response == "ACTION_MAIL": self.send_auto_email(); response = "📧 Tamamdır, maili gönderdim!"
        elif response == "ACTION_UPDATE": self.check_web_update(); return 
        time.sleep(0.5) 
        try:
            conn = DB.get_conn()
            conn.cursor().execute("INSERT INTO chat_logs (user, message, timestamp) VALUES (?, ?, ?)", ("Makbule", response, timestamp))
            conn.commit(); conn.close()
        except: pass

    def add_chat_bubble(self, text, sender, time_str):
        is_me = sender == self.user
        is_makbule = sender == "Makbule"
        align = "e" if is_me else "w"
        if is_me: bg_color = COLORS["chat_me"]; text_color = "white"
        elif is_makbule: bg_color = COLORS["makbule_chat"]; text_color = "white"
        else: bg_color = COLORS["chat_other"]; text_color = "white"
        
        container = ctk.CTkFrame(self.chat_frame, fg_color="transparent")
        container.pack(anchor=align, pady=5, padx=10)
        if not is_me:
            name_lbl = ctk.CTkLabel(container, text=f"{sender} - {time_str}", font=("Arial", 10), text_color="gray")
            name_lbl.pack(anchor="w")
        bubble = ctk.CTkLabel(container, text=text, fg_color=bg_color, text_color=text_color, corner_radius=15, padx=15, pady=10, wraplength=500, justify="left", font=("Arial", 14))
        bubble.pack()
        # --- OTOMATİK KAYDIRMA EKLENDİ ---
        self.after(10, lambda: self.chat_frame._parent_canvas.yview_moveto(1.0))

    # --- 1. DASHBOARD ---
    def show_dashboard(self):
        self.clear_main(); self.active_nav("dash")
        self.refresh_app_data()
        self.animation_running = True 
        header_frame = ctk.CTkFrame(self.main, fg_color="transparent")
        header_frame.pack(fill="x", pady=(0, 20))
        ctk.CTkLabel(header_frame, text="DEPO DURUMLARI", font=FONTS["h2"], text_color="white").pack(side="left")
        ctk.CTkButton(header_frame, text="🔄 YENİLE", width=100, height=40, fg_color=COLORS["accent"], text_color="black", font=("Arial", 12, "bold"), command=self.show_dashboard).pack(side="right")
        scroll_frame = ctk.CTkScrollableFrame(self.main, fg_color="transparent", height=500); scroll_frame.pack(fill="both", expand=True)
        grid = ctk.CTkFrame(scroll_frame, fg_color="transparent"); grid.pack(fill="both", expand=True)
        conn = DB.get_conn(); cur = conn.cursor(); cur.execute("SELECT name, count FROM depots"); data = {row[0]: row[1] for row in cur.fetchall()}; conn.close()
        colors = [COLORS["accent"], "#8B5CF6", "#10B981", COLORS["warning"], "#EC4899", "#F59E0B"]; row_idx = 0; col_idx = 0; grid.grid_columnconfigure(0, weight=1); grid.grid_columnconfigure(1, weight=1)
        for i, depot in enumerate(self.active_depots):
            val = data.get(depot, 0); col = colors[i % len(colors)]; is_critical = val < 10
            card = self.create_depot_card(grid, depot, val, col, row_idx, col_idx, is_critical)
            if is_critical: self.critical_widgets.append(card)
            col_idx += 1
            if col_idx > 1: col_idx = 0; row_idx += 1
        bottom = ctk.CTkFrame(self.main, fg_color="transparent"); bottom.pack(fill="x", pady=20)
        conn = DB.get_conn(); today = datetime.now().strftime("%Y-%m-%d")
        t_in = conn.cursor().execute(f"SELECT SUM(qty) FROM logs WHERE action='GİRİŞ' AND date LIKE '{today}%'").fetchone()[0] or 0
        t_out = conn.cursor().execute(f"SELECT SUM(qty) FROM logs WHERE action='ÇIKIŞ' AND date LIKE '{today}%'").fetchone()[0] or 0
        conn.close()
        self.create_mini_kpi(bottom, "BUGÜN GİREN", f"+{t_in}", COLORS["success"]); self.create_mini_kpi(bottom, "BUGÜN ÇIKAN", f"-{t_out}", COLORS["danger"])
        if self.critical_widgets: self.animate_critical_cards()

    def create_depot_card(self, parent, name, val, color, r, c, is_critical=False):
        border_col = COLORS["critical"] if is_critical else COLORS["border"]; border_w = 3 if is_critical else 1
        card = ctk.CTkFrame(parent, fg_color=COLORS["card"], corner_radius=20, border_width=border_w, border_color=border_col)
        card.grid(row=r, column=c, padx=10, pady=10, sticky="nsew", ipady=20)
        ctk.CTkLabel(card, text="📦 " + name, font=("Arial", 16, "bold"), text_color="gray").pack(pady=(20, 10))
        ctk.CTkLabel(card, text=str(val), font=("Roboto", 48, "bold"), text_color=color).pack(pady=5)
        ctk.CTkLabel(card, text="Palet Mevcut", font=("Arial", 12), text_color="gray").pack()
        if is_critical: ctk.CTkLabel(card, text="⚠️ KRİTİK STOK!", font=("Arial", 14, "bold"), text_color=COLORS["danger"]).pack(pady=5)
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
        f = ctk.CTkFrame(parent, fg_color=COLORS["card"], corner_radius=15, height=80); f.pack(side="left", fill="x", expand=True, padx=10)
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
        
        d_frame = ctk.CTkFrame(p, fg_color="transparent"); d_frame.pack(pady=10)
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
            try: valid_date = datetime(int(sel_y), int(sel_m), int(sel_d))
            except ValueError: ToastNotification(self, "Geçersiz Tarih!", COLORS["danger"]); return
            
            final_date_str = f"{sel_y}-{sel_m}-{sel_d} {datetime.now().strftime('%H:%M:%S')}"
            conn = DB.get_conn(); c = conn.cursor()
            if act == "ÇIKIŞ":
                curr = c.execute("SELECT count FROM depots WHERE name=?", (d,)).fetchone()[0]
                if curr < q: conn.close(); return ToastNotification(self, f"Yetersiz Stok! ({curr})", COLORS["danger"])
                c.execute("UPDATE depots SET count = count - ? WHERE name=?", (q, d))
            else: c.execute("UPDATE depots SET count = count + ? WHERE name=?", (q, d))
            
            c.execute("INSERT INTO logs (date, action, depot, qty, user) VALUES (?,?,?,?,?)", (final_date_str, act, d, q, self.user))
            conn.commit(); conn.close()
            ToastNotification(self, "İşlem Başarılı", COLORS["success"]); self.en_qty.delete(0, "end")
        except: ToastNotification(self, "Hatalı Giriş!", COLORS["warning"])

    def add_new_depot(self):
        name = self.entry_new_depot.get().strip().upper()
        if not name: return
        try:
            conn = DB.get_conn(); conn.cursor().execute("INSERT INTO depots (name, count) VALUES (?, 0)", (name,))
            conn.commit(); conn.close()
            ToastNotification(self, "Depo Eklendi", COLORS["success"])
            self.entry_new_depot.delete(0, "end"); self.refresh_app_data()
            self.cb_depo.configure(values=self.active_depots)
        except: ToastNotification(self, "Bu depo zaten var!", COLORS["danger"])

    def delete_selected_depot(self):
        name = self.cb_depo.get()
        if name not in self.active_depots: return
        if not messagebox.askyesno("Onay", f"'{name}' silinsin mi?"): return
        conn = DB.get_conn()
        conn.cursor().execute("DELETE FROM depots WHERE name=?", (name,))
        conn.commit(); conn.close()
        ToastNotification(self, "Depo Silindi", COLORS["success"])
        self.refresh_app_data(); self.cb_depo.configure(values=self.active_depots); self.cb_depo.set("Depo Seçiniz")

    def show_history(self):
        self.clear_main(); self.active_nav("hist"); self.refresh_app_data()
        top = ctk.CTkFrame(self.main, fg_color="transparent"); top.pack(fill="x", pady=(0, 10))
        ctk.CTkLabel(top, text="GEÇMİŞ & DÜZENLEME", font=FONTS["h2"]).pack(side="left")
        flt = ctk.CTkFrame(self.main, fg_color=COLORS["card"], corner_radius=10); flt.pack(fill="x", pady=10, padx=5)
        self.cb_y = ctk.CTkComboBox(flt, values=["Yıl"] + [str(y) for y in range(2024, 2030)], width=80); self.cb_y.pack(side="left", padx=5)
        self.cb_m = ctk.CTkComboBox(flt, values=["Ay"] + [f"{m:02d}" for m in range(1, 13)], width=70); self.cb_m.pack(side="left", padx=5)
        self.cb_d = ctk.CTkComboBox(flt, values=["Gün"] + [f"{d:02d}" for d in range(1, 32)], width=70); self.cb_d.pack(side="left", padx=5)
        conn = DB.get_conn(); users = [u[0] for u in conn.cursor().execute("SELECT name FROM users").fetchall()]; conn.close()
        self.cb_u = ctk.CTkComboBox(flt, values=["Kullanıcı"] + users, width=120); self.cb_u.pack(side="left", padx=5)
        self.ent_search = ctk.CTkEntry(flt, placeholder_text="Arama...", width=150); self.ent_search.pack(side="left", padx=15)
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
        self.tree.tag_configure("IN", foreground=COLORS["success"]); self.tree.tag_configure("OUT", foreground=COLORS["danger"])
        self.tree.pack(fill="both", expand=True, pady=10)
        btn_fr = ctk.CTkFrame(self.main, fg_color="transparent"); btn_fr.pack(fill="x", pady=5)
        ctk.CTkButton(btn_fr, text="✏️ DÜZELT", fg_color=COLORS["warning"], text_color="black", width=150, command=self.edit_transaction).pack(side="left", padx=5)
        ctk.CTkButton(btn_fr, text="🗑️ SİL", fg_color=COLORS["danger"], width=150, command=self.delete_transaction).pack(side="left", padx=5)
        self.load_history_combined()

    def reset_filter(self):
        self.cb_y.set("Yıl"); self.cb_m.set("Ay"); self.cb_d.set("Gün"); self.cb_u.set("Kullanıcı"); self.ent_search.delete(0, "end"); self.load_history_combined()

    def load_history_combined(self):
        for i in self.tree.get_children(): self.tree.delete(i)
        y, m, d, u = self.cb_y.get(), self.cb_m.get(), self.cb_d.get(), self.cb_u.get()
        search = self.ent_search.get().strip()
        query = "SELECT * FROM logs WHERE 1=1"
        params = []
        if y != "Yıl": query += " AND strftime('%Y', date) = ?"; params.append(y)
        if m != "Ay": query += " AND strftime('%m', date) = ?"; params.append(m)
        if d != "Gün": query += " AND strftime('%d', date) = ?"; params.append(d)
        if u != "Kullanıcı": query += " AND user = ?"; params.append(u)
        if search: query += " AND (depot LIKE ? OR user LIKE ? OR action LIKE ?)"; params.extend([f"%{search}%"]*3)
        query += " ORDER BY id DESC LIMIT 500"
        
        # --- GÜN ÇEVİRİ SÖZLÜĞÜ ---
        days_tr = {
            "Monday": "Pazartesi", "Tuesday": "Salı", "Wednesday": "Çarşamba",
            "Thursday": "Perşembe", "Friday": "Cuma", "Saturday": "Cumartesi",
            "Sunday": "Pazar"
        }
        
        conn = DB.get_conn()
        try:
            for r in conn.cursor().execute(query, params).fetchall():
                try: 
                    dt = datetime.strptime(r[1], "%Y-%m-%d %H:%M:%S")
                    d_str = dt.strftime("%Y-%m-%d")
                    t_str = dt.strftime("%H:%M")
                    # İngilizce günü alıp Türkçeye çeviriyoruz
                    day_eng = dt.strftime("%A")
                    day = days_tr.get(day_eng, day_eng)
                except: d_str, t_str, day = r[1], "-", "-"
                
                tag = "IN" if r[2] == "GİRİŞ" else "OUT"
                self.tree.insert("", "end", values=(r[0], d_str, t_str, day, r[2], r[3], r[4], r[5]), tags=(tag,))
        except: pass
        finally: conn.close()

    def delete_transaction(self):
        sel = self.tree.selection()
        if not sel: return
        item = self.tree.item(sel)['values']
        log_id, action, depot, qty = item[0], item[4], item[5], int(item[6])
        if not messagebox.askyesno("Onay", "Silinsin mi?"): return
        conn = DB.get_conn(); c = conn.cursor()
        if action == "GİRİŞ": c.execute("UPDATE depots SET count=count-? WHERE name=?", (qty, depot))
        else: c.execute("UPDATE depots SET count=count+? WHERE name=?", (qty, depot))
        c.execute("DELETE FROM logs WHERE id=?", (log_id,))
        conn.commit(); conn.close(); self.load_history_combined()

    def edit_transaction(self):
        sel = self.tree.selection()
        if not sel: return
        item = self.tree.item(sel)['values']
        old_id, old_date, _, _, old_act, old_dep, old_qty, _ = item
        top = ctk.CTkToplevel(self); top.geometry("300x400")
        ctk.CTkLabel(top, text="DÜZENLE", font=FONTS["bold"]).pack(pady=10)
        c_act = ctk.CTkComboBox(top, values=["GİRİŞ", "ÇIKIŞ"]); c_act.set(old_act); c_act.pack(pady=5)
        c_dep = ctk.CTkComboBox(top, values=self.active_depots); c_dep.set(old_dep); c_dep.pack(pady=5)
        e_qty = ctk.CTkEntry(top); e_qty.insert(0, str(old_qty)); e_qty.pack(pady=5)
        def save():
            try:
                na, nd, nq = c_act.get(), c_dep.get(), int(e_qty.get())
                conn = DB.get_conn(); c = conn.cursor()
                if old_act=="GİRİŞ": c.execute("UPDATE depots SET count=count-? WHERE name=?", (old_qty, old_dep))
                else: c.execute("UPDATE depots SET count=count+? WHERE name=?", (old_qty, old_dep))
                if na=="GİRİŞ": c.execute("UPDATE depots SET count=count+? WHERE name=?", (nq, nd))
                else: c.execute("UPDATE depots SET count=count-? WHERE name=?", (nq, nd))
                c.execute("UPDATE logs SET action=?, depot=?, qty=?, user=? WHERE id=?", (na, nd, nq, f"{self.user}*", old_id))
                conn.commit(); conn.close(); top.destroy(); self.load_history_combined()
            except: pass
        ctk.CTkButton(top, text="KAYDET", command=save).pack(pady=20)

    def show_reports(self):
        self.clear_main(); self.active_nav("report")
        ctk.CTkLabel(self.main, text="RAPOR MERKEZİ", font=FONTS["h2"]).pack(anchor="w", pady=20)
        r1 = ctk.CTkFrame(self.main, fg_color="transparent"); r1.pack(fill="x", padx=10, pady=10)
        ctk.CTkButton(r1, text="TÜM GEÇMİŞ (EXCEL)", height=50, command=lambda: self.export_adv("ALL")).pack(side="left", fill="x", expand=True, padx=5)
        ctk.CTkButton(r1, text="BU AYIN RAPORU", height=50, command=lambda: self.export_adv("MONTH")).pack(side="left", fill="x", expand=True, padx=5)

    def export_adv(self, mode):
        if not HAS_PANDAS: return ToastNotification(self, "Pandas Yok!", COLORS["danger"])
        report_dir = os.path.join(program_folder, "Raporlar"); os.makedirs(report_dir, exist_ok=True)
        filename = f"Rapor_{datetime.now().strftime('%Y%m%d_%H%M%S')}.xlsx"
        conn = DB.get_conn(); q = "SELECT * FROM logs"
        if mode == "MONTH": q += f" WHERE date LIKE '{datetime.now().strftime('%Y-%m')}%'"
        df = pd.read_sql(q, conn); conn.close()
        if df.empty: return ToastNotification(self, "Veri Yok", COLORS["warning"])
        with pd.ExcelWriter(os.path.join(report_dir, filename)) as w: df.to_excel(w, index=False)
        ToastNotification(self, "Kaydedildi", COLORS["success"]); os.startfile(report_dir)

    # --- MAIL AYARLARI (ESKİ TASARIM) ---
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

    def show_update_center(self):
        self.clear_main(); self.active_nav("update")
        ctk.CTkLabel(self.main, text=f"Sürüm: {APP_VERSION}", font=FONTS["h2"]).pack(pady=50)
        ctk.CTkLabel(self.main, text="Yeni özellikleri almak için butona basın.", text_color="gray").pack()
        ctk.CTkButton(self.main, text="İNTERNETTEN GÜNCELLE", width=200, height=50, font=FONTS["bold"], fg_color="#2563EB", command=self.check_web_update).pack(pady=20)

    def check_web_update(self):
        if not messagebox.askyesno("Onay", "Güncelleme indirilsin mi?\n(Program kapanıp yeniden açılacak)"): return
        
        try:
            context = ssl._create_unverified_context()
            
            if getattr(sys, 'frozen', False):
                exe_path = sys.executable
                exe_dir = os.path.dirname(exe_path)
                new_exe_path = os.path.join(exe_dir, "new_update.tmp")
                
                ToastNotification(self, "Exe indiriliyor...", COLORS["warning"])
                self.update()
                
                try:
                    urllib.request.urlretrieve(EXE_UPDATE_URL, new_exe_path)
                except Exception as e:
                    messagebox.showerror("İndirme Hatası", f"Dosya indirilemedi:\n{e}")
                    return

                if not os.path.exists(new_exe_path) or os.path.getsize(new_exe_path) < 1000:
                    messagebox.showerror("Hata", "İndirilen dosya bozuk veya eksik.")
                    return

                bat_path = os.path.join(exe_dir, "update.bat")
                exe_name = os.path.basename(exe_path)
                
                bat_content = f"""
@echo off
timeout /t 2 /nobreak > nul
del "{exe_name}"
move "new_update.tmp" "{exe_name}"
start "" "{exe_name}"
del "%~f0"
"""
                with open(bat_path, "w") as f: f.write(bat_content)
                os.startfile(bat_path)
                sys.exit()

            else:
                new_code = urllib.request.urlopen(UPDATE_URL, context=context).read()
                if not new_code: raise ValueError
                shutil.copy2(os.path.abspath(__file__), os.path.abspath(__file__)+".bak")
                with open(os.path.abspath(__file__), "wb") as f: f.write(new_code)
                messagebox.showinfo("Başarılı", "Kod güncellendi! Yeniden başlatılıyor."); sys.exit()

        except Exception as e:
            messagebox.showerror("Güncelleme Hatası", f"Hata:\n{e}\n\nLütfen internet bağlantınızı kontrol edin.")

    def show_users(self):
        self.clear_main(); self.active_nav("users")
        fr = ctk.CTkFrame(self.main); fr.pack(fill="both", expand=True, padx=20, pady=20)
        self.u_tree = ttk.Treeview(fr, columns=("AD", "ROL"), show="headings"); self.u_tree.pack(side="left", fill="both", expand=True)
        self.u_tree.heading("AD", text="KULLANICI"); self.u_tree.heading("ROL", text="ROL")
        self.u_tree.bind("<<TreeviewSelect>>", self.fill_user_form)
        pnl = ctk.CTkFrame(fr, width=300); pnl.pack(side="right", fill="y", padx=15)
        self.u_name = ctk.CTkEntry(pnl, placeholder_text="Kullanıcı Adı"); self.u_name.pack(pady=10)
        self.u_pass = ctk.CTkEntry(pnl, placeholder_text="Şifre", show="•"); self.u_pass.pack(pady=10)
        self.show_pass_var = ctk.BooleanVar(value=False)
        ctk.CTkCheckBox(pnl, text="Göster", variable=self.show_pass_var, command=self.toggle_password).pack(pady=5)
        self.u_role = ctk.CTkComboBox(pnl, values=["personel", "admin"]); self.u_role.pack(pady=10)
        ctk.CTkButton(pnl, text="KAYDET", fg_color=COLORS["success"], command=self.save_user).pack(pady=5)
        ctk.CTkButton(pnl, text="SİL", fg_color=COLORS["danger"], command=self.del_user).pack(pady=5)
        ctk.CTkButton(pnl, text="TEMİZLE", fg_color="gray", command=self.clear_user_form).pack(pady=15)
        self.refresh_users()

    def toggle_password(self):
        if self.show_pass_var.get(): self.u_pass.configure(show="")
        else: self.u_pass.configure(show="•")
    
    def refresh_users(self):
        for i in self.u_tree.get_children(): self.u_tree.delete(i)
        conn = DB.get_conn(); 
        for r in conn.cursor().execute("SELECT name, role FROM users").fetchall(): self.u_tree.insert("", "end", values=r)
        conn.close()

    def fill_user_form(self, event):
        sel = self.u_tree.selection()
        if not sel: return
        val = self.u_tree.item(sel)['values']
        conn = DB.get_conn(); d = conn.cursor().execute("SELECT name, pass, role FROM users WHERE name=?", (val[0],)).fetchone(); conn.close()
        if d: self.u_name.delete(0,"end"); self.u_name.insert(0,d[0]); self.u_pass.delete(0,"end"); self.u_pass.insert(0,d[1]); self.u_role.set(d[2])

    def clear_user_form(self): self.u_name.delete(0,"end"); self.u_pass.delete(0,"end"); self.u_role.set("personel")

    def save_user(self):
        try: conn = DB.get_conn(); conn.cursor().execute("INSERT OR REPLACE INTO users (name, pass, role) VALUES (?,?,?)", (self.u_name.get(), self.u_pass.get(), self.u_role.get())); conn.commit(); conn.close(); self.refresh_users(); ToastNotification(self, "Kaydedildi", COLORS["success"])
        except: pass

    def del_user(self):
        n = self.u_name.get()
        if n in ["admin", "tanju"]: ToastNotification(self, "Silinemez!", COLORS["danger"]); return
        if messagebox.askyesno("Sil", "Silinsin mi?"): conn=DB.get_conn(); conn.cursor().execute("DELETE FROM users WHERE name=?",(n,)); conn.commit(); conn.close(); self.refresh_users(); self.clear_user_form()

    def logout(self): self.destroy(); LoginWindow().mainloop()

if __name__ == "__main__":
    app = AnimatedSplash()
    app.mainloop()
