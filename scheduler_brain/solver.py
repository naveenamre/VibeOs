import json
import os
from datetime import datetime
from ortools.sat.python import cp_model

# Config Path (Docker ke andar ka path)
CONFIG_PATH = '/app/data/weekly_config.json'

def load_config():
    if os.path.exists(CONFIG_PATH):
        with open(CONFIG_PATH, 'r') as f:
            return json.load(f)
    return None

def get_minutes(time_str):
    """ '09:00' -> 540 minutes """
    h, m = map(int, time_str.split(':'))
    return h * 60 + m

def format_minutes(minutes):
    """ 540 -> '09:00' """
    h = (minutes // 60) % 24
    m = minutes % 60
    return f"{h:02d}:{m:02d}"

def solve_schedule(data):
    tasks = data.get('tasks', [])
    # Default Config
    start_hour = data.get('config', {}).get('start_hour', 7)
    end_hour = data.get('config', {}).get('end_hour', 23)
    
    # Load Weekly Rules
    weekly_rules = load_config()
    
    # Aaj kaunsa din hai? (Monday, Tuesday...)
    # (GUI se date aa sakti hai, abhi ke liye system date lete hain)
    today_name = datetime.now().strftime("%A") 
    print(f"📅 Planning for: {today_name}")

    day_rules = weekly_rules['days'].get(today_name, {})
    routines = weekly_rules.get('routines', [])

    model = cp_model.CpModel()
    
    # Day Horizon
    day_start = start_hour * 60
    day_end = end_hour * 60
    horizon = day_end - day_start

    task_starts = {}
    task_intervals = {}
    
    # --- 1. FIXED ROUTINES (Lunch/Sleep) ---
    # Inhe 'Dummy Tasks' bana ke block kar dete hain
    for r in routines:
        r_start = get_minutes(r['start']) - day_start
        r_end = get_minutes(r['end']) - day_start
        
        # Agar routine hamare working hours ke beech hai
        if 0 <= r_start < horizon:
            duration = r_end - r_start
            # Fixed Interval create karo
            model.NewIntervalVar(r_start, duration, r_end, f"routine_{r['name']}")

    # --- 2. TASK VARIABLES ---
    for task in tasks:
        t_id = task['id']
        duration = task['duration']
        
        start_var = model.NewIntVar(0, horizon, f'start_{t_id}')
        end_var = model.NewIntVar(0, horizon, f'end_{t_id}')
        interval_var = model.NewIntervalVar(start_var, duration, end_var, f'interval_{t_id}')
        
        task_starts[t_id] = start_var
        task_intervals[t_id] = interval_var

        # --- SMART ALLOCATION (The Magic v2.0 - With Backlog Logic) ---
        task_cat = task.get('category', 'Default')
        is_backlog = task.get('is_backlog', False) # Check backlog status
        
        # Is din ke slots check karo
        if 'slots' in day_rules:
            valid_slots = []
            for slot in day_rules['slots']:
                slot_type = slot['category'].lower()
                target_type = task_cat.lower()
                
                # Rule 1: Category Match (Study == Study)
                match = (slot_type == target_type)
                
                # Rule 2: Backlog Exception (Agar backlog hai, toh 'chill' slot chura lo)
                if is_backlog and slot_type == 'chill':
                    match = True
                    print(f"⚠️ Backlog detected for {task['name']}. Allowing Chill slot.")

                if match:
                    s_start = get_minutes(slot['start']) - day_start
                    s_end = get_minutes(slot['end']) - day_start
                    if s_start >= 0:
                        valid_slots.append((s_start, s_end))
            
            # Agar matching slots mile, toh task ko wahi force karo (Soft Constraint)
            if valid_slots:
                # Bools banayenge: "Is task in Slot A?" OR "Is task in Slot B?"
                slot_bools = []
                for s_start, s_end in valid_slots:
                    b = model.NewBoolVar(f'{t_id}_in_slot_{s_start}')
                    # Start >= SlotStart AND End <= SlotEnd
                    model.Add(start_var >= s_start).OnlyEnforceIf(b)
                    model.Add(end_var <= s_end).OnlyEnforceIf(b)
                    slot_bools.append(b)
                
                # Kam se kam ek slot mein hona chahiye (Strong Preference)
                if slot_bools:
                    model.Add(sum(slot_bools) >= 1)

    # Constraint: No Overlap
    # Routines ko 'Blocked Time' maante hain.
    
    # Conflict check with Routines (Manual)
    for r in routines:
        r_start = get_minutes(r['start']) - day_start
        r_end = get_minutes(r['end']) - day_start
        if 0 <= r_start < horizon:
            for t_id in task_starts:
                # Task end <= Routine start  OR  Task start >= Routine end
                t_start = task_starts[t_id]
                t_end = t_start + tasks[next(i for i, x in enumerate(tasks) if x['id'] == t_id)]['duration']
                
                left = model.NewBoolVar(f'{t_id}_left_{r["name"]}')
                right = model.NewBoolVar(f'{t_id}_right_{r["name"]}')
                
                model.Add(t_end <= r_start).OnlyEnforceIf(left)
                model.Add(t_start >= r_end).OnlyEnforceIf(right)
                
                model.AddBoolOr([left, right])

    model.AddNoOverlap(task_intervals.values())

    # --- OBJECTIVE ---
    # High priority first
    objective_terms = []
    for task in tasks:
        weight = 10 - task.get('priority', 1)
        objective_terms.append(task_starts[task['id']] * weight)
    
    model.Minimize(sum(objective_terms))

    # --- SOLVE ---
    solver = cp_model.CpSolver()
    status = solver.Solve(model)

    results = []
    if status in [cp_model.OPTIMAL, cp_model.FEASIBLE]:
        for task in tasks:
            start_min = solver.Value(task_starts[task['id']])
            actual_start_time = day_start + start_min
            
            results.append({
                "id": task['id'],
                "name": task['name'],
                "start_time": format_minutes(actual_start_time),
                "duration": task['duration'],
                "category": task.get('category', 'General')
            })
            
    return {"schedule": results, "status": "Optimized", "day_mode": day_rules.get('focus', 'General')}