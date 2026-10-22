from fastapi import FastAPI, HTTPException, Request
from fastapi.encoders import jsonable_encoder
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse, Response
from pydantic import BaseModel, ConfigDict, StrictBool, StrictStr, field_validator


class Task(BaseModel):
    id: int
    title: str
    done: bool


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


def create_app() -> FastAPI:
    app = FastAPI(title="Task API", version="1.0")
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
        return list(app.state.tasks.values())

    @app.get(
        "/tasks/{task_id}",
        response_model=Task,
        responses={
            400: {"description": "Invalid task ID"},
            404: {"description": "Task not found"},
        },
    )
    async def get_task(task_id: int) -> Task:
        task = app.state.tasks.get(task_id)
        if task is None:
            raise HTTPException(status_code=404, detail="Task not found")
        return task

    @app.post(
        "/tasks",
        status_code=201,
        response_model=Task,
        responses={400: {"description": "Invalid request"}},
    )
    async def create_task(task_data: TaskCreate) -> Task:
        task_id = app.state.next_task_id
        task = Task(id=task_id, title=task_data.title, done=False)
        app.state.tasks[task_id] = task
        app.state.next_task_id += 1
        return task

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
