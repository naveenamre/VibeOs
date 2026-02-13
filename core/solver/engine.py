# VibeOS_2026/core/solver/engine.py
import sys
import json
from ortools.sat.python import cp_model
# Note: Hum relative import use nahi kar rahe taaki direct run kar sakein
try:
    from masks import get_weekly_template
except ImportError:
    from core.solver.masks import get_weekly_template

def solve_schedule(tasks, day_name="Monday"):
    # 1. Initialize Model
    model = cp_model.CpModel()
    horizon = 24 * 60  # 1440 minutes in a day
    
    # 2. Get The Rules (Template)
    template_blocks = get_weekly_template(day_name)
    
    # 3. Create Variables
    task_vars = {}
    intervals = []
    
    # Helper: Convert Hour to Minute
    def h_to_m(h): return h * 60

    # --- LOGIC START ---
    for task in tasks:
        t_id = task['id']
        duration = task['duration']
        category = task.get('category', 'Any')
        
        # Variable: Start & End Time
        start_var = model.NewIntVar(0, horizon, f'start_{t_id}')
        end_var = model.NewIntVar(0, horizon, f'end_{t_id}')
        interval_var = model.NewIntervalVar(start_var, duration, end_var, f'interval_{t_id}')
        
        task_vars[t_id] = {"start": start_var, "end": end_var}
        intervals.append(interval_var)
        
        # CONSTRAINT 1: Template Matching
        valid_slots = []
        
        for block in template_blocks:
            # Match Logic: Agar Block type aur Task category same hai (ya Any hai)
            if block['type'] == category or block['type'] == "Any" or category == "Any":
                
                b_start = h_to_m(block['start'])
                b_end = h_to_m(block['end'])
                
                # Check if block is big enough
                if (b_end - b_start) >= duration:
                    is_in_block = model.NewBoolVar(f'{t_id}_in_{block["start"]}')
                    
                    # Logic: Task Start >= Block Start  AND  Task End <= Block End
                    model.Add(start_var >= b_start).OnlyEnforceIf(is_in_block)
                    model.Add(end_var <= b_end).OnlyEnforceIf(is_in_block)
                    
                    valid_slots.append(is_in_block)
        
        if valid_slots:
            # Task must fit in AT LEAST one valid block
            model.Add(sum(valid_slots) >= 1)
        else:
            print(f"⚠️ Warning: No space for task {task['name']} ({category})")

    # CONSTRAINT 2: No Overlap
    model.AddNoOverlap(intervals)
    
    # OBJECTIVE: Minimize gaps (Pack tightly)
    makespan = model.NewIntVar(0, horizon, 'makespan')
    model.AddMaxEquality(makespan, [v["end"] for v in task_vars.values()])
    model.Minimize(makespan)
    
    # --- SOLVE ---
    solver = cp_model.CpSolver()
    status = solver.Solve(model)
    
    schedule = []
    if status in [cp_model.OPTIMAL, cp_model.FEASIBLE]:
        for task in tasks:
            t_id = task['id']
            if t_id in task_vars:
                start_val = solver.Value(task_vars[t_id]["start"])
                
                # Convert back to HH:MM
                h = start_val // 60
                m = start_val % 60
                time_str = f"{h:02d}:{m:02d}"
                
                schedule.append({
                    "id": t_id,
                    "name": task['name'],
                    "start": time_str,
                    "duration": task['duration'],
                    "category": task.get('category', 'Any')
                })
        schedule.sort(key=lambda x: x['start'])
        return schedule
    else:
        return {"error": "No Solution Found"}

# --- TEST RUNNER ---
if __name__ == "__main__":
    # Dummy Input
    test_tasks = [
        {"id": 1, "name": "Physics Derivations", "duration": 60, "category": "Study"},
        {"id": 2, "name": "VibeOS Coding", "duration": 90, "category": "Code"},
        {"id": 3, "name": "Anime Episode", "duration": 30, "category": "Chill"},
        {"id": 4, "name": "Maths Problems", "duration": 60, "category": "Study"}
    ]
    
    print("🧠 Running VibeOS Engine on Monday Template...")
    result = solve_schedule(test_tasks, day_name="Monday")
    print(json.dumps(result, indent=4))