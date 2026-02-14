import os
import json

# --- PATH SETUP ---
BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
DATA_DIR = os.path.join(BASE_DIR, "data")
TEMPLATE_FILE = os.path.join(DATA_DIR, "week_template.json")

def load_week_template():
    """
    Reads the Master Architecture (Fixed Slots) from JSON.
    """
    if not os.path.exists(TEMPLATE_FILE):
        print(f"⚠️ Warning: Week Template not found at {TEMPLATE_FILE}")
        return {}
    
    try:
        with open(TEMPLATE_FILE, "r") as f:
            return json.load(f)
    except Exception as e:
        print(f"❌ Error loading Week Template: {e}")
        return {}

def get_slot_rules(category):
    """
    Future: Return specific rules for a category (e.g., 'Code' needs high energy).
    """
    # Abhi ke liye placeholder
    return {"energy_required": "High" if category == "Code" else "Medium"}