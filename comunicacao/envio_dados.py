import threading
import requests

# URL do seu endpoint
SERVER_URL = 'https://seu-servidor.com/api/'


def enviar_servidor(dados: dict) -> None:
    """
    Envia os dados para o servidor em uma thread separada.

    Parâmetros:
        dados (dict): Dicionário com os campos 'sentimento', 'tipo' e 'escala'.
    """
    def _task():
        try:
            response = requests.post(SERVER_URL, json=dados, timeout=5)
            response.raise_for_status()
            print(f"[envio_dados] Sucesso: {response.status_code}")
        except requests.RequestException as e:
            print(f"[envio_dados] Erro ao enviar dados: {e}")

    thread = threading.Thread(target=_task, daemon=True)
    thread.start()