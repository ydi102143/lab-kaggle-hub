from fastapi import APIRouter, Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates

from .db import get_conn

router = APIRouter()
templates = Jinja2Templates(directory="app/templates")

@router.get("/", response_class=HTMLResponse)
def index(request: Request):
    """Run一覧（最新20件）"""
    with get_conn() as conn:
        cur = conn.cursor()
        cur.execute(
            """
            SELECT id, status, score, created_at
            FROM run
            ORDER BY created_at DESC
            LIMIT 20
            """
        )
        rows = cur.fetchall()
        runs = [
            {
                "id": r[0],
                "status": r[1],
                "score": r[2],
                "created_at": r[3],
            }
            for r in rows
        ]
    return templates.TemplateResponse("index.html", {"request": request, "runs": runs})

@router.get("/runs/{run_id}", response_class=HTMLResponse)
def run_detail(run_id: str, request: Request):
    """Run詳細 + Artifacts"""
    with get_conn() as conn:
        cur = conn.cursor()
        cur.execute(
            """
            SELECT id, project_id, status, score, params_json, cv_json, created_at, finished_at
            FROM run
            WHERE id = %s
            """,
            (run_id,),
        )
        row = cur.fetchone()
        run = None
        artifacts = []
        if row:
            run = {
                "id": row[0],
                "project_id": row[1],
                "status": row[2],
                "score": row[3],
                "params_json": row[4],
                "cv_json": row[5],
                "created_at": row[6],
                "finished_at": row[7],
            }
            cur.execute(
                """
                SELECT id, type, uri, created_at
                FROM artifact
                WHERE run_id = %s
                ORDER BY created_at ASC
                """,
                (run_id,),
            )
            artifacts = [
                {"id": a[0], "type": a[1], "uri": a[2], "created_at": a[3]} for a in cur.fetchall()
            ]

    return templates.TemplateResponse(
        "run_detail.html",
        {"request": request, "run": run, "artifacts": artifacts},
    )
