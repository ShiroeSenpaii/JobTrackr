-- Funnel report: count applications by current status.
SELECT status, COUNT(*)::BIGINT AS count
FROM applications
GROUP BY status
ORDER BY count DESC, status ASC;

-- Weekly report: applications and interview events per week.
WITH weeks AS (
    SELECT generate_series(
        date_trunc('week', CURRENT_DATE) - (%(weeks)s::INT - 1) * INTERVAL '1 week',
        date_trunc('week', CURRENT_DATE),
        INTERVAL '1 week'
    )::DATE AS week_start
),
apps AS (
    SELECT date_trunc('week', applied_date)::DATE AS week_start,
           COUNT(*)::BIGINT AS applications_count
    FROM applications
    WHERE applied_date >= date_trunc('week', CURRENT_DATE) - (%(weeks)s::INT - 1) * INTERVAL '1 week'
    GROUP BY 1
),
interviews AS (
    SELECT date_trunc('week', e.event_date)::DATE AS week_start,
           COUNT(*)::BIGINT AS interviews_count
    FROM events e
    WHERE e.event_type = 'interview'
      AND e.event_date >= date_trunc('week', CURRENT_DATE) - (%(weeks)s::INT - 1) * INTERVAL '1 week'
    GROUP BY 1
)
SELECT w.week_start,
       COALESCE(a.applications_count, 0) AS applications_count,
       COALESCE(i.interviews_count, 0) AS interviews_count
FROM weeks w
LEFT JOIN apps a USING (week_start)
LEFT JOIN interviews i USING (week_start)
ORDER BY w.week_start;

-- Average days from application to first reply.
SELECT COALESCE(AVG(first_reply.event_date - a.applied_date), 0)::FLOAT8 AS avg_days_to_response
FROM applications a
JOIN LATERAL (
    SELECT e.event_date
    FROM events e
    WHERE e.application_id = a.id
      AND e.event_type IN ('reply', 'phone_screen', 'interview', 'offer', 'rejection')
    ORDER BY e.event_date ASC
    LIMIT 1
) AS first_reply ON TRUE;

-- Overdue tasks report.
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
ORDER BY t.due_date ASC;
