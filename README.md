# FlyRank Task API

A small in-memory task CRUD API built for the FlyRank Backend AI assignment. The repository provided for this work was empty, so no prior implementation or assignment-specific error format was available to preserve.

## Features and stack

- FastAPI with interactive Swagger UI and an OpenAPI schema.
- In-memory task storage, initialized with three sample tasks.
- Create, list, retrieve, update, and delete operations.
- Strict title and completion-status validation; invalid requests return HTTP 400.
- Pytest coverage using a fresh application instance per test.

## Local setup

Python 3.11 or newer is recommended.

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -r requirements-dev.txt
```

Start the API:

```powershell
python -m uvicorn main:app --reload
```

Run the tests:

```powershell
python -m pytest -q
```

## Endpoints

| Method | Path | Purpose | Successful status |
| --- | --- | --- | --- |
| GET | `/` | Service name, version, and endpoint list | 200 |
| GET | `/health` | Health check | 200 |
| GET | `/tasks` | List all tasks | 200 |
| GET | `/tasks/{task_id}` | Retrieve one task | 200 |
| POST | `/tasks` | Create a task | 201 |
| PUT | `/tasks/{task_id}` | Update title, done, or both | 200 |
| DELETE | `/tasks/{task_id}` | Delete a task | 204 (empty body) |

Unknown IDs return `404` with `{"detail":"Task not found"}`. Invalid or missing request bodies and invalid fields return `400` with a JSON `detail` error. Task titles must be strings containing at least one non-whitespace character; `done` must be a JSON boolean.

### Request examples

Create a task:

```json
{"title": "Write documentation"}
```

Update either field or both:

```json
{"title": "Review documentation", "done": true}
```

```json
{"done": true}
```

The API assigns IDs in increasing order, starts with IDs 1–3, and sets `done` to `false` for new tasks.

## Local API and captured HTTP evidence

Run the server with `python -m uvicorn main:app --reload`, then use:

```powershell
curl.exe -i http://127.0.0.1:8000/
curl.exe -i http://127.0.0.1:8000/health
curl.exe -i http://127.0.0.1:8000/tasks
curl.exe -i http://127.0.0.1:8000/tasks/999
curl.exe -i -X POST http://127.0.0.1:8000/tasks -H "Content-Type: application/json" --data-binary '{"title":"curl verification"}'
curl.exe -i -X PUT http://127.0.0.1:8000/tasks/4 -H "Content-Type: application/json" --data-binary '{"done":true}'
curl.exe -i -X DELETE http://127.0.0.1:8000/tasks/4
curl.exe -i http://127.0.0.1:8000/docs
curl.exe -i http://127.0.0.1:8000/openapi.json
```

The following status codes and bodies were captured from the running local Uvicorn server with `curl.exe -i` (the changing `Date` header is omitted):

```text
GET /                 HTTP/1.1 200 OK
{"name":"Task API","version":"1.0","endpoints":["/tasks"]}

GET /health           HTTP/1.1 200 OK
{"status":"ok"}

GET /tasks            HTTP/1.1 200 OK
[{"id":1,"title":"Buy groceries","done":false},{"id":2,"title":"Walk the dog","done":true},{"id":3,"title":"Read a book","done":false}]

GET /tasks/999        HTTP/1.1 404 Not Found
{"detail":"Task not found"}

POST /tasks           HTTP/1.1 201 Created
{"id":4,"title":"curl verification","done":false}

PUT /tasks/4           HTTP/1.1 200 OK
{"id":4,"title":"curl verification","done":true}

DELETE /tasks/4        HTTP/1.1 204 No Content
(empty response body)

POST /tasks (blank title) HTTP/1.1 400 Bad Request
{"detail":[{"type":"value_error","loc":["body","title"],"msg":"Value error, title must not be blank","input":"   ","ctx":{"error":{}}}]}

GET /docs              HTTP 200; content-type text/html; charset=utf-8
GET /openapi.json      HTTP 200; content-type application/json
```

Interactive Swagger documentation: `http://127.0.0.1:8000/docs`  
OpenAPI JSON: `http://127.0.0.1:8000/openapi.json`

## Deployment

[`render.yaml`](./render.yaml) configures a Render free web service, with `pip install -r requirements.txt` as its build command and Uvicorn bound to `0.0.0.0:$PORT`.

To deploy:

1. Sign in to Render and choose **New > Blueprint**.
2. Connect the existing [GitHub repository](https://github.com/RifatSadik22/FlyRankAi_Internship_BackendAi) and select the `main` branch.
3. Review the Blueprint and confirm the web service uses the `free` plan in `render.yaml`.
4. Create the Blueprint, wait for the deploy to finish, and copy the service's assigned `https://...onrender.com` URL.
5. Verify `/`, `/health`, `/tasks`, `/docs`, and `/openapi.json` on that real URL.

Render documents a free web-service tier, including spin-down after 15 minutes without inbound traffic and a roughly one-minute spin-up on the next request. This API has **not yet been deployed**: Render account access and repository authorization must be completed in the Render dashboard. No public API or Swagger URL is available to report yet. The local endpoints above were verified independently.

## GitHub

Existing repository: <https://github.com/RifatSadik22/FlyRankAi_Internship_BackendAi>

## Assignment evidence and limitations

- The GitHub repository was empty when inspected, and the workspace contained no assignment brief or original/manual implementation. An AI-vs-manual comparison therefore cannot be verified; no differences are claimed.
- No Swagger screenshot was captured. After deployment, open the service's `/docs` page and use your operating system's screenshot tool if screenshot evidence is required.
- Tasks exist only in process memory. They are reset when the process restarts, the service redeploys, or Render spins the free service down. No database or persistent storage is used.
- Render's free services have platform limits and may be unavailable while sleeping; check the provider's current free-tier terms before deployment.
