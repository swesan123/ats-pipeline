# ATS Pipeline

End-to-end job application pipeline with skill matching, explainable resume compilation, and human-verified AI workflows.

## Features

- **LaTeX Resume Parsing**: Convert LaTeX resumes to structured JSON
- **Job Skill Extraction**: Automatically extract required/preferred skills from job descriptions using AI
- **Job URL Scraping**: Extract job content from URLs (Greenhouse, Lever, LinkedIn, etc.)
- **Skill Matching**: Calculate job fit scores and identify skill gaps
- **Resume Rewriting**: Generate 4 bullet variations with reasoning chains for each improvement
- **Interactive Approval**: Review and approve resume changes with detailed justifications
- **PDF Generation**: Render updated resumes back to LaTeX and compile to PDF
- **CLI Interface**: Command-line interface with `ats` command for all operations
- **Full Application Flow**: Single `apply` command to run the entire pipeline
- **User Skills Management**: Prevent skill fabrication with user-provided skills JSON
- **Project Selection**: Automatically select relevant projects from your project library
- **Resume Reuse System**: Automatically detect and reuse resumes from similar jobs
- **Streamlit GUI**: Visual job management interface
- **Database Persistence**: SQLite database for tracking jobs, matches, and changes
- **Google Sheets Sync**: One-way sync from Google Sheets to database for job tracking
- **Resume Organization**: Organized resume storage with date-based folders and human-readable filenames
- **Resume Preview**: PDF preview and download in GUI
- **Analytics & Insights**: Comprehensive analytics dashboard with metrics, time-to-apply tracking, and missing skills analysis

## Prerequisites

