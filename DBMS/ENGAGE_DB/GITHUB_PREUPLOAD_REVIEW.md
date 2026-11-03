# STOP - REVIEW BEFORE GITHUB UPLOAD

The package has **NOT** been uploaded, pushed, or published to GitHub. Review with all three members, then obtain explicit approval before any upload.

1. Confirm each member's one-third contribution statement is accurate.
2. Run the application and complete the actual-result cells in `tests/TEST_RESULTS_TEMPLATE.md`.
3. Capture the 12 required local screenshots (`screenshots/CAPTURE_CHECKLIST.md`) and embed them inline in README.
4. Capture comparator website screenshots required by the faculty, with permitted sources/citations.
5. Record 3-5 minute video with all three team members visible; upload to YouTube (Unlisted or Public) and paste URL into both README and Word submission sheet.
6. Create GitHub repository and paste its URL into Word submission sheet.
7. Inspect every file before commit. In particular, never include `.env`, local database passwords, `.venv`, `__pycache__`, real private user records, or local upload content.
8. Execute SQL on a **fresh test schema**; sample data cannot be re-inserted into existing populated tables without duplicate-key errors.
9. Clarify that the Oracle mirror is a snapshot, not the live PostgreSQL data source.
10. Verify setup on a clean Windows computer where feasible; report result honestly.

**Manual Git commands after your approval and final inspection:**
```bat
cd /d "PATH_TO_EXTRACTED\ENGAGE_DB_GITHUB_READY"
git init
git add .
git status
git commit -m "ENGAGE DB DBMS submission"
git branch -M main
git remote add origin YOUR_REPO_URL
git push -u origin main
```
Do not run them until the team checks the published content and agrees.
