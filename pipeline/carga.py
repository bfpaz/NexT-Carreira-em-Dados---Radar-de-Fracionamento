import logging
import unicodedata
from pathlib import Path

import pandas as pd
from sqlalchemy import create_engine, text
from sqlalchemy.dialects.postgresql import ENUM

RAIZ_PROJETO = Path(__file__).resolve().parents[1]
PASTA_TRATADO = RAIZ_PROJETO / "data" / "tratado"
SQL_CRIACAO_TABELAS = RAIZ_PROJETO / "sql" / "criar_tabelas.sql"
logger = logging.getLogger(__name__)

try:
    from config import POSTGRES_URL
except ImportError:
    from config import POSTGRESS_URL as POSTGRES_URL


COLUNAS_ARQUIVOS = {
    "titulares": {
        "NumCPFCNPJ": "string",
        "NomTitularEmpreendimento": "string",
    },
    "distribuidora": {
        "NumCNPJDistribuidora": "string",
        "SigAgente": "string",
        "NomAgente": "string",
    },
    "municipios": {
        "NomMunicipio": "string",
        "SigUF": "string",
        "NomRegiao": "string",
    },
    "empreendimentos": {
        "CodEmpreendimento": "string",
        "DscClasseConsumo": "string",
        "DscSubGrupoTarifario": "string",
        "MdaPotenciaInstaladaKW": "float",
        "AnmPeriodoReferencia": "string",
        "DscPorte": "string",
        "CodCEP": "string",
        "QtdUCRecebeCredito": "int",
        "DthAtualizaCadastralEmpreend": "date",
        "DscModalidadeHabilitado": "string",
    },
}

ENUMS_POSTGRES = {
    "DscClasseConsumo": ENUM(
        "Residencial",
        "Comercial",
        "Rural",
        "Industrial",
        "Poder Público",
        "Serviço Público",
        "Iluminação pública",
        name="classe_consumo_enum",
        create_type=False,
    ),
    "DscSubGrupoTarifario": ENUM(
        "A1",
        "A2",
        "A3",
        "A3a",
        "A4",
        "AS",
        "B1",
        "B2",
        "B3",
        "B4",
        name="subgrupo_tarifario_enum",
        create_type=False,
    ),
    "DscPorte": ENUM(
        "Microgeracao",
        "Minigeracao",
        name="porte_enum",
        create_type=False,
    ),
}


def _ler_csv(caminho: Path, tabela: str) -> pd.DataFrame:
    dados = pd.read_csv(
        caminho,
        sep=";",
        encoding="utf-8",
        dtype="string",
        keep_default_na=False,
    )
    colunas = COLUNAS_ARQUIVOS[tabela]
    ausentes = set(colunas) - set(dados.columns)
    if ausentes:
        raise ValueError(f"Colunas ausentes em {caminho.name}: {sorted(ausentes)}")

    dados = dados[list(colunas)].replace("", pd.NA)
    for coluna, tipo in colunas.items():
        if tipo == "int":
            dados[coluna] = pd.to_numeric(dados[coluna], errors="raise").astype("Int64")
        elif tipo == "float":
            valores = dados[coluna].astype("string").str.strip()
            virgula_decimal = valores.str.contains(",", na=False)
            valores.loc[virgula_decimal] = (
                valores.loc[virgula_decimal]
                .str.replace(".", "", regex=False)
                .str.replace(",", ".", regex=False)
            )
            dados[coluna] = pd.to_numeric(valores, errors="raise").astype("Float64")
        elif tipo == "date":
            dados[coluna] = pd.to_datetime(dados[coluna], errors="coerce").dt.date
        else:
            dados[coluna] = dados[coluna].astype("string").str.strip()
    return dados


def _chave_texto(valor) -> str | None:
    if pd.isna(valor):
        return None
    return str(valor).strip().upper()


def _mapa_id(conexao, tabela: str, chave: str, id_coluna: str) -> dict:
    consulta = text(f'SELECT "{chave}", "{id_coluna}" FROM {tabela}')
    dados = pd.read_sql(consulta, conexao)
    return {
        _chave_texto(valor): int(identificador)
        for valor, identificador in zip(dados[chave], dados[id_coluna])
    }


def _mapa_id_municipio(conexao) -> dict:
    consulta = text(
        'SELECT "NomMunicipio", "SigUF", "NomRegiao", "idMunicipio" '
        "FROM municipios"
    )
    dados = pd.read_sql(consulta, conexao)
    return {
        tuple(_chave_texto(linha[coluna]) for coluna in ("NomMunicipio", "SigUF", "NomRegiao")): int(linha["idMunicipio"])
        for _, linha in dados.iterrows()
    }


