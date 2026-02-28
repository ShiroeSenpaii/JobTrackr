from datetime import date
from typing import Any, Optional

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field, model_validator
from psycopg.errors import ForeignKeyViolation

from app.db import get_conn

router = APIRouter(tags=["applications"])


class CompanyCreate(BaseModel):
    name: str = Field(min_length=1)
    website: Optional[str] = None


class RoleCreate(BaseModel):
    company_id: int
    title: str = Field(min_length=1)
    location: Optional[str] = None
    remote_flag: bool = False


class ApplicationCreate(BaseModel):
    role_id: int
    status: str = Field(min_length=1)
    applied_date: date
    source: Optional[str] = None
    salary_min: Optional[int] = None
    salary_max: Optional[int] = None

    @model_validator(mode="after")
    def validate_salary_range(self):
        if self.salary_min is not None and self.salary_max is not None and self.salary_min > self.salary_max:
            raise ValueError("salary_min cannot be greater than salary_max")
        return self


class ApplicationUpdate(BaseModel):
    role_id: Optional[int] = None
    status: Optional[str] = None
    applied_date: Optional[date] = None
    source: Optional[str] = None
    salary_min: Optional[int] = None
    salary_max: Optional[int] = None

    @model_validator(mode="after")
    def validate_salary_range(self):
        if self.salary_min is not None and self.salary_max is not None and self.salary_min > self.salary_max:
            raise ValueError("salary_min cannot be greater than salary_max")
        return self


class EventCreate(BaseModel):
    event_type: str = Field(min_length=1)
    event_date: date
    notes: Optional[str] = None


class TaskCreate(BaseModel):
    due_date: date
    done: bool = False
    text: str = Field(min_length=1)


@router.post("/companies")
def create_company(payload: CompanyCreate) -> dict[str, Any]:
    query = """
        INSERT INTO companies (name, website)
        VALUES (%s, %s)
        RETURNING id, name, website
    """
    with get_conn() as conn, conn.cursor() as cur:
        cur.execute(query, (payload.name, payload.website))
        created = cur.fetchone()

    return created


@router.post("/roles")
def create_role(payload: RoleCreate) -> dict[str, Any]:
    query = """
        INSERT INTO roles (company_id, title, location, remote_flag)
        VALUES (%s, %s, %s, %s)
        RETURNING id, company_id, title, location, remote_flag
    """
    try:
        with get_conn() as conn, conn.cursor() as cur:
            cur.execute(
                query,
                (payload.company_id, payload.title, payload.location, payload.remote_flag),
            )
            created = cur.fetchone()
    except ForeignKeyViolation as exc:
        raise HTTPException(status_code=400, detail="Invalid company_id") from exc

    return created


@router.post("/applications")
def create_application(payload: ApplicationCreate) -> dict[str, Any]:
    query = """
        INSERT INTO applications (role_id, status, applied_date, source, salary_min, salary_max)
        VALUES (%s, %s, %s, %s, %s, %s)
        RETURNING id, role_id, status, applied_date, source, salary_min, salary_max
    """
    try:
        with get_conn() as conn, conn.cursor() as cur:
            cur.execute(
                query,
                (
                    payload.role_id,
                    payload.status,
                    payload.applied_date,
                    payload.source,
                    payload.salary_min,
                    payload.salary_max,
                ),
            )
            created = cur.fetchone()
    except ForeignKeyViolation as exc:
        raise HTTPException(status_code=400, detail="Invalid role_id") from exc

    return created


@router.patch("/applications/{application_id}")
def update_application(application_id: int, payload: ApplicationUpdate) -> dict[str, Any]:
    data = payload.model_dump(exclude_none=True)
    if not data:
        raise HTTPException(status_code=400, detail="No fields provided for update")

    allowed_fields = {"role_id", "status", "applied_date", "source", "salary_min", "salary_max"}
    set_clauses = []
    values: list[Any] = []
    for field, value in data.items():
        if field not in allowed_fields:
            raise HTTPException(status_code=400, detail=f"Unsupported field: {field}")
        set_clauses.append(f"{field} = %s")
        values.append(value)

    values.append(application_id)

    query = f"""
        UPDATE applications
        SET {', '.join(set_clauses)}
        WHERE id = %s
        RETURNING id, role_id, status, applied_date, source, salary_min, salary_max
    """

    try:
        with get_conn() as conn, conn.cursor() as cur:
            cur.execute(query, tuple(values))
            updated = cur.fetchone()
    except ForeignKeyViolation as exc:
        raise HTTPException(status_code=400, detail="Invalid role_id") from exc

    if not updated:
        raise HTTPException(status_code=404, detail="Application not found")

    return updated


@router.post("/applications/{application_id}/events")
def create_event(application_id: int, payload: EventCreate) -> dict[str, Any]:
    query = """
        INSERT INTO events (application_id, event_type, event_date, notes)
        VALUES (%s, %s, %s, %s)
        RETURNING id, application_id, event_type, event_date, notes
    """
    try:
        with get_conn() as conn, conn.cursor() as cur:
            cur.execute(
                query,
                (application_id, payload.event_type, payload.event_date, payload.notes),
            )
            created = cur.fetchone()
    except ForeignKeyViolation as exc:
        raise HTTPException(status_code=400, detail="Invalid application_id") from exc

    return created


@router.post("/applications/{application_id}/tasks")
def create_task(application_id: int, payload: TaskCreate) -> dict[str, Any]:
    query = """
        INSERT INTO tasks (application_id, due_date, done, text)
        VALUES (%s, %s, %s, %s)
        RETURNING id, application_id, due_date, done, text
    """
    try:
        with get_conn() as conn, conn.cursor() as cur:
            cur.execute(
                query,
                (application_id, payload.due_date, payload.done, payload.text),
            )
            created = cur.fetchone()
    except ForeignKeyViolation as exc:
        raise HTTPException(status_code=400, detail="Invalid application_id") from exc

    return created
