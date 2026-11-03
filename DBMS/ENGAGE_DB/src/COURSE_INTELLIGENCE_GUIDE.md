# ENGAGE — Course Demand & Trends (Studio V9)

The orange Oracle interface in **Studio** has been replaced by **Course Demand & Trends**. The left-hand PostgreSQL Table Inspector is unchanged.

## Upgrade an existing installation (preserves your real data)

1. Back up your current ENGAGE folder and PostgreSQL database.
2. Copy the updated project files to your existing `engage_db_live_app` folder. **Keep your original `.env` file** with your PostgreSQL settings.
3. In Windows Command Prompt:

```bat
cd /d "C:\PATH\TO\engage_db_live_app"
call .venv\Scripts\activate
python setup_postgres.py
python app.py
```

If the virtual environment does not exist, first run `python -m venv .venv`, `call .venv\Scripts\activate`, and `python -m pip install -r requirements.txt`.

Open **http://127.0.0.1:5000**, click **Studio**. `python setup_postgres.py` adds the sharing table and SQL views **without removing existing records**. **Do not run `seed.py` on a database you want to preserve**: that command resets demo data.

Alternatively, double-click `RUN_COURSE_STUDIO.bat` after configuring your `.env`.

## Features

**Analyze Demand** — type a course/exam goal or resource topic (for example `JEE`, `Physics`, `NEET`). Type a minimum monthly student budget (e.g. `2000`). ENGAGE returns:

- Total number of profiles in `student_profile`.
- Number and percentage whose `exam_goal` matches the course.
- Number whose goal matches **and** `max_monthly_budget >= 2000`.
- Percentage of goal students who meet the threshold.
- An numerical KPIs with an animated-style needle position; switch between **Goal %** and **Qualified %**.

The denominator is **the number of student profiles**, not total site visitors or India's student population. Budget is the student's **self-reported maximum monthly education budget**, not a payment commitment. The budget filter is inclusive.

**Find Trending** — ranks all learning resources and exam goals from highest to lowest weighted engagement:

| Action | Score per recorded action | Table |
|---|---:|---|
| Like | 1 | `likes` |
| Share (copied post link) | 2 | `post_shares` |
| Comment | 4 | `comments` |
| Save | 3 | `saved` |
| Repost | 5 | `reposts` |

Post actions are aggregated **separately** in `course_post_engagement` so JOIN multiplication does not inflate scores. A repost is not double-counted as a share. A share counts once per student/post and only after a copied-link event. Each post's `post_learning_signal` associates it with an exam goal and topic.

**Find Course** — click the button to show a course search field and a student-profile selector. This reads the selected profile's `max_monthly_budget`, searches resource names/topics/goals, and shows every matching resource with `learning_resource.monthly_cost <= profile budget`, sorted by related topic trending score descending. It does **not** apply the separate demand-analysis minimum budget to course prices.

**Important:** ENGAGE's `learning_resource` catalog represents resources. Unless you record provider-specific reactions, the trending score of a resource is a **proxy based on posts tagged with that goal and topic**, not actual likes received by that provider. Tie-breakers are quality score, then cost. No conversion history is present, so counts reflect a *potential target audience*, **not predicted enrollments or guaranteed sales**.

## Search beyond JEE

Search is **not limited to predefined choices**. New exam goals entered by students or added to the `learning_resource` table appear in search automatically. The provided baseline demo data currently has only **JEE** student profiles and JEE resources. A NEET search will not fabricate NEET students; add NEET profiles/resources to see their real counts. A `GENERAL` post alone is not a course unless someone has a matching student profile or learning resource.

When a new post caption explicitly mentions a known course goal, ENGAGE now adds a matching `post_learning_signal` row so new likes/comments/saves/reposts/shares update the relevant score.

## Database views and endpoints

- `course_post_engagement`: per-post engagement counts and weighted score
- `course_goal_trending`: goal-level scores
- `course_resource_trending`: resource-level topic scores
- `/api/studio/course-filters`
- `/api/studio/course-demand?course=JEE&budget=2000`
- `/api/studio/trending`
- `/api/studio/find-course?course=JEE&user_id=U007`

See `COURSE_INTELLIGENCE_QUERIES.sql` for ready-to-run PostgreSQL queries for your DBMS demonstration.

## Privacy / production note

Studio currently exposes aggregate profile and budget information as part of a classroom demo. Before deploying publicly, require proper sign-in/admin access for aggregate audience analytics and ensure users consent to this use of their declared preferences. A small student sample is not representative of the wider market.
