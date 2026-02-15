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
    🛡️ PRESERVED: De-duplication logic.
    🔥 NEW: 'Busy Mask' logic to prevent Free slots overlapping with Constant blocks.
    """
    free_slots = []
    constant_blocks = []
    
    # 1. Get Current Mode Logic
    mode_name = week_template.get("current_mode", "Normal")
    modes = week_template.get("modes", {})
    active_schedule = modes.get(mode_name, {})
    
    current = start_date

    print(f"   📅 Generating Slots for Mode: {mode_name}")

    for _ in range(days_ahead):
        day_name = current.strftime("%A")
        date_str = current.strftime("%Y-%m-%d")
        
        # 2. Get Day Schedule
        day_config = active_schedule.get(day_name)

        # Reference Check ("Tuesday": "Monday")
        if isinstance(day_config, str):
            ref_day = day_config
            day_config = active_schedule.get(ref_day)
        
        if not day_config or not isinstance(day_config, list):
            current += timedelta(days=1)
            continue

        # --- STEP A: Parse All Raw Blocks ---
        daily_items = []
        for s in day_config:
            try:
                # Time Parsing
                start_dt = datetime.strptime(f"{date_str} {s['start']}", "%Y-%m-%d %H:%M")
                end_dt = datetime.strptime(f"{date_str} {s['end']}", "%Y-%m-%d %H:%M")
                
                # Handle Midnight Crossing
                if end_dt < start_dt:
                    end_dt += timedelta(days=1)

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
                daily_items.append(item)

            except ValueError as e:
                print(f"   ⚠️ Invalid time format in {day_name}: {e}")

        # --- STEP B: Separate Constant & Build Mask ---
        # Constant blocks are King. They reserve the time first.
        occupied_ranges = []
        seen_times = set() # Local dedupe per day for exact duplicates

        for item in daily_items:
            time_key = item['start'].isoformat()
            
            if item["category"] == "Constant":
                # Add to constant list
                if time_key not in seen_times:
                    constant_blocks.append(item)
                    occupied_ranges.append((item["start"], item["end"]))
                    seen_times.add(time_key)

        # --- STEP C: Filter Free Slots ---
        # Only allow Free slots that DO NOT overlap with Constant blocks
        for item in daily_items:
            if item["category"] != "Constant":
                time_key = item['start'].isoformat()
                if time_key in seen_times: continue # Skip if processed

                is_overlapping = False
                
                # Check overlap against ALL constant blocks
                # Overlap Formula: (StartA < EndB) and (EndA > StartB)
                for occ_start, occ_end in occupied_ranges:
                    if item["start"] < occ_end and item["end"] > occ_start:
                        is_overlapping = True
                        # print(f"   🛡️ Conflict Avoided: '{item['label']}' overlapped with a Constant block.")
                        break
                
                if not is_overlapping:
                    free_slots.append(item)
                    seen_times.add(time_key)

        current += timedelta(days=1)
    
    # Sort slots by time
    free_slots.sort(key=lambda x: x['start'])
    constant_blocks.sort(key=lambda x: x['start'])
    
    return free_slots, constant_blocks