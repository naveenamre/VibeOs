import sqlite3
import os

# Path to Fluid DB
db_path = "gui/fluid-calendar/prisma/dev.db"

if not os.path.exists(db_path):
    print("❌ Database file hi nahi mili!")
else:
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    # 1. Check User
    cursor.execute("SELECT id, email, name FROM User")
    users = cursor.fetchall()
    print(f"\n👤 Users Found: {len(users)}")
    for u in users: print(f" - {u}")

    # 2. Check Calendar Feed
    cursor.execute("SELECT id, name, userId FROM CalendarFeed")
    feeds = cursor.fetchall()
    print(f"\n📅 Feeds Found: {len(feeds)}")
    for f in feeds: print(f" - {f}")

    # 3. Check Events
    cursor.execute("SELECT title, start, end FROM CalendarEvent")
    events = cursor.fetchall()
    print(f"\n🗓️  Events Found: {len(events)}")
    for e in events: 
        print(f" - {e[0]} ({e[1]})")

    conn.close()