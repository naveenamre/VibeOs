import sys
import os
import uvicorn
import logging
import threading
import time
from fastapi import FastAPI, BackgroundTasks, HTTPException, Header
from datetime import datetime
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler

# --- PATH SETUP ---
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
INPUTS_DIR = os.path.join(BASE_DIR, "data", "inputs")
sys.path.append(BASE_DIR)

# --- IMPORTS FROM BRAIN 🧠 ---
from core.loader.ingest import ingest_data
from core.solver.engine import run_planner
from core.solver.ghost import run_ghost_protocol

# --- LOGGING SETUP ---
logging.basicConfig(level=logging.INFO, format="%(asctime)s - [API] - %(message)s")
logger = logging.getLogger(__name__)

app = FastAPI(title="VibeOS 3.0 Server", version="Watcher.Edition")

# --- CORE LOGIC (The Intelligent Pipeline) ---
def run_full_pipeline(source: str = "Manual"):
    """
    The Intelligent Pipeline:
    0. Ghost Protocol: Sync UI changes (Delete/Moves) back to DB.
    1. Ingest Data: Load new requirements from JSON.
    2. Run Planner: Optimize and Sync to Fluid Calendar.
    """
    logger.info(f"🚀 Pipeline Triggered by: {source}")
    try:
        # Step 0: Ghost (Sync Reality) 👻
        logger.info("👻 Step 0: Running Ghost Protocol (Reality Check)...")
        run_ghost_protocol()

        # Step 1: Ingest (Load Inputs) 📥
        logger.info("📥 Step 1: Ingesting Data...")
        ingest_data()
        
        # Step 2: Plan & Sync (Execute) 🧠
        logger.info("🧠 Step 2: Running Planner & Sync Engine...")
        run_planner()
        
        logger.info("✅ Pipeline Completed Successfully.")
    except Exception as e:
        logger.error(f"❌ Pipeline Failed: {e}")

# --- 👀 THE WATCHER CLASS (Chowkidaar) ---
class VibeFileHandler(FileSystemEventHandler):
    def on_created(self, event):
        # Sirf JSON files pe react karo
        if not event.is_directory and event.src_path.endswith(".json"):
            logger.info(f"👀 New File Detected: {event.src_path}")
            
            # Thoda sa delay taaki file poori save ho jaye
            time.sleep(1)
            
            # Pipeline Trigger karo
            run_full_pipeline(source="Auto-Watcher")

def start_watcher():
    """Starts monitoring the inputs directory in background"""
    if not os.path.exists(INPUTS_DIR):
        os.makedirs(INPUTS_DIR)
        
    event_handler = VibeFileHandler()
    observer = Observer()
    observer.schedule(event_handler, INPUTS_DIR, recursive=False)
    observer.start()
    logger.info(f"👀 Watcher Active on: {INPUTS_DIR}")
    
    # Keep thread alive
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        observer.stop()
    observer.join()

# --- SERVER LIFECYCLE ---
@app.on_event("startup")
async def startup_event():
    # Server start hote hi Watcher thread bhi start kar do
    logger.info("🟢 Starting Background Watcher Thread...")
    threading.Thread(target=start_watcher, daemon=True).start()

# --- ROUTES ---

@app.get("/")
def home():
    return {
        "status": "Online",
        "system": "VibeOS 3.0 (Watcher Active 👀)",
        "location": "India (IST)",
        "timestamp": datetime.now()
    }

@app.post("/trigger")
def trigger_pipeline(
    background_tasks: BackgroundTasks, 
    x_source: str = Header(default="n8n", alias="X-Source")
):
    """
    Manual Trigger (for n8n or Testing)
    """
    background_tasks.add_task(run_full_pipeline, source=x_source)
    return {
        "status": "Accepted", 
        "message": "VibeOS Pipeline started. Ghost -> Ingest -> Plan."
    }

@app.get("/health")
def health_check():
    return {"status": "healthy"}

if __name__ == "__main__":
    print("🌍 Starting VibeOS Server on Port 8000...")
    uvicorn.run(app, host="0.0.0.0", port=8000)