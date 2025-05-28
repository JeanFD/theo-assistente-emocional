import threading
import requests

# URLs dos seus endpoints específicos
URL_REGISTRO_SENTIMENTO = 'http://192.168.1.110:8000/api/registro-sentimento/'
URL_REGISTRO_BPM = 'http://192.168.1.110:8000/api/registro-bpm/'
URL_PERFIL = 'http://192.168.1.110:8000/api/perfil/' # Pode precisar de um ID, ex: /api/perfil/1/

# --- Função para Sentimentos ---
def enviar_dados_sentimento(dados_sentimento: dict) -> None:
    """
    Envia os dados de sentimento para o servidor.
    """
    def _task():
        payload = {
            "usuario_id": 1,
            "sentimento": dados_sentimento.get("sentimento"),
            "tipo": dados_sentimento.get("tipo"),
            "escala": dados_sentimento.get("escala"),
            # "usuario_id": ID_DO_USUARIO_LOGADO # Você precisará adicionar o ID do usuário aqui
        }
        try:
            # Assumindo que sua API espera um POST para criar um novo registro
            print(payload)
            response = requests.post(URL_REGISTRO_SENTIMENTO, json=payload, timeout=5)
            print(response)
            response.raise_for_status()
            print(f"[API] Sentimento enviado: {response.status_code}, {response.json()}")
        except requests.RequestException as e:
            print(f"[API] Erro ao enviar sentimento: {e}")

    thread = threading.Thread(target=_task, daemon=True)
    thread.start()

# --- Função para BPM ---
def enviar_dados_bpm(dados_bpm: dict) -> None:

    """
    Envia os dados de BPM para o servidor.
    """
    def _task():
        payload = {
            "usuario_id": 1,
            "bpm": dados_bpm.get("bpm"),
            # "usuario_id": ID_DO_USUARIO_LOGADO # Adicionar ID do usuário
        }
        try:
            print(payload)

            response = requests.post(URL_REGISTRO_BPM, json=payload, timeout=5)
            response.raise_for_status()
            
            print(f"[API] BPM enviado: {response.status_code}, {response.json()}")
        except requests.RequestException as e:
            print(f"[API] Erro ao enviar BPM: {e}")

    thread = threading.Thread(target=_task, daemon=True)
    thread.start()

# --- Função para Perfil ---
def enviar_dados_perfil(dados_perfil: dict, usuario_id=None) -> None: # Adicionado usuario_id opcional
    """
    Envia (atualiza) os dados do perfil para o servidor.
    A API de perfil geralmente usa PUT ou PATCH para um recurso existente.
    """
    def _task():
        payload = {
            "usuario_id": 1,
            "sexo": dados_perfil.get("sexo"),
            "idade": dados_perfil.get("idade"),
            # "voz": dados_perfil.get("voz") # Se sua API de perfil também aceitar isso
        }
        # Se sua API de perfil requer um ID na URL para atualizar (ex: /api/perfil/1/)
        # e você tem esse ID, você pode construir a URL dinamicamente.
        # Caso contrário, se for um POST para criar ou um PUT para um endpoint fixo, ajuste.
        
        # Exemplo para PUT (atualização completa)
        # Você precisaria de uma forma de obter o ID do perfil do usuário logado.
        # Se não houver perfil, talvez seja um POST para criar.
        # Por simplicidade, vamos assumir que você tem um ID ou que a API lida com isso.
        
        # url_final_perfil = URL_PERFIL
        # if usuario_id:
        #     url_final_perfil = f"{URL_PERFIL}{usuario_id}/" # Exemplo: /api/perfil/1/
        
        try:
            # Se for criar um novo perfil ou se o endpoint não requer ID na URL para PUT
            # response = requests.post(URL_PERFIL, json=payload, timeout=5) 
            # Se for atualizar um perfil existente (precisa do ID)
            # response = requests.put(url_final_perfil, json=payload, timeout=5)
            
            # Como sua APIView 'PerfilAPIView' provavelmente lida com GET/POST/PUT/PATCH
            # para o perfil do usuário autenticado, um POST ou PUT para URL_PERFIL pode ser suficiente
            # dependendo da sua implementação no Django.
            
            # Vamos simular um PUT, assumindo que o backend identifica o usuário pela sessão/token
            response = requests.post(URL_PERFIL, json=payload, timeout=5) # Ou POST/PATCH
            response.raise_for_status()
            print(f"[API] Perfil atualizado: {response.status_code}, {response.json()}")
        except requests.RequestException as e:
            print(f"[API] Erro ao atualizar perfil: {e}")

    thread = threading.Thread(target=_task, daemon=True)
    thread.start()