import os
import uuid
from datetime import date, timedelta
from urllib.parse import parse_qsl, urlencode, urlparse, urlunparse

import pytest
from fastapi.testclient import TestClient
from psycopg import connect

from app.main import app


@pytest.fixture(scope="module")
def test_client():
    base_url = os.getenv("TEST_DATABASE_URL", os.getenv("DATABASE_URL", "postgresql://postgres:postgres@localhost:5432/jobtrackr"))
    schema_name = f"test_{uuid.uuid4().hex[:8]}"

    with connect(base_url) as admin_conn:
        with admin_conn.cursor() as cur:
            cur.execute(f'CREATE SCHEMA "{schema_name}"')
            cur.execute(f'SET search_path TO "{schema_name}"')
            schema_sql = open("sql/schema.sql", "r", encoding="utf-8").read()
            cur.execute(schema_sql)
        admin_conn.commit()

    parsed = urlparse(base_url)
    params = dict(parse_qsl(parsed.query, keep_blank_values=True))
    params["options"] = f"-csearch_path={schema_name}"
    scoped_url = urlunparse(parsed._replace(query=urlencode(params)))

    old_database_url = os.environ.get("DATABASE_URL")
    os.environ["DATABASE_URL"] = scoped_url

    client = TestClient(app)

    yield client

    if old_database_url is None:
        os.environ.pop("DATABASE_URL", None)
    else:
        os.environ["DATABASE_URL"] = old_database_url

    with connect(base_url) as admin_conn:
        with admin_conn.cursor() as cur:
            cur.execute(f'DROP SCHEMA IF EXISTS "{schema_name}" CASCADE')
        admin_conn.commit()


def _seed_minimal_data(client: TestClient):
    company = client.post("/companies", json={"name": "Acme", "website": "https://acme.test"}).json()
    role = client.post(
        "/roles",
        json={
            "company_id": company["id"],
            "title": "Backend Engineer",
            "location": "Remote",
            "remote_flag": True,
        },
    ).json()

    applied_day = date.today() - timedelta(days=6)
    app_1 = client.post(
        "/applications",
        json={
            "role_id": role["id"],
            "status": "applied",
            "applied_date": applied_day.isoformat(),
            "source": "LinkedIn",
            "salary_min": 90000,
            "salary_max": 120000,
        },
    ).json()
    app_2 = client.post(
        "/applications",
        json={
            "role_id": role["id"],
            "status": "interview",
            "applied_date": (applied_day - timedelta(days=7)).isoformat(),
            "source": "Referral",
            "salary_min": 100000,
            "salary_max": 140000,
        },
    ).json()

    client.post(
        f"/applications/{app_1['id']}/events",
        json={"event_type": "reply", "event_date": (applied_day + timedelta(days=2)).isoformat(), "notes": "Recruiter reply"},
    )
    client.post(
        f"/applications/{app_2['id']}/events",
        json={"event_type": "interview", "event_date": (applied_day - timedelta(days=4)).isoformat(), "notes": "Phone screen"},
    )

    client.post(
        f"/applications/{app_1['id']}/tasks",
        json={"due_date": (date.today() - timedelta(days=1)).isoformat(), "done": False, "text": "Follow up email"},
    )


def test_reports_endpoints(test_client: TestClient):
    _seed_minimal_data(test_client)

    funnel = test_client.get("/reports/funnel")
    assert funnel.status_code == 200
    funnel_data = {item["status"]: item["count"] for item in funnel.json()["funnel"]}
    assert funnel_data["applied"] == 1
    assert funnel_data["interview"] == 1

    weekly = test_client.get("/reports/weekly?weeks=4")
    assert weekly.status_code == 200
    assert weekly.json()["weeks"] == 4
    assert len(weekly.json()["data"]) == 4

    ttr = test_client.get("/reports/time-to-response")
    assert ttr.status_code == 200
    assert ttr.json()["avg_days_to_response"] >= 0

    overdue = test_client.get("/reports/overdue-tasks")
    assert overdue.status_code == 200
    assert overdue.json()["count"] == 1
    assert overdue.json()["tasks"][0]["text"] == "Follow up email"
