
import logging
from datetime import datetime
from pathlib import Path

import polars as pl
import pandas as pd

logger = logging.getLogger(__name__)


RAIZ_PROJETO = Path(__file__).resolve().parents[1]
PASTA_RAW = RAIZ_PROJETO / "data" / "raw"
PASTA_TRATADO = RAIZ_PROJETO / "data" / "tratado"

titular = ["NumCPFCNPJ", "NomTitularEmpreendimento"]
distribuidora = ["NumCNPJDistribuidora", "SigAgente", "NomAgente"]
municipios = ["NomMunicipio", "SigUF", "NomRegiao"]
empreendimento = [
    "CodEmpreendimento",
    "DscClasseConsumo",
    "DscSubGrupoTarifario",
    "MdaPotenciaInstaladaKW",
    "AnmPeriodoReferencia",
    "DscPorte",
    "CodCEP",
    "QtdUCRecebeCredito",
    "DthAtualizaCadastralEmpreend",
    "DscModalidadeHabilitado",
]


def encontrar_csv_mais_recente() -> Path:
    arquivos = list(PASTA_RAW.glob("*_geracao_distribuida.csv"))
    if not arquivos:
        raise FileNotFoundError(
            "Nenhum CSV de geração distribuída encontrado em "
            f"{PASTA_RAW}. Execute primeiro `python pipeline/01_coleta.py` "
            "para baixar a base da ANEEL."
        )
    return max(arquivos, key=lambda arquivo: arquivo.stat().st_mtime)


def transformar(caminho_csv: str | Path | None = None) -> pd.DataFrame:
    origem = Path(caminho_csv) if caminho_csv else encontrar_csv_mais_recente()
    if not origem.is_absolute():
        origem = (RAIZ_PROJETO / origem).resolve()
    if not origem.is_file():
        raise FileNotFoundError(f"CSV não encontrado: {origem}")

    logger.info("Abrindo arquivo CSV da pasta raw.")
    consulta = pl.scan_csv(
        origem,
        separator=";",
        quote_char='"',
        encoding="utf8",
        infer_schema=False,
    )

    colunas_entrada = consulta.collect_schema().names()
    colunas_saida = list(dict.fromkeys(titular + distribuidora + municipios + empreendimento))
    colunas_ausentes = sorted(set(colunas_saida) - set(colunas_entrada))
    if colunas_ausentes:
        raise ValueError(f"Colunas ausentes no CSV: {colunas_ausentes}")

    df_tratado = (
        consulta
        .filter(pl.col("SigAgente").str.strip_chars() == "Neoenergia PE")
        .filter(pl.col("SigUF").str.strip_chars() == "PE")
        .filter(pl.col("SigTipoGeracao").str.strip_chars() == "UFV")
        .filter(pl.col("NumCPFCNPJ").is_not_null())
        .filter(pl.col("NumCPFCNPJ").str.strip_chars() != "")
        .filter(pl.col("NomTitularEmpreendimento").is_not_null())
        .filter(pl.col("NomTitularEmpreendimento").str.strip_chars() != "")
        .select(colunas_saida)
        .collect(engine="streaming")
    )

    df_filtrado = pd.DataFrame(
        df_tratado.to_dict(as_series=False), columns=colunas_saida
    )
    logger.info(
        "DataFrame filtrado carregado: %d linhas e %d colunas",
        len(df_filtrado),
        len(df_filtrado.columns),
    )
    # Guarda o carimbo do CSV de origem para reutilizá-lo no arquivo derivado.
    df_filtrado.attrs["carimbo_geracao"] = origem.stem.removesuffix(
        "_geracao_distribuida"
    )
    return df_filtrado


