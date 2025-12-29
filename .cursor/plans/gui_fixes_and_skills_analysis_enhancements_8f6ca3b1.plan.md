---
name: GUI Fixes and Skills Analysis Enhancements
overview: Fix GUI bugs (dialog error, button placement, table height), enhance skills analysis with categorization and evidence-based decomposition, and improve UX with refresh icons and better skill filtering.
todos:
  - id: fix_dialog_error
    content: Fix st.dialog() error in jobs_page.py - replace with st.modal() or conditional rendering
    status: pending
  - id: move_add_job_button
    content: Move Add Job button to be before refresh button in jobs_page.py
    status: pending
  - id: increase_table_height
    content: Increase job list table height to accommodate 100+ rows in job_list.py
    status: pending
  - id: explain_priority_vs_frequency
    content: Add clear explanations for priority score vs frequency in analytics_page.py
    status: pending
  - id: categorize_skills
    content: Implement skill categorization (Programming Languages, Frameworks, DevOps, etc.) in analytics_page.py and skills_aggregator.py
    status: pending
  - id: refresh_button_icon
    content: Change 'Refresh Skills Data' button to just refresh icon in analytics_page.py
    status: pending
  - id: filter_generic_skills
    content: Implement filtering of generic/vague skills (Generative AI, Deep Learning, Algorithms) in skills_aggregator.py
    status: pending
  - id: evidence_extraction
    content: Implement job evidence extraction from job descriptions in skills_aggregator.py
    status: pending
  - id: resume_coverage_check
    content: Implement resume coverage checking for skills in skills_aggregator.py
    status: pending
  - id: evidence_based_decomposition
    content: Implement evidence-based skill decomposition (only from job evidence + resume validation) in skills_aggregator.py
    status: pending
    dependencies:
      - evidence_extraction
      - resume_coverage_check
  - id: update_schema_evidence
    content: Add evidence tracking columns to missing_skills_aggregation table in schema.py
    status: pending
  - id: display_skills_by_category
    content: Display skills grouped by category in analytics page tabs
    status: pending
    dependencies:
      - categorize_skills
  - id: display_skill_evidence
    content: Display job evidence and resume coverage for each skill in analytics page
    status: pending
    dependencies:
      - evidence_extraction
      - resume_coverage_check
---

# GUI Fixes and Skills Analysis Enhancements

## Overview

This plan addresses multiple GUI bugs and enhances the skills analysis system with evidence-based decomposition and better categorization.---

## Part 1: GUI Bug Fixes

### 1.1 Fix Add Job Dialog Error

**File**: `src/gui/jobs_page.py`**Issue**: `st.dialog()` is not a context manager in current Streamlit version, causing `TypeError: 'function' object does not support the context manager protocol`.**Solution**: Replace `st.dialog()` with `st.modal()` (Streamlit 1.28+) or use `st.expander()` with session state for dialog-like behavior. Check Streamlit version and use appropriate API.**Alternative**: Use a modal pattern with `st.session_state` and conditional rendering.

### 1.2 Move Add Job Button

**File**: `src/gui/jobs_page.py`**Current**: Add Job button appears on top of Google Sheets sync section.**Fix**: Move Add Job button to be in front of (before) the refresh button in the top row. Update column layout:

- Current: `col_refresh, col_add, col_spacer`
- New: `col_add, col_refresh, col_spacer` (swap order)

### 1.3 Increase Table Height

**File**: `src/gui/job_list.py`**Issue**: Table height is too small for 100+ jobs.**Fix**: Add `height` parameter to `st.dataframe()` to accommodate 100+ rows. Use `height=600` or calculate based on row count (min 400, max 800).---

## Part 2: Skills Analysis Enhancements

### 2.1 Explain Priority Score vs Frequency

**File**: `src/gui/analytics_page.py`**Current**: Users don't understand the difference between priority score and frequency.**Fix**: Add clear explanations:

- **Priority Score**: Weighted score prioritizing required skills (required × 3.0 + preferred × 1.5 + general × 1.0). Shows which skills will have biggest impact on fit scores.
- **Frequency**: Raw count of how often a skill appears across all jobs. Shows most common missing skills.

Add tooltips or info text explaining the difference.

### 2.2 Categorize Skills

**File**: `src/gui/analytics_page.py` and `src/analytics/skills_aggregator.py`**Categories to implement**:

- Programming Languages
- Frameworks & Libraries
- DevOps & Infrastructure
- Databases & Storage
- Cloud Platforms
- Operating Systems & Systems
- Software Engineering Practices
- Security
- Data & Machine Learning
- Tools & Productivity
- Other

**Implementation**:

- Create `_categorize_skill()` function similar to `_categorize_skills()` in `job_details.py`
- Group skills by category in the analytics page
- Display skills in expandable sections by category
- Show category totals

### 2.3 Change Refresh Button to Icon

**File**: `src/gui/analytics_page.py`**Current**: "Refresh Skills Data" button with text.**Fix**: Change to just a refresh icon (🔄) like the jobs page, positioned similarly.

