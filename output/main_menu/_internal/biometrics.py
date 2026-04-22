# -*- coding: utf-8 -*-
import cv2
import math
import sqlite3
import os
import csv
import time
import numpy as np
import json
import sys
from datetime import datetime
from fpdf import FPDF
from PIL import ImageFont, ImageDraw, Image

def resource_path(relative_path):
    if hasattr(sys, '_MEIPASS'):
        return os.path.join(sys._MEIPASS, relative_path)
    return os.path.join(os.path.abspath("."), relative_path)

# --- СТАБІЛЬНИЙ ІМПОРТ ДЛЯ MEDIAPIPE 0.10.x ---
try:
    import mediapipe as mp
    # Для версії 0.10.9 найкраще працює звернення через mp.solutions
    # але ми додамо перевірку для PyInstaller
    mp_face_mesh = mp.solutions.face_mesh
    mp_drawing = mp.solutions.drawing_utils
    mp_drawing_styles = mp.solutions.drawing_styles
    print("[SUCCESS] MediaPipe системи активовані.")
except (ImportError, AttributeError):
    # План Б: якщо mp.solutions недоступний (буває в деяких збірках EXE)
    try:
        import mediapipe.python.solutions.face_mesh as mp_face_mesh
        import mediapipe.python.solutions.drawing_utils as mp_drawing
        import mediapipe.python.solutions.drawing_styles as mp_drawing_styles
    except Exception as e:
        print(f"[!] Помилка ініціалізації AI: {e}")
        # Тут НЕ використовуємо input(), щоб не "валити" EXE без консолі
        sys.exit(1)

class ReportGenerator:
    """Генерація PDF з підтримкою української мови та графіки"""
    def create_pdf(self, shape, ratio, haircut, desc, scan_path, style_path):
        try:
            pdf = FPDF()
            pdf.add_page()
            # Використання системного шрифту для кирилиці
            font_path = "C:\\Windows\\Fonts\\arial.ttf"
            pdf.add_font("ArialUA", "", font_path)
            pdf.set_font("ArialUA", size=12)
            
            pdf.set_font("ArialUA", size=22)
            pdf.cell(200, 20, txt="BARBERVISION PRO - ЗВІТ АНАЛІЗУ", ln=True, align='C')
            
            pdf.set_font("ArialUA", size=10)
            pdf.cell(200, 8, txt=f"Дата: {datetime.now().strftime('%Y-%m-%d %H:%M')}", ln=True)
            pdf.cell(200, 8, txt="Спеціаліст: Давід Закарадзе (Група 451)", ln=True)
            
            pdf.ln(10)
            pdf.set_fill_color(240, 240, 240)
            pdf.set_font("ArialUA", size=14)
            pdf.cell(190, 12, txt=f"  ФОРМА ОБЛИЧЧЯ: {shape} (Ratio: {ratio})", ln=True, fill=True)
            pdf.cell(190, 12, txt=f"  РЕКОМЕНДОВАНИЙ СТИЛЬ: {haircut}", ln=True, fill=True)
            
            pdf.ln(5)
            pdf.set_font("ArialUA", size=11)
            pdf.multi_cell(190, 8, txt=f"Порада майстра: {desc}", border=1)
            
            curr_y = pdf.get_y() + 10
            if os.path.exists(scan_path):
                pdf.image(scan_path, x=10, y=curr_y, w=90)
            if style_path and os.path.exists(style_path):
                pdf.image(style_path, x=110, y=curr_y, w=90)
                
            fname = f"reports/report_{datetime.now().strftime('%H%M%S')}.pdf"
            pdf.output(fname)
            return fname
        except Exception as e:
            return f"Error: {e}"

