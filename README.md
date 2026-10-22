# FlyRank Task API — Week 3 Assignment A2

This FastAPI Task API keeps the same routes and task response format as the previous assignment, but stores tasks in SQLite so changes survive an application restart.

## Features and technology

- FastAPI with interactive Swagger UI at `/docs` and OpenAPI JSON at `/openapi.json`.
- Python's built-in `sqlite3` module; no ORM, database server, or database dependency to install.
- SQLite provides a simple, single-file database and persistent storage across process restarts.
- Parameterized SQL for task values and transaction-managed database writes.
- Input validation, JSON error responses, and 41 automated tests.

## Database initialization and location

The database is named `tasks.db` and is stored beside `main.py` at:

```text
<repository root>\tasks.db
```

The application uses an absolute path derived from the source file, not the shell's current directory. On first startup it creates the database file and the `tasks` table automatically:

```sql
CREATE TABLE tasks (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    title TEXT NOT NULL,
    done INTEGER NOT NULL DEFAULT 0 CHECK (done IN (0, 1))
);
```

If the table has zero rows, startup inserts the three sample tasks. Existing rows are not reseeded on later restarts. Database initialization takes a write transaction before checking the row count, so concurrent starts cannot seed duplicates. SQLite stores `done` as `0` or `1`; API responses convert it to a JSON boolean. The database is ignored by Git, so each fresh clone creates its own local file and sample data.

## Local setup

Python 3.10 or newer is required; Python 3.11 is recommended.

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -r requirements-dev.txt
```

Start the application from the repository root:

```powershell
python -m uvicorn main:app --reload
```

This command creates `tasks.db` and its table automatically if needed. Run the test suite with:

```powershell
python -m pytest -q
```

Tests use temporary databases and do not change the development `tasks.db`.

## API endpoints

| Method | Path | Description | Success |
| --- | --- | --- | --- |
| GET | `/` | API name, version, and endpoint list | 200 |
| GET | `/health` | Health check | 200 |
| GET | `/tasks` | List tasks from SQLite | 200 |
| GET | `/tasks/{task_id}` | Retrieve a task from SQLite | 200 |
| POST | `/tasks` | Create a task | 201 |
| PUT | `/tasks/{task_id}` | Update title, done, or both | 200 |
| DELETE | `/tasks/{task_id}` | Delete a task | 204, empty body |

Task objects have the form `{"id": 1, "title": "Buy groceries", "done": false}`. Creation requires a non-blank string title:

```json
{"title": "Prepare a report"}
```

Updates accept either or both supported fields:

```json
{"done": true}
```

```json
{"title": "Report prepared", "done": true}
```

Invalid or empty request bodies return HTTP 400. Unknown task IDs return HTTP 404 with `{"error":"Task not found"}`. Successful deletion returns HTTP 204 with no response body.

Local interactive documentation: <http://127.0.0.1:8000/docs>

Local OpenAPI schema: <http://127.0.0.1:8000/openapi.json>

## HTTP checks and observed results

Start the server, then run these commands in PowerShell:

```powershell
$postBody = Join-Path $env:TEMP "task-create.json"
$putBody = Join-Path $env:TEMP "task-update.json"
$blankBody = Join-Path $env:TEMP "task-blank.json"
ConvertTo-Json -InputObject @{title='SQLite restart evidence'} -Compress | Set-Content -LiteralPath $postBody -Encoding ascii -NoNewline
ConvertTo-Json -InputObject @{done=$true} -Compress | Set-Content -LiteralPath $putBody -Encoding ascii -NoNewline
ConvertTo-Json -InputObject @{title='   '} -Compress | Set-Content -LiteralPath $blankBody -Encoding ascii -NoNewline
curl.exe -sS -i http://127.0.0.1:8000/
curl.exe -sS -i http://127.0.0.1:8000/health
curl.exe -sS -i http://127.0.0.1:8000/tasks
curl.exe -sS -i http://127.0.0.1:8000/tasks/999
curl.exe -sS -i -X POST http://127.0.0.1:8000/tasks -H "Content-Type: application/json" --data-binary "@$postBody"
curl.exe -sS -i -X PUT http://127.0.0.1:8000/tasks/4 -H "Content-Type: application/json" --data-binary "@$putBody"
curl.exe -sS -i -X POST http://127.0.0.1:8000/tasks -H "Content-Type: application/json" --data-binary "@$blankBody"
curl.exe -sS -i -X PUT http://127.0.0.1:8000/tasks/1 -H "Content-Type: application/json" --data-binary '{}'
curl.exe -sS -i -X DELETE http://127.0.0.1:8000/tasks/4
curl.exe -sS -i -o NUL http://127.0.0.1:8000/docs
curl.exe -sS -i -o NUL http://127.0.0.1:8000/openapi.json
```

The JSON request bodies are put in temporary files because Windows PowerShell can strip JSON quote marks when passing inline JSON to a native executable. These responses were captured with `curl.exe -i` from the running local server. The varying `Date` headers are omitted:

On a fresh database, the POST below creates task ID 4. If you have already created tasks, use the ID returned by your POST when running the PUT and DELETE commands.

```text
GET /                 HTTP/1.1 200 OK
{"name":"Task API","version":"1.0","endpoints":["/tasks"]}

