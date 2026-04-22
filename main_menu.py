# -*- coding: utf-8 -*-
import tkinter as tk
from tkinter import messagebox, ttk
import sqlite3
import os
import cv2
import biometrics  
from PIL import Image, ImageTk
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
import json
import shutil
from datetime import datetime

def load_settings():
    default_settings = {"camera_id": 0, "theme": "Dark"}
    if not os.path.exists("settings.json"):
        with open("settings.json", "w") as f:
            json.dump(default_settings, f)
        return default_settings
    with open("settings.json", "r") as f:
        try: return json.load(f)
        except: return default_settings

def save_settings(new_settings):
    with open("settings.json", "w") as f:
        json.dump(new_settings, f)

plt.rcParams['font.family'] = 'Arial'
DB_NAME = 'barber_pro.db'

TRANSLATIONS = {
    'uk': {
        'title': "BarberVision PRO - Група 451",
        'auth': "АВТОРИЗАЦІЯ",
        'login_lbl': "Логін:",
        'pass_lbl': "Пароль:",
        'btn_login': "УВІЙТИ",
        'btn_reg': "РЕЄСТРАЦІЯ",
        'reg_title': "НОВИЙ МАЙСТЕР",
        'back': "Назад",
        'new_anal': "НОВИЙ АНАЛІЗ",
        'history': "ІСТОРІЯ",
        'stats': "СТАТИСТИКА",
        'logout': "ВИХІД",
        'admin_panel': "АДМІН-ПАНЕЛЬ",
        'del_btn': "ВИДАЛИТИ ЗАПИС",
        'open_pdf': "ВІДКРИТИ PDF",
        'confirm_del': "Видалити",
        'no_data': "Дані відсутні",
        'welcome': "Вітаємо, майстре ",
        'chart_title': "Розподіл форм обличчя",
        'ovl': "Овал", 'obl': "Прямокутне", 'sqr': "Квадрат", 'rnd': "Кругле", 'hrt': "Серце",
        'reg_success': "Майстер успішно створений: ",
        'reg_err': "Цей логін уже зайнятий!",
        'fill_all': "Заповніть усі поля!",
        'manage_users': "Управління акаунтами",
        'cant_del_admin': "Ви не можете видалити адміністратора!",
        'settings_btn': "НАЛАШТУВАННЯ",
        'cam_lbl': "Номер камери (0, 1, 2):",
        'search_lbl': "Пошук за формою:",
        'about_btn': "ПРО ПРОГРАМУ",
        'about_text': "BarberVision PRO v9.1\nРозроблено студентом гр. 451\nЗакарадзе Давідом\n\nВикористано нейромережі MediaPipe\nдля антропометричного аналізу обличчя.",
        'sort_lbl': "Сортувати за:",
        'sort_id': "Номером",
        'sort_date': "Датою",
        'sort_shape': "Формою",
        'backup_btn': "РЕЗЕРВНА КОПІЯ (BACKUP)",
        'backup_success': "Бекап бази даних успішно створено в папці /backups",
        'backup_err': "Помилка при створенні бекапу: ",
        'save_cam_btn': "ЗБЕРЕГТИ НАЛАШТУВАННЯ",
        'save_success': "Налаштування збережено!"
    },
    'en': {
        'title': "BarberVision PRO - Group 451",
        'auth': "AUTHORIZATION",
        'login_lbl': "Login:",
        'pass_lbl': "Password:",
        'btn_login': "LOGIN",
        'btn_reg': "REGISTER",
        'reg_title': "NEW MASTER",
        'back': "Back",
        'new_anal': "NEW ANALYSIS",
        'history': "HISTORY",
        'stats': "STATISTICS",
        'logout': "LOGOUT",
        'admin_panel': "ADMIN PANEL",
        'del_btn': "DELETE",
        'open_pdf': "OPEN PDF",
        'confirm_del': "Delete",
        'no_data': "No data",
        'welcome': "Welcome, master ",
        'chart_title': "Face Shape Distribution",
        'ovl': "Oval", 'obl': "Oblong", 'sqr': "Square", 'rnd': "Round", 'hrt': "Heart",
        'reg_success': "Master created: ",
        'reg_err': "Login taken!",
        'fill_all': "Fill all fields!",
        'manage_users': "User Management",
        'cant_del_admin': "Cannot delete admin!",
        'settings_btn': "SETTINGS",
        'cam_lbl': "Camera ID (0, 1, 2):",
        'search_lbl': "Search by shape:",
        'about_btn': "ABOUT",
        'about_text': "BarberVision PRO v9.1\nDev by David Zakaradze (451)\n\nPowered by MediaPipe AI.",
        'sort_lbl': "Sort by:",
        'sort_id': "ID",
        'sort_date': "Date",
        'sort_shape': "Shape",
        'backup_btn': "CREATE DATABASE BACKUP",
        'backup_success': "Database backup created in /backups folder",
        'backup_err': "Backup error: ",
        'save_cam_btn': "SAVE SETTINGS",
        'save_success': "Settings saved successfully!"
    }
}

