# ENGAGE DB - Functional dependencies and normalization (DA1)

## Illustrative unnormalized relation
`ENGAGE_RECORD(user_id, user_name, email, post_id, caption, {hashtags}, {likes}, {comments})` combines repeating hashtag, like and comment groups. Those groups are not atomic and cause update/insertion/deletion anomalies. This is an **illustrative starting relation**, not a table implemented in the app.

## Functional dependencies (representative)
- `user_id -> user_name, full_name, handle, email, city, bio, avatar_color, avatar_url`
- `post_id -> user_id, caption, content_type, genre, post_date, language, location`
- `hashtag_id -> hashtag_name, purpose`
- `comment_id -> user_id, post_id, comment_text, sentiment, parent_comment_id`
- `(post_id, user_id) -> liked_at` in `LIKES`; the entire composite key identifies a like
- `(post_id, user_id) -> saved_at` in `SAVED`
- `(follower_user_id, following_user_id) -> followed_at` in `FOLLOWING`
- `reach_id -> post_id, impressions, unique_reach`; additionally `post_id` is UNIQUE in `REACH`

## Step 1 - First Normal Form (1NF)
Eliminate repeating lists. Each like, saved post, follow relation and post/hashtag connection becomes a separate row in its own table. Columns are atomic under the application's data model.

## Step 2 - Second Normal Form (2NF)
Separating `POST` and `ENGAGE_USER` prevents user-name and email being copied into tables whose composite keys are `(post_id,user_id)`. In `LIKES`, no attribute such as caption depends on only `post_id`; in `SAVED`, no user-profile attribute depends on only `user_id`.

## Step 3 - Third Normal Form (3NF)
Store user details only in `ENGAGE_USER`, post details in `POST`, hashtag names in `HASHTAG`, and comment content in `COMMENTS`. Relationship tables hold identifiers plus relationship attributes; this prevents non-key-to-non-key transitive dependencies across combined activity records. The core design supports 3NF for these principal functional dependencies. Full formal proof of every supplementary table would require confirming additional business-specific FDs.

## BCNF observations
For the junction tables with PK `(post_id,user_id)` or `(post_id,hashtag_id)`, each declared nontrivial determinant is a superkey under the stated constraints. The report does **not** claim that every application extension is BCNF-proved.

## Deliberately stored/derived values
`ENGAGE_USER.follower_count` and `following_count` are cached counts of `FOLLOWING`; application code updates them after follow operations. `REACH.impressions` and `unique_reach` are stored performance measures. These are practical performance/state values, not normalization evidence; their consistency must be tested.
