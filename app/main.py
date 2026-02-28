from fastapi import FastAPI

from app.routes import applications, reports

app = FastAPI(title="JobTrackr", version="0.1.0")

app.include_router(applications.router)
app.include_router(reports.router)


@app.get("/health")
def healthcheck() -> dict[str, str]:
    return {"status": "ok"}
