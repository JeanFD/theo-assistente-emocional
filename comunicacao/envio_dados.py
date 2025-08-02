import threading
import requests

# --- Configuração da API ---
BASE_URL = 'http://127.0.0.1:8000/api/'
USERNAME = 'admin'
PASSWORD = '123' # Use a senha que você definiu para o admin

# --- Variável global para o token ---
access_token = None

def login_and_get_token():
    """Faz login e armazena o token de acesso."""
    global access_token
    try:
        print("[API] Tentando fazer login para obter token...")
        response = requests.post(f"{BASE_URL}token/", json={'username': USERNAME, 'password': PASSWORD})
        response.raise_for_status()
        
        data = response.json()
        access_token = data.get('access')
        
        if access_token:
            print("[API] Login e obtenção de token bem-sucedidos.")
            return True
        else:
            print("[API] Falha ao obter token do response.")
            return False
    except requests.RequestException as e:
        print(f"[API] Erro no login: {e}")
        return False

def enviar_servidor(dados: dict) -> None:
    """
    Envia dados para o servidor, fazendo login para obter um token de acesso
    e usando-o na requisição de registro.
    """
    def _task():
        global access_token

        # 1. Garante que temos um token
        if not access_token:
            if not login_and_get_token():
                print("[API] Falha ao enviar dados: não foi possível obter o token.")
                return

        # 2. Prepara a requisição de registro
        endpoint = 'registro-bpm/' if 'bpm' in dados and dados.get('bpm') is not None else 'registro-sentimento/'
        url = f"{BASE_URL}{endpoint}"
        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {access_token}"
        }

        try:
            # 3. Envia os dados com o token de autorização
            print(f"[API] Enviando dados para {url}...")
            response = requests.post(url, json=dados, headers=headers)
            
            # Se o token expirou (401), tenta logar de novo e reenviar
            if response.status_code == 401:
                print("[API] Token possivelmente expirado. Tentando novo login...")
                if login_and_get_token():
                    headers["Authorization"] = f"Bearer {access_token}"
                    response = requests.post(url, json=dados, headers=headers)

            response.raise_for_status()
            print(f"[API] Sucesso ao enviar para {url}: {response.status_code}")

        except requests.RequestException as e:
            print(f"[API] Erro final ao enviar dados para {url}: {e}")

    # Inicia a tarefa em uma thread separada
    thread = threading.Thread(target=_task, daemon=True)
    thread.start()