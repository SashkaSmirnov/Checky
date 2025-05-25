import sqlite3

# initializes the database and creates a tasks table if it doesn't exist
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

# adds a new task
def add_task(user_id, title, tag, due_date, completed=False):
    conn = sqlite3.connect('tasks.db')
    c = conn.cursor()
    c.execute('''
        INSERT INTO tasks (user_id, title, tag, due_date, completed)
        VALUES (?, ?, ?, ?, ?)
    ''', (user_id, title, tag, due_date, int(completed)))
    conn.commit()
    conn.close()

# retrieves all tasks for a given user, sorted by completion and due date
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

# marks a task as completed
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

# deletes a task
def delete_task(task_id):
    conn = sqlite3.connect('tasks.db')
    c = conn.cursor()
    c.execute('DELETE FROM tasks WHERE task_id = ?', (task_id,))
    conn.commit()
    conn.close()