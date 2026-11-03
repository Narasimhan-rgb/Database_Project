"""Live course-demand and engagement trend queries against ENGAGE PostgreSQL.

All filters are parameterized. Counts represent self-reported student profiles,
not purchases, enrollment probabilities, or an external population estimate.
"""
from decimal import Decimal, InvalidOperation
from flask import Blueprint, jsonify, request
from db import PostgresDB, json_rows

course_bp = Blueprint('course_intelligence', __name__)


def success(data):
    return jsonify({'ok': True, 'data': data})


def error(message, status=400):
    return jsonify({'ok': False, 'error': str(message)}), status


def _course_term(raw):
    term = str(raw or '').strip()
    if not term:
        raise ValueError('Enter a course or exam goal, such as JEE, NEET or GATE.')
    if len(term) > 120:
        raise ValueError('Course search is limited to 120 characters.')
    return term


def _budget(raw):
    try:
        value = Decimal(str(raw if raw not in (None, '') else '0'))
    except (InvalidOperation, ValueError):
        raise ValueError('Enter a valid monthly budget in rupees.') from None
    if not value.is_finite() or value < 0 or value > Decimal('9999999999.99'):
        raise ValueError('Budget must be between ₹0 and ₹9,999,999,999.99.')
    return value


# A search can match an exam goal or one of its actual resource titles/topics.
# If a new goal is added to PostgreSQL, it becomes searchable without code changes.
FIND_GOALS_SQL = """
WITH possible AS (
    SELECT TRIM(exam_goal) AS exam_goal FROM student_profile
    UNION SELECT TRIM(exam_goal) FROM learning_resource
    UNION SELECT TRIM(exam_goal) FROM post_learning_signal
)
SELECT DISTINCT p.exam_goal
FROM possible p
WHERE p.exam_goal <> '' AND (
    POSITION(LOWER(%s) IN LOWER(p.exam_goal)) > 0
    OR EXISTS (
        SELECT 1 FROM learning_resource lr
        WHERE LOWER(TRIM(lr.exam_goal)) = LOWER(p.exam_goal)
          AND (
               POSITION(LOWER(%s) IN LOWER(lr.title)) > 0
               OR POSITION(LOWER(%s) IN LOWER(lr.topic)) > 0
          )
    )
)
ORDER BY p.exam_goal
"""


def _matching_goals(db, term):
    return [r['exam_goal'] for r in db.query(FIND_GOALS_SQL, (term, term, term))]


@course_bp.get('/api/studio/course-filters')
def course_filters():
    db = PostgresDB()
    try:
        goals = db.query("""
            SELECT DISTINCT TRIM(exam_goal) AS goal FROM (
              SELECT exam_goal FROM student_profile
              UNION SELECT exam_goal FROM learning_resource
              UNION SELECT exam_goal FROM post_learning_signal
            ) goals WHERE TRIM(exam_goal) <> '' ORDER BY goal
        """)
        students = json_rows(db.query("""
            SELECT sp.user_id, u.user_name, sp.exam_goal, sp.max_monthly_budget
            FROM student_profile sp JOIN engage_user u ON u.user_id=sp.user_id
            ORDER BY u.user_name, sp.user_id
        """))
        return success({'goals': [x['goal'] for x in goals], 'students': students})
    except Exception as exc:
        return error(f'Could not read course filters: {exc}', 503)


@course_bp.get('/api/studio/course-demand')
def course_demand():
    try:
        term = _course_term(request.args.get('course'))
        min_budget = _budget(request.args.get('budget'))
        db = PostgresDB()
        goals = _matching_goals(db, term)
        norm_goals = [g.strip().lower() for g in goals]
        stats = db.query("""
            SELECT COUNT(*) AS total_students,
              COUNT(*) FILTER (WHERE LOWER(TRIM(exam_goal))=ANY(%s::text[])) AS goal_students,
              COUNT(*) FILTER (WHERE LOWER(TRIM(exam_goal))=ANY(%s::text[])
                                AND max_monthly_budget >= %s) AS qualified_students
            FROM student_profile
        """, (norm_goals, norm_goals, min_budget))[0]
        all_count = int(stats['total_students'])
        goal_count = int(stats['goal_students'])
        qualified_count = int(stats['qualified_students'])
        return success({
            'query': term, 'matched_goals': goals,
            'minimum_budget': float(min_budget),
            'total_students': all_count,
            'goal_students': goal_count,
            'qualified_students': qualified_count,
            'goal_percentage': round(goal_count * 100 / all_count, 2) if all_count else 0,
            'qualified_percentage': round(qualified_count * 100 / all_count, 2) if all_count else 0,
            'qualified_within_goal_percentage': round(qualified_count * 100 / goal_count, 2) if goal_count else 0,
            'measurement': 'Self-reported profiles only. Budget is the student\'s maximum monthly amount. These are potential matches, not enrollment predictions.'
        })
    except ValueError as exc:
        return error(exc)
    except Exception as exc:
        return error(f'Course-demand lookup failed: {exc}', 503)


