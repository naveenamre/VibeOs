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
    """Jugaad to ensure Projects table exists without running full setup"""
    cursor.execute('''CREATE TABLE IF NOT EXISTS projects (
        id TEXT PRIMARY KEY,
        name TEXT,
        category TEXT,
        priority INTEGER,
        color TEXT,
        tags TEXT,
        reality_factor REAL DEFAULT 1.0
    )''')
    
    # Ensure Tasks table has project_id column
    # (Simple check: Try adding it, ignore if exists - but for now assuming tasks table exists)

def ingest_data():
    print("📥 Starting VibeOS Ingestion (Enterprise Mode)...")
    
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
    
    # 🔥 Auto-Create Projects Table if missing
    ensure_schema(cursor)

    new_tasks_count = 0

    for file_path in files:
        try:
            with open(file_path, "r", encoding='utf-8') as f:
                data = json.load(f)
                
            # --- 0. CALCULATE FILE PRIORITY ---
            file_prio = get_file_priority(file_path)
                
            # --- 1. PROCESS PROJECT ---
            p_name = data.get("project_name", "General Project")
            p_category = data.get("category", "General")
            
            # Agar file name mein '1_' hai toh wo priority use karo, warna JSON wali
            p_priority = file_prio if file_prio else data.get("priority", 1)
            
            color = data.get("color", "#FFFFFF")
            tags = ",".join(data.get("tags", []))
            p_reality = data.get("reality_factor", 1.0) 

            # Upsert Project
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
                print(f"   🆕 Project: {p_name} (Prio: {p_priority})")

            # --- 2. PROCESS TASKS ---
            tasks = data.get("tasks", [])
            for task in tasks:
                t_name = task.get("name")
                
                # Deduplication Check
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
                
                t_category = task.get("category", p_category)
                # Task priority inherits from Project/File unless overridden
                t_priority = task.get("priority", p_priority)

                initial_status = 'BLOCKED' if dependency else 'PENDING'

                # 🛡️ THE MEGA INSERT
                cursor.execute('''
                    INSERT INTO tasks (
                        id, project_id, name, status, 
                        is_soft_deleted, idempotency_key, 
                        category, priority, 
                        duration, actual_duration, energy_req, 
                        task_type, fixed_slot, dependency, 
                        deadline_offset, notes
                    )
                    VALUES (?, ?, ?, ?, 0, ?, ?, ?, ?, NULL, ?, ?, ?, ?, ?, ?)
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
        print(f"✅ Ingestion Done. {new_tasks_count} tasks loaded.")
    else:
        print("💤 System up to date.")

if __name__ == "__main__":
    ingest_data()