GET /health           HTTP/1.1 200 OK
{"status":"ok"}

GET /tasks            HTTP/1.1 200 OK
[{"id":1,"title":"Buy groceries","done":false},{"id":2,"title":"Walk the dog","done":true},{"id":3,"title":"Read a book","done":false}]

GET /tasks/999        HTTP/1.1 404 Not Found
{"error":"Task not found"}

POST /tasks           HTTP/1.1 201 Created
{"id":4,"title":"SQLite restart evidence","done":false}

PUT /tasks/4           HTTP/1.1 200 OK
{"id":4,"title":"SQLite restart evidence","done":true}

POST /tasks (blank title) HTTP/1.1 400 Bad Request
{"detail":[{"type":"value_error","loc":["body","title"],"msg":"Value error, title must not be blank","input":"   ","ctx":{"error":{}}}]}

PUT /tasks/1 (empty body) HTTP/1.1 400 Bad Request
{"detail":"At least one of title or done must be provided"}

GET /tasks/4 after restarting Uvicorn HTTP/1.1 200 OK
{"id":4,"title":"SQLite restart evidence","done":true}

DELETE /tasks/4        HTTP/1.1 204 No Content
(empty response body)

GET /tasks/4 after delete HTTP/1.1 404 Not Found
{"error":"Task not found"}

GET /docs              HTTP 200; content-type text/html; charset=utf-8
GET /openapi.json      HTTP 200; content-type application/json
```

The server was stopped after creating and updating task 4, then restarted against the same `tasks.db`. The task still existed with `done: true`. It was deleted after this check; the local database is back to the three sample tasks.

## SQLite query exploration

[`explore_tasks.sql`](./explore_tasks.sql) contains the read-only queries executed against the application's `tasks.db`:

```sql
SELECT * FROM tasks ORDER BY id;
SELECT * FROM tasks WHERE done = 1 ORDER BY id;
SELECT COUNT(*) FROM tasks;
```

Observed results from that database:

```text
SELECT * FROM tasks ORDER BY id;
[(1, 'Buy groceries', 0), (2, 'Walk the dog', 1), (3, 'Read a book', 0)]

SELECT * FROM tasks WHERE done = 1 ORDER BY id;
[(2, 'Walk the dog', 1)]

SELECT COUNT(*) FROM tasks;
[(3,)]
```

The `UPDATE tasks SET done = 1` and `DELETE FROM tasks WHERE done = 1` examples were run only against a disposable database: the update changed 3 rows, the delete removed 3 rows, and the disposable database ended with 0 rows. The application database was not changed by those destructive checks.

### DB Browser screenshot

DB Browser for SQLite was not installed in the available environment, so no screenshot is included and no DB Browser use is claimed. To capture the requested evidence:

1. Install DB Browser for SQLite from its [official download page](https://sqlitebrowser.org/dl/).
2. Open `tasks.db` in the repository root (`File > Open Database`).
3. In **Browse Data**, select the `tasks` table and capture the table and its rows.
4. In **Execute SQL**, run `SELECT * FROM tasks WHERE done = 1;` and optionally capture that result too.
5. Save the screenshot as `screenshots/database-viewer.png` and add it to the repository if the assignment requires it.

The API and the viewer should show the same file-backed records; the viewer step and screenshot remain manual.

## GitHub and deployment

Public repository: <https://github.com/RifatSadik22/FlyRankAi_Internship_BackendAi>

The repository includes [`render.yaml`](./render.yaml) for an optional Render free web service. Render free services have platform limitations, including spin-down after inactivity; local SQLite files on hosted services may also be ephemeral. No public deployment URL is claimed by this assignment evidence.

## Limitations and assignment notes

- Tasks are local to the SQLite file. Do not delete `tasks.db` if you need to retain its data.
- A new clone has no database file until the application starts; initialization and sample seeding happen automatically.
- The Week 3 assignment PDF was available. It specifies `{"error":"Task not found"}` for an unknown task ID; the implementation and tests use that exact shape.
- No original hand-built Week 2 implementation was present to compare, so no AI-vs-manual differences are claimed.