SHAPE_MAP = {'Oval': 'ovl', 'Oblong': 'obl', 'Square': 'sqr', 'Round': 'rnd', 'Heart': 'hrt'}

class SplashScreen:
    def __init__(self, root):
        self.root = root
        self.root.overrideredirect(True)
        self.root.geometry("500x300")
        self.root.configure(bg="#1e1e1e")
        sw, sh = self.root.winfo_screenwidth(), self.root.winfo_screenheight()
        self.root.geometry(f"500x300+{int(sw/2-250)}+{int(sh/2-150)}")
        tk.Label(self.root, text="BarberVision PRO", font=("Arial", 28, "bold"), bg="#1e1e1e", fg="#00ff00").pack(pady=(60, 10))
        tk.Label(self.root, text="Група 451 | Давід Закарадзе", font=("Arial", 12), bg="#1e1e1e", fg="gray").pack()
        tk.Label(self.root, text="Ініціалізація AI модулів...", font=("Arial", 10, "italic"), bg="#1e1e1e", fg="#555").pack(side="bottom", pady=20)
        self.root.after(3000, self.finish)
    def finish(self): self.root.destroy()

class BarberAppUI:
    def __init__(self, root):
        self.root = root
        self.lang = 'uk'; self.current_user = ""; self.current_frame_type = 'login'
        self.init_db(); self.setup_styles(); self.show_login_frame()

    def init_db(self):
        conn = sqlite3.connect(DB_NAME); cur = conn.cursor()
        cur.execute("CREATE TABLE IF NOT EXISTS users (id INTEGER PRIMARY KEY, login TEXT UNIQUE, password TEXT)")
        cur.execute("INSERT OR IGNORE INTO users (login, password) VALUES ('admin', '451')")
        conn.commit(); conn.close()

    def setup_styles(self):
        self.root.title(TRANSLATIONS[self.lang]['title'])
        self.root.geometry("950x850"); self.root.configure(bg="#1e1e1e")

    def switch_lang(self, lang_code):
        self.lang = lang_code
        if self.current_frame_type == 'login': self.show_login_frame()
        elif self.current_frame_type == 'reg': self.show_register_frame()
        elif self.current_frame_type == 'dash': self.show_dashboard(self.current_user)

    def clear_window(self):
        for widget in self.root.winfo_children(): widget.destroy()

    def add_lang_buttons(self):
        lang_f = tk.Frame(self.root, bg="#1e1e1e")
        lang_f.place(relx=1.0, x=-20, y=20, anchor="ne")
        tk.Button(lang_f, text="UA", font=("Arial", 9, "bold"), bg="#333", fg="#00ff00", bd=0, command=lambda: self.switch_lang('uk')).pack(side="left", padx=5)
        tk.Button(lang_f, text="EN", font=("Arial", 9, "bold"), bg="#333", fg="#00ff00", bd=0, command=lambda: self.switch_lang('en')).pack(side="left", padx=5)

    def show_login_frame(self):
        self.current_frame_type = 'login'; self.clear_window(); self.add_lang_buttons()
        t = TRANSLATIONS[self.lang]
        f = tk.Frame(self.root, bg="#2d2d2d", padx=50, pady=50, highlightbackground="#00ff00", highlightthickness=2)
        f.place(relx=0.5, rely=0.5, anchor="center")
        tk.Label(f, text=t['auth'], font=("Arial", 22, "bold"), bg="#2d2d2d", fg="#00ff00").pack(pady=20)
        tk.Label(f, text=t['login_lbl'], bg="#2d2d2d", fg="white").pack()
        self.e_login = tk.Entry(f, width=30, font=("Arial", 12)); self.e_login.pack(pady=10); self.e_login.insert(0, "admin")
        tk.Label(f, text=t['pass_lbl'], bg="#2d2d2d", fg="white").pack()
        self.e_pass = tk.Entry(f, show="*", width=30, font=("Arial", 12)); self.e_pass.pack(pady=10)
        tk.Button(f, text=t['btn_login'], width=20, bg="#00ff00", fg="black", font=("Arial", 12, "bold"), command=self.check_login).pack(pady=20)
        tk.Button(f, text=t['btn_reg'], bg="#2d2d2d", fg="gray", bd=0, command=self.show_register_frame).pack()

    def check_login(self):
        l, p = self.e_login.get().strip(), self.e_pass.get().strip()
        conn = sqlite3.connect(DB_NAME); cur = conn.cursor()
        cur.execute("SELECT * FROM users WHERE login=? AND password=?", (l, p))
        if cur.fetchone(): self.show_dashboard(l)
        else: messagebox.showerror("!", "Error: Invalid Credentials")
        conn.close()

    def show_register_frame(self):
        self.current_frame_type = 'reg'; self.clear_window(); self.add_lang_buttons()
        t = TRANSLATIONS[self.lang]
        f = tk.Frame(self.root, bg="#2d2d2d", padx=50, pady=50, highlightbackground="#00ff00", highlightthickness=2)
        f.place(relx=0.5, rely=0.5, anchor="center")
        tk.Label(f, text=t['reg_title'], font=("Arial", 18, "bold"), bg="#2d2d2d", fg="#00ff00").pack(pady=20)
        self.r_login = tk.Entry(f, width=30, font=("Arial", 12)); self.r_login.pack(pady=10)
        self.r_pass = tk.Entry(f, show="*", width=30, font=("Arial", 12)); self.r_pass.pack(pady=10)
        tk.Button(f, text=t['btn_reg'], width=20, bg="#00ff00", font=("Arial", 12, "bold"), command=self.do_register).pack(pady=20)
        tk.Button(f, text=t['back'], bg="#2d2d2d", fg="gray", bd=0, command=self.show_login_frame).pack()

    def do_register(self):
        l, p = self.r_login.get().strip(), self.r_pass.get().strip(); t = TRANSLATIONS[self.lang]
        if l and p:
            try:
                conn = sqlite3.connect(DB_NAME); cur = conn.cursor()
                cur.execute("INSERT INTO users (login, password) VALUES (?, ?)", (l, p))
                conn.commit(); conn.close(); messagebox.showinfo("OK", t['reg_success'] + l); self.show_login_frame()
            except: messagebox.showerror("Error", t['reg_err'])
        else: messagebox.showwarning("!", t['fill_all'])

    def show_dashboard(self, username):
        self.current_frame_type = 'dash'; self.current_user = username
        self.clear_window(); self.add_lang_buttons()
        t = TRANSLATIONS[self.lang]

        logo_f = tk.Frame(self.root, bg="#1e1e1e"); logo_f.pack(pady=30)
        try:
            img = Image.open("logo.png").resize((180, 180), Image.Resampling.LANCZOS)
            self.logo_img = ImageTk.PhotoImage(img); tk.Label(logo_f, image=self.logo_img, bg="#1e1e1e").pack()
        except:
            tk.Label(logo_f, text="✂️ BarberVision PRO", font=("Arial", 28, "bold"), bg="#1e1e1e", fg="#00ff00").pack()

        tk.Label(self.root, text=t['welcome'] + username.upper(), font=("Arial", 14), bg="#1e1e1e", fg="#888888").pack()

        main_f = tk.Frame(self.root, bg="#1e1e1e"); main_f.pack(expand=True, pady=10)
        
        # КНОПКИ 
        tk.Button(main_f, text=t['new_anal'], font=("Arial", 13, "bold"), width=35, height=2, bg="#00ff00", fg="black", bd=0, command=self.start_camera).pack(pady=8)
        tk.Button(main_f, text=t['history'], font=("Arial", 13, "bold"), width=35, height=2, bg="#333", fg="white", bd=0, command=self.show_history).pack(pady=8)
        tk.Button(main_f, text=t['stats'], font=("Arial", 13, "bold"), width=35, height=2, bg="#333", fg="white", bd=0, command=self.show_stats).pack(pady=8)
        tk.Button(main_f, text=t['settings_btn'], font=("Arial", 13, "bold"), width=35, height=2, bg="#333", fg="white", bd=0, command=self.show_settings).pack(pady=8)
        tk.Button(main_f, text=t['about_btn'], font=("Arial", 13, "bold"), width=35, height=2, bg="#555", fg="white", bd=0, command=lambda: messagebox.showinfo("About", t['about_text'])).pack(pady=8)
        
        if username.lower() == "admin":
            tk.Button(main_f, text=t['admin_panel'], font=("Arial", 13, "bold"), width=35, height=2, bg="#007acc", fg="white", bd=0, command=self.show_admin_panel).pack(pady=8)

        tk.Button(main_f, text=t['logout'], font=("Arial", 13, "bold"), width=35, height=2, bg="#444", fg="white", bd=0, command=self.show_login_frame).pack(pady=20)

    def start_camera(self):
        self.root.withdraw()
        try: biometrics.BarberVisionApp().run()
        finally: self.root.deiconify()

    def show_settings(self):
        self.clear_window(); t = TRANSLATIONS[self.lang]
        tk.Button(self.root, text="< " + t['back'], font=("Arial", 10, "bold"), bg="#333", 
                  fg="white", bd=0, command=lambda: self.show_dashboard(self.current_user)).pack(anchor="nw", padx=20, pady=20)
        
        settings = load_settings()
        f = tk.Frame(self.root, bg="#2d2d2d", padx=50, pady=50, highlightbackground="#00ff00", highlightthickness=1)
        f.place(relx=0.5, rely=0.5, anchor="center")
        
        tk.Label(f, text=t['settings_btn'], font=("Arial", 18, "bold"), bg="#2d2d2d", fg="#00ff00").pack(pady=10)
        
        # Вибір камери
        tk.Label(f, text=t['cam_lbl'], bg="#2d2d2d", fg="white").pack()
        cam_entry = tk.Entry(f, width=10, font=("Arial", 12), justify="center")
        cam_entry.pack(pady=10)
        cam_entry.insert(0, str(settings.get('camera_id', 0)))
        
        def save():
            try:
                save_settings({"camera_id": int(cam_entry.get()), "theme": "Dark"})
                messagebox.showinfo("OK", t['save_success'])
            except: 
                messagebox.showerror("Err", "Digits only!" if self.lang == 'en' else "Тільки цифри!")
        
        tk.Button(f, text=t['save_cam_btn'], bg="#00ff00", font=("Arial", 10, "bold"), 
                  width=25, height=1, command=save).pack(pady=10)

        # --- ЛОГІКА БЕКАПУ ---
        def run_backup():
            try:
                if not os.path.exists("backups"):
                    os.makedirs("backups")
                
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                backup_name = f"backups/barber_pro_backup_{timestamp}.db"
                
                shutil.copy2(DB_NAME, backup_name)
                messagebox.showinfo("Backup", t['backup_success'])
            except Exception as e:
                messagebox.showerror("Error", f"{t['backup_err']} {e}")

        tk.Label(f, text="--- " + ("Система" if self.lang=='uk' else "System") + " ---", bg="#2d2d2d", fg="gray").pack(pady=(20, 5))
        
        # Кнопка Бекапу
        tk.Button(f, text="📂 " + t['backup_btn'], bg="#007acc", fg="white", font=("Arial", 10, "bold"), 
                  width=25, height=2, command=run_backup).pack(pady=5)

    def show_history(self):
        self.clear_window(); t = TRANSLATIONS[self.lang]
        tk.Button(self.root, text="< " + t['back'], font=("Arial", 10, "bold"), bg="#333", fg="white", bd=0, 
                  command=lambda: self.show_dashboard(self.current_user)).pack(anchor="nw", padx=20, pady=20)
        
        # --- ПАНЕЛЬ КЕРУВАННЯ ---
        ctrl_f = tk.Frame(self.root, bg="#1e1e1e")
        ctrl_f.pack(fill="x", padx=20, pady=10)
        
        # Пошук
        tk.Label(ctrl_f, text=t['search_lbl'], bg="#1e1e1e", fg="white").pack(side="left")
        search_entry = tk.Entry(ctrl_f, width=15)
        search_entry.pack(side="left", padx=10)

        # Сортування
        tk.Label(ctrl_f, text=t['sort_lbl'], bg="#1e1e1e", fg="white").pack(side="left", padx=(20, 0))
        
        sort_options = {
            t['sort_id']: "id DESC", 
            t['sort_date']: "date_time DESC", 
            t['sort_shape']: "face_shape ASC"
        }
        
        sort_combo = ttk.Combobox(ctrl_f, values=list(sort_options.keys()), state="readonly", width=15)
        sort_combo.set(list(sort_options.keys())[0]) # За замовчуванням за ID
        sort_combo.pack(side="left", padx=10)

        # --- ТАБЛИЦЯ ---
        tree_f = tk.Frame(self.root, bg="#1e1e1e")
        tree_f.pack(fill="both", expand=True, padx=20)
        
        tree = ttk.Treeview(tree_f, columns=('#', 'Date', 'Shape', 'Ratio'), show='headings', height=15)
        for c, h in zip(('#', 'Date', 'Shape', 'Ratio'), ('№', 'Date', 'Shape', 'Ratio')):
            tree.heading(c, text=h); tree.column(c, width=100, anchor="center")
        tree.pack(side="left", fill="both", expand=True)
        sb = ttk.Scrollbar(tree_f, orient="vertical", command=tree.yview); tree.configure(yscroll=sb.set); sb.pack(side="right", fill="y")

        # --- ЛОГІКА ОНОВЛЕННЯ ДАНИХ ---
        def load_data(*args):
            query = search_entry.get().strip()
            sort_choice = sort_combo.get()
            order_by = sort_options.get(sort_choice, "id DESC")
            
            for i in tree.get_children(): tree.delete(i)
            
            conn = sqlite3.connect(DB_NAME); cur = conn.cursor()
            sql = f"SELECT id, date_time, face_shape, ratio, screenshot_path, pdf_path FROM client_history WHERE face_shape LIKE ? ORDER BY {order_by}"
            cur.execute(sql, (f'%{query}%',))
            
            for idx, r in enumerate(cur.fetchall(), 1):
                tree.insert('', 'end', values=(idx, r[1], r[2], r[3]), tags=(r[0], r[4], r[5]))
            conn.close()

        # Прив'язка подій
        search_entry.bind('<KeyRelease>', load_data)
        sort_combo.bind('<<ComboboxSelected>>', load_data)
        
        load_data() # Перше завантаження

        # --- КНОПКИ ДІЙ ---
        btn_frame = tk.Frame(self.root, bg="#1e1e1e"); btn_frame.pack(pady=20)
        
        def open_pdf_file():
            sel = tree.selection()
            if not sel: return
            p_path = tree.item(sel[0])['tags'][2]
            if p_path and os.path.exists(p_path): os.startfile(os.path.normpath(p_path))
            else: messagebox.showerror("Err", "File not found")

        def delete_hist():
            sel = tree.selection()
            if sel and messagebox.askyesno("?", t['confirm_del']):
                item = tree.item(sel[0]); db_id = item['tags'][0]
                img_p, pdf_p = item['tags'][1], item['tags'][2]
                if img_p and os.path.exists(img_p): os.remove(img_p)
                if pdf_p and os.path.exists(pdf_p): os.remove(pdf_p)
                conn = sqlite3.connect(DB_NAME); cur = conn.cursor()
                cur.execute("DELETE FROM client_history WHERE id=?", (db_id,))
                conn.commit(); conn.close(); tree.delete(sel)

        tk.Button(btn_frame, text="📄 " + t['open_pdf'], font=("Arial", 11, "bold"), bg="#007acc", fg="white", width=20, height=2, command=open_pdf_file).pack(side="left", padx=10)
        tk.Button(btn_frame, text=t['del_btn'], font=("Arial", 11, "bold"), bg="#ff4444", fg="white", width=20, height=2, command=delete_hist).pack(side="left", padx=10)

    def show_stats(self):
        self.clear_window(); t = TRANSLATIONS[self.lang]
        tk.Button(self.root, text="< " + t['back'], font=("Arial", 10, "bold"), bg="#333", fg="white", bd=0, command=lambda: self.show_dashboard(self.current_user)).pack(anchor="nw", padx=20, pady=20)
        conn = sqlite3.connect(DB_NAME); cur = conn.cursor(); cur.execute("SELECT face_shape, COUNT(*) FROM client_history GROUP BY face_shape"); data = cur.fetchall(); conn.close()
        if data:
            lbls = [t[SHAPE_MAP.get(d[0], 'ovl')] for d in data]; vals = [d[1] for d in data]
            fig, ax = plt.subplots(figsize=(7, 6), dpi=100); fig.patch.set_facecolor('#1e1e1e')
            ax.pie(vals, labels=lbls, autopct='%1.1f%%', startangle=140, colors=['#00ff00', '#00cc00', '#009900', '#006600', '#33ff33'], textprops={'color':"w", 'weight':'bold'})
            ax.set_title(t['chart_title'], color="#00ff00", fontsize=16, fontweight='bold')
            FigureCanvasTkAgg(fig, master=self.root).get_tk_widget().pack(pady=10)
        else: tk.Label(self.root, text=t['no_data'], font=("Arial", 16), bg="#1e1e1e", fg="#888888").pack(expand=True)

    def show_admin_panel(self):
        self.clear_window(); t = TRANSLATIONS[self.lang]
        tk.Button(self.root, text="< " + t['back'], font=("Arial", 10, "bold"), bg="#333", fg="white", bd=0, command=lambda: self.show_dashboard(self.current_user)).pack(anchor="nw", padx=20, pady=20)
        tk.Label(self.root, text=t['manage_users'], font=("Arial", 18, "bold"), bg="#1e1e1e", fg="#007acc").pack(pady=10)
        tree_f = tk.Frame(self.root, bg="#1e1e1e"); tree_f.pack(fill="both", expand=True, padx=50)
        tree = ttk.Treeview(tree_f, columns=('ID', 'Login'), show='headings', height=10)
        tree.heading('ID', text='ID'); tree.heading('Login', text='Login')
        tree.column('ID', width=100, anchor="center"); tree.column('Login', width=300, anchor="center")
        tree.pack(side="left", fill="both", expand=True)
        conn = sqlite3.connect(DB_NAME); cur = conn.cursor(); cur.execute("SELECT id, login FROM users")
        for r in cur.fetchall(): tree.insert('', 'end', values=r)
        conn.close()
        def delete_user():
            sel = tree.selection()
            if not sel: return
            item = tree.item(sel[0]); u_id, u_login = item['values']
            if u_login.lower() == "admin": messagebox.showwarning("!", t['cant_del_admin']); return
            if messagebox.askyesno("?", f"{t['confirm_del']} {u_login}?"):
                conn = sqlite3.connect(DB_NAME); cur = conn.cursor(); cur.execute("DELETE FROM users WHERE id=?", (u_id,)); conn.commit(); conn.close(); tree.delete(sel)
        tk.Button(self.root, text=t['del_btn'], font=("Arial", 11, "bold"), bg="#ff4444", fg="white", bd=0, width=20, height=2, command=delete_user).pack(pady=20)

if __name__ == "__main__":
    splash_root = tk.Tk(); SplashScreen(splash_root); splash_root.mainloop()
    root = tk.Tk(); app = BarberAppUI(root); root.mainloop()