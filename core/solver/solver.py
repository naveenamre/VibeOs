from ortools.sat.python import cp_model
from datetime import datetime, timedelta
import collections

class VibeOptimizer:
    def __init__(self, tasks, slots):
        """
        tasks: List [{'name': '...', 'duration': 60, 'category': 'Code', 'group_id': 1, 'order': 1}]
        slots: List [{'start': datetime_obj, 'end': datetime_obj, 'category': 'Code'}]
        """
        self.tasks = tasks
        self.slots = slots
        self.model = cp_model.CpModel()
        self.solver = cp_model.CpSolver()
        self.solution = []

    def solve(self):
        print(f"🧠 OR-Tools Optimizing: {len(self.tasks)} Tasks into {len(self.slots)} Slots...")

        # --- VARIABLES ---
        # allocation[(task_idx, slot_idx)] = BoolVar (Is task T in slot S?)
        allocation = {}
        
        # Helper to track which slot a task is assigned to (for ordering constraints)
        task_slot_indices = {} 

        for t_idx, task in enumerate(self.tasks):
            # Optimization: Sirf matching category aur fitting duration wale slots hi consider karo
            # Isse memory bachegi aur speed badhegi
            valid_slots = []
            
            for s_idx, slot in enumerate(self.slots):
                # 1. Category Match
                if slot['category'] != task['category']:
                    continue
                
                # 2. Duration Match (Slot bada ya barabar hona chahiye)
                slot_duration_mins = (slot['end'] - slot['start']).total_seconds() / 60
                if slot_duration_mins < task['duration']:
                    continue
                
                # Agar fit hai, toh variable banao
                is_assigned = self.model.NewBoolVar(f't{t_idx}_s{s_idx}')
                allocation[(t_idx, s_idx)] = is_assigned
                valid_slots.append(is_assigned)
            
            # Constraint 1: Har Task ko MAXIMUM 1 Slot milna chahiye
            # (Agar slots full hain, toh shayad task assign na ho paye - Backlog)
            if valid_slots:
                self.model.Add(sum(valid_slots) <= 1)
                # Ideally we want it to be == 1, but <= 1 prevents crash if slots are full
                # We add a maximization objective later to force assignment.
            else:
                print(f"   ⚠️ Impossible to fit: {task['name']} (No matching slots found)")

        # Constraint 2: Slot Capacity (No Overlap)
        # Ek slot mein ek hi task (Simple logic for V1)
        # Future mein hum 'packing' kar sakte hain, abhi 1 Slot = 1 Task rakhte hain safety ke liye.
        for s_idx in range(len(self.slots)):
            tasks_in_slot = []
            for t_idx in range(len(self.tasks)):
                if (t_idx, s_idx) in allocation:
                    tasks_in_slot.append(allocation[(t_idx, s_idx)])
            
            if tasks_in_slot:
                self.model.Add(sum(tasks_in_slot) <= 1)

        # Constraint 3: Sequence Handling (Dependency)
        # Group ID same hai toh Order 1 pehle aana chahiye Order 2 se.
        # Group tasks together
        tasks_by_group = collections.defaultdict(list)
        for t_idx, task in enumerate(self.tasks):
            tasks_by_group[task['group_id']].append((t_idx, task['order']))

        for group_id, task_list in tasks_by_group.items():
            # Sort by order (1, 2, 3...)
            task_list.sort(key=lambda x: x[1])
            
            for i in range(len(task_list) - 1):
                t1_idx = task_list[i][0]
                t2_idx = task_list[i+1][0]
                
                # Logic: Agar dono assigned hain, toh Slot1_Index < Slot2_Index hona chahiye
                # (Assuming slots are sorted by time)
                
                # Hum model mein imply karte hain:
                # If T1 in S_a AND T2 in S_b => a < b
                
                for (t1, s1), var1 in allocation.items():
                    if t1 != t1_idx: continue
                    
                    for (t2, s2), var2 in allocation.items():
                        if t2 != t2_idx: continue
                        
                        # Constraint: s1 index must be less than s2 index
                        if s1 >= s2:
                            # Ye combination illegal hai
                            # Model ko bolo: var1 aur var2 dono 1 nahi ho sakte
                            self.model.AddBoolOr([var1.Not(), var2.Not()])

        # --- OBJECTIVE ---
        # 1. Maximize number of assigned tasks
        # 2. Prefer earlier slots (Minimize slot index)
        objective_terms = []
        for (t_idx, s_idx), var in allocation.items():
            # Big reward for assigning task (1000 points)
            # Small penalty for later slots (minus s_idx) -> Encourages early completion
            weight = 1000 - s_idx 
            objective_terms.append(var * weight)
        
        self.model.Maximize(sum(objective_terms))

        # --- SOLVE ---
        status = self.solver.Solve(self.model)

        final_schedule = []
        if status == cp_model.OPTIMAL or status == cp_model.FEASIBLE:
            print("   ✅ Solution Found!")
            
            for (t_idx, s_idx), var in allocation.items():
                if self.solver.Value(var) == 1:
                    slot = self.slots[s_idx]
                    task = self.tasks[t_idx]
                    
                    # Create Scheduled Item
                    final_schedule.append({
                        "title": task['name'],
                        "start": slot['start'],
                        "end": slot['start'] + timedelta(minutes=task['duration'])
                    })
        else:
            print("   ❌ No Solution Found.")
        
        return final_schedule