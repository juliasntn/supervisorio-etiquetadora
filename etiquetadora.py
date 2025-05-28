import socket
import pandas as pd
import time
from opcua import Client, ua
import atexit
from typing import Optional, Tuple

class EtiquetadoraOPCUA:
    def __init__(self):
        self.socket_client: Optional[socket.socket] = None
        self.opcua_client: Optional[Client] = None
        self.subscriptions = []
        self._setup_connections()

    def _setup_connections(self):
        """Estabelece conexões iniciais"""
        self._connect_opcua()
        self._connect_socket()
        atexit.register(self.cleanup)

    def _connect_opcua(self, max_retries: int = 3) -> bool:
        """Conecta ao servidor OPC UA com tratamento de retry"""
        for attempt in range(max_retries):
            try:
                if self.opcua_client:
                    try:
                        self.opcua_client.disconnect()
                    except:
                        pass

                self.opcua_client = Client("opc.tcp://10.79.22.213:49310")
                self.opcua_client.connect()
                print("Conectado ao servidor OPC UA.")
                return True
            except (ua.UaError, ConnectionError, TimeoutError) as e:
                print(f"Tentativa {attempt + 1}: Erro ao conectar OPC UA - {e}")
                time.sleep(2)
        return False

    def _connect_socket(self, max_retries: int = 3) -> bool:
        """Conecta ao socket da etiquetadora com tratamento de retry"""
        for attempt in range(max_retries):
            try:
                if self.socket_client:
                    try:
                        self.socket_client.close()
                    except:
                        pass

                self.socket_client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                self.socket_client.settimeout(5.0)
                self.socket_client.connect(("10.79.22.132", 3002))
                print("Conectado à etiquetadora via socket.")
                return True
            except (socket.error, TimeoutError) as e:
                print(f"Tentativa {attempt + 1}: Erro ao conectar socket - {e}")
                time.sleep(2)
        return False

    def _is_opcua_connected(self) -> bool:
        """Verifica se a conexão OPC UA está ativa"""
        try:
            if self.opcua_client:
                # Tenta ler um nó simples para verificar a conexão
                root = self.opcua_client.get_root_node()
                root.get_child(["0:Objects"])
                return True
        except:
            return False
        return False

    def _is_socket_connected(self) -> bool:
        """Verifica se o socket está conectado"""
        return self.socket_client is not None and self.socket_client.fileno() != -1

    def _check_connections(self) -> bool:
        """Verifica e reconecta se necessário"""
        connections_ok = True

        # Verifica conexão OPC UA
        if not self._is_opcua_connected():
            print("Conexão OPC UA perdida, reconectando...")
            connections_ok = self._connect_opcua() and connections_ok

        # Verifica conexão Socket
        if not self._is_socket_connected():
            print("Conexão Socket perdida, reconectando...")
            connections_ok = self._connect_socket() and connections_ok

        return connections_ok

    def _get_csv_data(self, csv_file: str) -> Optional[Tuple[str, str]]:
        """Obtém dados do CSV e remove a linha processada"""
        try:
            df = pd.read_csv(csv_file)
            if df.empty:
                print(f"Arquivo {csv_file} vazio")
                return None

            # Verifica se as colunas necessárias existem
            if not all(col in df.columns for col in ['data', 'hora']):
                raise ValueError("Colunas 'data' ou 'hora' não encontradas")

            data = df.iloc[0]['data']
            hora = df.iloc[0]['hora']
            
            # Remove a linha processada
            df.iloc[1:].to_csv(csv_file, index=False)
            return data, hora

        except (FileNotFoundError, pd.errors.EmptyDataError, ValueError) as e:
            print(f"Erro ao processar CSV {csv_file}: {e}")
            return None

    def _send_to_printer(self, command: str, max_attempts: int = 3) -> bool:
        """Envia comando para a etiquetadora com tratamento de erro"""
        for attempt in range(max_attempts):
            try:
                if not self._check_connections():
                    continue

                self.socket_client.sendall((command + '\r').encode('utf-8'))
                response = self.socket_client.recv(1024).decode('utf-8')
                print(f"Resposta da etiquetadora: {response}")
                return True

            except (socket.error, TimeoutError) as e:
                print(f"Erro ao enviar comando (tentativa {attempt + 1}): {e}")
                self.socket_client = None
                time.sleep(1)

        print(f"Falha após {max_attempts} tentativas")
        return False

    def cleanup(self):
        """Limpeza de recursos"""
        print("Encerrando conexões...")
        
        # Fecha conexão socket
        if self.socket_client:
            try:
                self.socket_client.close()
            except Exception as e:
                print(f"Erro ao fechar socket: {e}")

        # Fecha conexão OPC UA
        if self.opcua_client:
            try:
                # Remove todas as subscrições
                for sub in self.subscriptions:
                    try:
                        sub.delete()
                    except Exception as e:
                        print(f"Erro ao deletar subscrição: {e}")
                
                self.opcua_client.disconnect()
            except Exception as e:
                print(f"Erro ao desconectar OPC UA: {e}")

    def start_monitoring(self):
        """Inicia o monitoramento dos nós OPC UA"""
        class OPCUAHandler:
            def __init__(self, parent):
                self.parent = parent
                self.waiting_rotation = False

            def datachange_notification(self, node, val, data):
                try:
                    node_str = str(node)
                    print(f"Alteração detectada - Nó: {node_str}, Valor: {val}")

                    # Sensor de presença ativado
                    if node_str.endswith("SENSOR_PRESENCA_TDP13") and val == 1:
                        print("Produto detectado na posição TDP13")
                        self.waiting_rotation = True

                    # Sensor de rotação ativado quando esperado
                    elif node_str.endswith("SENSOR_ROTACAO_MESA_90") and val and self.waiting_rotation:
                        print("Mesa rotacionou para posição de trabalho")
                        self.waiting_rotation = False
                        self._handle_rotation()

                    # Status da etiquetadora
                    elif node_str.endswith("ETIQUEDORA_FIMDECICLO"):
                        print(f"Status etiquetadora: {'Ativo' if val else 'Inativo'}")

                except Exception as e:
                    print(f"Erro no handler: {e}")

            def _handle_rotation(self):
                """Processa a rotação da mesa"""
                try:
                    node = self.parent.opcua_client.get_node(
                        "ns=2;s=L599_TRPEMB599001.TRPEMB599001_VR2.LINE_STATION_13"
                    )
                    station = node.get_value()

                    if station in {4, 5, 6}:  # Estações válidas
                        self._process_station(station)

                except Exception as e:
                    print(f"Erro ao processar rotação: {e}")

            def _process_station(self, station_id: int):
                """Processa dados para uma estação específica"""
                csv_file = f'timestamp_fila59{station_id}.csv'
                csv_data = self.parent._get_csv_data(csv_file)

                if csv_data:
                    data, hora = csv_data
                    command = f"SLA|59{station_id}|VAR1={data}|VAR2={hora}|"
                    
                    if self.parent._send_to_printer(command):
                        time.sleep(1)  # Intervalo entre comandos
                        self.parent._send_to_printer("PRN")  # Comando de impressão

        try:
            if not self._is_opcua_connected():
                raise ConnectionError("Conexão OPC UA não disponível")

            # Configura os nós a serem monitorados
            nodes_to_monitor = [
                "ns=2;s=L599_TRPEMB599001.TRPEMB599001_VR2.SENSOR_PRESENCA_TDP13",
                "ns=2;s=L599_TRPEMB599001.TRPEMB599001_VR2.SENSOR_ROTACAO_MESA_90",
                "ns=2;s=L599_TRPEMB599001.TRPEMB599001_VR2.ETIQUEDORA_FIMDECICLO"
            ]

            # Cria handler e subscrição
            handler = OPCUAHandler(self)
            subscription = self.opcua_client.create_subscription(100, handler)
            self.subscriptions.append(subscription)

            # Subescreve aos nós
            nodes = [self.opcua_client.get_node(n) for n in nodes_to_monitor]
            subscription.subscribe_data_change(nodes)
            print(f"Iniciado monitoramento de {len(nodes)} nós")

            # Loop principal
            while True:
                time.sleep(1)
                self._check_connections()

        except KeyboardInterrupt:
            print("Monitoramento interrompido pelo usuário")
        except Exception as e:
            print(f"Erro no monitoramento: {e}")
        finally:
            self.cleanup()

def main():
    system = EtiquetadoraOPCUA()
    system.start_monitoring()

if __name__ == "__main__":
    main()