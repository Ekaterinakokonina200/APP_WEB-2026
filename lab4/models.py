import sqlite3
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime

DATABASE = 'users.db'

def get_db():
    conn = sqlite3.connect(DATABASE)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    """Инициализация базы данных"""
    conn = get_db()
    cursor = conn.cursor()
    
    # Таблица ролей
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS roles (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL UNIQUE,
            description TEXT
        )
    ''')
    
    # Таблица пользователей
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            login TEXT NOT NULL UNIQUE,
            password_hash TEXT NOT NULL,
            last_name TEXT,
            first_name TEXT NOT NULL,
            middle_name TEXT,
            role_id INTEGER,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (role_id) REFERENCES roles (id)
        )
    ''')
    
    # Добавляем роли по умолчанию
    cursor.execute('INSERT OR IGNORE INTO roles (id, name, description) VALUES (1, "admin", "Administrator")')
    cursor.execute('INSERT OR IGNORE INTO roles (id, name, description) VALUES (2, "user", "Regular user")')
    
    # Добавляем тестового пользователя (пароль: Admin123!)
    admin_password = generate_password_hash('Admin123!')
    cursor.execute('''
        INSERT OR IGNORE INTO users (id, login, password_hash, last_name, first_name, middle_name, role_id)
        VALUES (1, 'admin', ?, 'Admin', 'Admin', 'Adminovich', 1)
    ''', (admin_password,))
    
    conn.commit()
    conn.close()

def get_user_by_id(user_id):
    conn = get_db()
    user = conn.execute('''
        SELECT u.*, r.name as role_name, r.description as role_description
        FROM users u
        LEFT JOIN roles r ON u.role_id = r.id
        WHERE u.id = ?
    ''', (user_id,)).fetchone()
    conn.close()
    return user

def get_user_by_login(login):
    conn = get_db()
    user = conn.execute('''
        SELECT u.*, r.name as role_name
        FROM users u
        LEFT JOIN roles r ON u.role_id = r.id
        WHERE u.login = ?
    ''', (login,)).fetchone()
    conn.close()
    return user

def get_all_users():
    conn = get_db()
    users = conn.execute('''
        SELECT u.*, r.name as role_name
        FROM users u
        LEFT JOIN roles r ON u.role_id = r.id
        ORDER BY u.id
    ''').fetchall()
    conn.close()
    return users

def get_all_roles():
    conn = get_db()
    roles = conn.execute('SELECT * FROM roles').fetchall()
    conn.close()
    return roles

def create_user(login, password, last_name, first_name, middle_name, role_id):
    conn = get_db()
    cursor = conn.cursor()
    password_hash = generate_password_hash(password)
    try:
        cursor.execute('''
            INSERT INTO users (login, password_hash, last_name, first_name, middle_name, role_id)
            VALUES (?, ?, ?, ?, ?, ?)
        ''', (login, password_hash, last_name, first_name, middle_name, role_id))
        conn.commit()
        return True, None
    except sqlite3.IntegrityError as e:
        return False, str(e)
    finally:
        conn.close()

def update_user(user_id, last_name, first_name, middle_name, role_id):
    conn = get_db()
    cursor = conn.cursor()
    try:
        cursor.execute('''
            UPDATE users
            SET last_name = ?, first_name = ?, middle_name = ?, role_id = ?
            WHERE id = ?
        ''', (last_name, first_name, middle_name, role_id, user_id))
        conn.commit()
        return True, None
    except Exception as e:
        return False, str(e)
    finally:
        conn.close()

def delete_user(user_id):
    conn = get_db()
    cursor = conn.cursor()
    try:
        cursor.execute('DELETE FROM users WHERE id = ?', (user_id,))
        conn.commit()
        return True, None
    except Exception as e:
        return False, str(e)
    finally:
        conn.close()

def change_password(user_id, new_password):
    conn = get_db()
    cursor = conn.cursor()
    password_hash = generate_password_hash(new_password)
    try:
        cursor.execute('UPDATE users SET password_hash = ? WHERE id = ?', (password_hash, user_id))
        conn.commit()
        return True, None
    except Exception as e:
        return False, str(e)
    finally:
        conn.close()