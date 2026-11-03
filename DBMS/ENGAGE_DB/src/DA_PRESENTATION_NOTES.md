# ENGAGE DB V8.1 — Presentation Notes

## Architecture

ENGAGE V8.1 is a full-stack student opportunity and learning-engagement application backed primarily by **PostgreSQL**.

The normal application and the DBMS demonstration use the same database. A UI action such as Like, Save, Repost, Comment or Follow immediately changes a relational table, so the result can be verified with SQL during the review.

## Core ER model

The 12 PPT tables are implemented as PostgreSQL tables:

`engage_user`, `following`, `post`, `likes`, `saved`, `reposts`, `post_hashtag`, `hashtag`, `comment_hashtag`, `comments`, `comment_likes`, `reach`.

## What to say during the demo

1. **Full stack:** “The frontend sends the interaction to Flask, Flask writes it to PostgreSQL, and the same row is immediately available to SQL queries.”
2. **ER alignment:** “These 12 relational tables implement the entities and relationship tables from our ER diagram using primary keys, foreign keys and composite keys.”
3. **Live interaction:** Like a post, then query the `likes` table.
4. **Preference analysis:** Run `SELECT * FROM user_preference_summary WHERE user_id='U007';` to show Narasimhan's email, preferred genre, weighted preference score and recommended post.
5. **Advanced SQL:** Open PostgreSQL directly and run joins, GROUP BY, nested subqueries, correlated EXISTS and views from `POSTGRES_DEMO_QUERIES.sql`.
6. **Faculty mode:** There is no fixed two-query interface. Each team member can execute any valid SQL requested by faculty directly in PostgreSQL.

## Formulas implemented

User preference signal weights:
- LIKE = 1
- COMMENT = 3
- SAVE = 4
- REPOST = 5

Engagement Quality Score:

`Likes×1 + Comments×3 + Reposts×5 + Saves×4`

These are visible in PostgreSQL views so every recommendation/ranking is explainable from stored data.
