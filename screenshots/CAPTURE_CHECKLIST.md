# Required live screenshots - capture on the team computer

Two **real student-profile screenshots provided by the team** are already in this folder and embedded in README.md. These are not substitutes for the remaining application/SQL test evidence.

1. `01_home_feed.png` - ENGAGE homepage with posts; no sensitive data.
2. `02_create_post.png` - create a harmless post and show its new post ID.
3. `03_like_before_after.png` - show like interaction result and count.
4. `04_save_before_after.png` - saved post and saved-item list.
5. `05_comment_before_after.png` - new comment and post detail.
6. `06_follow_before_after.png` - follow status and counts.
7. `07_postgres_tables.png` - pgAdmin showing core tables.
8. `08_oracle_query_output.png` - SQL*Plus showing assigned SELECT output.
9. `09_constraint_violation.png` - invalid/duplicate data error with safe demo IDs.
10. `10_student_profile_saved.png` - saved preferences and matching student profile row.
11. `11_resource_rankings.png` - ranked recommendations after saving profile.
12. `12_app_health.png` - HTTP /api/health showing PostgreSQL connected (hide usernames if sensitive).

Capture with Win+Shift+S and save **PNG** at the filenames above. For each screenshot, record the action, SQL verification, expected outcome, actual observed result and date in `tests/TEST_RESULTS_TEMPLATE.md`. Verify screenshots before GitHub upload; remove personal tokens, emails and database passwords. Then embed the new screenshots inline in README using `![Description](screenshots/01_home_feed.png)` (replace filename for each). Do not fabricate results or upload stale screenshots as current evidence.
