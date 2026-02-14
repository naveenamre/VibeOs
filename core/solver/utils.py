from datetime import datetime, timedelta, timezone

def to_utc_iso(dt_local):
    """
    Convert Local Time (IST) to UTC ISO format for Database.
    Subtracts 5:30 hours.
    """
    dt_utc = dt_local - timedelta(hours=5, minutes=30)
    return dt_utc.replace(tzinfo=timezone.utc).strftime("%Y-%m-%dT%H:%M:%S.000Z")

def to_iso_now():
    """Current UTC time string"""
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%S.000Z")

def flatten_template_to_slots(week_template, start_date, days_ahead=14):
    """
    Converts 'Monday: 9am' -> '2026-02-16 09:00:00'
    Generates actual time slots for the next X days.
    """
    slots = []
    current = start_date
    
    for _ in range(days_ahead):
        day_name = current.strftime("%A")
        date_str = current.strftime("%Y-%m-%d")
        
        if day_name in week_template:
            for s in week_template[day_name]:
                try:
                    # Combine Date + Time
                    start_dt = datetime.strptime(f"{date_str} {s['start']}", "%Y-%m-%d %H:%M")
                    end_dt = start_dt + timedelta(minutes=s['duration'])
                    
                    slots.append({
                        "start": start_dt,
                        "end": end_dt,
                        "category": s['category'],
                        "duration": s['duration']
                    })
                except ValueError:
                    print(f"⚠️ Invalid time format in template for {day_name}")
                    
        current += timedelta(days=1)
    
    # Sort slots by time (Crucial for sequencing)
    slots.sort(key=lambda x: x['start'])
    return slots