import json
import sqlite3
import os
import glob
import uuid
from datetime import datetime

# --- CONFIG ---
BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
INPUTS_DIR = os.path.join(BASE_DIR, "data", "inputs")
DB_PATH = os.path.join(BASE_DIR, "data", "db", "vibe_core.db")

def get_db_connection():
    return sqlite3.connect(DB_PATH)

def get_file_priority(filename):
    """
    Extracts priority from filename like '1_learn_english.json'
    Lower number = Higher Priority.
    """
    basename = os.path.basename(filename)
    try:
        # Agar start mein number aur underscore hai (e.g. "1_")
        if basename[0].isdigit() and "_" in basename:
            number = int(basename.split('_')[0])
            # 1 -> Priority 110 (Top)
            # 2 -> Priority 100
            return 120 - (number * 10) 
    except:
        pass
    return None # Return None if no prefix found

def ensure_schema(cursor):
    """Ensures tables exist with all required columns"""
    # Projects Table
    cursor.execute('''CREATE TABLE IF NOT EXISTS projects (
        id TEXT PRIMARY KEY,
        name TEXT,
        category TEXT,
        priority INTEGER,
        color TEXT,
        tags TEXT,
        reality_factor REAL DEFAULT 1.0
    )''')
    
    # Tasks Table (Updated with all flexible fields)
    cursor.execute('''CREATE TABLE IF NOT EXISTS tasks (
        id TEXT PRIMARY KEY, 
        project_id TEXT, 
        name TEXT, 
        status TEXT DEFAULT 'PENDING',
        category TEXT, 
        priority INTEGER, 
        duration INTEGER, 
        actual_duration INTEGER,
        energy_req TEXT,
        task_type TEXT, 
        fixed_slot TEXT, 
        dependency TEXT, 
        deadline_offset INTEGER,
        notes TEXT,
        scheduled_start TEXT, 
        calendar_event_id TEXT, 
        idempotency_key TEXT,
        is_soft_deleted INTEGER DEFAULT 0, 
        created_at TEXT
    )''')

def ingest_data():
    print("📥 Starting VibeOS Ingestion (Pro Mode)...")
    
    if not os.path.exists(INPUTS_DIR):
        print("❌ Inputs folder missing.")
        return

    files = glob.glob(os.path.join(INPUTS_DIR, "*.json"))
    if not files:
        print("✨ No input files found.")
        return
    
    # Sort files by numeric prefix (1_ first, 2_ second)
    files.sort(key=lambda f: int(os.path.basename(f).split('_')[0]) if os.path.basename(f)[0].isdigit() else 999)

    conn = get_db_connection()
    cursor = conn.cursor()
    
    # 🔥 Auto-Create Tables if missing
    ensure_schema(cursor)

    new_tasks_count = 0

    for file_path in files:
        try:
            with open(file_path, "r", encoding='utf-8') as f:
                data = json.load(f)
                
            # --- 0. EXTRACT METADATA ---
            file_prio = get_file_priority(file_path)
            
            p_name = data.get("project_name", "General Project")
            
            # 🔥 SMART CATEGORY: Use 'default_category' (New) or fallback to 'category' (Old)
            p_category = data.get("default_category", data.get("category", "General"))
            
            p_priority = file_prio if file_prio else data.get("priority", 1)
            p_tag = data.get("project_tag", "General") # Just for logs/reference
            
            color = data.get("color", "#FFFFFF")
            tags = ",".join(data.get("tags", []))
            p_reality = data.get("reality_factor", 1.0) 

            # --- 1. PROCESS PROJECT ---
            cursor.execute("SELECT id FROM projects WHERE name = ?", (p_name,))
            row = cursor.fetchone()
            
            if row:
                project_id = row[0]
                # Update Priority if file changed
                cursor.execute("UPDATE projects SET priority = ? WHERE id = ?", (p_priority, project_id))
            else:
                project_id = str(uuid.uuid4())
                cursor.execute(
                    '''INSERT INTO projects 
                    (id, name, category, priority, color, tags, reality_factor) 
                    VALUES (?, ?, ?, ?, ?, ?, ?)''',
                    (project_id, p_name, p_category, p_priority, color, tags, p_reality)
                )
                print(f"   🆕 Project: {p_name} (Cat: {p_category})")

            # --- 2. PROCESS TASKS ---
            tasks = data.get("tasks", [])
            for task in tasks:
                t_name = task.get("name")
                
                # Deduplication Check (Same name in same project = Skip)
                cursor.execute("SELECT id FROM tasks WHERE name = ? AND project_id = ?", (t_name, project_id))
                if cursor.fetchone():
                    continue 

                # Prepare Fields
                task_id = str(uuid.uuid4())
                idempotency_key = str(uuid.uuid4())
                
                duration = task.get("duration", 60)
                energy = task.get("energy", "Medium")
                t_type = task.get("type", "Flexible")
                fixed_slot = task.get("fixed_slot", None)
                dependency = task.get("depends_on", None)
                offset = task.get("deadline_offset_days", 0)
                notes = task.get("notes", "")
                
                # Task category inherits from Project Default if not specified
                t_category = task.get("category", p_category)
                t_priority = task.get("priority", p_priority)

                initial_status = 'BLOCKED' if dependency else 'PENDING'

                # 🛡️ THE MEGA INSERT (Matches New Schema)
                cursor.execute('''
                    INSERT INTO tasks (
                        id, project_id, name, status, 
                        is_soft_deleted, idempotency_key, 
                        category, priority, 
                        duration, actual_duration, energy_req, 
                        task_type, fixed_slot, dependency, 
                        deadline_offset, notes, created_at
                    )
                    VALUES (?, ?, ?, ?, 0, ?, ?, ?, ?, NULL, ?, ?, ?, ?, ?, ?, datetime('now'))
                ''', (
                    task_id, project_id, t_name, initial_status,
                    idempotency_key,
                    t_category, t_priority,
                    duration, energy,
                    t_type, fixed_slot, dependency,
                    offset, notes
                ))
                
                new_tasks_count += 1
                # print(f"   ➕ Task: {t_name}")

        except Exception as e:
            print(f"   ❌ Error in {os.path.basename(file_path)}: {e}")

    conn.commit()
    conn.close()
    
    if new_tasks_count > 0:
        print(f"✅ Ingestion Done. {new_tasks_count} new tasks loaded.")
    else:
        print("💤 System up to date.")

if __name__ == "__main__":
    ingest_data()