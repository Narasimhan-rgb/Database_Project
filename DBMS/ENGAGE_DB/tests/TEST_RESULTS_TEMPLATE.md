# Local end-to-end test evidence - record actual outcomes

Use a disposable/test account and capture screenshots. Do not state PASS without witnessing the run.

| ID | Test case | Expected result | Actual result | Evidence file | Status |
|---|---|---|---|---|---|
| T01 | Create post with a caption | POST and REACH records; feed updates | **TO RECORD** | 02_create_post.png | PENDING |
| T02 | Create post with blank caption | HTTP 400; no row inserted | **TO RECORD** | - | PENDING |
| T03 | Like post | LIKES row toggles and count updates | **TO RECORD** | 03_like_before_after.png | PENDING |
| T04 | Save post | SAVED row toggles and status updates | **TO RECORD** | 04_save_before_after.png | PENDING |
| T05 | Comment with text | COMMENTS row created | **TO RECORD** | 05_comment_before_after.png | PENDING |
| T06 | Comment with blank text | HTTP 400; no row inserted | **TO RECORD** | - | PENDING |
| T07 | Follow another user | FOLLOWING row and user counts updated | **TO RECORD** | 06_follow_before_after.png | PENDING |
| T08 | Attempt self-follow | HTTP 400 | **TO RECORD** | - | PENDING |
| T09 | Save student's learning profile | STUDENT_PROFILE row updated | **TO RECORD** | 10_student_profile_saved.png | PENDING |
| T10 | Compare budget 20 vs 2000000 | Ranking/affordability score changes; screenshot observed | 2 supplied UI screenshots show score difference, database not independently verified | learning_profile_budget_20.png; learning_profile_budget_2000000.png | UI OBSERVED ONLY |
| T11 | Duplicate PK or invalid FK on test schema | DB constraint rejection | **TO RECORD** | 09_constraint_violation.png | PENDING |
| T12 | SQL JOIN, GROUP BY and subquery | Expected schema-derived rows | **TO RECORD** | 08_oracle_query_output.png | PENDING |
| T13 | Oracle mirror after sync | Matching selected counts | **TO RECORD** | 08_oracle_query_output.png | PENDING |
| T14 | Fresh-environment setup | App starts after dependencies + DB setup | **TO RECORD** | 12_app_health.png | PENDING |

Before recording a screenshot, run `SELECT COUNT(*)` for key tables in pgAdmin or SQL*Plus and note the precise database. Oracle is a snapshot and will not update until the explicit synchronization script is run.
