PRAGMA foreign_keys = ON;

CREATE TABLE IF NOT EXISTS reports (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    report_code TEXT UNIQUE,
    title TEXT NOT NULL,
    observation_type TEXT NOT NULL,
    industry_type TEXT,
    description TEXT NOT NULL,
    district TEXT NOT NULL,
    locality TEXT NOT NULL,
    address_landmark TEXT NOT NULL,
    latitude REAL,
    longitude REAL,
    industrial_unit_name TEXT,
    assigned_jurisdiction TEXT NOT NULL,
    incident_date TEXT NOT NULL,
    incident_time TEXT NOT NULL,
    image_filename TEXT NOT NULL,
    status TEXT NOT NULL DEFAULT 'Reported',
    authority_remark TEXT,
    action_taken TEXT,
    submitter_key TEXT NOT NULL DEFAULT 'demo-citizen',
    created_at TEXT NOT NULL,
    updated_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS status_history (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    report_id INTEGER NOT NULL,
    status TEXT NOT NULL,
    public_remark TEXT,
    action_taken TEXT,
    actor TEXT NOT NULL,
    created_at TEXT NOT NULL,
    FOREIGN KEY (report_id) REFERENCES reports(id) ON DELETE CASCADE
);

CREATE INDEX IF NOT EXISTS idx_reports_created_at ON reports(created_at DESC);
CREATE INDEX IF NOT EXISTS idx_reports_status ON reports(status);
CREATE INDEX IF NOT EXISTS idx_reports_district ON reports(district);
CREATE INDEX IF NOT EXISTS idx_history_report ON status_history(report_id, created_at);
