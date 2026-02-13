import sqlite3
import os

# Path check kar lo (Extension .dbcd hi honi chahiye)
db_path = os.path.join("gui", "fluid-calendar", "prisma", "dev.dbcd")

if os.path.exists(db_path):
    try:
        conn = sqlite3.connect(db_path)
        c = conn.cursor()
        
        print(f"🧹 Cleaning Database at: {db_path}")

        # 1. DELETE EVENTS (Pehle Events udaate hain)
        c.execute("DELETE FROM CalendarEvent")
        print("✅ All Events Deleted")

        # 2. DELETE FEEDS (Fir Calendar Feed)
        c.execute("DELETE FROM CalendarFeed WHERE name = 'VibeOS'")
        print("✅ VibeOS Feed Deleted")
        
        conn.commit()
        conn.close()
        print("✨ Database ab ekdum Clean hai!")
    except Exception as e:
        print(f"❌ Error: {e}")
else:
    print(f"❌ Database file nahi mili: {db_path}")