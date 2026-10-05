from pathlib import Path
from zipfile import ZipFile
from datetime import datetime
import logging
import requests

def executar_coleta():
    
    
    
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s | %(levelname)s | %(message)s",
    )
    logger = logging.getLogger(__name__)
    
    URL = "https://dadosabertos.aneel.gov.br/dataset/5e0fafd2-21b9-4d5b-b622-40438d40aba2/resource/b1bd71e7-d0ad-4214-9053-cbd58e9564a7/download/empreendimento-geracao-distribuida.zip"
    
    PASTA_RAW = Path("data/raw")
    CARIMBO_GERACAO = datetime.now().strftime("%Y%m%d_%H%M%S")
    NOME_ARQUIVO = f"{CARIMBO_GERACAO}_geracao_distribuida"
    DESTINO_ZIP = PASTA_RAW / f"{NOME_ARQUIVO}.zip"
    DESTINO_CSV = PASTA_RAW / f"{NOME_ARQUIVO}.csv"
    
    PASTA_RAW.mkdir(parents=True, exist_ok=True)
    
    logger.info("Início da coleta de geração distribuída.")
    response = requests.get(URL, timeout=60)
    response.raise_for_status()
    
    DESTINO_ZIP.write_bytes(response.content)
    
    with ZipFile(DESTINO_ZIP, "r") as zip_file:
        arquivos_csv = [
            nome for nome in zip_file.namelist()
            if nome.lower().endswith(".csv")
        ]
    
        if not arquivos_csv:
            raise FileNotFoundError("Nenhum arquivo CSV foi encontrado no ZIP baixado.")
    
        with zip_file.open(arquivos_csv[0]) as arquivo_csv:
            DESTINO_CSV.write_bytes(arquivo_csv.read())
    
    logger.info("Fim da coleta de geração distribuída.")
    logger.info("CSVs encontrados: %s", arquivos_csv)
    logger.info("ZIP salvo na pasta raw.")
    logger.info("CSV salvo na pasta raw.")

    return DESTINO_CSV