def _extrair_e_salvar(
    df_filtrado: pd.DataFrame,
    colunas: list[str],
    nome_arquivo: str,
    preencher_nulos: bool = True,
    distintas: bool = False,
    tipos: dict[str, str] | None = None,
) -> pd.DataFrame:
    """Seleciona colunas, normaliza nulos e salva uma tabela derivada."""
    colunas_ausentes = sorted(set(colunas) - set(df_filtrado.columns))
    if colunas_ausentes:
        raise ValueError(f"Colunas ausentes no DataFrame: {colunas_ausentes}")

    df_extraido = df_filtrado.loc[:, colunas].copy()
    df_extraido = df_extraido.astype({coluna: "string" for coluna in colunas})
    if nome_arquivo == "titulares":
        # O mesmo CPF/CNPJ pode aparecer em vários empreendimentos e até com
        # grafias diferentes do titular. A dimensão exige uma linha por documento.
        df_extraido["NumCPFCNPJ"] = df_extraido["NumCPFCNPJ"].str.strip()
    if preencher_nulos:
        colunas_tipadas = set(tipos or {})
        colunas_texto = [
            coluna for coluna in colunas if coluna not in colunas_tipadas
        ]
        df_extraido[colunas_texto] = df_extraido[colunas_texto].fillna("N/I")
    if tipos:
        for coluna, tipo in tipos.items():
            if tipo == "date":
                df_extraido[coluna] = pd.to_datetime(
                    df_extraido[coluna], errors="coerce"
                ).dt.date
            elif tipo == "int":
                df_extraido[coluna] = pd.to_numeric(
                    df_extraido[coluna], errors="raise"
                ).astype("Int64")
            elif tipo == "float":
                valores = df_extraido[coluna].astype("string").str.strip()
                com_virgula_decimal = valores.str.contains(",", na=False)
                valores.loc[com_virgula_decimal] = (
                    valores.loc[com_virgula_decimal]
                    .str.replace(".", "", regex=False)
                    .str.replace(",", ".", regex=False)
                )
                df_extraido[coluna] = pd.to_numeric(
                    valores, errors="raise"
                ).astype("Float64")
            else:
                df_extraido[coluna] = df_extraido[coluna].astype(tipo)

    colunas_texto = [
        coluna
        for coluna in colunas
        if tipos is None or coluna not in tipos or tipos[coluna] == "string"
    ]
    for coluna in colunas_texto:
        df_extraido[coluna] = df_extraido[coluna].str.upper()

    if nome_arquivo == "titulares":
        df_extraido = df_extraido.drop_duplicates(
            subset=["NumCPFCNPJ"], keep="first"
        ).reset_index(drop=True)
    elif distintas:
        df_extraido = df_extraido.drop_duplicates().reset_index(drop=True)

    PASTA_TRATADO.mkdir(parents=True, exist_ok=True)
    carimbo = df_filtrado.attrs.get("carimbo_geracao")
    if not carimbo:
        carimbo = datetime.now().strftime("%Y%m%d_%H%M%S")
    caminho_saida = PASTA_TRATADO / f"{carimbo}_{nome_arquivo}.csv"
    df_extraido.to_csv(caminho_saida, index=False, sep=";", encoding="utf-8")
    logger.info("Arquivo %s salvo na pasta tratado.", nome_arquivo)
    return df_extraido


def exportar_titulares(df_filtrado: pd.DataFrame) -> pd.DataFrame:
    """Exporta CPF/CNPJ e titular como texto, preservando valores nulos."""
    return _extrair_e_salvar(
        df_filtrado,
        titular,
        "titulares",
        preencher_nulos=False,
        distintas=False,
        tipos={
            "NumCPFCNPJ": "string",
            "NomTitularEmpreendimento": "string",
        },
    )


def exportar_distribuidora(df_filtrado: pd.DataFrame) -> pd.DataFrame:
    """Exporta as colunas da distribuidora como texto e preenche nulos com N/I."""
    return _extrair_e_salvar(
        df_filtrado,
        distribuidora,
        "distribuidora",
        distintas=True,
        tipos={coluna: "string" for coluna in distribuidora},
    )


def extrair_municipios(df_filtrado: pd.DataFrame) -> pd.DataFrame:
    return _extrair_e_salvar(
        df_filtrado,
        municipios,
        "municipios",
        distintas=True,
        tipos={coluna: "string" for coluna in municipios},
    )


def extrair_empreendimentos(df_filtrado: pd.DataFrame) -> pd.DataFrame:
    return _extrair_e_salvar(
        df_filtrado,
        empreendimento,
        "empreendimentos",
        tipos={
            "CodEmpreendimento": "string",
            "DthAtualizaCadastralEmpreend": "date",
            "AnmPeriodoReferencia": "string",
            "DscModalidadeHabilitado": "string",
            "QtdUCRecebeCredito": "int",
            "DscPorte": "string",
            "MdaPotenciaInstaladaKW": "float",
            "DscSubGrupoTarifario": "string",
            "DscClasseConsumo": "string",
            "CodCEP": "string",
        },
    )


if __name__ == "__main__":
    df_filtrado = transformar()
    exportar_titulares(df_filtrado)
    exportar_distribuidora(df_filtrado)
    extrair_municipios(df_filtrado)
    extrair_empreendimentos(df_filtrado)
