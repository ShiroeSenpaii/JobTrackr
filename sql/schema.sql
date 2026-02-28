CREATE TABLE IF NOT EXISTS companies (
    id BIGSERIAL PRIMARY KEY,
    name TEXT NOT NULL,
    website TEXT
);

CREATE TABLE IF NOT EXISTS roles (
    id BIGSERIAL PRIMARY KEY,
    company_id BIGINT NOT NULL REFERENCES companies(id) ON DELETE CASCADE,
    title TEXT NOT NULL,
    location TEXT,
    remote_flag BOOLEAN NOT NULL DEFAULT FALSE
);

CREATE TABLE IF NOT EXISTS applications (
    id BIGSERIAL PRIMARY KEY,
    role_id BIGINT NOT NULL REFERENCES roles(id) ON DELETE CASCADE,
    status TEXT NOT NULL,
    applied_date DATE NOT NULL,
    source TEXT,
    salary_min INTEGER,
    salary_max INTEGER
);

CREATE TABLE IF NOT EXISTS events (
    id BIGSERIAL PRIMARY KEY,
    application_id BIGINT NOT NULL REFERENCES applications(id) ON DELETE CASCADE,
    event_type TEXT NOT NULL,
    event_date DATE NOT NULL,
    notes TEXT
);

CREATE TABLE IF NOT EXISTS tasks (
    id BIGSERIAL PRIMARY KEY,
    application_id BIGINT NOT NULL REFERENCES applications(id) ON DELETE CASCADE,
    due_date DATE NOT NULL,
    done BOOLEAN NOT NULL DEFAULT FALSE,
    text TEXT NOT NULL
);

CREATE INDEX IF NOT EXISTS idx_events_application_id ON events(application_id);
CREATE INDEX IF NOT EXISTS idx_tasks_application_id ON tasks(application_id);
CREATE INDEX IF NOT EXISTS idx_applications_applied_date ON applications(applied_date);
CREATE INDEX IF NOT EXISTS idx_applications_status ON applications(status);
