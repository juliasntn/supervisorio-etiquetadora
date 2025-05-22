from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
import pyodbc

app = FastAPI()

# Configuração do banco de dados
DB_CONFIG = {
    "driver": "{SQL Server}",
    "server": "10.79.22.206",
    "database": "TESTEGLY",
    "uid": "ROOT",
    "pwd": "root"
}

# Função para conectar ao banco
def get_db_connection():
    return pyodbc.connect(
        f"DRIVER={DB_CONFIG['driver']};"
        f"SERVER={DB_CONFIG['server']};"
        f"DATABASE={DB_CONFIG['database']};"
        f"UID={DB_CONFIG['uid']};"
        f"PWD={DB_CONFIG['pwd']}"
    )

# Classe modelo banco de dados
class UpdateData(BaseModel):
    data: str
    hora: str



# Endpoint para buscar dados
@app.get("/dados")
def get_dados():
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT id, FORMAT(datahora, 'dd/MM/yyyy') AS data, FORMAT(datahora, 'HH:mm') AS hora FROM contagem_pallets")
    dados = [{"id": row.id, "data": row.data, "hora": row.hora} for row in cursor.fetchall()]
    conn.close()
    return dados

# Endpoint para atualizar um registro
@app.put("/dados/{id}")
def update_dado(id: int, request: UpdateData):
    conn = get_db_connection()
    cursor = conn.cursor()

    # Ajustando a conversão correta da data e hora
    datahora_formatada = f"{request.data} {request.hora}:00"

    try:
        cursor.execute(
            "UPDATE contagem_pallets SET datahora = CONVERT(datetime, ?, 103) WHERE id = ?",
            (datahora_formatada, id)
        )
        conn.commit()
        conn.close()
        return {"message": "Registro atualizado com sucesso!"}
    except pyodbc.Error as e:
        conn.rollback()
        return {"error": f"Erro ao atualizar: {e}"}
    
# Endpoint para excluir um registro
@app.delete("/dados/{id}")
def delete_dado(id: int):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("DELETE FROM contagem_pallets WHERE id = ?", (id,))
    conn.commit()
    conn.close()
    return {"message": "Registro excluído com sucesso!"}