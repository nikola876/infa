from flask import Flask, render_template, request, redirect, url_for
import sqlite3

app = Flask(__name__)

def init_db():
    with sqlite3.connect("tasks.db") as conn:
        cursor = conn.cursor()
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS tasks (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                text TEXT NOT NULL,
                done INTEGER DEFAULT 0
            )
        """)
        conn.commit()

init_db()

def get_tasks():
    with sqlite3.connect("tasks.db") as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT id, text, done FROM tasks")
        return [{"id": row[0], "text": row[1], "done": bool(row[2])} for row in cursor.fetchall()]

@app.route('/')
def index():
    return render_template('index.html', tasks=get_tasks())

@app.route('/add', methods=['POST'])
def add_task():
    task = request.form.get('task')
    if task:
        with sqlite3.connect("tasks.db") as conn:
            conn.execute("INSERT INTO tasks (text) VALUES (?)", (task,))
            conn.commit()
    return redirect(url_for('index'))

@app.route('/complete/<int:task_id>')
def complete_task(task_id):
    with sqlite3.connect("tasks.db") as conn:
        conn.execute("UPDATE tasks SET done = 1 WHERE id = ?", (task_id,))
        conn.commit()
    return redirect(url_for('index'))

@app.route('/delete/<int:task_id>')
def delete_task(task_id):
    with sqlite3.connect("tasks.db") as conn:
        conn.execute("DELETE FROM tasks WHERE id = ?", (task_id,))
        conn.commit()
    return redirect(url_for('index'))

@app.route('/edit/<int:task_id>', methods=['POST'])
def edit_task(task_id):
    new_text = request.form.get('task')
    if new_text:
        with sqlite3.connect("tasks.db") as conn:
            conn.execute("UPDATE tasks SET text = ? WHERE id = ?", (new_text, task_id))
            conn.commit()
    return redirect(url_for('index'))

if __name__ == '__main__':
    app.run(debug=True)