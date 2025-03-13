from fastapi import FastAPI, Request
from starlette import status
from starlette.responses import RedirectResponse

from .database import Base, engine
from .routers.auth import router as auth_router
from .routers.todo import router as todo_router
from fastapi.staticfiles import StaticFiles
import os

script_directory = os.path.dirname(__file__)
static_abs_path = os.path.join(script_directory, 'static/')
app = FastAPI()
app.mount("/static" , StaticFiles(directory=static_abs_path), name="static")

@app.get("/", status_code=status.HTTP_302_FOUND)
def read_root(request: Request):
    return RedirectResponse(url="/todo/todo-page")
app.include_router(auth_router)
app.include_router(todo_router)

Base.metadata.create_all(bind=engine)

