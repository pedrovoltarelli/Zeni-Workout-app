import mysql.connector
from mysql.connector import Error, pooling
import os
import uuid
from datetime import datetime
from typing import Dict, Any, Optional, List


class MySQLClient:
    def __init__(self):
        self.connection_pool = self._create_connection_pool()

    def _create_connection_pool(self):
        try:
            config = {
    "user": os.getenv("MYSQL_USER", "root"),
    "password": os.getenv("MYSQL_PASSWORD", "Pxdrinmv01!"),
    "host": os.getenv("MYSQL_HOST", "localhost"),
    "database": os.getenv("MYSQL_DATABASE", "zeni_saas"),
    "pool_name": "mypool",
    "pool_size": 5
}
            
            return pooling.MySQLConnectionPool(**config)
        except Error as e:
            raise Exception(f"Error creating MySQL connection pool: {e}")

    def get_connection(self):
        try:
            return self.connection_pool.get_connection()
        except Error as e:
            raise Exception(f"Error getting connection from pool: {e}")

    def execute_query(self, query: str, params: tuple = None, fetch_one=False, fetch_all=False):
        connection = None
        cursor = None
        try:
            connection = self.get_connection()
            cursor = connection.cursor(dictionary=True)
            if params:
                cursor.execute(query, params)
            else:
                cursor.execute(query)

            if fetch_one:
                return cursor.fetchone()
            if fetch_all:
                return cursor.fetchall()
            
            connection.commit()
            return cursor.rowcount

        except Error as e:
            if connection:
                connection.rollback()
            raise Exception(f"Database error: {e}")
        finally:
            if cursor:
                cursor.close()
            if connection:
                connection.close()

    def create_record(self, table: str, data: Dict[str, Any]) -> str:
        """Insere um registro na tabela e retorna o id"""
        if 'id' not in data:
            data['id'] = str(uuid.uuid4())
        # Converte datetime para string (se houver)
        for key, value in data.items():
            if isinstance(value, datetime):
                data[key] = value.isoformat()

        columns = ', '.join(data.keys())
        placeholders = ', '.join(['%s'] * len(data))
        query = f"INSERT INTO {table} ({columns}) VALUES ({placeholders})"

        self.execute_query(query, tuple(data.values()))
        return data['id']

    def update_record(self, table: str, record_id: str, update_data: Dict[str, Any]) -> int:
        """Atualiza um registro pelo id, retorna número de linhas afetadas"""
        if not update_data:
            raise Exception("Nenhum dado para atualizar fornecido")

        for key, value in update_data.items():
            if isinstance(value, datetime):
                update_data[key] = value.isoformat()

        set_clause = ', '.join([f"{k} = %s" for k in update_data.keys()])
        query = f"UPDATE {table} SET {set_clause} WHERE id = %s"
        params = tuple(update_data.values()) + (record_id,)

        return self.execute_query(query, params)

    def delete_record(self, table: str, record_id: str) -> int:
        """Deleta um registro pelo id, retorna número de linhas afetadas"""
        query = f"DELETE FROM {table} WHERE id = %s"
        return self.execute_query(query, (record_id,))

    def find_one(self, table: str, filter_dict: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        where_clause = ' AND '.join([f"{k} = %s" for k in filter_dict.keys()])
        query = f"SELECT * FROM {table} WHERE {where_clause}"
        return self.execute_query(query, tuple(filter_dict.values()), fetch_one=True)

    def find_all(self, table: str, filter_dict: Dict[str, Any] = None) -> List[Dict[str, Any]]:
        if filter_dict:
            where_clause = ' AND '.join([f"{k} = %s" for k in filter_dict.keys()])
            query = f"SELECT * FROM {table} WHERE {where_clause}"
            params = tuple(filter_dict.values())
        else:
            query = f"SELECT * FROM {table}"
            params = None
        return self.execute_query(query, params, fetch_all=True)


# Cria instância global
mysql_client = MySQLClient()

if __name__ == "__main__":
    # Teste rápido (rodar para testar)
    try:
        new_id = mysql_client.create_record("test_table", {"name": "Teste", "created_at": datetime.utcnow()})
        print(f"Registro criado com id: {new_id}")
        updated = mysql_client.update_record("test_table", new_id, {"name": "Teste Atualizado"})
        print(f"Registros atualizados: {updated}")
        deleted = mysql_client.delete_record("test_table", new_id)
        print(f"Registros deletados: {deleted}")
    except Exception as e:
        print(f"Erro: {e}")
