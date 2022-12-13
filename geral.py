
import sqlite3 as sql
from typing import List
from hashlib import sha256

def hash_string(senha: str):
    return sha256(senha.encode('utf-8')).hexdigest()[:15]

def call_database_and_execute(statement,parameters = []) -> List[sql.Row]:
    """função para auxiliar no uso do banco de dados SQL"""
    db = sql.connect("database.db")
    db.row_factory = sql.Row
    data = db.cursor().execute(statement,parameters)
    
    final_data =  data.fetchall()
    db.commit()
    db.close()
    return final_data
