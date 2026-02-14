import sqlite3
import os

class VibeArchitect:
    def __init__(self, db_path):
        self.db_path = db_path

    def get_db_connection(self):
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        return conn

    def get_daily_batch(self, limit_per_category=2):
        """
        Ye function decide karta hai ki AAJ kaunse tasks schedule hone chahiye.
        Pura backlog nahi uthata, sirf 'Paced' batch uthata hai.
        """
        conn = self.get_db_connection()
        cursor = conn.cursor()

        print("   🏗️  Architect: Reviewing Backlog for Daily Batch...")

        # 1. Fetch ALL Pending Tasks (Sorted by Priority)
        # Hum 'is_soft_deleted=0' check kar rahe hain taaki deleted tasks wapas na aayein
        cursor.execute("""
            SELECT * FROM tasks 
            WHERE status = 'PENDING' AND is_soft_deleted = 0
            ORDER BY priority DESC, created_at ASC
        """)
        all_tasks = [dict(row) for row in cursor.fetchall()]
        
        if not all_tasks:
            conn.close()
            return []

        # 2. APPLY PACING RULES (The "Thoda-Thoda" Logic) 🐢
        # Hum har category se sirf limited tasks uthayenge
        
        daily_batch = []
        category_counts = {}
        
        # Custom Limits (Future mein config se aa sakta hai)
        limits = {
            "Language": 1,   # Roz 1 Lecture
            "Study": 2,      # Roz 2 Study Sessions
            "Code": 2,       # Roz 2 Code Sessions
            "Project": 1,    # Roz 1 Project Task
            "General": 3     # Chote mote kaam
        }

        for task in all_tasks:
            cat = task.get('category', 'General')
            limit = limits.get(cat, limit_per_category)
            
            # Counter initialize
            if cat not in category_counts:
                category_counts[cat] = 0
            
            # Agar limit bachi hai, toh task utha lo
            if category_counts[cat] < limit:
                daily_batch.append(task)
                category_counts[cat] += 1
        
        print(f"   🏗️  Architect: Selected {len(daily_batch)} tasks from {len(all_tasks)} pending items.")
        print(f"       (Breakdown: {category_counts})")

        conn.close()
        return daily_batch