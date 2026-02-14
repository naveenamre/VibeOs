import os
import json
import glob

# --- PATH SETUP ---
BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
DATA_DIR = os.path.join(BASE_DIR, "data")
INPUTS_DIR = os.path.join(DATA_DIR, "inputs")

def load_all_inputs():
    """
    Scans data/inputs/ folder and merges all JSON files (Syllabus + Backlog).
    """
    master_list = []
    
    if not os.path.exists(INPUTS_DIR):
        os.makedirs(INPUTS_DIR)
        print(f"📂 Created missing folder: {INPUTS_DIR}")
        return []

    # Get all .json files
    json_files = glob.glob(os.path.join(INPUTS_DIR, "*.json"))
    
    if not json_files:
        print("⚠️ No input files found in data/inputs/")
        return []

    print(f"📂 Loading Data from {len(json_files)} files...")

    for file_path in json_files:
        try:
            with open(file_path, "r") as f:
                data = json.load(f)
                
                # Normalize Data (List vs Dict)
                if isinstance(data, list):
                    master_list.extend(data)
                elif isinstance(data, dict):
                    master_list.append(data)
                    
                print(f"   📄 Loaded: {os.path.basename(file_path)}")
        except Exception as e:
            print(f"   ❌ Error loading {os.path.basename(file_path)}: {e}")

    return master_list