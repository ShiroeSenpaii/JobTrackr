from fastapi import APIRouter, Query

from app.db import get_conn

router = APIRouter(prefix="/reports", tags=["reports"])


@router.get("/funnel")
def report_funnel() -> dict:
    query = """
        SELECT status, COUNT(*)::BIGINT AS count
        FROM applications
        GROUP BY status
        ORDER BY count DESC, status ASC
    """
    with get_conn() as conn, conn.cursor() as cur:
        cur.execute(query)
        rows = cur.fetchall()
    return {"funnel": rows}


@router.get("/weekly")
def report_weekly(weeks: int = Query(default=8, ge=1, le=52)) -> dict:
    query = """
        WITH weekly_series AS (
            SELECT generate_series(
                date_trunc('week', CURRENT_DATE) - (%s::INT - 1) * INTERVAL '1 week',
                date_trunc('week', CURRENT_DATE),
                INTERVAL '1 week'
            )::DATE AS week_start
        ),
        weekly_apps AS (
            SELECT date_trunc('week', applied_date)::DATE AS week_start,
                   COUNT(*)::BIGINT AS applications_count
            FROM applications
            WHERE applied_date >= date_trunc('week', CURRENT_DATE) - (%s::INT - 1) * INTERVAL '1 week'
            GROUP BY 1
        ),
        weekly_interviews AS (
            SELECT date_trunc('week', e.event_date)::DATE AS week_start,
                   COUNT(*)::BIGINT AS interviews_count
            FROM events e
            WHERE e.event_type = 'interview'
              AND e.event_date >= date_trunc('week', CURRENT_DATE) - (%s::INT - 1) * INTERVAL '1 week'
            GROUP BY 1
        )
        SELECT s.week_start,
               COALESCE(a.applications_count, 0) AS applications_count,
               COALESCE(i.interviews_count, 0) AS interviews_count
        FROM weekly_series s
        LEFT JOIN weekly_apps a USING (week_start)
        LEFT JOIN weekly_interviews i USING (week_start)
        ORDER BY s.week_start
    """
    with get_conn() as conn, conn.cursor() as cur:
        cur.execute(query, (weeks, weeks, weeks))
        rows = cur.fetchall()
    return {"weeks": weeks, "data": rows}


@router.get("/time-to-response")
def report_time_to_response() -> dict:
    query = """
        SELECT COALESCE(AVG(first_reply.event_date - a.applied_date), 0)::FLOAT8 AS avg_days_to_response
        FROM applications a
        JOIN LATERAL (
            SELECT e.event_date
            FROM events e
            WHERE e.application_id = a.id
              AND e.event_type IN ('reply', 'phone_screen', 'interview', 'offer', 'rejection')
            ORDER BY e.event_date ASC
            LIMIT 1
        ) AS first_reply ON TRUE
    """
    with get_conn() as conn, conn.cursor() as cur:
        cur.execute(query)
        row = cur.fetchone()
    return row


@router.get("/overdue-tasks")
def report_overdue_tasks() -> dict:
    query = """
        SELECT t.id,
               t.application_id,
               t.due_date,
               t.done,
               t.text,
               a.status,
               r.title AS role_title,
               c.name AS company_name
        FROM tasks t
        JOIN applications a ON a.id = t.application_id
        JOIN roles r ON r.id = a.role_id
        JOIN companies c ON c.id = r.company_id
        WHERE t.done = FALSE
          AND t.due_date < CURRENT_DATE
        ORDER BY t.due_date ASC
    """
    with get_conn() as conn, conn.cursor() as cur:
        cur.execute(query)
        rows = cur.fetchall()

    return {"count": len(rows), "tasks": rows}
