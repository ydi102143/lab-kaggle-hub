# lab-kaggle-hub (walking skeleton)

## Quickstart
1) Infra
```
docker compose -f infra/docker-compose.yml up -d
psql -h localhost -U app -d app -f infra/sql/001_init.sql
```

2) API
```
cd app
pip install -U pip poetry
poetry install
cp ../.env.example .env
poetry run uvicorn app.api.main:app --reload --port 8000
```

3) Create project (example)
```
curl -X POST http://localhost:8000/projects -H "Content-Type: application/json" -d '{"org_id":"00000000-0000-0000-0000-000000000000","name":"kaggle-study","metric":"auc"}'
```

4) Create run
```
# save RunConfig as runconfig.json then:
curl -X POST 'http://localhost:8000/runs?project_id=<PROJECT_ID>&pipeline_id=<PIPELINE_ID>' -H "Content-Type: application/json" -d @runconfig.json
```
