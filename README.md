# ENGAGE DB — Social Engagement and Learning Analytics

**Project files:** [DBMS/ENGAGE_DB](DBMS/ENGAGE_DB/)  
**YouTube demonstration:** [Watch ENGAGE DB](https://youtu.be/8axdOZ_n8Vw)


**BACSE202 Database Management Systems | Fall 2026–2027 | VIT Chennai**  
**Faculty:** Dr. S. Geetha · **Slot:** D1 + TD1 · **Class:** CH202670101707

## Project abstract (under 150 words)
ENGAGE DB is an educational social-engagement web application designed to demonstrate relational database management and explainable learning-resource discovery. Students can publish posts, like, save, comment and follow peers. The system stores relationships through primary/foreign keys and analyzes them using SQL joins, aggregates, subqueries and views. Students explicitly provide an exam goal, monthly budget and preferred learning mode; the recommendation workflow combines these declared preferences with engagement signals to rank sample educational resources. Flask provides the backend, PostgreSQL stores live data, and an optional Oracle snapshot supports SQL*Plus demonstrations. The project uses synthetic student profiles and fictional learning-provider entries. The repository includes the ER model, schema scripts, seed data, normalization evidence, assigned SQL queries, and a test plan.

## Team and equal contribution plan

| Team member | Register number | Equal share | Area to demonstrate |
|---|---|---:|---|
| D Narasimhan | 25BCE5028 | 33.33% | Frontend/Flask integration, post and comment workflows, database connection and mirror |
| D Shri Vishwa | 25BCE5127 | 33.33% | ER/relational design, normalization, likes/saves and referential integrity |
| Skandhan | 25BCE5175 | 33.33% | Recommendation/analytics, follows, test cases and presentation evidence |

The above is an **equal contribution/presentation plan**: confirm with all members and change it if actual contributions differ. All three jointly review SQL, reports, tests and the recorded demonstration. Detailed allocation: `docs/CONTRIBUTIONS.md`.

## Five working application flows to demonstrate

| Feature | UI action | Flask endpoint | PostgreSQL tables involved |
|---|---|---|---|
| Create post | Compose and publish | `POST /api/post` | `post`, `reach`, `hashtag`, `post_hashtag` |
| Like post | Like/unlike | `POST /api/post/<post_id>/like` | `likes`, `post` |
| Save post | Save/unsave | `POST /api/post/<post_id>/save` | `saved`, `post` |
| Comment | Submit text | `POST /api/post/<post_id>/comment` | `comments`, `comment_hashtag` |
| Follow | Follow/unfollow another user | `POST /api/follow/<target_id>` | `following`, `engage_user` |

Additional features include learning-profile updates, recommendations, engagement/trending summaries, messages, stories and database query demos. Application routes exist in the provided code; **live end-to-end tests and database screenshots must still be captured by the team**.

## Implemented features — project summary

ENGAGE DB provides a database-backed educational social platform with the following workflows:

- **Create posts:** Students publish learning-related content through the Flask application.
- **Like, save, and comment:** User interactions are recorded in related PostgreSQL tables.
- **Follow users:** The system stores follower–following relationships.
- **Learning profiles:** Students select an exam goal, monthly budget, and preferred study mode.
- **Explainable recommendations:** Learning opportunities are scored for goal relevance, interests, affordability, mode, and quality.
- **Engagement analytics:** SQL joins, aggregates, and subqueries analyze posts, likes, saves, comments, and hashtags.

Application screenshots and ER-design images can be included here after the corresponding files have been added to the repository by their contributors.

## Technology and DBMS versions

- **Frontend:** HTML, CSS, JavaScript. **Backend:** Python and Flask (`Flask==3.0.3` in `requirements.txt`).
- **Live database:** PostgreSQL (`engage_meta`), via psycopg 3. Install a local PostgreSQL server; use its actual version for the final report.
- **Optional database mirror:** Oracle Database Free, configured as `FREEPDB1`, with `python-oracledb`; Oracle Free 23c was used in the project environment. Verify your running Oracle version before finalizing.
- **Operating system for supplied launch scripts:** Windows CMD.
- **Python:** 3.11+ recommended (the uploaded source included a Python 3.13 virtual environment, not redistributable here).

## Database layout and constraints

**12 core tables:** `engage_user` (PK user_id), `post` (PK post_id, FK user_id), `following` (composite PK two user IDs), `likes` and `saved` (composite post/user PKs), `reposts` (PK repost_id), `hashtag` (PK hashtag_id), `post_hashtag` (junction PK), `comments` (PK comment_id, parent-comment self-FK), `comment_likes`, `comment_hashtag`, and `reach` (PK reach_id, unique FK post_id). The primary/foreign-key model controls duplicates and invalid references.

**Oracle demonstrator extension (three tables):** `student_profile`, `learning_resource`, `post_learning_signal`. PostgreSQL also contains implementation-only support tables, activity history, recommendation outputs, shares, views and indexes; see `database/postgresql_schema.sql`.

**Sample data:** `database/sample_data.sql` contains **272 Oracle INSERT statements over 15 tables**, built from synthetic sample records, ordered for FK dependencies. In the original application, `src/sample_data.py` plus `src/seed.py` load PostgreSQL data. The 272 records describe the base sample, not the extra optional demo expansion.

## Fresh installation — Windows / PostgreSQL (primary application)

1. Install Python, PostgreSQL, and create an empty database `engage_meta` (via pgAdmin or `createdb`). Start PostgreSQL service.
2. Clone/extract repository; open CMD **inside `DBMS/ENGAGE_DB/src`**.
3. Run the commands below. Copy `.env.example` into `.env` and enter your own local database password; do not commit `.env`.

```bat
cd /d "PATH_TO_REPOSITORY\DBMS\ENGAGE_DB\src"
py -m venv .venv
call .venv\Scripts\activate
python -m pip install -r ..\requirements.txt
copy .env.example .env
notepad .env
python setup_postgres.py
python seed.py
python app.py
```

Open `http://127.0.0.1:5000` and test `http://127.0.0.1:5000/api/health`. **Run `seed.py` only on a fresh disposable demo database**: it resets sample data. For an existing database with valuable records, use `setup_postgres.py` for schema updates instead, and back up first.

The original expanded demo can be added separately with `python demo_expansion.py`, but this is optional and changes demo counts.

## Oracle mirror — optional, use a separate schema

Ensure Oracle service and `FREEPDB1` are running. Add valid `ORACLE_USER`, `ORACLE_PASSWORD`, `ORACLE_DSN` to the untracked `src/.env`. From `src`, run:

```bat
python setup_oracle.py
python sync_postgres_to_oracle.py
sqlplus BCE5028@localhost/FREEPDB1
```

The Oracle user in the last command is an example used in the team lab. The mirror is a **snapshot** and does not instantly reflect subsequent PostgreSQL changes. To rebuild an isolated demonstration schema manually, use `database/schema.sql`, then `database/sample_data.sql` in SQL*Plus; **do not rerun INSERTs against existing seeded records**. Oracle and PostgreSQL SQL syntax are not completely interchangeable.

## SQL scripts and usage

- `database/schema.sql` — Oracle 15-table DDL (fresh schema only).
- `database/sample_data.sql` — all 272 baseline Oracle INSERTs and COMMIT (fresh schema only).
- `database/core_12_tables_inserts.sql` — 237 INSERTs for the original ER tables.
- `database/queries.sql` — common and 3-person assigned Oracle analytical queries.
- `database/crud_transaction_demo.sql` — safe SAVEPOINT / INSERT / UPDATE / DELETE / ROLLBACK example.
- `database/postgresql_schema.sql` — live app PostgreSQL DDL, indexes and analytic views.
- `database/postgresql_queries.sql` — native PostgreSQL analytics examples.

SQL concepts demonstrated: `SELECT`, `INSERT`, `UPDATE`, `DELETE`, `JOIN`, `LEFT JOIN`, `GROUP BY`, `COUNT`, nested subqueries, views, indexing and transactions. Details in `report/DBMS_Project_Report.pdf`.

## Normalization and recommendation method

Database normalization to 3NF for the major core relations is explained in `docs/NORMALIZATION.md`, including unnormalized relation, FDs, 1NF/2NF/3NF decomposition and cached counters.

For student-interest scoring, the PostgreSQL view combines **like ×1 + save ×4 + comment ×3 + repost ×5**, plus a bounded weak view/dwell signal. The separate course-trending view uses **likes ×1 + shares ×2 + comments ×4 + saves ×3 + reposts ×5**. Resource ranking uses goal match, interest, affordability, learning mode and quality. These are distinct formulas, not interchangeable metrics. The user explicitly enters budget; the app must not infer income from engagement clicks.

## Test plan, evidence status, and known limitations

- Static Python compilation and repository consistency checks may be run using `python -m unittest discover -s tests -v` at the repository root. This **does not replace live DB tests**.
- Complete real actions and actual-output fields in `tests/TEST_RESULTS_TEMPLATE.md`. Capture before/after UI and matching SQL results.
- Known limitations: Oracle mirror needs manual sync; seeded providers/costs are fictional; sample data is nonproduction; screenshots of two recommendation views alone do not prove complete end-to-end CRUD; no real-user authorization/authentication guarantees are claimed.
- Do not commit private emails, passwords, API keys, personal records, `.venv`, or locally uploaded user images. `.gitignore` protects local configuration; manually review `git status` before upload.

## Deliverables / references

- **IEEE-style references:** report PDF under `report/`; includes B. Batrinca and P. C. Treleaven, *Social media analytics: a survey of techniques, tools and platforms*, *AI & Society*, 2015, DOI: `10.1007/s00146-014-0549-4`.
- **Slide deck:** `presentation/engage db.pptx` (8 slides).
- **Video demo (3–5 minutes, all three members shown):** https://youtu.be/8axdOZ_n8Vw.
- **GitHub repository:** https://github.com/Narasimhan-rgb/Database_Project/tree/main/DBMS/ENGAGE_DB.
- **Submission sheet:** `submission/BACSE202_ENGAGE_DB_Submission.docx`.
