from datetime import datetime, timedelta, timezone

def to_utc_iso(dt_local):
    """IST to UTC for Database storage"""
    # Local time se 5:30 ghante ghatao taaki Calendar par sahi dikhe
    # Assumes dt_local is naive IST
    dt_utc = dt_local - timedelta(hours=5, minutes=30)
    return dt_utc.replace(tzinfo=timezone.utc).strftime("%Y-%m-%dT%H:%M:%S.000Z")

def to_iso_now():
    """Current UTC time in ISO format (Required for DB timestamps)"""
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%S.000Z")

def flatten_template_to_slots(week_template, start_date, days_ahead=7):
    """
    Parses Week Template into actionable Time Slots.
    Handles 'Tuesday': 'Monday' references intelligently.
    🛡️ PRESERVED: De-duplication logic to prevent double booking.
    🔥 NEW: Separates 'Constant' blocks from 'Free' slots.
    """
    free_slots = []
    constant_blocks = []
    current = start_date
    
    # 1. Get Current Mode Logic
    mode_name = week_template.get("current_mode", "Normal")
    modes = week_template.get("modes", {})
    active_schedule = modes.get(mode_name, {})
    
    # Track unique slots to prevent overlaps (e.g., if template has duplicates)
    seen_times = set()

    print(f"   📅 Generating Slots for Mode: {mode_name}")

    for _ in range(days_ahead):
        day_name = current.strftime("%A")
        date_str = current.strftime("%Y-%m-%d")
        
        # 2. Get Day Schedule
        day_config = active_schedule.get(day_name)

        # --- SMART REFERENCE CHECK ---
        # Agar "Tuesday": "Monday" likha hai, toh Monday ka data uthao
        if isinstance(day_config, str):
            ref_day = day_config
            day_config = active_schedule.get(ref_day)
        
        # Agar data list hai, tabhi process karo
        if isinstance(day_config, list):
            for s in day_config:
                try:
                    # Time Parsing
                    start_dt = datetime.strptime(f"{date_str} {s['start']}", "%Y-%m-%d %H:%M")
                    end_dt = datetime.strptime(f"{date_str} {s['end']}", "%Y-%m-%d %H:%M")
                    
                    # Handle Midnight Crossing (23:30 to 00:00)
                    if end_dt < start_dt:
                        end_dt += timedelta(days=1)

                    # 🛡️ DE-DUPLICATION LOGIC (As requested, untouched)
                    # Hum check karte hain ki kya ye time slot pehle hi add ho chuka hai?
                    time_key = start_dt.isoformat()
                    
                    if time_key in seen_times:
                        continue # Skip duplicate slot
                    
                    seen_times.add(time_key)

                    duration_mins = int((end_dt - start_dt).total_seconds() / 60)
                    category = s.get('category', 'General')
                    
                    item = {
                        "start": start_dt,
                        "end": end_dt,
                        "duration": duration_mins,
                        "category": category,
                        "label": s.get('label', category),
                        "energy_supply": s.get('energy_supply', 'Medium'),
                        "notes": s.get('notes', "")
                    }

                    # 🛑 SEPARATION LOGIC (New)
                    if category == "Constant":
                        constant_blocks.append(item)
                    else:
                        free_slots.append(item)

                except ValueError as e:
                    print(f"   ⚠️ Invalid time format in {day_name}: {e}")
                    
        current += timedelta(days=1)
    
    # Sort slots by time (Zaroori hai sequence ke liye)
    free_slots.sort(key=lambda x: x['start'])
    constant_blocks.sort(key=lambda x: x['start'])
    
    return free_slots, constant_blocks