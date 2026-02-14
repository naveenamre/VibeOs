from ortools.sat.python import cp_model
from datetime import timedelta

class VibeOptimizer:
    def __init__(self, tasks, slots):
        self.tasks = tasks
        self.slots = slots
        self.model = cp_model.CpModel()
        self.solver = cp_model.CpSolver()

    def solve(self):
        print(f"   🧠 OR-Tools Optimizing: {len(self.tasks)} Tasks into {len(self.slots)} Slots...")
        
        # Data Structures
        allocation = {}      # (t_idx, s_idx) -> BoolVar
        task_intervals = []  # List of IntervalVars for NoOverlap constraint
        
        # Energy Scoring Map
        energy_map = {"High": 3, "Medium": 2, "Low": 1, "Any": 2}

        # 1. CREATE VARIABLES
        for t_idx, task in enumerate(self.tasks):
            possible_slots = []
            
            # Task Data
            t_duration = task.get('duration', 60)
            t_type = task.get('task_type', 'Flexible')
            t_fixed_slot = task.get('fixed_slot')
            t_cat = task.get('category', 'General')
            
            for s_idx, slot in enumerate(self.slots):
                # Slot Data
                s_duration = slot.get('duration', 0)
                s_start = slot['start']
                s_cat = slot.get('category', 'General')
                s_start_str = s_start.strftime("%H:%M")

                # --- HARD FILTERS ---
                
                # Filter 1: Duration (Slot must be big enough)
                if s_duration < t_duration:
                    continue

                # Filter 2: Fixed Tasks
                if t_type == 'Fixed' and t_fixed_slot != s_start_str:
                    continue
                
                # Filter 3: Category Match (Flexible tasks stick to their zones)
                if t_type == 'Flexible' and s_cat != t_cat:
                    continue

                # ✅ CREATE DECISION VARIABLE
                # BoolVar: "Kya Task T, Slot S mein jayega?"
                is_present = self.model.NewBoolVar(f't{t_idx}_s{s_idx}')
                allocation[(t_idx, s_idx)] = is_present
                possible_slots.append(is_present)

                # 🌟 CRITICAL: INTERVAL VARIABLE FOR NO-OVERLAP
                # Hum model ko bata rahe hain: "Agar ye task select hua, toh ye time block reserve kar lo"
                
                # Convert Start Time to integer (Minutes timestamp)
                # Hum timestamp use kar rahe hain taaki absolute comparison ho sake
                start_min = int(s_start.timestamp() / 60) 
                
                # End Time Variable (Start + Duration)
                end_var = self.model.NewIntVar(start_min + t_duration, start_min + t_duration, f'end_{t_idx}_{s_idx}')
                
                # Create Optional Interval
                # Ye tabhi active hoga jab is_present == True hoga
                interval = self.model.NewOptionalIntervalVar(
                    start_min,          # Start Time (Integer)
                    t_duration,         # Size (Duration)
                    end_var,            # End Time
                    is_present,         # Active Flag
                    f'interval_t{t_idx}_s{s_idx}'
                )
                task_intervals.append(interval)

            # Constraint: Task can be in AT MOST 1 slot
            if possible_slots:
                self.model.Add(sum(possible_slots) <= 1)
        
        # 🛡️ THE ULTIMATE SHIELD: NO OVERLAP
        # Ye line ensure karti hai ki koi bhi do selected intervals overlap na karein.
        # Chaahe slot duplicate ho ya kuch bhi ho, agar time same hai toh clash nahi hoga.
        self.model.AddNoOverlap(task_intervals)

        # 2. OBJECTIVE FUNCTION (SCORING) 🎯
        objective_terms = []
        for (t_idx, s_idx), var in allocation.items():
            task = self.tasks[t_idx]
            slot = self.slots[s_idx]
            
            t_prio = task.get('priority', 1)
            t_energy = task.get('energy_req', 'Medium')
            s_energy = slot.get('energy_supply', 'Medium')

            # Base Score (Schedule karna hi apne aap mein jeet hai)
            score = 10000 
            
            # Priority Bonus (High Prio wins conflicts)
            # Increased weight to 5000 to ensure Priority > Slot Order
            score += t_prio * 5000 
            
            # Energy Match
            req = energy_map.get(t_energy, 2)
            sup = energy_map.get(s_energy, 2)
            if req == sup: score += 500
            elif req > sup: score -= 1000 # Penalty
            else: score += 100
            
            # Urgency: Prefer earlier slots (Tomorrow < Next Week)
            # s_idx jitna chhota, utna better.
            score -= s_idx * 10 

            objective_terms.append(var * score)

        self.model.Maximize(sum(objective_terms))

        # 3. SOLVE
        status = self.solver.Solve(self.model)
        schedule = []
        
        if status in [cp_model.OPTIMAL, cp_model.FEASIBLE]:
            print(f"   ✅ Solution Found! (Score: {self.solver.ObjectiveValue()})")
            for (t_idx, s_idx), var in allocation.items():
                if self.solver.Value(var) == 1:
                    slot = self.slots[s_idx]
                    task = self.tasks[t_idx]
                    
                    schedule.append({
                        "task_id": task.get('id'),
                        "name": task.get('name'),
                        "start": slot['start'],
                        "end": slot['start'] + timedelta(minutes=task.get('duration', 60)),
                        "slot_energy": slot.get('energy_supply', 'Medium')
                    })
        else:
            print("   ⚠️ No feasible solution found. Tasks will remain in Backlog.")
            
        return schedule