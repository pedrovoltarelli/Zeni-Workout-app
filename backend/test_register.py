from mysql_client import mysql_client
from datetime import datetime
import uuid

user = {
    "id": str(uuid.uuid4()),
    "name": "Pedro Voltarelli",
    "email": "pedrovoltarelli587@gmail.com",
    "password": "Pxdrinmv01!",
    "created_at": datetime.utcnow().isoformat()
}

inserted_id = mysql_client.insert_one("users", user)
print("Usuário inserido com ID:", inserted_id)
                       