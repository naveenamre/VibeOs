from flask import Flask, request, jsonify
from solver import solve_schedule
from db_handler import init_db, add_task, get_tasks_for_date
from planner import distribute_tasks
from datetime import datetime

app = Flask(__name__)

# Server start hone par Table check karo
with app.app_context():
    try:
        init_db()
        print("✅ Database Connected & Initialized")
    except Exception as e:
        print(f"❌ DB Error: {e}")

@app.route('/health', methods=['GET'])
def health():
    return jsonify({"status": "VibeOS Architect is Live"})

# 1. ADD TASKS TO WAREHOUSE (From GUI/Gemini)
@app.route('/add_tasks', methods=['POST'])
def api_add_tasks():
    data = request.json
    tasks = data.get('tasks', [])
    ids = []
    for t in tasks:
        new_id = add_task(t)
        ids.append(new_id)
    
    # Auto-Plan after adding
    distribute_tasks()
    
    return jsonify({"message": f"{len(ids)} tasks stored & planned", "ids": ids})

# 2. GET SCHEDULE FOR A SPECIFIC DATE
@app.route('/get_schedule', methods=['GET'])
def api_get_schedule():
    # Date query param (YYYY-MM-DD), default is Today
    date_str = request.args.get('date', datetime.now().strftime('%Y-%m-%d'))
    
    # 1. DB se us date ke tasks nikalo
    db_tasks = get_tasks_for_date(date_str)
    
    if not db_tasks:
        return jsonify({"schedule": [], "message": "No tasks scheduled for this date"})
    
    # 2. Format them for Solver (Solver needs specific JSON format)
    formatted_tasks = []
    for t in db_tasks:
        formatted_tasks.append({
            "id": t['id'],
            "name": t['title'],
            "duration": t['duration_minutes'],
            "category": t['category'],
            "priority": t['priority'],
            "is_backlog": t['is_backlog']
        })
    
    # 3. Run Solver (Smart Allocation for THAT specific day)
    # Solver ko sirf us din ke tasks aur config chahiye
    solver_input = {
        "tasks": formatted_tasks,
        "config": {"start_hour": 7, "end_hour": 23} # Ye dynamic bhi kar sakte hain
    }
    
    schedule_result = solve_schedule(solver_input)
    return jsonify(schedule_result)

# 3. FORCE RE-PLAN (Button Click)
@app.route('/replan', methods=['POST'])
def api_replan():
    result = distribute_tasks()
    return jsonify(result)

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)