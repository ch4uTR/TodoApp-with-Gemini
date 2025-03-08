from fastapi import APIRouter, Depends, HTTPException, Path, Request
from pydantic import BaseModel, Field
from typing import Annotated
from starlette import status
from sqlalchemy.orm import Session
from database import Base, engine, LocalSession
from models import Todo, User
from routers.auth import  get_current_user
from dotenv import load_dotenv
import os
import google.generativeai as genai
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.messages import HumanMessage, AIMessage
import markdown
from bs4 import BeautifulSoup

from starlette.responses import RedirectResponse
from fastapi.templating import Jinja2Templates
templates = Jinja2Templates(directory="templates")


router = APIRouter(
    prefix="/todo",
    tags=["Todo"]
)


class TodoRequest(BaseModel):
    title: str = Field(min_length=1, max_length=100)
    description: str = Field(min_length=1, max_length=1000)
    priority: int = Field(default=1, gt=0, lt=6)

class TodoUpdateRequest(BaseModel):
    title: str = Field(min_length=1, max_length=100)
    description: str = Field(min_length=1, max_length=1000)
    priority: int = Field(default=1, gt=0, lt=6)
    is_completed: bool = Field(default=False)



def get_db():
    db = LocalSession(bind=engine)
    try:
        yield db
    finally:
        db.close()

db_dependency = Annotated[Session, Depends(get_db)]
user_dependency = Annotated[dict, Depends(get_current_user)]


def redirect_to_login():
    redirect_response = RedirectResponse(url="/auth/login-page", status_code=status.HTTP_302_FOUND)
    redirect_response.delete_cookie("access_token")
    return redirect_response
@router.get("/todo-page")
async def render_todo_page(db: db_dependency, request: Request):
    try:
        user = await  get_current_user(request.cookies.get("access_token"))
        if user is None:
            return redirect_to_login()

        todos = db.query(Todo).filter(Todo.owner_id == user.get("id")).all()
        return templates.TemplateResponse("todo.html", {"request" : request, "todos" : todos, "user" : user})
    except:
        return redirect_to_login()

@router.get("/add-todo-page")
async def render_add_todo_page(request: Request):
    try:
        user = await  get_current_user(request.cookies.get("access_token"))
        if user is None:
            return redirect_to_login()

        return templates.TemplateResponse("add-todo.html", {"request" : request, "user" : user})
    except:
        return redirect_to_login()

@router.get("/edit-todo-page/{todo_id}")
async def render_add_todo_page(db: db_dependency, request: Request, todo_id: int = Path(gt=0)):
    try:
        user = await  get_current_user(request.cookies.get("access_token"))
        if user is None:
            return redirect_to_login()

        todo = db.query(Todo).filter(Todo.owner_id == user.get("id"), Todo.id == todo_id).first()

        return templates.TemplateResponse("edit-todo.html", {"request" : request, "todo" : todo, "user" : user})
    except:
        return redirect_to_login()


@router.get("/")
async def get_all_todos(db: db_dependency, user_dict : user_dependency):

    if user_dict is None:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Not authenticated")

    todos = db.query(Todo).filter(Todo.owner_id == user_dict.get("id")).all()

    if todos is None:
        raise status.HTTP_404_NOT_FOUND

    return todos


@router.get("/todo/{todo_id}", status_code = status.HTTP_200_OK)
async def get_by_id(db:db_dependency, user_dict : user_dependency, todo_id:int = Path(gt=0)):

    if user_dict is None:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Not authenticated")

    todo = db.query(Todo).filter(Todo.id == todo_id , Todo.owner_id == user_dict.get("id")).first()

    if todo is not None:
        return todo

    raise HTTPException(status_code=404, detail="Not found")

@router.post("/todo", status_code = status.HTTP_201_CREATED)
async def create_todo(db: db_dependency, user_dict: user_dependency, todo_request: TodoRequest):

    if user_dict is None:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Not authenticated")

    todo = Todo(
        title = todo_request.title,
        description= create_todo_with_gemini(todo_request.description),
        priority= todo_request.priority,
        owner_id= user_dict.get("id")
    )
    db.add(todo)
    db.commit()


@router.put("/todo/{todo_id}", status_code=status.HTTP_200_OK)
async def update_todo(db:db_dependency, user_dict: user_dependency,
                      todo_request: TodoUpdateRequest,
                      todo_id: int = Path(gt=0)):
    if user_dict is None:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Not authenticated")

    todo = db.query(Todo).filter(Todo.id == todo_id, Todo.owner_id == user_dict.get("id")).first()
    if todo is None:
        raise HTTPException(status_code=404, detail="Todo not found!")

    todo.title = todo_request.title
    todo.description = todo_request.description
    todo.priority = todo_request.priority
    todo.is_completed = todo_request.is_completed
    db.add(todo)
    db.commit()


@router.delete("/todo/{todo_id}", status_code = status.HTTP_200_OK)
async def delete_todo(user_dict : user_dependency, db: db_dependency, todo_id: int = Path(gt=0)):

    if user_dict is None:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Not authenticated")

    todo = db.query(Todo).filter(Todo.id == todo_id, Todo.owner_id == user_dict.get("id")).first()
    if todo is None:
        raise HTTPException(status_code=404, detail="Todo not found!")

    db.delete(todo)
    db.commit()

def create_todo_with_gemini(todo_string: str):
    load_dotenv()

    genai.configure(api_key=os.environ.get("GOOGLE_API_KEY"))
    llm = ChatGoogleGenerativeAI(model="gemini-2.0-flash")
    response = llm.invoke(
        [
            HumanMessage(content="I like taking notes, so I am writing down my todos. I will provide you a todo item. What i want you to do is to create a longer and more comprehensive description of that todo item. Do not add any text except for your description. My next message will be my todo."),
            HumanMessage(content=todo_string)

        ]
    )
    return markdown_to_text(response.content)

def markdown_to_text(markdown_string: str):
    html = markdown.markdown(markdown_string)
    soup = BeautifulSoup(html, "html.parser")
    text = soup.get_text()
    return text
