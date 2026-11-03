# PPT alignment with the final ENGAGE story

## What already matches
The ER diagram/database layer already supports the mechanism needed by the final idea:
- USER identifies students/community members.
- POST + HASHTAG describe content they consume.
- LIKES, SAVED, REPOSTS, COMMENTS and COMMENT_LIKES capture engagement.
- FOLLOWING captures community relationships.
- REACH captures content exposure/performance.

These 12 relational tables should remain your main ER-diagram evidence.

## What should change in the presentation story
The older generic line “social media engagement analytics database” is too broad for the final product story. Use this instead:

**Problem statement**
Students preparing for exams such as JEE do not have equal access to coaching, mentoring and study resources. A student may repeatedly consume useful exam content but still not know which free, affordable or premium learning option fits their goals, preferred learning mode and selected budget.

**Solution**
ENGAGE is a student opportunity intelligence platform with a social-style feed. It records normal engagement signals—views, likes, saves, comments and reposts—and combines them with an explicit student learning profile such as exam goal, preferred mode and maximum monthly budget. PostgreSQL then produces explainable recommendations for study resources, mock tests, coaching alternatives, scholarships and peer learning.

**Ethical design sentence**
ENGAGE does not infer whether a student is poor or rich from behavior. Affordability is a profile preference entered by the student and can be changed at any time.

**Demo story**
- Student A: JEE goal + ₹800 budget + online preference → free/low-cost resources rank highly.
- Student B: JEE goal + ₹6500 budget + hybrid preference → the same interest signals can include premium alternatives.
- Both recommendation lists can be explained using SQL columns for interest score, affordability score, goal score and total score.

## Architecture line for the PPT
`Social-style feed → PostgreSQL ER tables → weighted engagement signals → student-selected constraints → explainable opportunity recommendations`

Optional portability demo:
`PostgreSQL live DB → Oracle mirror for cross-DBMS SQL demonstration`
