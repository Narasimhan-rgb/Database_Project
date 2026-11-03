# ENGAGE V8.1 — Student Opportunity Intelligence

ENGAGE is a social-style student engagement application backed by a relational DBMS. The familiar feed is not the final product goal: it provides interaction signals that help ENGAGE recommend suitable learning resources, coaching alternatives, scholarships, mock-test options and peer-study opportunities.

## Story implemented
Two students may prepare for the same exam but have different constraints. ENGAGE does **not** infer income or socioeconomic status from clicks. The student explicitly selects an exam goal, monthly budget and preferred mode. Likes, saves, comments, reposts and viewed-post dwell are then used as learning-interest signals. PostgreSQL combines both parts into explainable ranked recommendations.

Example:
- U007 Narasimhan: JEE goal, ₹6500 selected monthly budget, hybrid preference.
- U008 Arun: JEE goal, ₹800 selected monthly budget, online/affordable-first preference.
- Both can engage with JEE content, but their ranked resource lists differ because affordability is an explicit constraint.

## PPT / ER alignment
The original ER model remains the core DBMS layer with 12 tables:
`engage_user`, `following`, `post`, `likes`, `saved`, `reposts`, `post_hashtag`, `hashtag`, `comment_hashtag`, `comments`, `comment_likes`, `reach`.

The application adds separate tables/views for the student-intelligence use case:
`student_profile`, `post_learning_signal`, `learning_resource`, `resource_recommendation`, `post_view_event`, `student_topic_scores`, `student_resource_matches`, and `student_recommendation_explainer`.

## Feed behavior
The Home page contains education-oriented, Instagram-style cards and reel/carousel labels. A post shown long enough in the viewport records a weak `post_view_event`. Explicit actions have stronger weights:
- view = weak signal
- like = 1
- comment = 3
- save = 4
- repost = 5

The weighted topic scores can be queried directly in `student_topic_scores`.

## PostgreSQL first run
```bat
cd /d "D:\AJVRPS TECH\projects\ENGAGE_DB\engage_db_live_app"
call .venv\Scripts\activate
python -m pip install -r requirements.txt
python setup_postgres.py
python seed.py
python app.py
```

Open:
- App: `http://127.0.0.1:5000`

The V7 feed error `could not determine data type of parameter $4` is fixed in V8 by explicitly typing the nullable profile filter.

## Strong faculty-demo queries
```sql
SELECT *
FROM student_recommendation_explainer
WHERE user_id='U007'
ORDER BY recommendation_rank;
```

```sql
SELECT *
FROM student_recommendation_explainer
WHERE user_id='U008'
ORDER BY recommendation_rank;
```

```sql
SELECT *
FROM student_topic_scores
WHERE user_id='U007'
ORDER BY topic_score DESC;
```

```sql
SELECT l.user_id,p.post_id,pls.topic,p.caption
FROM likes l
JOIN post p ON p.post_id=l.post_id
JOIN post_learning_signal pls ON pls.post_id=p.post_id
WHERE l.user_id='U007';
```

For the DBMS review, run SQL directly in PostgreSQL using pgAdmin Query Tool or psql. `POSTGRES_DEMO_QUERIES.sql` contains JOIN, GROUP BY, aggregate, view, nested-subquery and correlated-EXISTS examples. There is no separate Query Lab page in the website.

## Optional Oracle mirror
PostgreSQL is the live application source of truth. Oracle is an optional mirror for DBMS portability demonstrations, so the website does not risk two databases diverging on every click.

Add to `.env`:
```env
ORACLE_USER=BCE5028
ORACLE_PASSWORD=your_oracle_password
ORACLE_DSN=localhost/FREEPDB1
```

Then run:
```bat
python setup_oracle.py
python sync_postgres_to_oracle.py
```

After synchronization, open Oracle directly in SQL*Plus or SQL Developer and run relational queries such as `SELECT * FROM likes;`. PostgreSQL remains the live application source of truth.

## Important demo-data note
Learning providers, costs and recommendations in the seed data are fictional demonstration records. They are designed to demonstrate DBMS/recommendation logic, not to claim current real-world coaching prices or scholarship eligibility.


## V9: Course Demand & Trends Studio

The Studio now shows PostgreSQL tables on the left and a live **Course Demand & Trends** panel on the right. The Oracle SQL box has been removed from the user interface. The optional Oracle mirror scripts and endpoints remain for DBMS demonstrations outside the Studio.

New features: searchable goals and course topics, budget-qualified student counts and percentages, four clear numerical KPI cards, weighted engagement trending leaderboard, and a student-profile-budget-aware course finder. The score uses likes ×1, shares ×2, comments ×4, saves ×3 and reposts ×5. See `COURSE_INTELLIGENCE_GUIDE.md` and `COURSE_INTELLIGENCE_QUERIES.sql`.

Existing installation upgrade: run `python setup_postgres.py` **without** `python seed.py`; only run `seed.py` if you deliberately want to reset demo records.


## V11 — Discover, rank and save (no meter)

Studio now uses numeric demand KPI cards instead of a speedometer, with live filters for course, budget, delivery mode and ranking. Trending results update from PostgreSQL engagement events. The learning profile Save Profile button writes to PostgreSQL and shows a confirmation. The dashboard is styled as a clean social-discovery workspace.

**Safest upgrade (does not delete existing database rows):**

```bat
python setup_postgres.py
python demo_expansion.py
python app.py
```

Alternatively double-click `ADD_25_DEMO_RECORDS.bat` after database setup. Additional demo data uses `ON CONFLICT DO NOTHING` for repeat-safe installs. Adds **25 student profiles**, **25 themed posts** with likes/comments/saves/shares/reposts, and **20 fictional resource listings** across seven study goals. Existing production/personal profiles are not overwritten.

**Fresh demo database only (DESTRUCTIVE):** `python seed.py` resets all sample application records, then loads the original + expanded data; with 35 demo profiles it yields JEE 21/35 = 60%. Do not run `seed.py` on a database that contains anything you need to keep.

All expanded users, posts, prices and providers are simulated for a DBMS demo. The trending scores are calculated from stored posts and interactions, not from actual provider engagement.