class FaceAnalyzer:
    """Математичний аналіз антропометрії обличчя"""
    def __init__(self):
        self.buffer = []
        self.size = 25 # Розмір вікна для ковзного середнього 

    def get_dist_px(self, p1, p2, w, h):
        """Розрахунок Евклідової відстані"""
        return math.sqrt(((p1.x - p2.x) * w)**2 + ((p1.y - p2.y) * h)**2)

    def analyze(self, landmarks, w, h):
        """Детекція пропорцій та класифікація"""
        # Отримання ключових відстаней 
        face_h = self.get_dist_px(landmarks[10], landmarks[152], w, h)
        w_ch = self.get_dist_px(landmarks[234], landmarks[454], w, h)
        w_j = self.get_dist_px(landmarks[58], landmarks[288], w, h)

        ratio = round(face_h / w_ch, 2) # Морфологічний коефіцієнт 
        jaw_idx = w_j / w_ch            # Індекс щелепи 
        
        # Реалізація методу ковзного середнього 
        self.buffer.append(ratio)
        if len(self.buffer) > self.size: self.buffer.pop(0)
        avg = sum(self.buffer) / len(self.buffer)

        # Логіка класифікації форм 
        if avg > 1.45: shape = "Oblong"
        elif avg > 1.18: shape = "Heart" if jaw_idx < 0.73 else "Oval"
        else: shape = "Square" if jaw_idx > 0.92 else "Round"
            
        return shape, round(avg, 2)

    def check_database(self):
        """Автоматичне створення та наповнення БД, якщо її немає"""
        if not os.path.exists(self.db_name):
            print("[SYSTEM] Базу не знайдено. Ініціалізація...")
            conn = sqlite3.connect(self.db_name)
            cursor = conn.cursor()
            
            # Створюємо таблиці (код з твого init_db.py)
            cursor.execute('''CREATE TABLE IF NOT EXISTS recommendations (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                shape_name TEXT,
                haircut_name TEXT,
                description TEXT,
                photo_path TEXT)''')

            cursor.execute('''CREATE TABLE IF NOT EXISTS client_history (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                date_time TEXT, face_shape TEXT, ratio REAL,
                screenshot_path TEXT, pdf_path TEXT)''')

            # Наповнюємо даними (тільки якщо таблиця порожня)
            data = [
                ('Oval', 'Classic Taper / Pompadour', 'Універсальна форма...', 'haircuts/oval.jpg'),
                ('Oblong', 'Textured Crop / Side Part', 'Потрібно візуально зменшити вертикаль...', 'haircuts/oblong.jpg'),
                ('Square', 'Buzz Cut / Crew Cut', 'Сильна щелепа — ваша перевага...', 'haircuts/square.jpg'),
                ('Round', 'High Fade / Pompadour', 'Потрібно візуально витягнути обличчя...', 'haircuts/round.jpg'),
                ('Heart', 'Longer Fringe / Side Swept', 'Збалансовуємо широкий лоб...', 'haircuts/heart.jpg'),
                ('Diamond', 'Messy Quiff / Long Hair', 'Пом’якшуємо вилиці...', 'haircuts/diamond.jpg')
            ]
            cursor.executemany('INSERT INTO recommendations (shape_name, haircut_name, description, photo_path) VALUES (?, ?, ?, ?)', data)
            conn.commit()
            conn.close()
            print("[SYSTEM] База даних готова до роботи.")

