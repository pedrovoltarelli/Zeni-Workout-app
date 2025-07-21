from fastapi import FastAPI, APIRouter, HTTPException
from dotenv import load_dotenv
from starlette.middleware.cors import CORSMiddleware
import os
import logging
from pathlib import Path
from pydantic import BaseModel, Field
from typing import List, Optional
import uuid
from datetime import datetime, timedelta
import secrets
import bcrypt
from mysql_client import mysql_client

ROOT_DIR = Path(__file__).parent
load_dotenv(ROOT_DIR / '.env')

app = FastAPI()
api_router = APIRouter(prefix="/api")

# Models
class StatusCheck(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    client_name: str
    timestamp: datetime = Field(default_factory=datetime.utcnow)

class StatusCheckCreate(BaseModel):
    client_name: str

class User(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    name: str
    email: str
    password: str
    created_at: datetime = Field(default_factory=datetime.utcnow)

class UserCreate(BaseModel):
    name: str
    email: str
    password: str

class UserLogin(BaseModel):
    email: str
    password: str

class UserUpdate(BaseModel):
    email: str
    name: Optional[str] = None
    password: Optional[str] = None

class ForgotPasswordRequest(BaseModel):
    email: str

class ResetPasswordRequest(BaseModel):
    token: str
    new_password: str
    confirm_password: str

class PasswordResetToken(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    user_id: str
    token: str
    expires_at: datetime
    used: bool = False
    created_at: datetime = Field(default_factory=datetime.utcnow)

class ChatMessage(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    session_id: str
    user_id: str
    message: str
    response: str
    timestamp: datetime = Field(default_factory=datetime.utcnow)

class ChatRequest(BaseModel):
    session_id: str
    user_id: str
    message: str

class WorkoutPlan(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    user_id: str
    title: str
    category: str
    exercises: List[dict]
    duration: str
    difficulty: str
    created_by_ai: bool = False
    created_at: datetime = Field(default_factory=datetime.utcnow)

# Helpers
def convert_datetime_to_string(obj):
    if isinstance(obj, dict):
        return {k: convert_datetime_to_string(v) for k, v in obj.items()}
    elif isinstance(obj, list):
        import json
        return json.dumps(obj)
    elif isinstance(obj, datetime):
        return obj.isoformat()
    return obj

# Routes
@api_router.get("/")
async def root():
    return {"message": "Hello World"}

@api_router.post("/status", response_model=StatusCheck)
async def create_status_check(input: StatusCheckCreate):
    status_obj = StatusCheck(**input.dict())
    status_data = convert_datetime_to_string(status_obj.dict())
    mysql_client.create_record('status_checks', status_data)
    return status_obj

@api_router.get("/status", response_model=List[StatusCheck])
async def get_status_checks():
    data = mysql_client.find_all('status_checks')
    return [StatusCheck(**item) for item in data]

@api_router.post("/register")
async def register(user_data: UserCreate):
    existing_user = mysql_client.find_one('users', {'email': user_data.email})
    if existing_user:
        raise HTTPException(status_code=400, detail="Email já cadastrado")

    hashed_password = bcrypt.hashpw(user_data.password.encode(), bcrypt.gensalt()).decode()
    user = User(**user_data.dict(), password=hashed_password)
    user_data_dict = convert_datetime_to_string(user.dict())

    user_id = mysql_client.create_record('users', user_data_dict)
    return {"message": "Usuário criado com sucesso", "user_id": user_id, "name": user.name}

@api_router.post("/login")
async def login(login_data: UserLogin):
    user = mysql_client.find_one('users', {'email': login_data.email})
    if not user or not bcrypt.checkpw(login_data.password.encode(), user['password'].encode()):
        raise HTTPException(status_code=401, detail="Email ou senha incorretos")
    return {"message": "Login realizado com sucesso", "user_id": user['id'], "name": user['name']}

@api_router.put("/users/update")
async def update_user(user_update: UserUpdate):
    user = mysql_client.find_one('users', {'email': user_update.email})
    if not user:
        raise HTTPException(status_code=404, detail="Usuário não encontrado")

    updates = {}
    if user_update.name:
        updates['name'] = user_update.name
    if user_update.password:
        updates['password'] = bcrypt.hashpw(user_update.password.encode(), bcrypt.gensalt()).decode()

    if not updates:
        raise HTTPException(status_code=400, detail="Nada para atualizar")

    mysql_client.update_record('users', user['id'], updates)
    return {"message": "Usuário atualizado com sucesso"}

@api_router.delete("/users/{user_id}")
async def delete_user(user_id: str):
    deleted = mysql_client.delete_record('users', user_id)
    if deleted == 0:
        raise HTTPException(status_code=404, detail="Usuário não encontrado")
    return {"message": "Usuário excluído com sucesso"}

@api_router.post("/forgot-password")
async def forgot_password(request: ForgotPasswordRequest):
    user = mysql_client.find_one('users', {'email': request.email})
    if not user:
        return {"message": "Se o email estiver cadastrado, você receberá um link de recuperação"}
    reset_token = secrets.token_urlsafe(32)
    expires_at = datetime.utcnow() + timedelta(hours=1)
    token_data = PasswordResetToken(user_id=user['id'], token=reset_token, expires_at=expires_at)
    mysql_client.create_record('password_reset_tokens', convert_datetime_to_string(token_data.dict()))
    reset_link = f"http://localhost:3000/reset-password?token={reset_token}"
    return {"message": "Se o email estiver cadastrado, você receberá um link de recuperação", "reset_link": reset_link}

@api_router.post("/reset-password")
async def reset_password(request: ResetPasswordRequest):
    if request.new_password != request.confirm_password:
        raise HTTPException(status_code=400, detail="As senhas não coincidem")
    token = mysql_client.find_one('password_reset_tokens', {'token': request.token, 'used': False})
    if not token:
        raise HTTPException(status_code=400, detail="Token inválido ou expirado")
    expires_at = token['expires_at']
    if isinstance(expires_at, str):
        expires_at = datetime.fromisoformat(expires_at.replace('Z', '+00:00'))
    if expires_at < datetime.utcnow():
        raise HTTPException(status_code=400, detail="Token expirado")
    hashed_pw = bcrypt.hashpw(request.new_password.encode(), bcrypt.gensalt()).decode()
    mysql_client.update_record('users', token['user_id'], {'password': hashed_pw})
    mysql_client.update_record('password_reset_tokens', token['id'], {'used': True})
    return {"message": "Senha alterada com sucesso"}

@api_router.get("/validate-reset-token/{token}")
async def validate_reset_token(token: str):
    token_data = mysql_client.find_one('password_reset_tokens', {'token': token, 'used': False})
    if not token_data:
        raise HTTPException(status_code=400, detail="Token inválido")
    expires_at = token_data['expires_at']
    if isinstance(expires_at, str):
        expires_at = datetime.fromisoformat(expires_at.replace('Z', '+00:00'))
    if expires_at < datetime.utcnow():
        raise HTTPException(status_code=400, detail="Token expirado")
    return {"message": "Token válido"}

@api_router.post("/chat")
async def chat_with_ai(chat_request: ChatRequest):
    response = f"Resposta da IA para: {chat_request.message}"
    chat_message = ChatMessage(session_id=chat_request.session_id, user_id=chat_request.user_id, message=chat_request.message, response=response)
    mysql_client.create_record('chat_messages', convert_datetime_to_string(chat_message.dict()))
    return {"response": response, "session_id": chat_request.session_id}

@api_router.get("/chat/{session_id}")
async def get_chat_history(session_id: str):
    return mysql_client.find_all('chat_messages', {'session_id': session_id})

@api_router.post("/workouts")
async def save_workout(workout: WorkoutPlan):
    mysql_client.create_record('workouts', convert_datetime_to_string(workout.dict()))
    return {"message": "Treino salvo com sucesso", "workout_id": workout.id}

@api_router.get("/workouts/{user_id}")
async def get_user_workouts(user_id: str):
    return mysql_client.find_all('workouts', {'user_id': user_id})

# Middleware e Start
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(api_router)

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8001)
