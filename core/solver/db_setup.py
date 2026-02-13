import sqlite3
import os

# Database Path
DB_PATH = os.path.join("data", "vibeos.db")

def init_db():
    # Ensure data directory exists
    os.makedirs("data", exist_ok=True)
    
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    # 1. TASKS TABLE (Input Queue)
    # Isme wo tasks rahenge jo abhi schedule nahi huye
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS tasks (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            duration INTEGER NOT NULL,
            category TEXT DEFAULT 'Any',
            priority INTEGER DEFAULT 3,
            deadline DATE,
            status TEXT DEFAULT 'PENDING', -- PENDING, SCHEDULED, DONE
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')

    # 2. SCHEDULE TABLE (Output Plan)
    # Jo Python Engine calculate karke dega, wo yahan save hoga
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS schedule (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            task_id INTEGER,
            day_date DATE,
            start_time TEXT,
            end_time TEXT,
            category TEXT,
            FOREIGN KEY(task_id) REFERENCES tasks(id)
        )
    ''')
    
    # 3. HISTORY TABLE (For Reality Factor)
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS history (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            task_name TEXT,
            category TEXT,
            planned_duration INTEGER,
            actual_duration INTEGER,
            completed_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')

    conn.commit()
    conn.close()
    print(f"✅ Database initialized at: {DB_PATH}")

if __name__ == "__main__":
    init_db()