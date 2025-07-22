# Exemplo de teste simples
from backend.mysql_client import mysql_client
import bcrypt
from backend.mysql_client import mysql_client
from datetime import datetime

senha = "Pxdrinmv01!"
hashed_password = bcrypt.hashpw(senha.encode(), bcrypt.gensalt()).decode()

user = {
    "name": "Pedro Voltarelli",
    "email": "pedrovoltarelli587@gmail.com",
    "password": hashed_password,
    "created_at": datetime.utcnow()
}
user_id = mysql_client.create_record("users", user)
print("ID criado:", user_id)

import bcrypt
from backend.mysql_client import mysql_client
from datetime import datetime

senha = "Pxdrinmv01!"
hashed_password = bcrypt.hashpw(senha.encode(), bcrypt.gensalt()).decode()

user = {
    "name": "Teste",
    "email": "pedrovoltarelli587@gmail.com",
    "password": hashed_password,
    "created_at": datetime.utcnow()
}
user_id = mysql_client.create_record("users", user)
print("ID criado:", user_id)
from datetime import datetime

# Criar registro
user = {
    "name": "Teste",
    "email": "teste@email.com",
    "password": "senha_hash",
    "created_at": datetime.utcnow()
}
user_id = mysql_client.create_record("users", user)
print("ID criado:", user_id)

# Buscar registro
found = mysql_client.find_one("users", {"email": "teste@email.com"})
print("Encontrado:", found)

# Atualizar registro
updated = mysql_client.update_record("users", user_id, {"name": "Teste Atualizado"})
print("Atualizado:", updated)