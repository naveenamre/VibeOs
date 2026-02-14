import sys
import os
import json
import sqlite3
from datetime import datetime, timezone

# --- PATH SETUP ---
BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
DATA_DIR = os.path.join(BASE_DIR, "data")
INPUTS_DIR = os.path.join(DATA_DIR, "inputs")
FLUID_DB_PATH = os.path.join(BASE_DIR, "gui", "fluid-calendar", "prisma", "dev.dbcd")
BACKLOG_FILE = os.path.join(INPUTS_DIR, "00_backlog_recovery.json") # "00" taaki sabse pehle load ho

# --- DB CONNECTION ---
def get_db_connection():
    return sqlite3.connect(FLUID_DB_PATH)

def add_to_backlog_file(course_name, topic, category="General", duration=60):
    """
    Missed task ko JSON mein convert karke 'inputs' folder mein daal deta hai.
    Original category retain karega taaki Architect usse sahi slot mein daal sake.
    """
    new_entry = {
        "course_name": course_name,
        "category": category, # <--- FIXED: Ab ye 'Backlog' nahi, Original Category lega
        "subtasks": [
            {"topic": f"[RECOVERY] {topic}", "duration": duration}
        ]
    }
    
    # Existing backlog load karo ya naya banao
    current_data = []
    if os.path.exists(BACKLOG_FILE):
        try:
            with open(BACKLOG_FILE, "r") as f:
                current_data = json.load(f)
        except: pass
    
    current_data.append(new_entry)
    
    with open(BACKLOG_FILE, "w") as f:
        json.dump(current_data, f, indent=2)
    
    print(f"   🔄 Added to Recovery Queue: {topic} ({category})")

def process_past_tasks():
    print("🕸️ Backlog Manager Starting...")
    
    conn = get_db_connection()
    cursor = conn.cursor()
    
    # 1. Get Past Events (Jo abhi se pehle khatam ho chuke hain)
    # Fluid Calendar UTC mein store karta hai, toh hum UTC compare karenge.
    now_utc = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%S.000Z")
    
    # Query: Events that ended BEFORE now
    cursor.execute("SELECT id, title, start, end FROM CalendarEvent WHERE end < ? ORDER BY start ASC", (now_utc,))
    past_events = cursor.fetchall()
    
    if not past_events:
        print("✨ No past tasks found to review!")
        return

    print(f"🧐 Found {len(past_events)} past tasks. Time for Reality Check!")
    print("-" * 50)

    tasks_moved = 0
    
    for event in past_events:
        event_id, title, start, end = event
        
        # Human Readable Time
        try:
            # ISO string se datetime object (UTC)
            # Sirf display ke liye simple string splitting use karte hain
            display_time = start.split("T")[0] 
        except:
            display_time = "Unknown Date"

        # Ask User
        print(f"\n📅 {display_time} | 📝 Task: {title}")
        choice = input("   Did you finish this? (y/n/s=skip): ").strip().lower()
        
        if choice == 'y':
            print("   ✅ Great! Kept in history.")
            # Future: Mark as 'Done' inside DB if we add a status column
            
        elif choice == 'n':
            print("   ⚠️  Moving to Backlog...")
            
            # --- CATEGORY GUESSING LOGIC ---
            category = "General" # Default
            course_name = "Missed Task"
            topic_name = title

            # 1. Title Parse karo (Format: "Course: Topic")
            if ":" in title:
                parts = title.split(":", 1)
                course_name = parts[0].strip()
                topic_name = parts[1].strip()
            
            # 2. Keywords se Category Guess karo
            # Ye tere Course Names ke hisaab se keywords hain
            check_str = (course_name + " " + title).lower()
            
            if any(x in check_str for x in ["chem", "physics", "math", "study", "solid state"]):
                category = "Study"
            elif any(x in check_str for x in ["vibe", "code", "dev", "backend", "frontend", "api"]):
                category = "Code"
            elif "gym" in check_str or "workout" in check_str:
                category = "Gym"
                
            # 3. Add to JSON with Correct Category
            add_to_backlog_file(course_name, topic_name, category)
            
            # 4. Delete from Calendar (Taaki duplicate na dikhe)
            cursor.execute("DELETE FROM CalendarEvent WHERE id = ?", (event_id,))
            conn.commit()
            print("   🗑️  Removed from Calendar.")
            tasks_moved += 1
            
        elif choice == 's':
            print("   ⏩ Skipped review.")
    
    conn.close()
    
    print("-" * 50)
    if tasks_moved > 0:
        print(f"📉 {tasks_moved} tasks moved to 'data/inputs/00_backlog_recovery.json'.")
        print("👉 RUN 'python core/planner/architect.py' NOW to re-plan them!")
    else:
        print("🎉 No backlog created. You are on track!")

if __name__ == "__main__":
    process_past_tasks()