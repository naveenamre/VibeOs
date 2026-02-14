import sqlite3
import os
import sys

# --- PATH SETUP ---
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DB_PATH = os.path.join(BASE_DIR, "data", "db", "vibe_core.db")
SCHEMA_PATH = os.path.join(BASE_DIR, "core", "db", "schema.sql")

def init_db():
    print(f"⚙️  Initializing VibeOS Database...")
    print(f"   📂 Target: {DB_PATH}")
    
    # 1. Check if Schema exists
    if not os.path.exists(SCHEMA_PATH):
        print(f"   ❌ Error: Schema file not found at {SCHEMA_PATH}")
        return

    # 2. Connect to DB
    try:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        
        # 3. Read & Execute Schema (FIX: Added encoding='utf-8') 🛠️
        with open(SCHEMA_PATH, 'r', encoding='utf-8') as f:
            schema_sql = f.read()
            cursor.executescript(schema_sql)
        
        print("   ✅ Schema applied successfully.")
        
        # 4. Verification
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
        tables = cursor.fetchall()
        print(f"   📊 Tables Created: {[t[0] for t in tables]}")
        
        conn.commit()
        conn.close()
        print("\n✨ VibeOS Brain is Ready! (vibe_core.db)")
        
    except Exception as e:
        print(f"   ❌ Database Creation Failed: {e}")

if __name__ == "__main__":
    init_db()