@course_bp.get('/api/studio/trending')
def trending():
    db = PostgresDB()
    try:
        # Two separate views: one score for a goal, and one for resource-topic affinity.
        # No cross-joining multiple interaction tables; no duplicate event counts.
        goals = json_rows(db.query("""
            SELECT exam_goal, post_count, likes, shares, comments, saves, reposts, trending_score
            FROM course_goal_trending
            ORDER BY trending_score DESC, post_count DESC, exam_goal ASC
        """))
        resources = json_rows(db.query("""
            SELECT resource_id, provider_name, title, exam_goal, topic, monthly_cost,
                   likes, shares, comments, saves, reposts, trending_score
            FROM course_resource_trending
            ORDER BY trending_score DESC, title ASC, resource_id ASC
        """))
        return success({'goals': goals, 'resources': resources,
            'weights': {'like': 1, 'share': 2, 'comment': 4, 'save': 3, 'repost': 5},
            'note': 'Resources inherit the interaction score of posts tagged with the same goal and topic. This is topic popularity, not verified likes for a specific provider.'})
    except Exception as exc:
        return error(f'Could not calculate trends: {exc}. Run python setup_postgres.py to install the new views.', 503)


@course_bp.get('/api/studio/find-course')
def find_course():
    try:
        term = _course_term(request.args.get('course'))
        user_id = str(request.args.get('user_id') or '').strip()
        if not user_id or len(user_id) > 32:
            raise ValueError('Select a student profile to apply its budget.')
        db = PostgresDB()
        students = json_rows(db.query("""
            SELECT sp.user_id,u.user_name,sp.exam_goal,sp.max_monthly_budget
            FROM student_profile sp JOIN engage_user u ON u.user_id=sp.user_id
            WHERE sp.user_id=%s
        """, (user_id,)))
        if not students:
            return error('Student profile not found. Choose a student with a saved learning profile.', 404)
        student = students[0]
        goals = _matching_goals(db, term)
        sort_by = str(request.args.get('sort') or 'trending')
        sort_options = {
            'trending': 'trending_score DESC, quality_score DESC, monthly_cost ASC, title ASC',
            'price_asc': 'monthly_cost ASC, trending_score DESC, title ASC',
            'price_desc': 'monthly_cost DESC, trending_score DESC, title ASC',
            'quality': 'quality_score DESC, trending_score DESC, title ASC'
        }
        if sort_by not in sort_options:
            raise ValueError('Unknown course sort order')
        mode = str(request.args.get('mode') or 'all')
        if mode not in {'all','online','offline','hybrid'}:
            raise ValueError('Unknown delivery mode')
        # Direct exam-goal searches (e.g., JEE) return the entire catalog for that goal.
        # Topic searches (e.g., physics) narrow resources to matching titles/topics.
        is_goal_search = any(term.casefold() == goal.strip().casefold() for goal in goals)
        resources = json_rows(db.query(f"""
            SELECT resource_id, provider_name, title, exam_goal, topic, resource_type,
                delivery_mode, monthly_cost, quality_score, scholarship_available,
                description, resource_url,
                likes, shares, comments, saves, reposts, trending_score
            FROM course_resource_trending
            WHERE LOWER(TRIM(exam_goal)) = ANY(%s::text[])
              AND monthly_cost <= %s
              AND (%s = 'all' OR delivery_mode = %s)
              AND (%s OR POSITION(LOWER(%s) IN LOWER(exam_goal)) > 0
                OR POSITION(LOWER(%s) IN LOWER(title)) > 0
                OR POSITION(LOWER(%s) IN LOWER(topic)) > 0)
            ORDER BY {sort_options[sort_by]}
        """, ([g.lower().strip() for g in goals], student['max_monthly_budget'], mode, mode, is_goal_search, term, term, term)))
        return success({'query': term, 'matched_goals': goals, 'profile': student,
                        'available_count': len(resources), 'resources': resources, 'sort': sort_by, 'mode': mode,
                        'note': 'Within the selected student\'s stated monthly budget, ranked by interest in the tagged topic. No provider-specific engagement is implied.'})
    except ValueError as exc:
        return error(exc)
    except Exception as exc:
        return error(f'Course finder failed: {exc}. Run python setup_postgres.py to install the new views.', 503)
