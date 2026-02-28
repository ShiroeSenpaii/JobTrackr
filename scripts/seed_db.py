from datetime import date, timedelta

from psycopg import connect

from app.db import get_database_url


def main() -> None:
    with connect(get_database_url()) as conn:
        with conn.cursor() as cur:
            cur.execute("INSERT INTO companies (name, website) VALUES (%s, %s) RETURNING id", ("Acme", "https://acme.com"))
            company_id = cur.fetchone()[0]

            cur.execute(
                "INSERT INTO roles (company_id, title, location, remote_flag) VALUES (%s, %s, %s, %s) RETURNING id",
                (company_id, "Backend Engineer", "Remote", True),
            )
            role_id = cur.fetchone()[0]

            cur.execute(
                """
                INSERT INTO applications (role_id, status, applied_date, source, salary_min, salary_max)
                VALUES (%s, %s, %s, %s, %s, %s)
                RETURNING id
                """,
                (role_id, "applied", date.today() - timedelta(days=5), "LinkedIn", 90000, 120000),
            )
            app_id = cur.fetchone()[0]

            cur.execute(
                "INSERT INTO events (application_id, event_type, event_date, notes) VALUES (%s, %s, %s, %s)",
                (app_id, "reply", date.today() - timedelta(days=3), "Initial recruiter response"),
            )
            cur.execute(
                "INSERT INTO tasks (application_id, due_date, done, text) VALUES (%s, %s, %s, %s)",
                (app_id, date.today() + timedelta(days=2), False, "Prepare for phone screen"),
            )
        conn.commit()

    print("Seed data inserted.")


if __name__ == "__main__":
    main()
