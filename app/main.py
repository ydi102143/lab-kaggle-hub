import os, json, uuid
from datetime import datetime
from typing import Optional
from fastapi import FastAPI, HTTPException, Query
from pydantic import BaseModel
from .api.db import get_conn
from .api.schemas import RunConfig, RunResult
from .api.storage import ensure_bucket, presign_get, presign_put, S3_BUCKET

app = FastAPI(title="lab-kaggle-hub", version="0.1.0")

@app.on_event("startup")
def _startup():
    ensure_bucket()

class CreateProjectBody(BaseModel):
    org_id: str
    name: str
    competition: Optional[str] = None
    metric: str

@app.post("/projects")
def create_project(body: CreateProjectBody):
    with get_conn() as conn:
        cur = conn.cursor()
        pid = str(uuid.uuid4())
        cur.execute(
            "insert into project (id, org_id, name, competition, metric) values (%s,%s,%s,%s,%s)",
            (pid, body.org_id, body.name, body.competition, body.metric)
        )
    return {"id": pid}

@app.post("/runs")
def create_run(project_id: str, pipeline_id: str, cfg: RunConfig):
    run_id = str(uuid.uuid4())
    with get_conn() as conn:
        cur = conn.cursor()
        cur.execute(
            "insert into run (id, project_id, pipeline_id, params_json, status, seed, runner, created_at) values (%s,%s,%s,%s,%s,%s,%s, now())",
            (run_id, project_id, pipeline_id, json.dumps(cfg.model_dump()), "pending", cfg.seed, "kaggle")
        )
        cur.execute(
            "insert into audit_log(actor_id, action, target, payload) values (NULL, %s, %s, %s)",
            ("create_run", f"run:{run_id}", json.dumps({"project_id": project_id}))
        )

    base_prefix = f"{project_id}/{run_id}/"
    put_urls = {
        "oof": presign_put(base_prefix + "oof.csv"),
        "submission": presign_put(base_prefix + "submission.csv"),
        "model": presign_put(base_prefix + "model.bin"),
        "metrics": presign_put(base_prefix + "metrics.json"),
    }

    kaggle_link = f"https://www.kaggle.com/kernels?src=YOUR_NOTEBOOK_TEMPLATE&runId={run_id}"

    return {
        "run_id": run_id,
        "kaggle_link": kaggle_link,
        "artifact_put_urls": put_urls,
        "artifact_base": f"s3://{S3_BUCKET}/{base_prefix}"
    }

@app.get("/runs")
def list_runs(project_id: str = Query(...)):
    with get_conn() as conn:
        cur = conn.cursor()
        cur.execute(
            "select id, status, score, created_at, finished_at from run where project_id=%s order by created_at desc",
            (project_id,)
        )
        rows = cur.fetchall()
    data = [
        {"id": r[0], "status": r[1], "score": r[2], "created_at": r[3], "finished_at": r[4]}
        for r in rows
    ]
    return {"items": data}

@app.get("/runs/{run_id}")
def get_run(run_id: str):
    with get_conn() as conn:
        cur = conn.cursor()
        cur.execute("select project_id, status, score, params_json, cv_json, started_at, finished_at from run where id=%s", (run_id,))
        row = cur.fetchone()
        if not row:
            raise HTTPException(404, "run not found")
        project_id, status, score, params_json, cv_json, started_at, finished_at = row
        cur.execute("select id, type, uri, meta_json, created_at from artifact where run_id=%s", (run_id,))
        arts = [
            {"id": a[0], "type": a[1], "uri": a[2], "meta": a[3], "created_at": a[4]}
            for a in cur.fetchall()
        ]
    return {
        "id": run_id, "project_id": project_id, "status": status, "score": score,
        "params": params_json, "cv": cv_json, "started_at": started_at, "finished_at": finished_at,
        "artifacts": arts
    }

@app.post("/runs/{run_id}/complete", status_code=204)
def complete_run(run_id: str, result: RunResult):
    with get_conn() as conn:
        cur = conn.cursor()
        def add_artifact(t: str, uri: str):
            cur.execute(
                "insert into artifact (id, run_id, type, uri, meta_json) values (%s,%s,%s,%s,%s)",
                (str(uuid.uuid4()), run_id, t, uri, json.dumps({}))
            )
        arts = result.artifacts
        if "oof" in arts:        add_artifact("oof", arts["oof"])
        if "submission" in arts: add_artifact("submission", arts["submission"])
        if "model" in arts:      add_artifact("model", arts["model"])
        if "metrics" in arts:    add_artifact("metrics", arts["metrics"])
        for p in arts.get("plots", []):
            add_artifact("plot", p)

        cur.execute(
            "update run set status='finished', score=%s, cv_json=%s, finished_at=now() where id=%s",
            (result.score, json.dumps({"folds": result.cv_scores}), run_id)
        )
        cur.execute(
            "insert into audit_log(actor_id, action, target, payload) values (NULL, %s, %s, %s)",
            ("complete_run", f"run:{run_id}", json.dumps({"score": result.score}))
        )
    return

@app.get("/artifacts/{artifact_id}")
def get_artifact_url(artifact_id: str):
    with get_conn() as conn:
        cur = conn.cursor()
        cur.execute("select uri from artifact where id=%s", (artifact_id,))
        row = cur.fetchone()
        if not row:
            raise HTTPException(404, "artifact not found")
        uri = row[0]
    parts = uri.split("/", 3)
    key = parts[3] if len(parts) >= 4 else ""
    return {"url": presign_get(key)}
from .api import ui
app.include_router(ui.router)