def _preparar_chaves_estrangeiras(
    empreendimentos: pd.DataFrame,
    df_filtrado: pd.DataFrame,
    mapa_titulares: dict,
    mapa_distribuidoras: dict,
    mapa_municipios: dict,
) -> pd.DataFrame:
    colunas_origem = [
        "CodEmpreendimento",
        "NumCPFCNPJ",
        "NumCNPJDistribuidora",
        "NomMunicipio",
        "SigUF",
        "NomRegiao",
    ]
    ausentes = set(colunas_origem) - set(df_filtrado.columns)
    if ausentes:
        raise ValueError(
            "DataFrame transformado sem colunas para relacionar as FKs: "
            f"{sorted(ausentes)}"
        )

    referencias = df_filtrado[colunas_origem].copy()
    referencias["CodEmpreendimento"] = referencias["CodEmpreendimento"].map(_chave_texto)
    referencias = referencias.drop_duplicates(subset=["CodEmpreendimento"], keep="first")

    referencias["idTitular"] = referencias["NumCPFCNPJ"].map(
        lambda valor: mapa_titulares.get(_chave_texto(valor))
    )
    referencias["idDistribuidora"] = referencias["NumCNPJDistribuidora"].map(
        lambda valor: mapa_distribuidoras.get(_chave_texto(valor))
    )
    referencias["idMunicipio"] = referencias.apply(
        lambda linha: mapa_municipios.get(
            tuple(_chave_texto(linha[coluna]) for coluna in ("NomMunicipio", "SigUF", "NomRegiao"))
        ),
        axis=1,
    )

    referencias = referencias.set_index("CodEmpreendimento")
    codigos = empreendimentos["CodEmpreendimento"].map(_chave_texto)
    for chave in ("idTitular", "idDistribuidora", "idMunicipio"):
        empreendimentos[chave] = codigos.map(referencias[chave])
        if empreendimentos[chave].isna().any():
            faltantes = empreendimentos.loc[
                empreendimentos[chave].isna(), "CodEmpreendimento"
            ].head(5).tolist()
            raise ValueError(
                f"Não foi possível preencher {chave} para os empreendimentos: {faltantes}"
            )
        empreendimentos[chave] = empreendimentos[chave].astype("int64")

    return empreendimentos


def _chave_enum(valor: str) -> str:
    texto = unicodedata.normalize("NFKD", str(valor))
    sem_acentos = "".join(
        caractere
        for caractere in texto
        if not unicodedata.combining(caractere)
    )
    return sem_acentos.strip().casefold()


def _normalizar_enums(empreendimentos: pd.DataFrame) -> None:
    valores_validos = {
        "DscClasseConsumo": [
            "Residencial",
            "Comercial",
            "Rural",
            "Industrial",
            "Poder Público",
            "Serviço Público",
            "Iluminação pública",
        ],
        "DscSubGrupoTarifario": [
            "A1", "A2", "A3", "A3a", "A4", "AS", "B1", "B2", "B3", "B4"
        ],
        "DscPorte": ["Microgeracao", "Minigeracao"],
    }
    for coluna, rotulos in valores_validos.items():
        mapa = {_chave_enum(rotulo): rotulo for rotulo in rotulos}
        valores = empreendimentos[coluna]
        normalizados = valores.map(
            lambda valor: pd.NA
            if pd.isna(valor)
            else mapa.get(_chave_enum(valor))
        )
        desconhecidos = valores[normalizados.isna() & valores.notna()].drop_duplicates()
        if not desconhecidos.empty:
            raise ValueError(
                f"Valores não previstos no ENUM de {coluna}: "
                f"{desconhecidos.head(10).tolist()}"
            )
        empreendimentos[coluna] = normalizados.astype("string")


def carregar_no_banco(carimbo: str, df_filtrado: pd.DataFrame) -> None:
    arquivos = {
        tabela: PASTA_TRATADO / f"{carimbo}_{tabela}.csv"
        for tabela in COLUNAS_ARQUIVOS
    }
    ausentes = [str(caminho) for caminho in arquivos.values() if not caminho.is_file()]
    if ausentes:
        raise FileNotFoundError(
            "Arquivos tratados ausentes; carga cancelada: " + ", ".join(ausentes)
        )
    if not SQL_CRIACAO_TABELAS.is_file():
        raise FileNotFoundError(f"Arquivo SQL não encontrado: {SQL_CRIACAO_TABELAS}")

    dados = {tabela: _ler_csv(caminho, tabela) for tabela, caminho in arquivos.items()}
    dados["titulares"]["NumCPFCNPJ"] = dados["titulares"]["NumCPFCNPJ"].str.strip()
    dados["titulares"] = dados["titulares"].drop_duplicates(
        subset=["NumCPFCNPJ"], keep="first"
    )
    dados["distribuidora"]["NumCNPJDistribuidora"] = (
        dados["distribuidora"]["NumCNPJDistribuidora"].str.strip()
    )
    dados["distribuidora"] = dados["distribuidora"].drop_duplicates(
        subset=["NumCNPJDistribuidora"], keep="first"
    )
    dados["municipios"] = dados["municipios"].drop_duplicates(
        subset=["NomMunicipio", "SigUF", "NomRegiao"], keep="first"
    )

    _normalizar_enums(dados["empreendimentos"])

    engine = create_engine(POSTGRES_URL)
    try:
        with engine.begin() as conexao:
            comandos_sql = SQL_CRIACAO_TABELAS.read_text(encoding="utf-8").split(";")
            for comando in comandos_sql:
                if comando.strip():
                    conexao.exec_driver_sql(comando)

            for tabela in ("titulares", "distribuidora", "municipios"):
                dados[tabela].to_sql(
                    tabela,
                    conexao,
                    if_exists="append",
                    index=False,
                    chunksize=5000,
                )

            mapa_titulares = _mapa_id(
                conexao, "titulares", "NumCPFCNPJ", "idTitular"
            )
            mapa_distribuidoras = _mapa_id(
                conexao,
                "distribuidora",
                "NumCNPJDistribuidora",
                "idDistribuidora",
            )
            mapa_municipios = _mapa_id_municipio(conexao)

            empreendimentos = _preparar_chaves_estrangeiras(
                dados["empreendimentos"],
                df_filtrado,
                mapa_titulares,
                mapa_distribuidoras,
                mapa_municipios,
            )
            empreendimentos.to_sql(
                "empreendimentos",
                conexao,
                if_exists="append",
                index=False,
                chunksize=5000,
                dtype=ENUMS_POSTGRES,
            )
        logger.info("Carga concluída no PostgreSQL para o carimbo %s.", carimbo)
    finally:
        engine.dispose()
