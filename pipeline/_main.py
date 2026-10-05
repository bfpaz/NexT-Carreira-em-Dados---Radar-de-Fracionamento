import logging
from _coleta import executar_coleta
from _transformacao import executar_transformacao
from _carga import executar_carga

logging.basicConfig(level=logging.INFO, format="%(asctime)s | %(levelname)s | %(message)s")

def run_pipeline():
    logging.info("Iniciando pipeline de dados...")

    # 1. Coleta → retorna caminho do CSV bruto
    caminho_csv_bruto = executar_coleta()
    logging.info(f"Coleta concluída. Arquivo bruto: {caminho_csv_bruto}")

    # 2. Transformação → recebe CSV bruto e retorna CSV tratado
    caminho_csv_tratado = executar_transformacao(caminho_csv_bruto)
    logging.info(f"Transformação concluída. Arquivo tratado: {caminho_csv_tratado}")

    # 3. Carga → recebe CSV tratado e insere no banco
    executar_carga(caminho_csv_tratado)
    logging.info("Carga concluída com sucesso!")

if __name__ == "__main__":
    run_pipeline()
