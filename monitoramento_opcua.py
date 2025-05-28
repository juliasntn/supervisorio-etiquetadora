#Bibliotecas principais
import pyodbc #Conexão com o banco de dados
import pandas as pd #Conseguir planilhar o que eu quiser
from opcua import Client #Monitorar tags pelo OPC
import time #Horário atual
import logging #Log do script caso tenha algum problema
from datetime import datetime #Data e hora atual
import os
import configparser #Colocar os dados importantes de conexões fora do script para usuário conseguir alterar
from threading import Event 

# Configuração inicial
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('monitoramento.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# Carregar configurações
config = configparser.ConfigParser()
config.read('config.ini')

# Variáveis globais com valores padrão
DB_CONFIG = {
    'driver': config.get('DATABASE', 'Driver', fallback='ODBC Driver 17 for SQL Server'),
    'server': config.get('DATABASE', 'Server', fallback='10.79.22.206'),
    'database': config.get('DATABASE', 'Database', fallback='PALETIZADORAS'),
    'uid': config.get('DATABASE', 'UID', fallback='ROOT'),
    'pwd': config.get('DATABASE', 'PWD', fallback='root')
}

OPC_SERVER_URL = config.get('OPCUA', 'ServerURL', fallback='opc.tcp://10.79.22.213:49310')

NODES_TO_MONITOR = [
    "ns=2;s=L594_PAL594001.PAL594001.PAL_TOTAL_PALETES_TURNO_CORRENTE",
    "ns=2;s=L595_PAL595001.PAL595001.PAL_TOTAL_PALETES_TURNO_CORRENTE",
    "ns=2;s=L596_PAL596001.PAL596001.PAL_TOTAL_PALETES_TURNO_CORRENTE"
]

CSV_FILES = {
    '594': 'timestamp_fila594.csv',
    '595': 'timestamp_fila595.csv',
    '596': 'timestamp_fila596.csv'
}

# Evento para controle de encerramento
shutdown_event = Event()

def create_db_connection():
    """Cria e retorna uma conexão com o banco de dados"""
    connection_str = (
        f"Driver={DB_CONFIG['driver']};"
        f"Server={DB_CONFIG['server']};"
        f"Database={DB_CONFIG['database']};"
        f"UID={DB_CONFIG['uid']};"
        f"PWD={DB_CONFIG['pwd']}"
    )
    try:
        conn = pyodbc.connect(connection_str)
        logger.info("Conexão com o banco de dados estabelecida com sucesso")
        return conn
    except Exception as e:
        logger.error(f"Erro ao conectar ao banco de dados: {e}")
        return None

def registrar_timestamp_no_csv(line_number, conn):
    """Registra timestamp no CSV apropriado, separando data e hora"""
    csv_file = CSV_FILES.get(line_number)
    if not csv_file:
        logger.error(f"Número de linha inválido: {line_number}")
        return
    
    query = f"""
    SELECT TOP(1) timestamp 
    FROM PAL{line_number} 
    WHERE CAST(timestamp AS DATE) = CAST(GETDATE() AS DATE)
    ORDER BY timestamp DESC
    """
    
    try:
        with conn.cursor() as cursor:
            registro = cursor.execute(query).fetchone()
            if registro:
                timestamp = registro[0]
                data = timestamp.strftime('%Y-%m-%d')
                hora = timestamp.strftime('%H:%M:%S')
                
                # Verificar se o arquivo existe para adicionar cabeçalho
                file_exists = os.path.exists(csv_file)
                
                # Criar DataFrame com colunas separadas
                df = pd.DataFrame({
                    'data': [data],
                    'hora': [hora]
                })
                
                # Escrever no CSV
                df.to_csv(
                    csv_file, 
                    mode='a', 
                    index=False, 
                    header=not file_exists
                )
                logger.info(f"Registro adicionado - Data: {data}, Hora: {hora} - Arquivo: {csv_file}")
            else:
                logger.warning(f"Nenhum registro encontrado hoje para a linha {line_number}")
    except Exception as e:
        logger.error(f"Erro ao registrar timestamp para linha {line_number}: {e}")

class EnhancedSubHandler:
    def __init__(self, db_conn):
        self.db_conn = db_conn
        self.last_values = {}
    
    def datachange_notification(self, node, val, data):
        try:
            node_str = str(node)
            logger.debug(f"DataChange detectado! Nó: {node_str}, Valor: {val}")
            
            # Verificar se o valor mudou significativamente
            if node_str in self.last_values and self.last_values[node_str] == val:
                logger.debug(f"Valor inalterado para o nó {node_str}")
                return
                
            self.last_values[node_str] = val
            
            # Determinar qual linha foi alterada
            if "L594_" in node_str:
                line_num = '594'
            elif "L595_" in node_str:
                line_num = '595'
            elif "L596_" in node_str:
                line_num = '596'
            else:
                logger.warning(f"Nó não reconhecido: {node_str}")
                return
            
            # Pequena pausa para evitar registros duplicados de eventos rápidos
            time.sleep(1)
            
            registrar_timestamp_no_csv(line_num, self.db_conn)
            
        except Exception as e:
            logger.error(f"Erro ao processar mudança no nó {node_str}: {e}")

def monitorar_opcua(db_conn):
    """Monitora os nós OPC UA com reconexão automática"""
    tentativa_reconexao = 1
    max_tentativas = 5
    client = None
    sub = None
    
    while not shutdown_event.is_set():
        try:
            logger.info("Conectando ao servidor OPC UA...")
            client = Client(OPC_SERVER_URL)
            client.connect()
            logger.info("Conectado ao servidor OPC UA com sucesso")
            tentativa_reconexao = 1  # Resetar contador após conexão bem-sucedida
            
            handler = EnhancedSubHandler(db_conn)
            sub = client.create_subscription(100, handler)
            
            for node_str in NODES_TO_MONITOR:
                node = client.get_node(node_str)
                sub.subscribe_data_change(node)
                logger.debug(f"Monitorando nó: {node_str}")
            
            logger.info("Monitoramento ativo. Pressione Ctrl+C para interromper.")
            
            while not shutdown_event.is_set():
                time.sleep(0.5)  # Pausa reduzida para resposta mais rápida ao shutdown
                
        except Exception as e:
            logger.error(f"Erro durante o monitoramento: {e}")
            
            if tentativa_reconexao <= max_tentativas:
                wait_time = min(2 ** tentativa_reconexao, 60)  # Backoff exponencial com máximo de 60s
                logger.info(f"Tentativa {tentativa_reconexao}/{max_tentativas}. Reconectando em {wait_time} segundos...")
                time.sleep(wait_time)
                tentativa_reconexao += 1
            else:
                logger.error("Número máximo de tentativas de reconexão atingido. Encerrando...")
                shutdown_event.set()
                
        finally:
            try:
                if sub:
                    sub.delete()
                    logger.debug("Subscription OPC UA removida")
                if client:
                    client.disconnect()
                    logger.info("Desconectado do servidor OPC UA")
            except Exception as e:
                logger.error(f"Erro ao limpar recursos OPC UA: {e}")

def main():
    try:
        logger.info("Iniciando serviço de monitoramento")
        
        # Estabelecer conexão com o banco de dados
        db_conn = create_db_connection()
        if not db_conn:
            logger.error("Não foi possível estabelecer conexão com o banco de dados. Encerrando...")
            return
        
        # Iniciar monitoramento OPC UA
        monitorar_opcua(db_conn)
        
    except KeyboardInterrupt:
        logger.info("Monitoramento interrompido pelo usuário")
    except Exception as e:
        logger.error(f"Erro fatal: {e}")
    finally:
        shutdown_event.set()
        try:
            if db_conn:
                db_conn.close()
                logger.info("Conexão com banco de dados encerrada")
        except Exception as e:
            logger.error(f"Erro ao fechar conexão com banco de dados: {e}")
        
        logger.info("Serviço de monitoramento encerrado")

if __name__ == "__main__":
    main()