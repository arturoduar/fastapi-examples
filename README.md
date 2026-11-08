# fastapi_examples — a tour of FastAPI server features

One small application, organised as routers that each demonstrate a feature, with a
test file for every router.

| router | prefix | shows |
|--------|--------|-------|
| `basics.py`     | `/basics`     | path/query/header params, validation constraints, enums, `:path` converter, JSON body |
| `items.py`      | `/items`      | CRUD, response models, 201/204/404/409, pagination, filtering, sorting, PUT vs PATCH, role-protected DELETE |
| `auth.py`       | `/auth`       | registration, OAuth2 password flow → JWT, `Depends` chains, role checks (401 vs 403) |
| `background.py` | `/background` | `BackgroundTasks` (work after the response) |
| `streaming.py`  | `/stream`     | `StreamingResponse`, server-sent events, WebSocket echo |
| `uploads.py`    | `/uploads`    | `UploadFile` with a size limit, form fields |

Cross-cutting pieces in `main.py`: application factory (`create_app`), lifespan hook,
HTTP middleware (`X-Process-Time` header), exception handlers that turn domain errors
(`NotFoundError`, `DuplicateError`) into 404/409. Shared dependencies live in `deps.py`;
`store.py` is an in-memory stand-in for a database.

## Run it

```bash
cd 2026/fastapi_examples
python -m venv .venv && source .venv/bin/activate
pip install -e ".[dev]"

uvicorn app.main:app --reload        # http://127.0.0.1:8000/docs  (interactive Swagger UI)
pytest                               # run the tests
```

Settings come from environment variables: `APP_SECRET_KEY` (JWT signing key — **set it
to a long random value outside local experiments**), `APP_TOKEN_MINUTES`,
`APP_SEED_DEMO_DATA`.

Demo accounts (seeded when `APP_SEED_DEMO_DATA` is true, local use only):
`alice` / `alice-password` (role user), `admin` / `admin-password` (role admin).

## Try it with curl

```bash
curl 'localhost:8000/basics/search?q=foo&tags=a&tags=b&limit=5'
curl -X POST localhost:8000/basics/echo -H 'content-type: application/json' -d '{"text":"ab","repeat":3}'

curl 'localhost:8000/items?tag=tech&sort=price&limit=2'
curl -X POST localhost:8000/items -H 'content-type: application/json' \
     -d '{"name":"Thing","price":5.0,"tags":["x"]}'
curl -X PATCH localhost:8000/items/1 -H 'content-type: application/json' -d '{"price":11}'

TOKEN=$(curl -s -d 'username=admin&password=admin-password' localhost:8000/auth/token | python -c 'import sys,json;print(json.load(sys.stdin)["access_token"])')
curl -H "Authorization: Bearer $TOKEN" localhost:8000/auth/me
curl -X DELETE -H "Authorization: Bearer $TOKEN" localhost:8000/items/1 -i     # 204

curl -N 'localhost:8000/stream/sse?n=3'
curl -F 'file=@README.md' localhost:8000/uploads/file
```

## Testing patterns used (`tests/`)

* `conftest.py` — a **fresh app per test** via `create_app(settings)` (cheap password hashing, isolated in-memory data), a `TestClient` used as a context manager so the lifespan runs, and `login` / `user_headers` / `admin_headers` fixtures.
* Validation tests assert 422 and the location of the error; auth tests cover missing, malformed, forged, expired and orphaned tokens and 401-vs-403.
* `test_app.py` shows `app.dependency_overrides`, lifespan events, middleware headers and the OpenAPI schema.
* `test_units.py` tests the stores, hashing, JWT and settings without HTTP.
* WebSocket test uses `client.websocket_connect`.

## Verification status

FastAPI and httpx could not be installed where this was written (no package index
access), so **the tests have not been run against real FastAPI**. They were run — 74 passed — against a small throwaway
stand-in that implements the same decorators, `Depends`, parameter validation, response
models, background tasks, WebSockets and a test client on top of the installed Starlette
and pydantic. That checks the application logic and tests, not every FastAPI detail
(for instance exact 422 error messages, or generated OpenAPI contents). If something fails
on first `pytest`, it is most likely such a detail; send me the output.
