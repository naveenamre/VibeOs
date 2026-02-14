import sqlite3
import os
import sys

# Paths set kar lo
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
VIBE_DB = os.path.join(BASE_DIR, "data", "db", "vibe_core.db")
FLUID_DB = os.path.join(BASE_DIR, "gui", "fluid-calendar", "prisma", "dev.db")

def soft_reset():
    print("🧹 Starting Soft Reset (Tasks Only)...")

    # 1. Clean VibeOS (Backend)
    if os.path.exists(VIBE_DB):
        try:
            conn = sqlite3.connect(VIBE_DB)
            c = conn.cursor()
            # Sirf Tasks aur History udao, Schema mat chhedo
            c.execute("DELETE FROM tasks")
            c.execute("DELETE FROM history_log")
            conn.commit()
            conn.close()
            print("   ✅ VibeDB Cleaned (Tasks removed).")
        except Exception as e:
            print(f"   ❌ VibeDB Error: {e}")

    # 2. Clean Fluid Calendar (Frontend)
    if os.path.exists(FLUID_DB):
        try:
            conn = sqlite3.connect(FLUID_DB)
            c = conn.cursor()
            # DANGER: User mat udana! Sirf Events udao.
            c.execute("DELETE FROM CalendarEvent")
            conn.commit()
            conn.close()
            print("   ✅ Fluid Calendar Events Wiped (User Safe).")
        except Exception as e:
            print(f"   ❌ FluidDB Error: {e}")

    print("✨ Reset Complete. Now just run Trigger again!")

if __name__ == "__main__":
    soft_reset()