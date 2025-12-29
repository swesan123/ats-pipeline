"""Unit tests for MissingSkillsAggregator."""

import pytest
import json
from src.analytics.skills_aggregator import MissingSkillsAggregator
from src.db.database import Database
from src.models.job import JobPosting, JobSkills, JobMatch
from src.models.resume import Resume


def test_aggregate_missing_skills(test_db, sample_resume, sample_job_skills):
    """Test aggregating missing skills from job matches."""
    aggregator = MissingSkillsAggregator(test_db)
    
    # Create a job and match
    job = JobPosting(
        company="Test Co",
        title="Test Job",
        description="Test"
    )
    job_id = test_db.save_job(job, sample_job_skills)
    resume_id = test_db.save_resume(sample_resume)
    
    # Create a job match with missing skills
    job_match = JobMatch(
        fit_score=0.7,
        skill_gaps={
            'required_missing': ['Python', 'Docker'],
            'preferred_missing': ['Kubernetes']
        },
        missing_skills=['React'],
        matching_skills=['JavaScript'],
        recommendations=[]
    )
    test_db.save_job_match(job_match, job_id, resume_id)
    
    # Aggregate skills
    aggregated = aggregator.aggregate_missing_skills()
    
    assert len(aggregated) > 0
    # Check that Python appears (as required)
    python_data = aggregated.get('python')
    if python_data:
        assert python_data['required_count'] > 0
        assert python_data['priority_score'] >= 3.0


def test_rank_by_priority(test_db):
    """Test ranking skills by priority."""
    aggregator = MissingSkillsAggregator(test_db)
    
    # Update aggregation cache first
    aggregator.update_aggregation_cache()
    
    # Get ranked skills
    ranked = aggregator.rank_by_priority(limit=10)
    
    # Verify sorting (priority_score descending)
    if len(ranked) > 1:
        for i in range(len(ranked) - 1):
            assert ranked[i]['priority_score'] >= ranked[i+1]['priority_score']


def test_rank_by_frequency(test_db):
    """Test ranking skills by frequency."""
    aggregator = MissingSkillsAggregator(test_db)
    
    # Update aggregation cache first
    aggregator.update_aggregation_cache()
    
    # Get ranked skills
    ranked = aggregator.rank_by_frequency(limit=10)
    
    # Verify sorting (frequency_count descending)
    if len(ranked) > 1:
        for i in range(len(ranked) - 1):
            assert ranked[i]['frequency_count'] >= ranked[i+1]['frequency_count']


def test_update_aggregation_cache(test_db):
    """Test updating the aggregation cache."""
    aggregator = MissingSkillsAggregator(test_db)
    
    count = aggregator.update_aggregation_cache()
    
    # Verify cache was updated
    cursor = test_db.conn.cursor()
    cursor.execute("SELECT COUNT(*) as count FROM missing_skills_aggregation")
    result = cursor.fetchone()
    assert result['count'] == count

