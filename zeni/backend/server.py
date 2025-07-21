from fastapi import FastAPI, APIRouter, HTTPException
from dotenv import load_dotenv
from starlette.middleware.cors import CORSMiddleware
from databases import Database
from sqlalchemy import (create_engine, MetaData, Table, Column,
                        Integer, String, DateTime, Boolean, Text, JSON, ForeignKey, select, insert, update)
from pydantic import BaseModel, Field
from datetime import datetime, timedelta
import os
import logging
import secrets

# Load env variables
load_dotenv()

DATABASE_URL = os.getenv("MYSQL_URL", "mysql+aiomysql://root:senha@localhost:3306/zeni")
database = Database(DATABASE_URL)
metadata = MetaData()

# Define tables
users = Table(
    "users", metadata,
    Column("id", Integer, primary_key=True),
    Column("name", String(100)),
    Column("email", String(100), unique=True),
    Column("password", String(255)),
    Column("created_at", DateTime, default=datetime.utcnow)
)

password_reset_tokens = Table(
    "password_reset_tokens", metadata,
    Column("id", Integer, primary_key=True),
    Column("user_id", Integer, ForeignKey("users.id")),
    Column("token", String(255), unique=True),
    Column("expires_at", DateTime),
    Column("used", Boolean, default=False),
    Column("created_at", DateTime, default=datetime.utcnow)
)

# Create engine to sync tables
engine = create_engine(DATABASE_URL.replace('+aiomysql', ''))
metadata.create_all(engine)

# FastAPI app
app = FastAPI()
api_router = APIRouter(prefix="/api")

# Models
class UserCreate(BaseModel):
    name: str
    email: str
    password: str

class UserLogin(BaseModel):
    email: str
    password: str

class ForgotPasswordRequest(BaseModel):
    email: str

class ResetPasswordRequest(BaseModel):
    token: str
    new_password: str
    confirm_password: str

# Rotas principais
@api_router.post("/register")
async def register(user_data: UserCreate):
    query = select(users).where(users.c.email == user_data.email)
    existing_user = await database.fetch_one(query)
    if existing_user:
        raise HTTPException(status_code=400, detail="Email já cadastrado")

    query = insert(users).values(
        name=user_data.name,
        email=user_data.email,
        password=user_data.password,
        created_at=datetime.utcnow()
    )
    user_id = await database.execute(query)

    return {"message": "Usuário criado com sucesso", "user_id": user_id, "name": user_data.name}


@api_router.post("/login")
async def login(login_data: UserLogin):
    query = select(users).where(
        (users.c.email == login_data.email) & (users.c.password == login_data.password)
    )
    user = await database.fetch_one(query)
    if not user:
        raise HTTPException(status_code=401, detail="Email ou senha incorretos")

    return {"message": "Login realizado com sucesso", "user_id": user.id, "name": user.name}


@api_router.post("/forgot-password")
async def forgot_password(request: ForgotPasswordRequest):
    query = select(users).where(users.c.email == request.email)
    user = await database.fetch_one(query)
    if not user:
        return {"message": "Se o email estiver cadastrado, você receberá as instruções de recuperação"}

    reset_token = secrets.token_urlsafe(32)
    expires_at = datetime.utcnow() + timedelta(hours=1)

    query = insert(password_reset_tokens).values(
        user_id=user.id,
        token=reset_token,
        expires_at=expires_at,
        used=False,
        created_at=datetime.utcnow()
    )
    await database.execute(query)

    reset_link = f"http://localhost:3000/reset-password?token={reset_token}"

    return {
        "message": "Se o email estiver cadastrado, você receberá as instruções de recuperação",
        "reset_link": reset_link
    }


@api_router.post("/reset-password")
async def reset_password(request: ResetPasswordRequest):
    if request.new_password != request.confirm_password:
        raise HTTPException(status_code=400, detail="As senhas não coincidem")

    if len(request.new_password) < 6:
        raise HTTPException(status_code=400, detail="A senha deve ter pelo menos 6 caracteres")

    token_query = select(password_reset_tokens).where(
        (password_reset_tokens.c.token == request.token) &
        (password_reset_tokens.c.used == False) &
        (password_reset_tokens.c.expires_at > datetime.utcnow())
    )
    token_data = await database.fetch_one(token_query)
    if not token_data:
        raise HTTPException(status_code=400, detail="Token inválido ou expirado")

    await database.execute(
        update(users).where(users.c.id == token_data.user_id).values(password=request.new_password)
    )

    await database.execute(
        update(password_reset_tokens).where(password_reset_tokens.c.token == request.token).values(used=True)
    )

    return {"message": "Senha alterada com sucesso"}


@api_router.get("/verify-reset-token/{token}")
async def verify_reset_token(token: str):
    query = select(password_reset_tokens).where(
        (password_reset_tokens.c.token == token) &
        (password_reset_tokens.c.used == False) &
        (password_reset_tokens.c.expires_at > datetime.utcnow())
    )
    token_data = await database.fetch_one(query)
    if not token_data:
        raise HTTPException(status_code=400, detail="Token inválido ou expirado")
    return {"valid": True, "message": "Token válido"}

# Inicializar rotas e middleware
app.include_router(api_router)

app.add_middleware(
    CORSMiddleware,
    allow_credentials=True,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.on_event("startup")
async def startup():
    await database.connect()

@app.on_event("shutdown")
async def shutdown():
    await database.disconnect()

# Logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)
