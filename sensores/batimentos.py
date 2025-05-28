import serial
import time
from statistics import mean

# Esta é a função que seu código irá importar e chamar.
# Ela é bloqueante: executa pelo tempo determinado e só então retorna o valor.
def ler_batimentos(
    duracao_segundos: int,
    porta_serial: str = '/dev/ttyUSB0',
    # porta_serial: str = 'COM6',  # Use 'COM3' para Windows, '/dev/ttyACM0' para Linux
    baud_rate: int = 9600
) -> int:
    """
    Conecta-se ao Arduino, mede os batimentos cardíacos por um período
    determinado e retorna o BPM médio calculado. Esta função é bloqueante.

    Args:
        duracao_segundos (int): Por quantos segundos a medição deve ocorrer.
        porta_serial (str): A porta serial onde o Arduino está conectado.
        baud_rate (int): A taxa de bauds (deve ser a mesma do código Arduino).

    Returns:
        int: O valor do BPM (Batimentos Por Minuto) calculado. Retorna 0 se
             não for possível medir.
    """
    print(f"Função 'ler_batimentos' iniciada. Medindo por {duracao_segundos}s...")

    # --- Configurações do Algoritmo de BPM ---
    PEAK_THRESHOLD = 600
    REFRACTORY_PERIOD = 0.3 # 300ms

    # --- Variáveis de controle ---
    peak_timestamps = []
    last_peak_time = 0
    last_value = 0

    try:
        # 'with' garante que a porta serial será aberta e fechada corretamente
        with serial.Serial(porta_serial, baud_rate, timeout=0.1) as ser:
            print(f"Conexão com Arduino estabelecida em {porta_serial}.")
            ser.flushInput() # Limpa qualquer lixo na entrada da serial

            start_time = time.time()
            while time.time() - start_time < duracao_segundos:
                try:
                    linha = ser.readline().decode('utf-8').rstrip()
                    if not linha:
                        continue # Pula para a próxima iteração se a linha estiver vazia

                    current_value = int(linha)
                    current_time = time.time()

                    # Lógica de detecção de pico (mesma de antes)
                    is_peak = (
                        last_value > PEAK_THRESHOLD and
                        current_value < last_value and
                        (current_time - last_peak_time) > REFRACTORY_PERIOD
                    )

                    if is_peak:
                        peak_timestamps.append(current_time)
                        last_peak_time = current_time

                    last_value = current_value

                except (ValueError, UnicodeDecodeError):
                    # Ignora linhas malformadas sem parar a execução
                    continue
                except Exception as e:
                    print(f"Erro inesperado durante a leitura: {e}")
                    # Em um erro grave, podemos optar por parar
                    break

    except serial.SerialException as e:
        print(f"ERRO CRÍTICO: Não foi possível conectar ao Arduino em '{porta_serial}'. {e}")
        return 0 # Retorna 0 em caso de falha de conexão

    # --- Cálculo Final do BPM ---
    if len(peak_timestamps) < 2:
        print("Medição concluída. Batimentos insuficientes para calcular o BPM.")
        return 0
    else:
        intervals = [peak_timestamps[i] - peak_timestamps[i-1] for i in range(1, len(peak_timestamps))]
        avg_interval = mean(intervals)
        bpm = int(60 / avg_interval)
        print(f"Função 'ler_batimentos' concluída. BPM calculado: {bpm}")
        return bpm


# Bloco para teste direto do arquivo (não afeta a importação)
if __name__ == "__main__":
    print("--- Testando o módulo monitor_cardiaco.py diretamente ---")
    # Simula a chamada que seu outro código faria
    bpm_resultado = ler_batimentos(15, porta_serial='/dev/ttyACM0')

    print("\n--- TESTE FINALIZADO ---")
    if bpm_resultado > 0:
        print(f"Resultado do teste: {bpm_resultado} BPM")
    else:
        print("Resultado do teste: Falha na medição.")