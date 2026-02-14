import sqlite3
import os

class VibeArchitect:
    def __init__(self, db_path):
        self.db_path = db_path

    def get_db_connection(self):
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        return conn

    def get_balanced_batch(self, limit_per_subject=1):
        """
        Selects tasks for a single day based on 'Drip Feed' logic.
        Ensures we don't burnout on one subject (e.g. 1 Japanese, 1 C++ per day).
        Returns: (daily_batch, remaining_backlog)
        """
        conn = self.get_db_connection()
        cursor = conn.cursor()

        print("   🏗️  Architect: Analyzing Backlog for Balanced Pacing...")

        # 1. Fetch ALL Pending Tasks (Sorted by Priority)
        # Higher priority first, then older created_at
        cursor.execute("""
            SELECT * FROM tasks 
            WHERE status = 'PENDING' AND is_soft_deleted = 0
            ORDER BY priority DESC, created_at ASC
        """)
        all_tasks = [dict(row) for row in cursor.fetchall()]
        conn.close()
        
        if not all_tasks:
            return [], []

        # 2. FILTER FOR BALANCE (The Smart Selector)
        daily_batch = []
        remaining = []
        
        # Track usage per "Subject" to enforce limit
        # Key format: "Category_Subject" (e.g., "Learn_Japanese", "Code_VibeOS")
        used_keys = {} 

        for task in all_tasks:
            cat = task.get('category', 'General')
            name = task.get('name', '')
            
            # Smart Subject Detection: First word of name is usually the subject
            # e.g. "Japanese Lecture 1" -> "Japanese"
            # e.g. "C++ Lecture 2" -> "C++"
            subject = name.split()[0] if ' ' in name else 'Gen'
            
            # Unique Key for pacing
            key = f"{cat}_{subject}"

            # Check limit
            current_count = used_keys.get(key, 0)
            
            if current_count < limit_per_subject:
                daily_batch.append(task)
                used_keys[key] = current_count + 1
            else:
                # Agar aaj ka quota full hai, toh backlog mein daalo (for next days)
                remaining.append(task)
        
        print(f"   🏗️  Architect: Selected {len(daily_batch)} tasks for today. (Backlog: {len(remaining)})")
        
        return daily_batch, remaining