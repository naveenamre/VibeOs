import os
import json

# --- PATH SETUP ---
BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
# CORRECT PATH: data/config/week_template.json
TEMPLATE_FILE = os.path.join(BASE_DIR, "data", "config", "week_template.json")

def load_week_template():
    """
    Reads the Master Architecture from JSON.
    """
    if not os.path.exists(TEMPLATE_FILE):
        print(f"⚠️  Warning: Week Template not found at {TEMPLATE_FILE}")
        return {}
    
    try:
        with open(TEMPLATE_FILE, "r") as f:
            data = json.load(f)
            # Debug Print to confirm loading
            # print(f"   📄 Loaded Template. Modes found: {list(data.get('modes', {}).keys())}")
            return data
    except Exception as e:
        print(f"❌ Error loading Week Template: {e}")
        return {}