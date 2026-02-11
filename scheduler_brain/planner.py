import json
import os
from datetime import datetime, timedelta
from db_handler import get_pending_tasks, update_task_schedule

CONFIG_PATH = '/app/data/weekly_config.json'

def load_config():
    if os.path.exists(CONFIG_PATH):
        with open(CONFIG_PATH, 'r') as f:
            return json.load(f)
    return None

def get_minutes(time_str):
    h, m = map(int, time_str.split(':'))
    return h * 60 + m

def get_daily_capacity(day_name, config):
    """Calculate total available minutes for a specific day based on slots"""
    day_rules = config['days'].get(day_name, {})
    total_minutes = 0
    if 'slots' in day_rules:
        for slot in day_rules['slots']:
            start = get_minutes(slot['start'])
            end = get_minutes(slot['end'])
            total_minutes += (end - start)
    return total_minutes

def distribute_tasks():
    """Reads pending tasks from DB and assigns dates based on capacity"""
    pending_tasks = get_pending_tasks()
    config = load_config()
    
    if not pending_tasks or not config:
        return {"status": "No tasks or config found"}

    # Start planning from Tomorrow (or Today if early)
    # Abhi ke liye Maante hain planning "Tomorrow" se start hogi
    current_date = datetime.now().date()
    
    # Bucket Logic
    day_capacity_used = 0
    
    for task in pending_tasks:
        assigned = False
        attempts = 0
        
        # Try to fit task in current_date or next days
        while not assigned and attempts < 30: # Limit to 30 days lookahead
            day_name = current_date.strftime("%A")
            total_capacity = get_daily_capacity(day_name, config)
            
            # Agar task fit hota hai
            if (day_capacity_used + task['duration_minutes']) <= total_capacity:
                update_task_schedule(task['id'], current_date)
                day_capacity_used += task['duration_minutes']
                assigned = True
            else:
                # Bucket Full -> Move to Next Day
                current_date += timedelta(days=1)
                day_capacity_used = 0 # New day, fresh capacity
                attempts += 1
                
    return {"status": "Planning Complete", "tasks_processed": len(pending_tasks)}