### 2.4 Filter Generic/Vague Skills

**File**: `src/analytics/skills_aggregator.py`**Issue**: Generic skills like "Generative AI", "Deep Learning", "Algorithms" are too vague.**Solution**: Implement evidence-based filtering:

1. **Remove generic skills** that have no specific job evidence
2. **Decompose generic skills** only if they have:

- Explicit job requirement evidence (verbatim mentions in job descriptions)
- Resume evidence (actual usage in projects/experience)
- Cross-validation between jobs and resume

**Rules**:

- No ontology-based expansion
- No "general knowledge" decomposition
- Only decompose if job descriptions mention specific sub-skills
- Only recommend if resume comparison shows actual gap

**Implementation**:

- Add `_is_generic_skill()` function to identify vague skills
- Add `_decompose_skill_with_evidence()` function that:
- Extracts verbatim skill mentions from job descriptions
- Cross-checks against resume content
- Only creates sub-skills with job evidence
- Filter out skills without evidence in `aggregate_missing_skills()`

### 2.5 Evidence-Based Skill Decomposition

**File**: `src/analytics/skills_aggregator.py` (new methods)**Core Principle**: Skills can only be decomposed using:

1. **Resume Evidence** (primary): Existing bullets, projects, coursework, tools used
2. **Job Requirement Evidence** (secondary): Explicit mentions in job descriptions
3. **Intersection** (gold standard): Employers want it + you're close enough to learn it

**Implementation**:

- `_extract_skill_evidence_from_jobs(skill_name: str) -> List[str]`: Extract verbatim skill mentions from job descriptions
- `_check_resume_coverage(skill: str, resume: Resume) -> str`: Returns "covered", "partial", or "none"
- `_decompose_with_evidence(skill_name: str) -> Dict`: Creates decomposition only from job evidence, validates against resume

**Data Structure**:

```python
{
    "parent_skill": "Generative AI",
    "decomposed_from": "job_evidence",
    "children": [
        {
            "skill": "Prompt Engineering",
            "resume_coverage": "partial",
            "job_frequency": 18,
            "source_jobs": ["job_123", "job_456"]
        }
    ]
}
```

**Hard Rules** (enforce in code):

- No child skill without job evidence
- No skill recommendation without resume comparison
- No ontology-based expansion
- Every learning recommendation must cite jobs
- Every skill must explain "why it exists"

---

## Part 3: Database Schema Updates

### 3.1 Add Skill Evidence Tracking

**File**: `src/db/schema.py`Add columns to `missing_skills_aggregation` table:

- `job_evidence_json TEXT` - JSON array of job IDs and verbatim mentions
- `resume_coverage TEXT` - "covered", "partial", or "none"
- `is_generic BOOLEAN` - Whether skill is too generic/vague
- `decomposition_json TEXT` - JSON of evidence-based sub-skills

---

## Part 4: UI/UX Improvements

### 4.1 Skills Display by Category

**File**: `src/gui/analytics_page.py`**Changes**:

- Group skills by category in both "By Priority" and "By Frequency" tabs
- Use expandable sections for each category
- Show category summary (count, top skills)
- Add filter to show/hide generic skills

### 4.2 Skill Evidence Display

**File**: `src/gui/analytics_page.py`**New Feature**: For each skill, show:

- Job evidence count
- Resume coverage status
- Source jobs (expandable)
- Why this skill exists (explanation)

---

## Implementation Order

### Phase 1: Critical Bug Fixes (P0)

1. Fix `st.dialog()` error - replace with `st.modal()` or conditional rendering
2. Move Add Job button before refresh button
3. Increase table height for 100+ jobs

### Phase 2: Skills Analysis UI (P1)

4. Add priority score vs frequency explanation
5. Change refresh button to icon
6. Implement skill categorization
7. Display skills by category in analytics page

### Phase 3: Evidence-Based Filtering (P1)

8. Implement generic skill detection
9. Add job evidence extraction
10. Add resume coverage checking
11. Filter out skills without evidence
12. Implement evidence-based decomposition

### Phase 4: Database & Advanced Features (P2)

13. Update database schema for evidence tracking
14. Store skill evidence in aggregation cache
15. Display evidence in UI

---

## Files to Modify

### Modified Files

- `src/gui/jobs_page.py` - Fix dialog, move button, improve layout
- `src/gui/job_list.py` - Increase table height
- `src/gui/analytics_page.py` - Add explanations, categorization, evidence display, icon button
- `src/analytics/skills_aggregator.py` - Add evidence-based filtering and decomposition
- `src/db/schema.py` - Add evidence tracking columns

### New Files

- None (all functionality in existing files)

---

## Testing Requirements

1. **GUI Tests**:

- Verify Add Job dialog works without errors
- Verify button placement is correct
- Verify table displays 100+ rows properly

2. **Skills Analysis Tests**:

- Test generic skill filtering
- Test evidence extraction from jobs