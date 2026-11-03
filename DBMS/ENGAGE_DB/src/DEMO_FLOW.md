# 5-minute faculty demo flow

1. **Home** — show the education-style feed. Explain that viewing is a weak interest signal; Like/Save/Comment/Repost are stronger signals.
2. Select **U008 Arun** and open **For You**. Show the ₹800 selected budget and affordable/online preference.
3. Switch to **U007 Narasimhan**. Show the same JEE goal with a larger selected budget and compare the recommendation list.
4. Open **PostgreSQL directly** using pgAdmin Query Tool or psql. Open `POSTGRES_DEMO_QUERIES.sql`.
5. Run the table-verification query to prove the original 12-table PPT ER model is implemented.
6. Run the JOIN, GROUP BY, nested-subquery and correlated-EXISTS examples from the SQL file.
7. Like or Save a post in ENGAGE, return to PostgreSQL, and rerun the relevant query to show that the application changed the real relational database live.
8. Run the `student_recommendation_explainer` queries for U007 and U008 to prove that the same JEE goal can produce different recommendations using explicit budget constraints plus engagement signals.
9. Optional Oracle portability demo: run `SETUP_ORACLE_MIRROR.bat`, then inspect/query the mirrored Oracle tables separately in SQL*Plus or SQL Developer.
