"""Database interface for ATS pipeline."""

import json
import sqlite3
from datetime import datetime
from pathlib import Path
from typing import List, Optional

from src.models.resume import Resume, Reasoning
from src.models.job import JobPosting, JobSkills, JobMatch
from src.models.resume import Justification
from .schema import create_tables


class Database:
    """Database interface for storing resumes, jobs, matches, and changes."""
    
    def __init__(self, db_path: str = "ats_pipeline.db"):
        """Initialize database connection."""
        self.db_path = Path(db_path)
        self.conn = sqlite3.connect(str(self.db_path), check_same_thread=False)
        self.conn.row_factory = sqlite3.Row
        create_tables(self.conn)
    
    def close(self):
        """Close database connection."""
        self.conn.close()
    
    def save_resume(self, resume: Resume) -> int:
        """Save resume to database. Returns resume ID."""
        cursor = self.conn.cursor()
        resume_json = resume.model_dump_json()
        
        cursor.execute("""
            INSERT INTO resumes (version, resume_json, updated_at)
            VALUES (?, ?, ?)
        """, (resume.version, resume_json, datetime.now()))
        
        self.conn.commit()
        return cursor.lastrowid
    
    def get_resume(self, resume_id: int) -> Optional[Resume]:
        """Get resume by ID."""
        cursor = self.conn.cursor()
        cursor.execute("SELECT resume_json FROM resumes WHERE id = ?", (resume_id,))
        row = cursor.fetchone()
        
        if row:
            return Resume.model_validate_json(row["resume_json"])
        return None
    
    def get_latest_resume(self) -> Optional[Resume]:
        """Get the most recent resume."""
        cursor = self.conn.cursor()
        cursor.execute("""
            SELECT resume_json FROM resumes
            ORDER BY updated_at DESC
            LIMIT 1
        """)
        row = cursor.fetchone()
        
        if row:
            return Resume.model_validate_json(row["resume_json"])
        return None
    
    def save_job(self, job: JobPosting, job_skills: Optional[JobSkills] = None) -> int:
        """Save job posting to database. Returns job ID."""
        cursor = self.conn.cursor()
        job_skills_json = job_skills.model_dump_json() if job_skills else None
        
        cursor.execute("""
            INSERT INTO jobs (company, title, location, description, source_url, date_posted, job_skills_json)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        """, (
            job.company,
            job.title,
            job.location,
            job.description,
            job.source_url,
            job.date_posted,
            job_skills_json,
        ))
        
        self.conn.commit()
        return cursor.lastrowid
    
    def get_job(self, job_id: int) -> Optional[JobPosting]:
        """Get job posting by ID."""
        cursor = self.conn.cursor()
        cursor.execute("SELECT * FROM jobs WHERE id = ?", (job_id,))
        row = cursor.fetchone()
        
        if row:
            return JobPosting(
                company=row["company"],
                title=row["title"],
                location=row["location"],
                description=row["description"],
                source_url=row["source_url"],
                date_posted=datetime.fromisoformat(row["date_posted"]) if row["date_posted"] else None,
            )
        return None
    
    def get_job_skills(self, job_id: int) -> Optional[JobSkills]:
        """Get job skills for a job."""
        cursor = self.conn.cursor()
        cursor.execute("SELECT job_skills_json FROM jobs WHERE id = ?", (job_id,))
        row = cursor.fetchone()
        
        if row and row["job_skills_json"]:
            return JobSkills.model_validate_json(row["job_skills_json"])
        return None
    
    def list_jobs(self) -> List[dict]:
        """List all jobs."""
        cursor = self.conn.cursor()
        cursor.execute("""
            SELECT id, company, title, location, date_posted, created_at
            FROM jobs
            ORDER BY created_at DESC
        """)
        return [dict(row) for row in cursor.fetchall()]
    
    def save_job_match(
        self, 
        job_match: JobMatch, 
        job_id: int, 
        resume_id: int, 
        resume_customized_for_job: bool = False
    ) -> int:
        """Save job match to database. Returns match ID."""
        cursor = self.conn.cursor()
        match_details = {
            "skill_gaps": job_match.skill_gaps,
            "missing_skills": job_match.missing_skills,
            "matching_skills": job_match.matching_skills,
            "recommendations": job_match.recommendations,
        }
        match_details_json = json.dumps(match_details)
        
        cursor.execute("""
            INSERT INTO job_matches (job_id, resume_id, fit_score, match_details_json, resume_customized_for_job)
            VALUES (?, ?, ?, ?, ?)
        """, (job_id, resume_id, job_match.fit_score, match_details_json, resume_customized_for_job))
        
        self.conn.commit()
        return cursor.lastrowid
    
    def get_job_match(self, match_id: int) -> Optional[JobMatch]:
        """Get job match by ID."""
        cursor = self.conn.cursor()
        cursor.execute("SELECT * FROM job_matches WHERE id = ?", (match_id,))
        row = cursor.fetchone()
        
        if row:
            match_details = json.loads(row["match_details_json"])
            return JobMatch(
                job_id=row["job_id"],
                fit_score=row["fit_score"],
                skill_gaps=match_details.get("skill_gaps", {}),
                missing_skills=match_details.get("missing_skills", []),
                matching_skills=match_details.get("matching_skills", []),
                recommendations=match_details.get("recommendations", []),
            )
        return None
    
    def save_bullet_change(
        self,
        resume_id: int,
        bullet_id: str,
        original_text: str,
        new_text: str,
        justification: Justification,
        reasoning: Optional[Reasoning] = None,
        selected_variation_index: Optional[int] = None,
        approved_by_human: bool = False,
    ) -> int:
        """Save bullet change to database. Returns change ID."""
        cursor = self.conn.cursor()
        justification_json = justification.model_dump_json()
        reasoning_json = reasoning.model_dump_json() if reasoning else None
        
        cursor.execute("""
            INSERT INTO bullet_changes (
                resume_id, bullet_id, original_text, new_text,
                justification_json, reasoning_json,
                selected_variation_index, approved_by_human
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            resume_id,
            bullet_id,
            original_text,
            new_text,
            justification_json,
            reasoning_json,
            selected_variation_index,
            approved_by_human,
        ))
        
        self.conn.commit()
        return cursor.lastrowid
    
    def get_bullet_changes(self, resume_id: int) -> List[dict]:
        """Get all bullet changes for a resume."""
        cursor = self.conn.cursor()
        cursor.execute("""
            SELECT * FROM bullet_changes
            WHERE resume_id = ?
            ORDER BY created_at DESC
        """, (resume_id,))
        return [dict(row) for row in cursor.fetchall()]
    
    def save_application(
        self,
        job_id: int,
        resume_id: int,
        status: str = "pending",
        notes: Optional[str] = None,
    ) -> int:
        """Save application to database. Returns application ID."""
        cursor = self.conn.cursor()
        
        cursor.execute("""
            INSERT INTO applications (job_id, resume_id, status, applied_at, notes)
            VALUES (?, ?, ?, ?, ?)
        """, (job_id, resume_id, status, datetime.now(), notes))
        
        self.conn.commit()
        return cursor.lastrowid
    
    def get_applications(self, job_id: Optional[int] = None) -> List[dict]:
        """Get applications, optionally filtered by job_id."""
        cursor = self.conn.cursor()
        
        if job_id:
            cursor.execute("""
                SELECT * FROM applications
                WHERE job_id = ?
                ORDER BY created_at DESC
            """, (job_id,))
        else:
            cursor.execute("""
                SELECT * FROM applications
                ORDER BY created_at DESC
            """)
        
        return [dict(row) for row in cursor.fetchall()]
    
    def get_resumes_for_job(self, job_id: int) -> List[int]:
        """Get resume IDs customized for a specific job."""
        cursor = self.conn.cursor()
        cursor.execute("""
            SELECT resume_id FROM job_matches
            WHERE job_id = ? AND resume_customized_for_job = 1
            ORDER BY created_at DESC
        """, (job_id,))
        return [row[0] for row in cursor.fetchall()]
    
    def get_all_jobs(self) -> List[dict]:
        """Get all jobs from database with job_skills loaded."""
        cursor = self.conn.cursor()
        cursor.execute("""
            SELECT * FROM jobs
            ORDER BY created_at DESC
        """)
        jobs = []
        for row in cursor.fetchall():
            job_dict = dict(row)
            # Load job skills if available
            if job_dict.get("job_skills_json"):
                try:
                    job_skills = JobSkills.model_validate_json(job_dict["job_skills_json"])
                    job_dict["job_skills"] = job_skills
                except:
                    pass
            jobs.append(job_dict)
        return jobs

