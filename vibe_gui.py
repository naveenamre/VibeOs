import customtkinter as ctk
import requests
import json
import os
import time  # <--- Added for Date Logic
from tkinter import messagebox, filedialog
import threading

# --- CONFIGURATION ---
API_URL = "http://localhost:5000/optimize"
DATA_FILE = "data/vibe_data.json"       # Final Clean Data
SOURCE_FILE = "data/vibe_source.json"   # Super Productivity Export

# Theme Colors
CATEGORY_COLORS = {
    "Study": "#E53935", "Code": "#1E88E5", "Farm": "#43A047", 
    "Break": "#FB8C00", "Default": "#757575"
}

ctk.set_appearance_mode("Dark")
ctk.set_default_color_theme("blue")

class VibeSchedulerApp(ctk.CTk):
    def __init__(self):
        super().__init__()
        self.title("VibeOS Command Center (Final)")
        self.geometry("1100x700")
        self.grid_columnconfigure(0, weight=3)
        self.grid_columnconfigure(1, weight=1)
        self.grid_rowconfigure(0, weight=1)

        # --- LEFT PANEL ---
        self.left_frame = ctk.CTkFrame(self, fg_color="transparent")
        self.left_frame.grid(row=0, column=0, sticky="nsew", padx=20, pady=20)

        self.header = ctk.CTkLabel(self.left_frame, text="📅 Today's Master Plan", font=("Roboto", 24, "bold"))
        self.header.grid(row=0, column=0, sticky="w", pady=(0, 20))

        self.timeline_frame = ctk.CTkScrollableFrame(self.left_frame, label_text="Optimized Timeline")
        self.timeline_frame.grid(row=1, column=0, sticky="nsew")
        self.left_frame.grid_rowconfigure(1, weight=1)

        # Buttons
        self.btn_frame = ctk.CTkFrame(self.left_frame, fg_color="transparent")
        self.btn_frame.grid(row=2, column=0, sticky="ew", pady=20)
        
        self.optimize_btn = ctk.CTkButton(
            self.btn_frame, text="⚡ OPTIMIZE SCHEDULE", font=("Roboto", 16, "bold"), height=50,
            fg_color="#00E676", text_color="black", hover_color="#00C853",
            command=self.start_optimization
        )
        self.optimize_btn.pack(fill="x")

        # --- RIGHT PANEL ---
        self.right_frame = ctk.CTkFrame(self, fg_color="#2B2B2B")
        self.right_frame.grid(row=0, column=1, sticky="nsew", padx=(0, 20), pady=20)

        self.json_label = ctk.CTkLabel(self.right_frame, text="🛠️ Task Control", font=("Consolas", 14, "bold"))
        self.json_label.pack(pady=10)

        # Import Button
        self.import_btn = ctk.CTkButton(
            self.right_frame, text="📥 IMPORT FROM SUPER PROD", 
            fg_color="#FF9800", hover_color="#F57C00",
            command=self.import_from_super_prod
        )
        self.import_btn.pack(fill="x", padx=10, pady=(0, 10))

        self.json_editor = ctk.CTkTextbox(self.right_frame, font=("Consolas", 13), undo=True)
        self.json_editor.pack(fill="both", expand=True, padx=10, pady=(0, 10))

        self.load_data_from_file()

    def load_data_from_file(self):
        if os.path.exists(DATA_FILE):
            try:
                with open(DATA_FILE, 'r') as f:
                    self.json_editor.insert("0.0", f.read())
            except: self.load_template()
        else: self.load_template()

    def load_template(self):
        default = {"config": {"start_hour": 9, "end_hour": 18}, "tasks": []}
        self.json_editor.insert("0.0", json.dumps(default, indent=4))

    def import_from_super_prod(self):
        # 1. Ask user for file (Backup agar auto-sync nahi hai)
        file_path = filedialog.askopenfilename(
            initialdir=os.getcwd() + "/data",
            title="Select Super Productivity JSON",
            filetypes=[("JSON Files", "*.json")]
        )
        
        if not file_path: return

        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                sp_data = json.load(f)
            
            # 2. Parse Super Productivity Logic
            new_tasks = []
            raw_tasks = []
            
            # Structure check logic
            if isinstance(sp_data, list): raw_tasks = sp_data
            elif 'tasks' in sp_data:
                if isinstance(sp_data['tasks'], dict):
                    raw_tasks = sp_data['tasks'].values()
                else:
                    raw_tasks = sp_data['tasks']
            
            # --- DATE LOGIC SETUP ---
            current_time_ms = int(time.time() * 1000)
            TWO_DAYS_MS = 2 * 24 * 60 * 60 * 1000

            # 3. Conversion Loop
            task_id = 1
            backlog_count = 0

            for t in raw_tasks:
                # Sirf wo tasks lo jo DONE nahi hain
                if t.get('isDone', False) == False:
                    # Time Estimate (ms -> min)
                    time_ms = t.get('timeEstimate', 0)
                    duration_min = int(time_ms / 60000)
                    if duration_min == 0: duration_min = 30 

                    # Category Guessing
                    title = t.get('title', 'Unknown Task')
                    cat = "Default"
                    if "Study" in title or "Unit" in title: cat = "Study"
                    elif "Code" in title or "VibeOS" in title: cat = "Code"
                    
                    # --- BACKLOG LOGIC ---
                    created_at = t.get('created', current_time_ms)
                    age_ms = current_time_ms - created_at
                    
                    priority = 3
                    is_backlog = False

                    if age_ms > TWO_DAYS_MS:
                        priority = 5      # Urgent ban gaya
                        title = f"🔥 {title}"  # Visual Mark
                        is_backlog = True
                        backlog_count += 1
                    
                    new_tasks.append({
                        "id": task_id,
                        "name": title,
                        "duration": duration_min,
                        "priority": priority,
                        "category": cat,
                        "is_backlog": is_backlog # Brain ko batane ke liye
                    })
                    task_id += 1
            
            # 4. Update Editor
            current_text = self.json_editor.get("0.0", "end")
            # Safe parsing
            try:
                current_json = json.loads(current_text)
            except:
                current_json = {"config": {"start_hour": 9, "end_hour": 18}, "tasks": []}

            current_json['tasks'] = new_tasks
            
            self.json_editor.delete("0.0", "end")
            self.json_editor.insert("0.0", json.dumps(current_json, indent=4))
            
            msg = f"Imported {len(new_tasks)} tasks!"
            if backlog_count > 0:
                msg += f"\n⚠️ {backlog_count} Backlog Tasks Detected (Marked 🔥)"
            
            messagebox.showinfo("Import Success", msg)

        except Exception as e:
            messagebox.showerror("Import Error", f"Failed to parse: {str(e)}")

    def start_optimization(self):
        threading.Thread(target=self.run_optimization, daemon=True).start()

    def run_optimization(self):
        try:
            raw_text = self.json_editor.get("0.0", "end")
            payload = json.loads(raw_text)
            
            # Save Local
            with open(DATA_FILE, 'w') as f: f.write(raw_text)

            self.optimize_btn.configure(text="⏳ Thinking...", state="disabled")
            response = requests.post(API_URL, json=payload)
            
            if response.status_code == 200:
                data = response.json()
                self.after(0, self.display_schedule, data.get("schedule", []))
            else:
                self.after(0, lambda: messagebox.showerror("Error", response.text))
        except Exception as e:
            self.after(0, lambda: messagebox.showerror("Error", str(e)))
        finally:
            self.after(0, lambda: self.optimize_btn.configure(text="⚡ OPTIMIZE SCHEDULE", state="normal"))

    def display_schedule(self, schedule_list):
        for widget in self.timeline_frame.winfo_children(): widget.destroy()
        if not schedule_list: 
            ctk.CTkLabel(self.timeline_frame, text="No Schedule Found!").pack(pady=20)
            return
        
        schedule_list.sort(key=lambda x: x['start_time'])
        for task in schedule_list:
            cat = task.get('category', 'Default')
            if cat == 'Default':
                if 'study' in task['name'].lower(): cat = 'Study'
                elif 'code' in task['name'].lower(): cat = 'Code'
            
            card = ctk.CTkFrame(self.timeline_frame, fg_color="#424242", corner_radius=10)
            card.pack(fill="x", pady=5, padx=5)
            
            time_box = ctk.CTkFrame(card, fg_color=CATEGORY_COLORS.get(cat, "#757575"), width=80)
            time_box.pack(side="left", fill="y", padx=(0, 10))
            ctk.CTkLabel(time_box, text=task['start_time'], font=("Roboto", 16, "bold"), text_color="white").place(relx=0.5, rely=0.5, anchor="center")
            
            info_box = ctk.CTkFrame(card, fg_color="transparent")
            info_box.pack(side="left", fill="both", expand=True)
            ctk.CTkLabel(info_box, text=task['name'], font=("Roboto", 16, "bold"), anchor="w").pack(fill="x")
            ctk.CTkLabel(info_box, text=f"{task['duration']} min | {cat}", font=("Roboto", 12), text_color="gray", anchor="w").pack(fill="x")

if __name__ == "__main__":
    app = VibeSchedulerApp()
    app.mainloop()