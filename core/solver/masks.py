# VibeOS_2026/core/solver/masks.py

def get_weekly_template(day_name):
    """
    Returns the Fixed Time Blocks (The Constitution) for a given day.
    Format: Start Hour, End Hour, Category
    """
    
    # 🕒 MONDAY TEMPLATE (Hard Work Mode)
    if day_name == "Monday":
        return [
            {"start": 9,  "end": 12, "type": "Study"},  # 3h Deep Work
            {"start": 12, "end": 13, "type": "Break"},  # Lunch
            {"start": 13, "end": 14, "type": "Chill"},  # Power Nap / Anime
            {"start": 14, "end": 17, "type": "Code"},   # 3h Coding
            {"start": 17, "end": 18, "type": "Break"},  # Tea Time
            {"start": 18, "end": 20, "type": "Study"},  # Revision
            {"start": 21, "end": 23, "type": "Chill"}   # Gaming/Movies
        ]
    
    # 🕒 TUESDAY TEMPLATE (Coding Focus)
    elif day_name == "Tuesday":
        return [
            {"start": 9,  "end": 13, "type": "Code"},   # 4h Marathon
            {"start": 14, "end": 16, "type": "Study"},
            {"start": 17, "end": 20, "type": "Code"},
            {"start": 21, "end": 23, "type": "Chill"}
        ]

    # ... Baki din add kar lena ...
    
    # Default Fallback
    return [{"start": 10, "end": 18, "type": "Any"}]