import serial
import time
from statistics import mean

try:
    from serial.serialutil import SerialException
except ImportError:
    SerialException = Exception

def ler_batimentos(
    duracao_segundos: int,
    porta_serial: str = '/dev/ttyACM0',
    # porta_serial: str = 'COM8',
    baud_rate: int = 9600,
    simulacao: bool = False
) -> int:
    """
    Mede os batimentos cardíacos. O Arduino agora faz o pré-cálculo do BPM.
    Esta função coleta os valores de BPM enviados pelo Arduino durante um
    período e retorna a média deles.
    """
    # O modo de simulação continua funcionando como antes, sem alterações.
    if simulacao:
        print("\n--- MODO DE SIMULAÇÃO ATIVADO ---")
        print(f"Gerando dados de batimentos por {duracao_segundos} segundos...")
        bpm_simulado_alvo = 75
        intervalo_entre_picos = 60.0 / bpm_simulado_alvo
        peak_timestamps = []
        start_time = time.time()
        proximo_pico = start_time + intervalo_entre_picos
        while time.time() - start_time < duracao_segundos:
            if time.time() >= proximo_pico:
                print(f"SIM: Pico de batimento simulado.")
                peak_timestamps.append(time.time())
                proximo_pico += intervalo_entre_picos
            time.sleep(0.05)
        print("--- FIM DA SIMULAÇÃO ---")
        if not peak_timestamps: return 0 # Adicionado para evitar erro se não houver picos
        # ... o resto da lógica de cálculo da simulação permanece igual
        intervals = [peak_timestamps[i] - peak_timestamps[i - 1] for i in range(1, len(peak_timestamps))]
        if not intervals: return 0
        avg_interval = mean(intervals)
        return int(60 / avg_interval)

    else:
        # --- NOVA LÓGICA PARA LER O BPM PRÉ-CALCULADO DO ARDUINO ---
        print(f"\nFunção 'ler_batimentos' (MODO REAL). Lendo BPMs do Arduino por {duracao_segundos}s...")
        
        leituras_de_bpm = [] # Lista para armazenar os BPMs recebidos

        try:
            with serial.Serial(porta_serial, baud_rate, timeout=1) as ser:
                print(f"Conexão com Arduino estabelecida em {porta_serial}.")
                ser.flushInput()
                start_time = time.time()

                while time.time() - start_time < duracao_segundos:
                    # Verifica se há dados na porta serial para ler
                    if ser.in_waiting > 0:
                        try:
                            # Lê a linha enviada pelo Arduino (ex: "78.50")
                            linha = ser.readline().decode('utf-8').strip()
                            if linha:
                                # Converte o texto para um número float
                                bpm_recebido = float(linha)
                                print(f"-> BPM recebido do Arduino: {bpm_recebido:.2f}")
                                leituras_de_bpm.append(bpm_recebido)
                        except (ValueError, UnicodeDecodeError):
                            # Ignora linhas que não são números válidos, sem parar
                            pass
        except SerialException as e:
            print(f"ERRO CRÍTICO: Não foi possível conectar ao Arduino em '{porta_serial}'. {e}")
            return 0

    # --- CÁLCULO FINAL DA MÉDIA ---
    if not leituras_de_bpm:
        print("Medição concluída. Nenhum valor de BPM foi recebido do Arduino.")
        return 0
    else:
        # Calcula a média de todas as leituras de BPM recebidas
        bpm_medio = mean(leituras_de_bpm)
        print(f"Medição concluída. A média de BPM do período foi: {bpm_medio:.2f}")
        # Retorna o valor como um número inteiro
        return int(bpm_medio)