class BarberVisionApp:
    """Контролер біометричного модуля"""
    def __init__(self):
        self.db_name = 'barber_pro.db'
        self.check_database()
        # Ініціалізація AI детектора 
        self.detector = mp_face_mesh.FaceMesh(
            max_num_faces=1,
            refine_landmarks=True,
            min_detection_confidence=0.5,
            min_tracking_confidence=0.5
        )
        self.analyzer = FaceAnalyzer()
        self.db_name = 'barber_pro.db'
        self.pdf_gen = ReportGenerator()
        
        # Система екранних сповіщень
        self.notif_text = ""
        self.notif_time = 0
        self.notif_duration = 2.5 

        try:
            with open("settings.json", "r") as f:
                conf = json.load(f)
                cam_id = conf.get("camera_id", 0)
        except:
            cam_id = 0
            
        self.cap = cv2.VideoCapture(cam_id)
        self.cap.set(cv2.CAP_PROP_FRAME_WIDTH, 1280)
        self.cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 720)
        
        # Завантаження шрифтів для GUI
        try:
            self.font_ui = ImageFont.truetype("C:\\Windows\\Fonts\\arial.ttf", 22)
            self.font_status = ImageFont.truetype("C:\\Windows\\Fonts\\arial.ttf", 18)
            self.font_notif = ImageFont.truetype("C:\\Windows\\Fonts\\arial.ttf", 28)
        except:
            self.font_ui = self.font_status = self.font_notif = ImageFont.load_default()

    def trigger_notif(self, text):
        """Активація візуального підтвердження"""
        self.notif_text = text
        self.notif_time = time.time()

    def draw_ukr_text(self, img, text, pos, color=(0, 255, 0), font_mode="ui"):
        """Рендеринг кирилиці на кадрі"""
        img_pil = Image.fromarray(cv2.cvtColor(img, cv2.COLOR_BGR2RGB))
        draw = ImageDraw.Draw(img_pil)
        
        if font_mode == "status": fnt = self.font_status
        elif font_mode == "notif": fnt = self.font_notif
        else: fnt = self.font_ui
        
        draw.text(pos, text, font=fnt, fill=color)
        return cv2.cvtColor(np.array(img_pil), cv2.COLOR_RGB2BGR)



    def draw_ui(self, frame, shape, ratio, style_path, status_text, status_color):
        """Візуалізація інтерфейсу та оверлею"""
        h, w, _ = frame.shape
        sb_w = 400
        
        # Бічна панель результатів 
        overlay = frame.copy()
        cv2.rectangle(overlay, (w - sb_w, 0), (w, h), (25, 25, 25), -1)
        cv2.addWeighted(overlay, 0.8, frame, 0.2, 0, frame)

        # Живий індикатор статусу 
        cv2.circle(frame, (w-sb_w+35, 40), 8, status_color, -1)
        frame = self.draw_ukr_text(frame, status_text, (w-sb_w+55, 30), status_color, "status")

        cv2.putText(frame, "BIOMETRICS", (w-sb_w+80, 90), 2, 1.2, (0, 255, 0), 2)
        cv2.putText(frame, f"SHAPE: {shape}", (w-sb_w+30, 160), 2, 0.9, (255, 255, 255), 2)
        cv2.putText(frame, f"RATIO: {ratio}", (w-sb_w+30, 200), 1, 1.1, (200, 200, 200), 1)
        
        # Відображення рекомендованої стрижки 
        if style_path and os.path.exists(style_path):
            img = cv2.imread(style_path)
            if img is not None:
                img = cv2.resize(img, (340, 310))
                frame[h-400:h-90, w-sb_w+30:w-sb_w+370] = img
                frame = self.draw_ukr_text(frame, "РЕКОМЕНДОВАНИЙ СТИЛЬ", (w-sb_w+60, h-440), (255, 255, 0))

        # Екранне сповіщення 
        if time.time() - self.notif_time < self.notif_duration:
            n_overlay = frame.copy()
            cv2.rectangle(n_overlay, (w//2-300, 100), (w//2+300, 170), (0, 120, 0), -1)
            cv2.addWeighted(n_overlay, 0.7, frame, 0.3, 0, frame)
            frame = self.draw_ukr_text(frame, self.notif_text, (w//2-280, 115), (255, 255, 255), "notif")

        # Панель підказок
        cv2.rectangle(frame, (0, h-60), (w-sb_w, h), (0, 0, 0), -1)
        hints = "[S]-Скріншот  [P]-Звіт(Save)  [C]-Експорт CSV  [Q]-Вихід(Exit)"
        return self.draw_ukr_text(frame, hints, (30, h-45))

    def run(self):
        """Головний цикл обробки"""
        while self.cap.isOpened():
            # Автоматичне створення папок для роботи
            for folder in ['reports', 'backups']:
               if not os.path.exists(folder):
                 os.makedirs(folder, exist_ok=True)
            success, frame = self.cap.read()
            if not success: break
            
            frame = cv2.flip(frame, 1)
            h_f, w_f, _ = frame.shape
            
            # Обробка кадру нейромережею
            rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            results = self.detector.process(rgb_frame)

            current_shape = "Waiting..."
            current_ratio = 0.0
            style_p = None
            desc = ""
            res = None
            
            if not results.multi_face_landmarks:
                st_text = "ОБЛИЧЧЯ НЕ ВИЯВЛЕНО"
                st_color = (0, 0, 255)
            else:
                for face_lms in results.multi_face_landmarks:
                    # Візуалізація маски 
                    mp_drawing.draw_landmarks(
                        frame, face_lms, mp_face_mesh.FACEMESH_TESSELATION,
                        None, mp_drawing_styles.get_default_face_mesh_tesselation_style())

                    # Біометричний аналіз
                    current_shape, current_ratio = self.analyzer.analyze(face_lms.landmark, w_f, h_f)
                    
                    if len(self.analyzer.buffer) < self.analyzer.size:
                        st_text = "СКАНУВАННЯ..."
                        st_color = (0, 255, 255)
                    else:
                        st_text = "СИСТЕМА ГОТОВА"
                        st_color = (0, 255, 0)

                    # Запит рекомендацій з БД 
                    try:
                        conn = sqlite3.connect(self.db_name)
                        cursor = conn.cursor()
                        cursor.execute("SELECT haircut_name, photo_path, description FROM recommendations WHERE shape_name = ?", (current_shape,))
                        res = cursor.fetchone()
                        conn.close()
                        if res: style_p, desc = res[1], res[2]
                    except: pass

            frame = self.draw_ui(frame, current_shape, current_ratio, style_p, st_text, st_color)
            cv2.imshow('BarberVision PRO - David Zakaradze', frame)

            key = cv2.waitKey(1) & 0xFF
            
            # Обробка подій клавіатури
            if key == ord('s'):
                path = f"reports/img_{datetime.now().strftime('%H%M%S')}.jpg"
                cv2.imwrite(path, frame)
                self.trigger_notif("ЗБЕРЕЖЕНО СКРІНШОТ")

            elif key == ord('p') and results.multi_face_landmarks:
                try:
                    timestamp = datetime.now().strftime('%H%M%S')
                    snap_path = f"reports/pdf_snap_{timestamp}.jpg"
                    cv2.imwrite(snap_path, frame)
                    
                    h_name = res[0] if res else "Unknown"
                    pdf_path = self.pdf_gen.create_pdf(current_shape, current_ratio, h_name, desc, snap_path, style_p)
                    
                    # Запис в історію БД 
                    conn = sqlite3.connect(self.db_name)
                    cursor = conn.cursor()
                    cursor.execute("""INSERT INTO client_history 
                                  (date_time, face_shape, ratio, screenshot_path, pdf_path) 
                                  VALUES (?, ?, ?, ?, ?)""", 
                                  (datetime.now().strftime('%Y-%m-%d %H:%M'), 
                                   current_shape, current_ratio, os.path.abspath(snap_path), os.path.abspath(pdf_path)))
                    conn.commit()
                    conn.close()
                    self.trigger_notif("PDF-ЗВІТ СФОРМОВАНО ТА ЗБЕРЕЖЕНО")
                except Exception as e:
                    self.trigger_notif("ПОМИЛКА ЗБЕРЕЖЕННЯ")

            elif key == ord('c'):
                # Експорт історії в CSV 
                csv_path = f"reports/history_{datetime.now().strftime('%H%M%S')}.csv"
                try:
                    conn = sqlite3.connect(self.db_name); cur = conn.cursor()
                    cur.execute("SELECT * FROM client_history"); data = cur.fetchall(); conn.close()
                    with open(csv_path, 'w', newline='', encoding='utf-8-sig') as f:
                        writer = csv.writer(f)
                        writer.writerow(['ID', 'Час', 'Форма', 'Коефіцієнт', 'Фото', 'PDF'])
                        writer.writerows(data)
                    self.trigger_notif("ІСТОРІЮ ЕКСПОРТОВАНО В CSV")
                except: pass

            elif key == ord('q'): break

        self.cap.release()
        cv2.destroyAllWindows()

if __name__ == "__main__":
    try:
        BarberVisionApp().run()
    except Exception as e:
        print(f"Критичний збій: {e}")