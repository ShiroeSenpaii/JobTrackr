# JobTrackr

JobTrackr is a portfolio-ready beginner backend project for tracking job applications with FastAPI + PostgreSQL using **raw SQL** (`psycopg`) and no ORM.

## Stack

- Python 3.11
- FastAPI
- PostgreSQL (via Docker Compose)
- psycopg (parameterized SQL everywhere)

## Project Structure

```text
app/
  main.py
  db.py
  routes/
    applications.py
    reports.py
sql/
  schema.sql
  reports.sql
scripts/
  init_db.py
tests/
  test_reports.py
docker-compose.yml
requirements.txt
README.md
```

## 1) Run in GitHub Codespaces (exact steps)

1. Create/open this repository in **GitHub Codespaces**.
2. Open a terminal in the Codespace.
3. Start PostgreSQL:
   ```bash
   docker-compose up -d
   ```
4. Create and activate a virtual environment:
   ```bash
   python3.11 -m venv .venv
   source .venv/bin/activate
   ```
5. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```
6. Set environment variable (optional if using defaults):
   ```bash
   export DATABASE_URL="postgresql://postgres:postgres@localhost:5432/jobtrackr"
   ```
7. Initialize DB schema:
   ```bash
   python scripts/init_db.py
   ```
8. Run API:
   ```bash
   uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
   ```
9. Open docs:
   - `https://<your-codespace-name>-8000.app.github.dev/docs`

## API Endpoints

### Create company
```bash
curl -X POST http://localhost:8000/companies \
  -H "Content-Type: application/json" \
  -d '{"name":"Acme","website":"https://acme.com"}'
```

### Create role
```bash
curl -X POST http://localhost:8000/roles \
  -H "Content-Type: application/json" \
  -d '{"company_id":1,"title":"Backend Engineer","location":"Remote","remote_flag":true}'
```

### Create application
```bash
curl -X POST http://localhost:8000/applications \
  -H "Content-Type: application/json" \
  -d '{"role_id":1,"status":"applied","applied_date":"2026-01-10","source":"LinkedIn","salary_min":90000,"salary_max":120000}'
```

### Update application
```bash
curl -X PATCH http://localhost:8000/applications/1 \
  -H "Content-Type: application/json" \
  -d '{"status":"interview","salary_min":95000,"salary_max":130000}'
```

### Add event
```bash
curl -X POST http://localhost:8000/applications/1/events \
  -H "Content-Type: application/json" \
  -d '{"event_type":"reply","event_date":"2026-01-12","notes":"Recruiter replied"}'
```

### Add task
```bash
curl -X POST http://localhost:8000/applications/1/tasks \
  -H "Content-Type: application/json" \
  -d '{"due_date":"2026-01-15","done":false,"text":"Send follow-up"}'
```

### Reports
```bash
curl http://localhost:8000/reports/funnel
curl "http://localhost:8000/reports/weekly?weeks=8"
curl http://localhost:8000/reports/time-to-response
curl http://localhost:8000/reports/overdue-tasks
```

## Testing

Make sure PostgreSQL is running and schema can be created in your target database.

```bash
pytest -q
```

## Notes

- Uses foreign keys for relational integrity.
- Indexes included for report performance:
  - `events.application_id`
  - `tasks.application_id`
  - `applications.applied_date`
  - `applications.status`
- SQL for reports is documented in `sql/reports.sql` and implemented in `app/routes/reports.py`.
