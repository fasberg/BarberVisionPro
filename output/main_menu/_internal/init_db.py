# -*- coding: utf-8 -*-
import sqlite3
import os

def init_database():
    db_path = 'barber_pro.db'
    if os.path.exists(db_path): 
        try: os.remove(db_path)
        except: pass
    
    for folder in ['haircuts', 'reports']:
        if not os.path.exists(folder): os.makedirs(folder)

    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    # Таблиця рекомендацій 
    cursor.execute('''CREATE TABLE recommendations (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        shape_name TEXT,
        haircut_name TEXT,
        description TEXT,
        photo_path TEXT)''')

    # Таблиця історії клієнтів
    cursor.execute('''CREATE TABLE client_history (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        date_time TEXT,
        face_shape TEXT,
        ratio REAL,
        screenshot_path TEXT,
        pdf_path TEXT)''') 

    # Наповнення експертними даними
    data = [
        ('Oval', 'Classic Taper / Pompadour', 
         'Універсальна форма. Рекомендується зберігати природний баланс, уникаючи занадто довгих чолок.', 
         'haircuts/oval.jpg'),
        ('Oblong', 'Textured Crop / Side Part', 
         'Потрібно візуально зменшити вертикаль. Вибирайте зачіски з більшим об’ємом з боків.', 
         'haircuts/oblong.jpg'),
        ('Square', 'Buzz Cut / Crew Cut', 
         'Сильна щелепа — ваша перевага. Класичні мілітарі-стрижки найкраще підкреслюють мужність.', 
         'haircuts/square.jpg'),
        ('Round', 'High Fade / Pompadour', 
         'Потрібно візуально витягнути обличчя. Додаємо висоти зверху та максимально прибираємо боки.', 
         'haircuts/round.jpg'),
        ('Heart', 'Longer Fringe / Side Swept', 
         'Збалансовуємо широкий лоб. Рекомендується середня довжина, що додає маси знизу.', 
         'haircuts/heart.jpg'),
        ('Diamond', 'Messy Quiff / Long Hair', 
         'Пом’якшуємо вилиці. Добре підходять текстуровані зачіски з пасмами на чоло.', 
         'haircuts/diamond.jpg')
    ]

    cursor.executemany('INSERT INTO recommendations (shape_name, haircut_name, description, photo_path) VALUES (?, ?, ?, ?)', data)
    conn.commit()
    conn.close()
    print("--- Database v4.0 Initialized Successfully (Group 451) ---")

if __name__ == "__main__":
    init_database()