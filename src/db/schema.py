"""Database schema definitions."""

import sqlite3
from pathlib import Path


def create_tables(conn: sqlite3.Connection) -> None:
    """Create all database tables."""
    cursor = conn.cursor()
    
    # Resumes table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS resumes (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            version INTEGER NOT NULL,
            resume_json TEXT NOT NULL,
            file_path TEXT,
            job_id INTEGER,
            is_customized BOOLEAN DEFAULT 0,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (job_id) REFERENCES jobs(id)
        )
    """)
    
    # Add new columns if they don't exist (for existing databases)
    for column in ["file_path", "job_id", "is_customized"]:
        try:
            cursor.execute(f"ALTER TABLE resumes ADD COLUMN {column} {('TEXT' if column == 'file_path' else 'INTEGER' if column == 'job_id' else 'BOOLEAN DEFAULT 0')}")
        except sqlite3.OperationalError:
            pass  # Column already exists
    
    # Jobs table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS jobs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            company TEXT NOT NULL,
            title TEXT NOT NULL,
            location TEXT,
            description TEXT NOT NULL,
            source_url TEXT,
            date_posted TIMESTAMP,
            job_skills_json TEXT,
            status TEXT DEFAULT 'New',
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)
    
    # Add status column if it doesn't exist (for existing databases)
    try:
        cursor.execute("ALTER TABLE jobs ADD COLUMN status TEXT DEFAULT 'New'")
    except sqlite3.OperationalError:
        pass  # Column already exists
    
    # Add Google Sheets columns if they don't exist
    google_sheets_columns = [
        ("date_applied", "TIMESTAMP"),
        ("notes", "TEXT"),
        ("contact_name", "TEXT"),
        ("contact_info", "TEXT"),
        ("interview_dates", "TEXT"),
        ("offer_outcome", "TEXT"),
    ]
    for column_name, column_type in google_sheets_columns:
        try:
            cursor.execute(f"ALTER TABLE jobs ADD COLUMN {column_name} {column_type}")
        except sqlite3.OperationalError:
            pass  # Column already exists
    
    # Job matches table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS job_matches (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            job_id INTEGER,
            resume_id INTEGER,
            fit_score REAL NOT NULL,
            match_details_json TEXT,
            resume_customized_for_job BOOLEAN DEFAULT 0,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (job_id) REFERENCES jobs(id),
            FOREIGN KEY (resume_id) REFERENCES resumes(id)
        )
    """)
    
    # Bullet changes table (with reasoning_json)
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS bullet_changes (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            resume_id INTEGER,
            bullet_id TEXT NOT NULL,
            original_text TEXT NOT NULL,
            new_text TEXT NOT NULL,
            justification_json TEXT NOT NULL,
            reasoning_json TEXT,
            selected_variation_index INTEGER,
            approved_by_human BOOLEAN DEFAULT 0,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (resume_id) REFERENCES resumes(id)
        )
    """)
    
    # Applications table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS applications (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            job_id INTEGER,
            resume_id INTEGER,
            status TEXT DEFAULT 'pending',
            applied_at TIMESTAMP,
            notes TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (job_id) REFERENCES jobs(id),
            FOREIGN KEY (resume_id) REFERENCES resumes(id)
        )
    """)
    
    # Contacts table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS contacts (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            job_id INTEGER,
            name TEXT,
            email TEXT,
            phone TEXT,
            linkedin TEXT,
            notes TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (job_id) REFERENCES jobs(id)
        )
    """)
    
    # Analytics events table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS analytics_events (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            event_type TEXT NOT NULL,
            metadata_json TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)
    
    # Time-to-apply tracking
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS time_to_apply (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            job_id INTEGER NOT NULL,
            created_at TIMESTAMP NOT NULL,
            applied_at TIMESTAMP,
            duration_seconds INTEGER,
            FOREIGN KEY (job_id) REFERENCES jobs(id)
        )
    """)
    
    # Missing skills aggregation cache
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS missing_skills_aggregation (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            skill_name TEXT NOT NULL,
            frequency_count INTEGER DEFAULT 0,
            required_count INTEGER DEFAULT 0,
            preferred_count INTEGER DEFAULT 0,
            general_count INTEGER DEFAULT 0,
            priority_score REAL DEFAULT 0.0,
            last_updated TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            UNIQUE(skill_name)
        )
    """)
    
    # Add evidence tracking columns if they don't exist
    evidence_columns = [
        ("job_evidence_json", "TEXT"),
        ("resume_coverage", "TEXT"),
        ("is_generic", "BOOLEAN DEFAULT 0"),
        ("decomposition_json", "TEXT"),
    ]
    for column_name, column_type in evidence_columns:
        try:
            cursor.execute(f"ALTER TABLE missing_skills_aggregation ADD COLUMN {column_name} {column_type}")
        except sqlite3.OperationalError:
            pass  # Column already exists
    
    # Create indexes
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_job_matches_job_id ON job_matches(job_id)")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_job_matches_resume_id ON job_matches(resume_id)")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_bullet_changes_resume_id ON bullet_changes(resume_id)")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_applications_job_id ON applications(job_id)")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_applications_resume_id ON applications(resume_id)")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_analytics_events_event_type ON analytics_events(event_type)")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_analytics_events_created_at ON analytics_events(created_at)")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_time_to_apply_job_id ON time_to_apply(job_id)")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_missing_skills_skill_name ON missing_skills_aggregation(skill_name)")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_missing_skills_priority_score ON missing_skills_aggregation(priority_score)")
    
    conn.commit()

