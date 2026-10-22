from pathlib import Path
import sqlite3

from fastapi import FastAPI, HTTPException, Request
from fastapi.encoders import jsonable_encoder
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse, Response
from pydantic import BaseModel, ConfigDict, StrictBool, StrictStr, field_validator

from database import (
    DEFAULT_DATABASE_PATH,
    database_connection,
    initialize_database,
)


class Task(BaseModel):
    id: int
    title: str
    done: bool


class TaskNotFoundError(Exception):
    pass


def task_from_row(row: sqlite3.Row) -> Task:
    return Task(id=row["id"], title=row["title"], done=bool(row["done"]))


class TaskCreate(BaseModel):
    title: StrictStr

    @field_validator("title")
    @classmethod
    def title_must_not_be_blank(cls, value: str) -> str:
        if not value.strip():
            raise ValueError("title must not be blank")
        return value


class TaskUpdate(BaseModel):
    model_config = ConfigDict(extra="forbid")

    title: StrictStr | None = None
    done: StrictBool | None = None

    @field_validator("title")
    @classmethod
    def title_must_not_be_blank(cls, value: str | None) -> str | None:
        if value is not None and not value.strip():
            raise ValueError("title must not be blank")
        return value


def create_app(database_path: Path = DEFAULT_DATABASE_PATH) -> FastAPI:
    app = FastAPI(title="Task API", version="1.0")
    app.state.database_path = database_path
    initialize_database(database_path)
    app.state.tasks = {
        1: Task(id=1, title="Buy groceries", done=False),
        2: Task(id=2, title="Walk the dog", done=True),
        3: Task(id=3, title="Read a book", done=False),
    }
    app.state.next_task_id = 4

    @app.exception_handler(RequestValidationError)
    async def validation_error_handler(
        _request: Request, exc: RequestValidationError
    ) -> JSONResponse:
        return JSONResponse(
            status_code=400,
            content={"detail": jsonable_encoder(exc.errors())},
        )

    @app.exception_handler(TaskNotFoundError)
    async def task_not_found_handler(
        _request: Request, _exc: TaskNotFoundError
    ) -> JSONResponse:
        return JSONResponse(status_code=404, content={"error": "Task not found"})

    @app.get("/")
    async def root() -> dict[str, object]:
        return {
            "name": "Task API",
            "version": "1.0",
            "endpoints": ["/tasks"],
        }

    @app.get("/health")
    async def health() -> dict[str, str]:
        return {"status": "ok"}

    @app.get("/tasks", response_model=list[Task])
    async def list_tasks() -> list[Task]:
        with database_connection(app.state.database_path) as connection:
            rows = connection.execute("SELECT * FROM tasks ORDER BY id").fetchall()
        return [task_from_row(row) for row in rows]

    @app.get(
        "/tasks/{task_id}",
        response_model=Task,
        responses={
            400: {"description": "Invalid task ID"},
            404: {"description": "Task not found"},
        },
    )
    async def get_task(task_id: int) -> Task:
        with database_connection(app.state.database_path) as connection:
            row = connection.execute(
                "SELECT * FROM tasks WHERE id = ?", (task_id,)
            ).fetchone()
        if row is None:
            raise TaskNotFoundError
        return task_from_row(row)

    @app.post(
        "/tasks",
        status_code=201,
        response_model=Task,
        responses={400: {"description": "Invalid request"}},
    )
    async def create_task(task_data: TaskCreate) -> Task:
        with database_connection(app.state.database_path) as connection:
            cursor = connection.execute(
                "INSERT INTO tasks (title, done) VALUES (?, ?)",
                (task_data.title, 0),
            )
            row = connection.execute(
                "SELECT * FROM tasks WHERE id = ?", (cursor.lastrowid,)
            ).fetchone()
        return task_from_row(row)

    @app.put(
        "/tasks/{task_id}",
        response_model=Task,
        responses={
            400: {"description": "Invalid request or task ID"},
            404: {"description": "Task not found"},
        },
    )
    async def update_task(task_id: int, updates: TaskUpdate) -> Task:
        task = app.state.tasks.get(task_id)
        if task is None:
            raise HTTPException(status_code=404, detail="Task not found")
        if not updates.model_fields_set:
            raise HTTPException(
                status_code=400,
                detail="At least one of title or done must be provided",
            )
        if "title" in updates.model_fields_set and updates.title is None:
            raise HTTPException(status_code=400, detail="title must not be null")
        if "done" in updates.model_fields_set and updates.done is None:
            raise HTTPException(status_code=400, detail="done must not be null")

        changes = updates.model_dump(exclude_unset=True)
        updated_task = task.model_copy(update=changes)
        app.state.tasks[task_id] = updated_task
        return updated_task

    @app.delete(
        "/tasks/{task_id}",
        status_code=204,
        responses={
            400: {"description": "Invalid task ID"},
            404: {"description": "Task not found"},
        },
    )
    async def delete_task(task_id: int) -> Response:
        if task_id not in app.state.tasks:
            raise HTTPException(status_code=404, detail="Task not found")
        del app.state.tasks[task_id]
        return Response(status_code=204)

    return app


app = create_app()
