import time
import concurrent.futures

def ler_batimentos():
    """
    Função que simula a leitura de um sensor, demorando 5 segundos,
    e retorna o valor lido.
    """
    print("Thread: Iniciando a leitura dos batimentos...")
    time.sleep(5)
    batimentos = 120
    print(f"Thread: Leitura concluída. Valor: {batimentos} bpm.")
    return batimentos

# O 'with' garante que as threads sejam finalizadas corretamente
with concurrent.futures.ThreadPoolExecutor() as executor:
    # Submete a função para ser executada em uma thread do pool.
    # Isso retorna um objeto 'Future' imediatamente.
    future = executor.submit(ler_batimentos)
    
    print("Programa Principal: A leitura de batimentos foi iniciada em segundo plano.")
    print("Programa Principal: Posso continuar executando outras tarefas aqui.")
    
    # Exemplo de outra tarefa no programa principal
    for i in range(3):
        print(f"Programa Principal: Executando tarefa {i+1}...")
        time.sleep(1)
        
    # Para obter o resultado da função, use o método .result() do future.
    # Se a thread ainda não terminou, esta chamada irá esperar por ela.
    print("Programa Principal: Aguardando o resultado da thread...")
    resultado_batimentos = future.result()
    
    print(f"\nPrograma Principal: Resultado final recebido! Batimentos: {resultado_batimentos} bpm.")