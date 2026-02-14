-- 1. PROJECTS (Container)
CREATE TABLE IF NOT EXISTS projects (
    id TEXT PRIMARY KEY,
    name TEXT NOT NULL,
    category TEXT DEFAULT 'General',
    priority INTEGER DEFAULT 1,
    color TEXT DEFAULT '#FFFFFF',
    tags TEXT,
    reality_factor REAL DEFAULT 1.0, 
    created_at TEXT DEFAULT CURRENT_TIMESTAMP
);

-- 2. TASKS (The Intelligent Unit) 🧠
CREATE TABLE IF NOT EXISTS tasks (
    id TEXT PRIMARY KEY,
    project_id TEXT,
    name TEXT NOT NULL,
    
    -- STATE MANAGEMENT
    status TEXT DEFAULT 'PENDING',      -- PENDING, SCHEDULED, DONE, MISSED
    is_soft_deleted BOOLEAN DEFAULT 0,  -- 1 = User deleted from Calendar
    
    -- SYNC KEYS 🔑 (FIXED HERE)
    calendar_event_id TEXT,             -- Fluid Calendar ID (Matches engine.py)
    scheduled_start TEXT,               -- Calculated Start Time (Matches engine.py)
    external_id TEXT,                   -- Backup/Future Sync ID
    idempotency_key TEXT,               -- To prevent double processing
    last_synced_at TEXT,                
    
    -- CORE ATTRIBUTES
    category TEXT DEFAULT 'General',
    priority INTEGER DEFAULT 1,
    
    -- TIME & ENERGY
    duration INTEGER DEFAULT 60,
    actual_duration INTEGER,
    energy_req TEXT DEFAULT 'Medium',
    
    -- SOLVER CONSTRAINTS 🧩
    task_type TEXT DEFAULT 'Flexible',
    fixed_slot TEXT,
    dependency TEXT,
    deadline_offset INTEGER,
    
    -- METADATA
    notes TEXT,
    created_at TEXT DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY(project_id) REFERENCES projects(id)
);

-- 3. IDEMPOTENCY STORE (Security) 🛡️
CREATE TABLE IF NOT EXISTS processed_requests (
    request_id TEXT PRIMARY KEY,
    processed_at TEXT DEFAULT CURRENT_TIMESTAMP,
    status TEXT DEFAULT 'SUCCESS'
);

-- 4. HISTORY LOG (Analytics) 📉
CREATE TABLE IF NOT EXISTS history_log (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    task_id TEXT,
    action TEXT,
    planned_start TEXT,
    actual_start TEXT,
    time_diff_minutes INTEGER,
    timestamp TEXT DEFAULT CURRENT_TIMESTAMP
);

-- 5. SYSTEM CONFIG
CREATE TABLE IF NOT EXISTS system_config (
    key TEXT PRIMARY KEY,
    value TEXT
);

INSERT OR IGNORE INTO system_config (key, value) VALUES ('current_mode', 'Normal');
INSERT OR IGNORE INTO system_config (key, value) VALUES ('global_reality_factor', '1.0');