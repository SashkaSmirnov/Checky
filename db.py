import sqlite3

def init_db():
    conn = sqlite3.connect('tasks.db')
    c = conn.cursor()
    c.execute('''
        CREATE TABLE IF NOT EXISTS tasks (
            user_id INTEGER,
            task_id INTEGER PRIMARY KEY AUTOINCREMENT,
            title TEXT,
            tag TEXT,
            due_date TEXT,
            completed BOOLEAN DEFAULT 0
        )
    ''')
    conn.commit()
    conn.close()

def add_task(user_id, title, tag, due_date, completed=False):
    conn = sqlite3.connect('tasks.db')
    c = conn.cursor()
    c.execute('''
        INSERT INTO tasks (user_id, title, tag, due_date, completed)
        VALUES (?, ?, ?, ?, ?)
    ''', (user_id, title, tag, due_date, int(completed)))
    conn.commit()
    conn.close()

def get_user_tasks(user_id):
    conn = sqlite3.connect('tasks.db')
    c = conn.cursor()
    c.execute('''
        SELECT task_id, title, tag, due_date, completed 
        FROM tasks 
        WHERE user_id=?
        ORDER BY completed, datetime(due_date)
    ''', (user_id,))
    tasks = c.fetchall()
    conn.close()
    return tasks

def mark_task_completed(task_id):
    conn = sqlite3.connect('tasks.db')
    c = conn.cursor()
    c.execute('''
        UPDATE tasks 
        SET completed = 1 
        WHERE task_id = ?
    ''', (task_id,))
    conn.commit()
    conn.close()

def delete_task(task_id):
    conn = sqlite3.connect('tasks.db')
    c = conn.cursor()
    c.execute('DELETE FROM tasks WHERE task_id = ?', (task_id,))
    conn.commit()
    conn.close()