- Python 3.10 or higher
- LaTeX distribution (for PDF generation):
  - **Linux/WSL**: 
    ```bash
    sudo apt-get install texlive-latex-base texlive-latex-extra texlive-fonts-extra
    ```
    This installs the base LaTeX packages plus the `newtxtext` and `newtxmath` packages needed for Times New Roman font.
  - **macOS**: `brew install --cask mactex` or `brew install basictex`
  - **Windows**: Install [MiKTeX](https://miktex.org/download) or [TeX Live](https://www.tug.org/texlive/)
- OpenAI API key (for skill extraction and resume rewriting)

## Installation

1. **Clone the repository:**
   ```bash
   git clone <repository-url>
   cd ats-pipeline
   ```

2. **Create a virtual environment (recommended):**
   ```bash
   python3 -m venv venv
   
   # Activate virtual environment
   # On Linux/macOS:
   source venv/bin/activate
   # On Windows:
   venv\Scripts\activate
   ```

3. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
   ```
   
   This installs all required packages including:
   - `pydantic>=2.0.0` - Data validation and serialization
   - `openai>=1.0.0` - AI-powered skill extraction and resume rewriting
   - `click>=8.0.0` - CLI framework for the `ats` command-line interface
   - `python-dotenv>=1.0.0` - Environment variable management (for `.env` file support)
   - `streamlit>=1.28.0` - Web GUI framework
   - `pandas>=2.0.0` - Data manipulation
   - `jinja2>=3.1.0` - Template engine
   - `requests>=2.31.0` - HTTP library for web scraping
   - `beautifulsoup4>=4.12.0` - HTML parsing for job URL extraction
   - `lxml>=4.9.0` - Fast XML/HTML parser
   - `playwright>=1.40.0` - Browser automation for JavaScript-heavy job boards
   
   **Note:** After installing, run `python3 -m playwright install` to set up browser binaries for Playwright:
   ```bash
   python3 -m playwright install
   ```

4. **Install development dependencies (optional, for testing):**
   ```bash
   pip install -r requirements-dev.txt
   ```

5. **Install the package (to use `ats` command):**
   ```bash
   pip install -e .
   ```

6. **Set up Playwright browsers (required for job URL extraction):**
   After installing dependencies, you need to install browser binaries for Playwright:
   ```bash
   python3 -m playwright install
   ```
   
   This downloads Chromium, Firefox, and WebKit browsers needed for scraping JavaScript-heavy job boards (Greenhouse, Lever, etc.).
   
   **Linux/WSL System Dependencies:**
   If you see warnings about missing system libraries (libwebp, libx264, etc.), install them:
   ```bash
   # Option 1: Use Playwright's install-deps (requires sudo)
   sudo python3 -m playwright install-deps
   
   # Option 2: Install manually on Ubuntu/Debian/WSL
   sudo apt-get update
   sudo apt-get install -y libwebp-dev libx264-dev
   ```
   
   **Note:** This step is only required if you plan to extract skills from job URLs. File-based extraction works without Playwright.

7. **Set up environment variables:**
   Create a `.env` file in the project root (optional) or export the variable:
   ```bash
   export OPENAI_API_KEY="your-api-key-here"
   ```
   
   Or create `.env` file:
   ```bash
   echo "OPENAI_API_KEY=your-api-key-here" > .env
   ```

## Setup Checklist

Before using the pipeline, ensure you have:

- ✅ Python 3.10+ installed
- ✅ Virtual environment activated
- ✅ Dependencies installed (`pip install -r requirements.txt`)
- ✅ Package installed in editable mode (`pip install -e .`)
- ✅ Playwright browsers installed (`python3 -m playwright install`) - **Required for job URL extraction**
- ✅ OpenAI API key set in `.env` file or environment variable
- ✅ LaTeX distribution installed (for PDF generation)

## Quick Start

### 0. Set Up User Skills (Recommended)

To prevent the system from making up skills, create a `data/user_skills.json` file listing all your skills and which projects use them:

```bash
# Copy the example template
cp data/user_skills.json.example data/user_skills.json

# Edit the file to list your skills and projects
nano data/user_skills.json  # or use your preferred editor
```

The user skills file format:
```json
{
  "skills": [
    {
      "name": "Python",
      "category": "Languages",
      "projects": ["Project Name 1", "Project Name 2"],
      "proficiency_level": "advanced"
    }
  ]
}
```

**Why use user skills?**
- Prevents skill fabrication: Only skills you've actually used are added to bullets
- Project-specific filtering: Skills are only added to projects where they're relevant
- Ensures accuracy: The system won't add skills you don't have

**Note:** If you don't provide a user skills file, the system may add skills that don't match your actual experience. It's recommended to create this file before running `rewrite-resume` or `apply`.

### 1. Convert LaTeX Resume to JSON

First, convert your LaTeX resume to JSON format. Output is automatically saved to `data/resume.json`:

```bash
ats convert-latex templates/resume.tex
```

### 2. Extract Skills from Job Description

Extract skills from a job URL or description file. Output is automatically saved to `data/job_skills.json`:

**From a job URL:**
```bash
ats extract-skills "https://boards.greenhouse.io/company/jobs/123456"
```

**From a file:**
```bash
ats extract-skills job_description.txt
```

**Force Playwright for JavaScript-heavy sites:**
```bash
ats extract-skills "https://jobs.lever.co/company/123" --use-playwright
```

**Important Notes for Job URL Extraction:**
- The scraper automatically detects job board type (Greenhouse, Lever, LinkedIn, etc.) and uses the appropriate extraction method
- **Playwright Setup Required**: For JavaScript-heavy job boards (Greenhouse, Lever, Ashby), you must install Playwright browsers:
  ```bash
  python3 -m playwright install
  ```
  This downloads browser binaries (~300MB). Only needed if extracting from URLs.
- **OpenAI API Key Required**: Skill extraction uses OpenAI API. Set `OPENAI_API_KEY` in `.env` file or environment variable.
- File-based extraction works without Playwright - you can always paste job descriptions into a text file instead.

### 3. Match Resume Against Job

Calculate fit score and identify skill gaps. Uses `data/resume.json` and `data/job_skills.json` by default:

```bash
ats match-job
```

Or specify custom paths:

```bash
ats match-job --resume-json data/resume.json --job-json data/job_skills.json
```

**Note:** The command uses options (flags), not positional arguments. Use `--resume-json` and `--job-json` flags if you need to specify custom paths.

### 4. Generate Resume Rewrite Proposals

Generate 4 variations for each bullet that needs adjustment. Output is automatically saved to `data/resume_updated.json`:

```bash
ats rewrite-resume --user-skills data/user_skills.json
```

Or specify custom paths:

```bash
ats rewrite-resume --resume-json data/resume.json --job-json data/job_skills.json --user-skills data/user_skills.json
```

**Important:** The command uses options (flags), not positional arguments. There is no `--output` option - output is always saved to `data/resume_updated.json`.

Options:
- `--resume-json`: Resume JSON file (default: `data/resume.json`)
- `--job-json`: Job skills JSON file (default: `data/job_skills.json`)
- `--user-skills`: User skills JSON file to prevent skill fabrication (recommended)
- `--reuse-threshold`: Minimum fit score to reuse existing resume (default: 0.90)
- `--similarity-threshold`: Minimum job similarity to consider reuse (default: 0.85)
- `--force-new`: Force generation of new resume even if reuse is available

This will:
- Check for reusable resumes from similar jobs (if database is available)
- Analyze your resume against job requirements
- Generate reasoning chains for each bullet that needs improvement
- Show 4 variations for each bullet
- Prompt you to approve/reject/select variations (y/n/r/1-4)

### 5. Render PDF

Generate a PDF from your updated resume JSON. Output is automatically saved to `data/resume.pdf`:

```bash
ats render-pdf
```

Or specify a custom resume file:

```bash
ats render-pdf --resume-json data/resume_updated.json
```

## CLI Commands Reference

After installing the package with `pip install -e .`, you can use the `ats` command:

**Important:** All commands use options (flags) instead of positional arguments. Output files are automatically saved to the `data/` folder and cannot be customized.

### `convert-latex`
Convert LaTeX resume to JSON format. Output is saved to `data/resume.json`.

```bash
ats convert-latex <input.tex>
```

### `extract-skills`
Extract skills from a job URL or description file. Output is saved to `data/job_skills.json`.

```bash
ats extract-skills <job_url_or_file> [--use-playwright]
```

Options:
- `--use-playwright`: Force use of Playwright for scraping (handles JavaScript-heavy sites)

Examples:
```bash
# Extract from URL
ats extract-skills "https://boards.greenhouse.io/company/jobs/123456"

# Extract from file
ats extract-skills job_description.txt

# Force Playwright for dynamic content
ats extract-skills "https://jobs.lever.co/company/123" --use-playwright
```

### `apply` ⭐ **NEW - Full Application Flow**
Run the entire application flow in one command: extract-skills → match-job → rewrite-resume → render-pdf.

```bash
ats apply <job_url> [--resume-json <path>] [--user-skills <path>] [--skip-match] [--use-playwright] [--reuse-threshold <float>] [--similarity-threshold <float>] [--force-new]
```

Options:
- `job_url`: Job posting URL (required)
- `--resume-json`: Resume JSON file (default: `data/resume.json`)
- `--user-skills`: User skills JSON file to prevent skill fabrication (default: `data/user_skills.json`)
- `--skip-match`: Skip the match-job step (optional)
- `--use-playwright`: Force use of Playwright for scraping
- `--reuse-threshold`: Minimum fit score to reuse existing resume (default: 0.90)
- `--similarity-threshold`: Minimum job similarity to consider reuse (default: 0.85)
- `--force-new`: Force generation of new resume even if reuse is available

Example:
```bash
ats apply "https://boards.greenhouse.io/company/jobs/123456" --user-skills data/user_skills.json
```

**User Skills File:**
To prevent the system from making up skills, create a `data/user_skills.json` file listing all your skills and which projects use them. See `data/user_skills.json.example` for the format.

The user skills file ensures that:
- Only skills you've actually used are added to bullets
- Skills are only added to projects where they're relevant
- No fabrication of experience or skills

### `match-job`
Calculate job fit score and show gap analysis. Uses `data/resume.json` and `data/job_skills.json` by default.

```bash
ats match-job [--resume-json <path>] [--job-json <path>] [--ontology <skills.json>]
```

Options:
- `--resume-json`: Resume JSON file (default: `data/resume.json`)
- `--job-json`: Job skills JSON file (default: `data/job_skills.json`)
- `--ontology`: Optional skill ontology JSON file

### `rewrite-resume`
Generate resume rewrite proposals with interactive approval. Output is saved to `data/resume_updated.json`.

```bash
ats rewrite-resume [--resume-json <path>] [--job-json <path>] [--ontology <skills.json>] [--user-skills <path>] [--reuse-threshold <float>] [--similarity-threshold <float>] [--force-new]
```

Options:
- `--resume-json`: Resume JSON file (default: `data/resume.json`)
- `--job-json`: Job skills JSON file (default: `data/job_skills.json`)
- `--ontology`: Optional skill ontology JSON file
- `--user-skills`: User skills JSON file to prevent skill fabrication
- `--reuse-threshold`: Minimum fit score to reuse existing resume (default: 0.90)
- `--similarity-threshold`: Minimum job similarity to consider reuse (default: 0.85)
- `--force-new`: Force generation of new resume even if reuse is available

### `render-pdf`
Generate PDF from JSON resume. Output is saved to `data/resume.pdf`.

```bash
ats render-pdf [--resume-json <path>]
```

Options:
- `--resume-json`: Resume JSON file (default: `data/resume_updated.json`)

### `sync-sheet`
Sync jobs from Google Sheets to database. See [Google Sheets Sync](#google-sheets-sync) section for detailed setup instructions.

```bash
ats sync-sheet --credentials <path> --spreadsheet-id <id> [--sheet-name <name>] [--dry-run]
```

Options:
- `--credentials`: Path to Google service account JSON file (required)
- `--spreadsheet-id`: Google Sheets spreadsheet ID (required)
- `--sheet-name`: Name of the sheet to sync from (default: "Sheet1")
- `--dry-run`: Preview changes without applying them

Examples:
```bash
# Preview changes
ats sync-sheet --credentials credentials.json --spreadsheet-id 1abc123def456 --dry-run

# Sync data
ats sync-sheet --credentials credentials.json --spreadsheet-id 1abc123def456
```

### Project Management Commands

#### `add-project`
Add projects from resume JSON to project library.

```bash
ats add-project [--resume-json <path>] [--name <project_name>]
```

Options:
- `--resume-json`: Resume JSON file (default: `data/resume.json`)
- `--name`: Specific project name to add (if not provided, adds all projects from resume)

Examples:
```bash
# Add all projects from resume
ats add-project --resume-json data/resume.json

# Add specific project
ats add-project --resume-json data/resume.json --name "My Project"
```

#### `list-projects`
List all projects in the library.

```bash
ats list-projects
```

#### `remove-project`
Remove a project from the library.

```bash
ats remove-project --name <project_name>
```

Options:
- `--name`: Project name to remove (required)

#### `select-projects`
Select most relevant projects for a job posting.

```bash
ats select-projects [--job-json <path>] [--max-projects <n>] [--min-score <float>] [--output <path>]
```

Options:
- `--job-json`: Job skills JSON file (default: `data/job_skills.json`)
- `--max-projects`: Maximum number of projects to select (default: 4)
- `--min-score`: Minimum relevance score to include (default: 0.3)
- `--output`: Output JSON file (default: `data/selected_projects.json`)

## GUI Usage

Launch the Streamlit GUI for visual job management:

```bash
# From the project root directory
streamlit run src/gui/main_window.py
```

**Note:** Make sure you're in the project root directory when running this command. The GUI files automatically add the project root to the Python path to resolve imports.

The GUI provides:
- **Left Panel**: Add jobs by pasting job descriptions or URLs
- **Right Panel**: View all jobs in a table with fit scores
- **Job Details**: Click a job to see details and generate resume
- **Interactive Approval**: Review reasoning chains and approve variations

## Project Structure

```
ats-pipeline/
├── src/
│   ├── models/          # Pydantic data models
│   ├── parsers/         # LaTeX resume parser
│   ├── extractors/      # Job skill extraction
│   ├── matching/        # Skill matching engine
│   ├── compilation/     # Resume rewriter with reasoning
│   ├── approval/        # Interactive approval workflow
│   ├── rendering/       # LaTeX renderer and PDF generator
│   ├── db/              # Database schema and interface
│   ├── cli/             # CLI commands
│   ├── gui/             # Streamlit GUI components
│   └── github/          # GitHub MCP integration
├── tests/               # Test suite
├── scripts/             # Utility scripts
├── templates/           # LaTeX resume template
├── data/                # Output directory (resume.json, job_skills.json, etc.)
├── requirements.txt     # Production dependencies
├── requirements-dev.txt # Development dependencies
└── pyproject.toml       # Project configuration
```

## Database

The application uses SQLite for data persistence. The database file (`ats_pipeline.db`) is created automatically on first use.

**Tables:**
- `resumes`: Versioned resume JSON snapshots with file paths and job associations
- `jobs`: Job postings with extracted skills and status tracking
- `job_matches`: Fit scores and gap analysis
- `bullet_changes`: Approval history with reasoning
- `applications`: Application tracking
- `contacts`: Contact information for job applications

## Google Sheets Sync

Sync your job tracking spreadsheet from Google Sheets to the database. This allows you to maintain your job applications in Google Sheets and automatically sync them to the ATS pipeline.

### Setup

1. **Create a Google Service Account:**
   - Go to [Google Cloud Console](https://console.cloud.google.com/)
   - Create a new project or select an existing one
   - Enable the Google Sheets API and Google Drive API
   - Create a Service Account:
     - Navigate to "IAM & Admin" → "Service Accounts"
     - Click "Create Service Account"
     - Give it a name (e.g., "ats-pipeline-sync")
     - Grant it "Editor" role (or create a custom role with Sheets and Drive access)
   - Create a key:
     - Click on the service account
     - Go to "Keys" tab
     - Click "Add Key" → "Create new key"
     - Choose JSON format
     - Download the JSON file (this is your credentials file)

2. **Share your Google Sheet:**
   - Open your Google Sheet
   - Click "Share" button
   - Add the service account email (found in the JSON file, e.g., `ats-pipeline-sync@project-id.iam.gserviceaccount.com`)
   - Give it "Editor" access
   - Click "Send"

3. **Get your Spreadsheet ID:**
   - Open your Google Sheet
   - The Spreadsheet ID is in the URL: `https://docs.google.com/spreadsheets/d/SPREADSHEET_ID/edit`
   - Copy the `SPREADSHEET_ID` part

### Sheet Format

Your Google Sheet should have the following columns (case-insensitive):

- **Company Name**: Company name
- **Job Title**: Job title
- **Job Link / Source**: URL where the job was posted
- **Date Added**: Date when you added the job (format: YYYY-MM-DD or MM/DD/YYYY)
- **Date Applied**: Date when you applied (format: YYYY-MM-DD or MM/DD/YYYY)
- **Interested**: "Yes" or "No" (maps to "Interested" status)
- **Notes**: Additional notes about the job
- **Job Description Link**: Link to full job description
- **Contact Name**: Name of recruiter/contact person
- **Contact Info**: Email, phone, or LinkedIn URL
- **Interview Date(s)**: Date(s) of interviews
- **Offer / Outcome**: Final outcome (Offer, Rejected, Interview, Withdrawn, etc.)

**Note:** The sync is flexible with column names - it will match variations like "Company", "company_name", etc.

### CLI Sync

Sync jobs from Google Sheets using the command line:

```bash
ats sync-sheet --credentials path/to/credentials.json --spreadsheet-id YOUR_SPREADSHEET_ID
```

Options:
- `--credentials`: Path to Google service account JSON file (required)
- `--spreadsheet-id`: Google Sheets spreadsheet ID (required)
- `--sheet-name`: Name of the sheet to sync from (default: "Sheet1")
- `--dry-run`: Preview changes without applying them

Examples:
```bash
# Dry run to preview changes
ats sync-sheet --credentials credentials.json --spreadsheet-id 1abc123def456 --dry-run

# Actually sync the data
ats sync-sheet --credentials credentials.json --spreadsheet-id 1abc123def456

# Sync from a specific sheet
ats sync-sheet --credentials credentials.json --spreadsheet-id 1abc123def456 --sheet-name "Job Applications"
```

### GUI Sync

You can also sync from the Streamlit GUI:

1. Launch the GUI: `streamlit run src/gui/main_window.py`
2. In the left panel, expand "Google Sheets Sync"
3. Enter:
   - **Credentials Path**: Path to your service account JSON file
   - **Spreadsheet ID**: Your spreadsheet ID
   - **Sheet Name**: Name of the sheet (default: "Sheet1")
4. Click "Sync (Dry Run)" to preview changes, or "Sync (Apply)" to sync

### How Sync Works

- **One-way sync**: Data flows from Google Sheets → Database (Sheet is the source of truth)
- **Job matching**: Jobs are matched by Company + Title, or by Source URL if available
- **Updates**: Existing jobs are updated with new information from the sheet
- **New jobs**: Jobs not in the database are added
- **Status mapping**: 
  - "Interested" = "Yes" → Status: "Interested"
  - "Offer / Outcome" column → Maps to status (Offer, Rejected, Interview, etc.)
- **Contacts**: Contact information is saved to the `contacts` table
- **Applications**: Application dates and interview dates are saved to the `applications` table

### Dependencies

Google Sheets sync requires additional packages:
```bash
pip install gspread google-auth
```

These are included in `requirements.txt` but if you get import errors, install them manually.

## Testing

Run the test suite:

```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=src --cov-report=html

# View coverage report
open htmlcov/index.html  # macOS/Linux
# or
start htmlcov/index.html  # Windows
```

## Development

### Running Tests

```bash
# Unit tests only
pytest tests/unit/

# Integration tests
pytest tests/integration/

# Specific test file
pytest tests/unit/test_models/test_resume.py
```

### Code Coverage

The project aims for 80%+ code coverage. Coverage reports are generated in HTML format:

```bash
pytest --cov=src --cov-report=html
```


## Troubleshooting

### LaTeX/PDF Generation Issues

**Error: `pdflatex not found`**
- Install a LaTeX distribution (see Prerequisites)
- Ensure `pdflatex` is in your PATH

**Error: `File 'newtxtext.sty' not found`**
- Install the required LaTeX font packages:
  ```bash
  # Linux/WSL
  sudo apt-get install texlive-fonts-extra
  
  # Or install full texlive distribution (includes all packages)
  sudo apt-get install texlive-full
  ```
- The template uses Times New Roman font via `newtxtext` and `newtxmath` packages

**Error: PDF compilation fails**
- Check that the LaTeX template is valid
- Ensure all required LaTeX packages are installed (see Prerequisites)
- Check the error output for missing packages
- Common missing packages: `newtxtext`, `newtxmath`, `enumitem`, `titlesec`

### OpenAI API Issues

**Error: `OpenAI API key required`**
- Set the `OPENAI_API_KEY` environment variable
- Or create a `.env` file with your API key

**Error: API rate limits**
- The application uses `gpt-4o-mini` by default for cost efficiency
- Consider upgrading your OpenAI plan if you hit rate limits

### Database Issues

**Error: Database locked**
- Close any other connections to the database
- The database uses SQLite, which supports concurrent reads but not concurrent writes

### Job URL Scraping Issues

**Error: `Playwright is not installed`**
- Install Playwright: `pip install playwright`
- Install browser binaries: `python3 -m playwright install`
- For JavaScript-heavy job boards (Greenhouse, Lever), Playwright is required

**Error: `Missing libraries: libwebpmux.so.3, libx264.so` (Linux/WSL)**
- Install system dependencies: `sudo python3 -m playwright install-deps`
- Or install manually: `sudo apt-get install -y libwebp-dev libx264-dev`
- These are system libraries required for browser rendering

**Error: `Failed to extract with requests`**
- The job board may require JavaScript rendering
- Use the `--use-playwright` flag: `ats extract-skills <url> --use-playwright`
- Ensure Playwright is installed and browsers are set up

**Error: Job content not extracted correctly**
- Some job boards have custom HTML structures
- Try using `--use-playwright` for better extraction
- For best results, use board-specific extractors (Greenhouse, Lever, LinkedIn are supported)

## Workflow Example

### Quick Workflow (Recommended): Using `apply` Command

The easiest way to process a job application is using the `apply` command, which runs the entire flow in one step:

1. **Set up user skills (one-time setup):**
   ```bash
   cp data/user_skills.json.example data/user_skills.json
   # Edit data/user_skills.json with your skills and projects
   ```

2. **Convert your LaTeX resume (one-time setup):**
   ```bash
   ats convert-latex templates/resume.tex
   # Output saved to data/resume.json
   ```

3. **Run the entire flow for a job:**
   ```bash
   ats apply "https://boards.greenhouse.io/company/jobs/123456" --user-skills data/user_skills.json
   ```
   
   This single command will:
   - Extract skills from the job URL
   - Match your resume against the job (optional, can skip with `--skip-match`)
   - Generate resume rewrite proposals with interactive approval
   - Render the final PDF
   
   **Output files:**
   - `data/job_skills.json` - Extracted job skills
   - `data/resume_updated.json` - Updated resume after approval
   - `data/resume.pdf` - Final PDF resume

### Step-by-Step Workflow (Manual)

If you prefer to run each step individually:

1. **Convert your LaTeX resume:**
   ```bash
   ats convert-latex templates/resume.tex
   # Output saved to data/resume.json
   ```

2. **Find a job and extract skills:**
   ```bash
   # From a job URL (recommended)
   ats extract-skills "https://boards.greenhouse.io/company/jobs/123456"
   
   # Or from a file
   ats extract-skills job.txt
   # Output saved to data/job_skills.json
   ```

3. **Check job fit:**
   ```bash
   ats match-job
   # Uses data/resume.json and data/job_skills.json by default
   ```

4. **Generate resume improvements:**
   ```bash
   ats rewrite-resume --user-skills data/user_skills.json
   # Output saved to data/resume_updated.json
   ```
   - Checks for reusable resumes from similar jobs
   - Review reasoning chains for each bullet
   - Select variations (1-4) or approve/reject
   - Optionally provide feedback for regeneration

5. **Generate final PDF:**
   ```bash
   ats render-pdf
   # Output saved to data/resume.pdf
   ```

## Project Management

The pipeline includes a project library system that allows you to store all your projects and automatically select the most relevant ones for each job application.

### Setting Up Your Project Library

1. **Add projects to the library:**
   ```bash
   # Add all projects from your resume
   ats add-project --resume-json data/resume.json
   
   # Or add a specific project
   ats add-project --resume-json data/resume.json --name "Project Name"
   ```

2. **List projects in library:**
   ```bash
   ats list-projects
   ```

3. **Select relevant projects for a job:**
   ```bash
   ats select-projects --job-json data/job_skills.json
   ```

The `rewrite-resume` and `apply` commands automatically select relevant projects from your library when generating resumes.

## Analytics & Insights

The ATS Pipeline includes a comprehensive analytics system to track your job application process and identify skill gaps.

### Accessing Analytics

Open the Streamlit GUI and navigate to the **Analytics** page in the top navigation bar.

### Key Metrics

The analytics dashboard displays:
- **Total Jobs Tracked**: Number of jobs in your database
- **Applications Submitted**: Jobs with status "Applied"
- **Average Time-to-Apply**: Average time from job creation to application submission
- **Resumes Generated**: Count of customized resumes created
- **Bullet Approval Rate**: Percentage of AI-generated bullets that were approved

### Time-to-Apply Tracking

Time-to-apply measures how long it takes you to apply for a job after adding it to the system.

**How it works:**
1. When you add a job (via GUI, CLI, or Google Sheets sync), tracking automatically starts
2. When you change the job status to "Applied", the time-to-apply is calculated and stored
3. The analytics dashboard shows:
   - Average, median, min, and max time-to-apply
   - Distribution histogram
   - Trends over time

**Use cases:**
- Identify bottlenecks in your application process
- Set goals for faster application turnaround
- Track improvement over time

### Missing Skills Analysis

The system aggregates missing skills across all your job applications to help you prioritize skill development.

**Two ranking methods:**

1. **By Priority Score** (recommended):
   - Calculates: `(required_count × 3.0) + (preferred_count × 1.5) + (general_count × 1.0)`
   - Prioritizes skills that are frequently required (not just preferred)
   - Shows which skills will have the biggest impact on your job fit scores

2. **By Frequency**:
   - Ranks skills by how often they appear across job postings
   - Useful for identifying common skill requirements in your target roles

**Using the analysis:**
1. Navigate to the Analytics page
2. Click "Refresh Skills Data" to update the aggregation (runs automatically after job matches)
3. Review the "By Priority" tab to see which skills to learn first
4. Use the "By Frequency" tab to see the most common missing skills

**Skill categories tracked:**
- Required missing skills (highest priority)
- Preferred missing skills (medium priority)
- General missing skills (lower priority)

### Application Funnel

The application funnel visualizes your job application pipeline:
- **Stages**: New → Interested → Applied → Interview → Offer/Rejected
- **Conversion Rates**: Percentage of jobs moving between stages
- **Status Distribution**: Count of jobs at each stage

Use this to:
- Identify where you're losing opportunities
- Track your application success rate
- Set goals for each stage

### Recent Activity

View recent system events including:
- Job additions
- Status changes
- Resume generations
- Bullet approvals/rejections

## Testing

The project includes comprehensive unit and integration tests.

### Running Tests

```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=src --cov-report=html

# Run specific test file
pytest tests/unit/test_analytics/test_event_tracker.py

# Run integration tests
pytest tests/integration/
```

### Test Coverage Goals

- **Unit Tests**: >80% coverage for analytics modules
- **Integration Tests**: Cover all major workflows
- **Critical Paths**: 100% coverage for time-to-apply and missing skills aggregation

### Test Structure

- `tests/unit/` - Unit tests for individual components
- `tests/integration/` - End-to-end workflow tests
- `tests/unit/test_analytics/` - Analytics-specific unit tests

## Security

**IMPORTANT: Never commit credentials or API keys to the repository!**

### Protected Files

The following files and directories are automatically ignored by git (see `.gitignore`):
- `.env` - Environment variables (including `OPENAI_API_KEY`)
- `*credentials*.json` - Google service account credentials
- `*service_account*.json` - Service account files
- `job-applications*.json` - Job application credentials
- `resumes/` - Generated resume files (may contain personal information)
- `data/` - Local data files (resumes, job skills, etc.)
- `*.db`, `*.sqlite` - Database files
- `*.key`, `*.pem`, `*.p12`, `*.pfx` - Private keys and certificates

### Best Practices

1. **API Keys**: Store API keys in `.env` file (already in `.gitignore`):
   ```bash
   echo "OPENAI_API_KEY=your-key-here" > .env
   ```

2. **Google Sheets Credentials**: 
   - Store service account JSON files outside the repository
   - Use absolute paths when referencing credentials
   - Never commit credential files to git

3. **Resume Files**: 
   - Generated resumes are stored in `resumes/` directory (automatically ignored)
   - Resume JSON files in `data/` are also ignored

4. **If You Accidentally Committed Credentials**:
   - **Immediately rotate/revoke the exposed credentials**
   - Remove the file from git: `git rm --cached <file>`
   - Update `.gitignore` to prevent future commits
   - Consider using `git filter-branch` or BFG Repo-Cleaner to remove from history

### Verifying No Secrets Are Committed

Before pushing, check for sensitive files:
```bash
# Check for credential files
git ls-files | grep -E "(credentials|service_account|\.key|\.pem)"

# Check for API keys in code
grep -r "sk-[a-zA-Z0-9]" . --exclude-dir=venv --exclude-dir=.git
```

## Contributing

1. Create a feature branch: `git checkout -b feature/your-feature-name`
2. Make your changes
3. Run validation: `make validate` or `python3 scripts/validate.py`
4. Write/update tests
5. Ensure tests pass: `make test` or `pytest`
6. Run full check: `make check` (runs validation + tests)
7. Submit a pull request

### Validation and Testing

Before committing, it's recommended to run validation to catch import errors and syntax issues:

```bash
# Quick validation (syntax only, faster)
make validate-fast

# Full validation (includes import checking)
make validate

# Run all tests
make test

# Run tests with coverage
make test-cov

# Run validation + tests together
make check
```

You can also validate specific files:
```bash
python3 scripts/validate.py --files src/gui/analytics_page.py src/gui/jobs_page.py
```

The validation script checks for:
- Syntax errors
- Import errors (missing imports, undefined names)
- Basic type issues

## License

[Add your license here]

## Support

For issues, questions, or contributions, please open an issue on GitHub.
