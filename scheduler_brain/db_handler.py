import psycopg2
from psycopg2.extras import RealDictCursor
import os

# Docker container ke andar se Postgres ko access karne ke credentials
DB_HOST = "postgres"
DB_NAME = "n8n"
DB_USER = "vibeuser"
DB_PASS = "vibepassword"

def get_db_connection():
    conn = psycopg2.connect(
        host=DB_HOST,
        database=DB_NAME,
        user=DB_USER,
        password=DB_PASS
    )
    return conn

def init_db():
    """Ensure tasks table exists"""
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute("""
        CREATE TABLE IF NOT EXISTS tasks (
            id SERIAL PRIMARY KEY,
            title VARCHAR(255) NOT NULL,
            duration_minutes INT NOT NULL,
            category VARCHAR(50) DEFAULT 'General',
            priority INT DEFAULT 3,
            status VARCHAR(20) DEFAULT 'PENDING',
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            scheduled_date DATE,
            is_backlog BOOLEAN DEFAULT FALSE
        );
    """)
    conn.commit()
    cur.close()
    conn.close()

def add_task(task):
    """Add a single task to DB"""
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute("""
        INSERT INTO tasks (title, duration_minutes, category, priority, is_backlog, status)
        VALUES (%s, %s, %s, %s, %s, 'PENDING')
        RETURNING id;
    """, (task['name'], task['duration'], task.get('category', 'General'), task.get('priority', 3), task.get('is_backlog', False)))
    task_id = cur.fetchone()[0]
    conn.commit()
    cur.close()
    conn.close()
    return task_id

def get_tasks_for_date(target_date):
    """Get tasks scheduled for a specific date"""
    conn = get_db_connection()
    cur = conn.cursor(cursor_factory=RealDictCursor)
    cur.execute("SELECT * FROM tasks WHERE scheduled_date = %s", (target_date,))
    tasks = cur.fetchall()
    cur.close()
    conn.close()
    return tasks

def get_pending_tasks():
    """Get all tasks that need scheduling"""
    conn = get_db_connection()
    cur = conn.cursor(cursor_factory=RealDictCursor)
    cur.execute("SELECT * FROM tasks WHERE status = 'PENDING' OR status = 'RESCHEDULE' ORDER BY priority DESC")
    tasks = cur.fetchall()
    cur.close()
    conn.close()
    return tasks

def update_task_schedule(task_id, date_str):
    """Assign a date to a task"""
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute("UPDATE tasks SET scheduled_date = %s, status = 'SCHEDULED' WHERE id = %s", (date_str, task_id))
    conn.commit()
    cur.close()
    conn.close()