import logging
import subprocess
import sys
from pathlib import Path

RAIZ_PROJETO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(RAIZ_PROJETO))

from pipeline.carga import carregar_no_banco
from pipeline.transforma import (
    exportar_distribuidora,
    exportar_titulares,
    extrair_empreendimentos,
    extrair_municipios,
    transformar,
)

SCRIPT_COLETA = RAIZ_PROJETO / "pipeline" / "coleta.py"
logger = logging.getLogger("pipeline")


def executar_pipeline() -> None:
    logger.info("Iniciando pipeline de coleta, transformação e carga.")
    subprocess.run(
        [sys.executable, str(SCRIPT_COLETA)],
        cwd=RAIZ_PROJETO,
        check=True,
    )

    df_filtrado = transformar()
    exportar_titulares(df_filtrado)
    exportar_distribuidora(df_filtrado)
    extrair_municipios(df_filtrado)
    extrair_empreendimentos(df_filtrado)

    carimbo = df_filtrado.attrs.get("carimbo_geracao")
    if not carimbo:
        raise ValueError("A transformação não informou o carimbo da coleta.")
    carregar_no_banco(carimbo, df_filtrado)
    logger.info("Pipeline concluída com sucesso.")


if __name__ == "__main__":
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s | %(levelname)s | %(message)s",
    )
    executar_pipeline()
