---
name: strict_bullet_and_skill_controls
overview: Tighten resume customization so bullets never fabricate skills, add project editing, fix laggy skills UI, and ensure ATS highlighting + prompts behave as expected.
todos: []
---

# Strict Bullet Controls, Project Editing, and Highlighting Fixes

## Goals

- **Stop skill fabrication completely** in bullet rewrites (experience + projects) and only allow additions that both match job keywords and exist in the Skills page.
- **Expose clear user controls** for how bullets are rewritten (reword-only vs keyword-focused) during resume customization.
- **Add full edit support for projects** (similar to Experience) in the GUI.
- **Fix UX issues**: lag when adding skills and final-line ATS highlighting not updating.

## 1. Hard-stop any fabricated skills in bullets

- **Files**: `src/compilation/resume_rewriter.py`, `src/compilation/bullet_validator.py`, `src/models/skills.py`.
- **Tasks**:
- Tighten `BulletValidator._extract_skills_from_text` to focus purely on allowed technical skills and ensure it doesn’t miss Skills-page skills that appear in bullets.
- In `_skill_is_valid`, keep strict check: only allow skills present in `UserSkills` and further **intersect** with the current job’s `JobSkills` (required+preferred) so additions must be both user-owned and job-relevant.
- In `ResumeRewriter._build_candidate_prompt` and `_build_reasoning_prompt`, explicitly:
    - Pass the **intersection of {Skills page} ∩ {job skills}** as the only allowed set to mention in bullets.
    - Rephrase guidance so that new bullets may **only reword** or **emphasize** that intersected set and never introduce unrelated skills.
- Add a small helper (e.g. `_get_allowed_job_skills_for_user`) to centralize this intersection so both prompts and validator use the same source of truth.

## 2. Reword-only vs keyword-focused modes for bullets

- **Files**: `src/gui/approval_workflow.py`, `src/compilation/resume_rewriter.py`, `src/gui/job_details.py`.
- **Tasks**:
- Extend the approval workflow UI to let you choose, per bullet session, between:
    - **Reword only** (no new skills, just clarity/strengthening), and
    - **Job-keyword mode** (can add skills, but only from the allowed intersection set).
- Thread a `rewrite_intent` (e.g. `"reword_only"` vs `"emphasize_skills"`) from `render_job_details` → `_handle_resume_generation_workflow` → `ResumeRewriter.generate_variations`.
- In `_build_candidate_prompt`, branch behavior based on `rewrite_intent`:
    - For `reword_only`, explicitly forbid **any** skill additions and require the set of skills in `bullet.skills` to be preserved.
    - For skill-emphasis modes, allow additions only from the allowed intersection set, as above.
- Ensure `BulletValidator` rejects candidates that change the skill set when `rewrite_intent` is `reword_only` (e.g. compare normalized skills before/after).

## 3. Project editing UI

- **Files**: `src/gui/projects_section.py`, `src/projects/project_library.py`, `src/models/resume.py`.
- **Tasks**:
- Mirror the inline **Edit** pattern used in `render_experience_section`:
    - For each project: show name, dates, tech_stack, bullets.
    - Add an `Edit` expander where you can modify name, dates, tech stack list, and each bullet’s text.
- Wire edits through `ProjectLibrary` to update the underlying JSON storage in the same way `ExperienceLibrary` does for experience.
- Ensure updated projects are used in resume generation (i.e., `resume.projects` reflects edits when building the customized resume).

## 4. Fix lag when adding skills

- **Files**: `src/gui/skills_section.py`, `src/analytics/analytics_service.py`.
- **Tasks**:
- Profile the path inside `"Add to My Skills"` and Skills add form:
    - Confirm if lag is primarily from `analytics.refresh_missing_skills_aggregation()` or repeated file I/O.
- Optimize by:
    - Avoiding an immediate full refresh on every added skill; instead, either:
    - Mark a `session_state` flag to defer refresh until user clicks **Refresh** in Missing Skills Analysis, or
    - Only refresh aggregates for the one skill that was added (if supported by `AnalyticsService`).
    - Minimizing redundant reads/writes of `user_skills.json` inside tight loops.
- Keep behavior the same from the user’s perspective (skill disappears from missing list after a refresh) but remove multi-second UI stalls.

## 5. Ensure ATS highlighting uses the updated resume

- **Files**: `src/rendering/latex_renderer.py`, `src/gui/job_details.py`, `src/utils/ats_keyword_tracker.py`.
- **Tasks**:
- Verify that when generating the final customized resume, the `ATSKeywordTracker` is instantiated with the **updated** resume structure or is passed both original and updated resumes as needed.
- Adjust `LaTeXRenderer._build_experience` and `_build_projects` so that keyword bolding is driven by the latest bullet texts and the current job’s allowed skills, not stale state from the original resume.
- Add or refine a small unit test (or golden-output test) that checks: the last bullet in an experience section receives bolding when it contains a job keyword that should be highlighted.

## 6. Wire feedback and AI assistant into prompts safely

- **Files**: `src/compilation/resume_rewriter.py`, `src/compilation/bullet_feedback.py`, `src/utils/skill_ai_assistant.py`.
- **Tasks**:
- Ensure `BulletFeedbackStore.preference_note()` is only used as a soft hint (style/length), never to relax hard constraints about skills.
- Confirm the AI Skill Assistant on the Skills page only **suggests** skills and never writes anything automatically without the explicit Add click (already true, just double-check behavior).
- Optionally, add a simple test for `SkillAIAssistant.suggest_skills` that runs in no-API-key mode (returns empty list) to avoid test fragility.

## 7. Quick regression checks

- Run `make validate` and `make test` (once `pytest` is installed) to ensure:
- No `NameError` or missing-import issues remain.
- New editing and bullet workflows don’t break existing tests.
- Manually sanity-check in the app:
- Editing experience and projects works and persists.
- Resume customization never introduces a skill not on the Skills page and not in the job’s skills.