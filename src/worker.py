"""
Worker Simples - Processa Fila de Análises
"""
import time
from database import init_db
from funcao2_processar import processar_fila


def main():
    """Worker que processa fila continuamente"""
    print("\n" + "="*60)
    print("⚡ Worker de Processamento")
    print("="*60)
    print("Aguardando análises na fila...")
    print("="*60 + "\n")

    processadas = 0

    while True:
        try:
            # Chama FUNÇÃO 2
            resultado = processar_fila()

            if resultado:
                processadas += 1
                print(f"\n📊 Total processado: {processadas}")
            else:
                time.sleep(2)  # Aguarda se fila vazia

        except KeyboardInterrupt:
            print(f"\n\n🛑 Worker encerrado. Total processado: {processadas}")
            break
        except Exception as e:
            print(f"\n❌ Erro: {e}")
            time.sleep(1)


if __name__ == '__main__':
    init_db()
    main()
