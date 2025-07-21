import mysql.connector
from mysql.connector import Error

try:
    connection = mysql.connector.connect(
        user='root',
        password='Pxdrinmv01!',
        host='localhost',
        database='zeni_saas'
    )
    if connection.is_connected():
        print("Conectado ao MySQL com sucesso!")
except Error as e:
    print(f"Erro ao conectar: {e}")
finally:
    if connection.is_connected():
        connection.close()
        print("Conexão fechada.")
