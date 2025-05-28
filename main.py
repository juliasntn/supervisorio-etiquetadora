from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
import csv
import pyodbc
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
import uvicorn
import threading
from monitoramento_opcua import main as start_monitoramento
from etiquetadora import main as start_etiquetadora

app = FastAPI()
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Permite requisições de qualquer origem (modifique conforme necessário)
    allow_methods=["GET", "POST", "PUT", "DELETE"],
    allow_headers=["*"]
)

################################ ETIQUETADORA ###################################

def run_monitoramento():
    start_monitoramento()

def run_etiquetadora():
    start_etiquetadora()

@app.on_event("startup")
def startup_event():
    # Executa os dois scripts em threads
    threading.Thread(target=run_monitoramento, daemon=True).start()
    threading.Thread(target=run_etiquetadora, daemon=True).start()

###################################################################################

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

app.mount("/static", StaticFiles(directory="static"), name="static")


### 594 ###
# Endpoint para buscar dados
@app.get("/dados")
def get_dados():
    dados = []
    with open("timestamp_fila594.csv", newline='', encoding='utf-8') as csvfile:
        reader = csv.reader(csvfile)
        for row in reader:
            dados.append({"data": row[0],"hora": row[1]})  # Considerando que cada linha contém apenas a hora
    return dados


# Endpoint para atualizar um registro
class UpdateData(BaseModel):
    hora: str

@app.put("/dados/{linha}")
def update_dado(linha: int, request: UpdateData):
    arquivo_csv = "timestamp_fila594.csv"

    try:
        # Ler os dados do CSV
        with open(arquivo_csv, newline='', encoding='utf-8') as csvfile:
            reader = list(csv.reader(csvfile))

        # Verificar se a linha é válida
        if linha < 0 or linha >= len(reader):
            raise HTTPException(status_code=404, detail="Linha não encontrada")

        # Atualizar a hora na linha correspondente
        reader[linha][1] = request.hora

        # Escrever as mudanças no CSV
        with open(arquivo_csv, 'w', newline='', encoding='utf-8') as csvfile:
            writer = csv.writer(csvfile)
            writer.writerows(reader)

        return {"message": "Horário atualizado com sucesso!"}

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erro ao atualizar: {e}")
        
# Endpoint para excluir um registro
@app.delete("/dados/{linha}")
def delete_dado(linha: int):
    arquivo_csv = "timestamp_fila594.csv"

    try:
        # Ler os dados do CSV
        with open(arquivo_csv, newline='', encoding='utf-8') as csvfile:
            reader = list(csv.reader(csvfile))

        # Verificar se a linha é válida
        if linha < 0 or linha >= len(reader):
            raise HTTPException(status_code=404, detail="Linha não encontrada")

        # Remover a linha do CSV
        del reader[linha]

        # Escrever as mudanças no CSV
        with open(arquivo_csv, 'w', newline='', encoding='utf-8') as csvfile:
            writer = csv.writer(csvfile)
            writer.writerows(reader)

        return {"message": "Linha excluída com sucesso!"}

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erro ao excluir: {e}")
    
### 595 ###
# Endpoint para buscar dados
@app.get("/dados595")
def get_dados():
    dados = []
    with open("timestamp_fila595.csv", newline='', encoding='utf-8') as csvfile:
        reader = csv.reader(csvfile)
        for row in reader:
            dados.append({"data": row[0],"hora": row[1]})  # Considerando que cada linha contém apenas a hora
    return dados


# Endpoint para atualizar um registro
class UpdateData(BaseModel):
    hora: str

@app.put("/dados595/{linha}")
def update_dado(linha: int, request: UpdateData):
    arquivo_csv = "timestamp_fila595.csv"

    try:
        # Ler os dados do CSV
        with open(arquivo_csv, newline='', encoding='utf-8') as csvfile:
            reader = list(csv.reader(csvfile))

        # Verificar se a linha é válida
        if linha < 0 or linha >= len(reader):
            raise HTTPException(status_code=404, detail="Linha não encontrada")

        # Atualizar a hora na linha correspondente
        reader[linha][1] = request.hora

        # Escrever as mudanças no CSV
        with open(arquivo_csv, 'w', newline='', encoding='utf-8') as csvfile:
            writer = csv.writer(csvfile)
            writer.writerows(reader)

        return {"message": "Horário atualizado com sucesso!"}

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erro ao atualizar: {e}")
        
# Endpoint para excluir um registro
@app.delete("/dados595/{linha}")
def delete_dado(linha: int):
    arquivo_csv = "timestamp_fila595.csv"

    try:
        # Ler os dados do CSV
        with open(arquivo_csv, newline='', encoding='utf-8') as csvfile:
            reader = list(csv.reader(csvfile))

        # Verificar se a linha é válida
        if linha < 0 or linha >= len(reader):
            raise HTTPException(status_code=404, detail="Linha não encontrada")

        # Remover a linha do CSV
        del reader[linha]

        # Escrever as mudanças no CSV
        with open(arquivo_csv, 'w', newline='', encoding='utf-8') as csvfile:
            writer = csv.writer(csvfile)
            writer.writerows(reader)

        return {"message": "Linha excluída com sucesso!"}

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erro ao excluir: {e}")

### 596 ###
# Endpoint para buscar dados
@app.get("/dados596")
def get_dados():
    dados = []
    with open("timestamp_fila596.csv", newline='', encoding='utf-8') as csvfile:
        reader = csv.reader(csvfile)
        for row in reader:
            dados.append({"data": row[0], "hora": row[1]})  # Considerando que cada linha contém apenas a hora
    return dados


# Endpoint para atualizar um registro
class UpdateData(BaseModel):
    hora: str

@app.put("/dados596/{linha}")
def update_dado(linha: int, request: UpdateData):
    arquivo_csv = "timestamp_fila596.csv"

    try:
        # Ler os dados do CSV
        with open(arquivo_csv, newline='', encoding='utf-8') as csvfile:
            reader = list(csv.reader(csvfile))

        # Verificar se a linha é válida
        if linha < 0 or linha >= len(reader):
            raise HTTPException(status_code=404, detail="Linha não encontrada")

        # Atualizar a hora na linha correspondente
        reader[linha][1] = request.hora

        # Escrever as mudanças no CSV
        with open(arquivo_csv, 'w', newline='', encoding='utf-8') as csvfile:
            writer = csv.writer(csvfile)
            writer.writerows(reader)

        return {"message": "Horário atualizado com sucesso!"}

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erro ao atualizar: {e}")
        
# Endpoint para excluir um registro
@app.delete("/dados596/{linha}")
def delete_dado(linha: int):
    arquivo_csv = "timestamp_fila596.csv"

    try:
        # Ler os dados do CSV
        with open(arquivo_csv, newline='', encoding='utf-8') as csvfile:
            reader = list(csv.reader(csvfile))

        # Verificar se a linha é válida
        if linha < 0 or linha >= len(reader):
            raise HTTPException(status_code=404, detail="Linha não encontrada")

        # Remover a linha do CSV
        del reader[linha]

        # Escrever as mudanças no CSV
        with open(arquivo_csv, 'w', newline='', encoding='utf-8') as csvfile:
            writer = csv.writer(csvfile)
            writer.writerows(reader)

        return {"message": "Linha excluída com sucesso!"}

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erro ao excluir: {e}")


if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)
