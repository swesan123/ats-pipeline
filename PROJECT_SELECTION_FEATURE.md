# Project Selection Feature Design

## Overview
Allow users to maintain a library of all their projects and automatically select the most relevant projects for each job application.

## Components

### 1. Project Library Storage
- **Location**: `data/projects_library.json`
- **Format**: Array of ProjectItem objects with additional metadata:
  ```json
  {
    "name": "Project Name",
    "tech_stack": ["Tech1", "Tech2"],
    "start_date": "Jan 2024",
    "end_date": "Mar 2024",
    "bullets": [...],
    "description": "Brief description",
    "relevance_keywords": ["keyword1", "keyword2"],
    "category": "ML/AI" | "Web" | "Mobile" | "Backend" | "Other"
  }
  ```

### 2. CLI Commands
```bash
# Add a project to library
ats add-project --name "Project Name" --tech-stack "Tech1,Tech2" --description "..." --from-json project.json

# List all projects
ats list-projects

# Remove a project
ats remove-project --name "Project Name"

# Select projects for a job
ats select-projects --job-json job_skills.json --max-projects 4
```

### 3. Project Relevance Scoring
- Score projects based on:
  - Tech stack overlap with job requirements (weighted)
  - Keyword matching in project description/bullets
  - Category alignment
  - Recency (more recent = higher score)
- Return top N projects sorted by relevance

### 4. Integration with Resume Rewrite
- Before rewriting resume:
  1. Score all projects in library against job requirements
  2. Select top N projects (default: 4)
  3. Replace resume.projects with selected projects
  4. Continue with normal rewrite flow

### 5. Database Schema (Optional)
Add `projects_library` table:
```sql
CREATE TABLE projects_library (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL,
    tech_stack TEXT,  -- JSON array
    start_date TEXT,
    end_date TEXT,
    bullets TEXT,  -- JSON array
    description TEXT,
    relevance_keywords TEXT,  -- JSON array
    category TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

## Implementation Steps

1. **Create Project Library Manager** (`src/projects/project_library.py`)
   - `add_project(project: ProjectItem) -> None`
   - `remove_project(name: str) -> None`
   - `get_all_projects() -> List[ProjectItem]`
   - `save_library() -> None`

2. **Create Project Selector** (`src/projects/project_selector.py`)
   - `score_project(project: ProjectItem, job_skills: JobSkills) -> float`
   - `select_projects(job_skills: JobSkills, max_projects: int = 4) -> List[ProjectItem]`

3. **Update CLI** (`src/cli/main.py`)
   - Add `add-project`, `list-projects`, `remove-project`, `select-projects` commands

4. **Update Resume Rewrite Flow** (`src/cli/main.py` in `rewrite_resume`)
   - Before generating proposals, call project selector
   - Replace resume.projects with selected projects

5. **Update GUI** (if applicable)
   - Add project library management UI
   - Show project selection in job details view

## Usage Example

```bash
# 1. Add projects to library
ats add-project --name "ML Project" --tech-stack "Python,TensorFlow" --description "..."

# 2. When rewriting resume for a job
ats rewrite-resume --resume-json data/resume.json --job-json data/job_skills.json
# Automatically selects top 4 relevant projects

# 3. Or manually select projects
ats select-projects --job-json data/job_skills.json --max-projects 3
# Outputs selected projects to data/selected_projects.json
```

