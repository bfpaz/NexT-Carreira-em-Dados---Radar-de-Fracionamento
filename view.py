import sys
from pathlib import Path

# Pandas converte o resultado da consulta em DataFrame.
import pandas as pd
import streamlit as st
from sqlalchemy import create_engine, text


# Adiciona a raiz do projeto ao caminho de importação para localizar config.py.
RAIZ_PROJETO = Path(__file__).resolve().parents[1]
if str(RAIZ_PROJETO) not in sys.path:
    sys.path.insert(0, str(RAIZ_PROJETO))

# Define os metadados e o layout da página Streamlit.
st.set_page_config(
    page_title="Radar de Fracionamento",
    page_icon="🔎",
    layout="wide",
)


@st.cache_resource
def obter_engine():
    # Cria e reutiliza o mecanismo de conexão com o PostgreSQL.
    from config import POSTGRES_URL

    return create_engine(POSTGRES_URL, pool_pre_ping=True)


def consultar(sql: str) -> pd.DataFrame:
    # Executa a consulta recebida e devolve o resultado como DataFrame.
    with obter_engine().connect() as conexao:
        return pd.read_sql_query(text(sql), conexao)


# Identifica os titulares que ultrapassam os limites de potência e resume os
# resultados por porte, classe de consumo e subgrupo tarifário.
SQL_SUSPEITOS_CATEGORIZADO = """
SELECT
    -- Campos que identificam cada grupo exibido nos gráficos.
    e."DscPorte" AS porte,
    e."DscClasseConsumo" AS classe_consumo,
    e."DscSubGrupoTarifario" AS subgrupo,
    -- Conta titulares sem duplicá-los e soma a potência instalada.
    COUNT(DISTINCT e."idTitular") AS qtd_suspeitos,
    SUM(e."MdaPotenciaInstaladaKW") AS potencia_total_kw
FROM empreendimentos e
INNER JOIN (
    -- Seleciona titulares e municípios cuja potência acumulada excede o limite.
    SELECT
        e2."idTitular",
        e2."idMunicipio",
        e2."DscPorte"
    FROM empreendimentos e2
    -- Considera apenas os portes sujeitos às regras de potência.
    WHERE e2."DscPorte" IN ('Microgeracao', 'Minigeracao')
    -- Calcula a potência acumulada de cada titular por município e porte.
    GROUP BY
        e2."idTitular",
        e2."idMunicipio",
        e2."DscPorte"
    HAVING
        -- Microgeração é sinalizada quando ultrapassa 75 kW.
        (
            e2."DscPorte" = 'Microgeracao'
            AND SUM(e2."MdaPotenciaInstaladaKW") > 75
        )
        OR
        -- Minigeração é sinalizada quando ultrapassa 3.000 kW.
        (
            e2."DscPorte" = 'Minigeracao'
            AND SUM(e2."MdaPotenciaInstaladaKW") > 3000
        )
) suspeitos
    -- Relaciona os empreendimentos aos titulares identificados como suspeitos.
    ON e."idTitular" = suspeitos."idTitular"
-- Consolida o resultado para cada combinação mostrada nos gráficos.
GROUP BY
    e."DscPorte",
    e."DscClasseConsumo",
    e."DscSubGrupoTarifario"
ORDER BY qtd_suspeitos DESC
"""

# Lista os grupos por titular, município e porte que excedem os limites de
# potência, incluindo quantidade de empreendimentos e potência acumulada.
SQL_SUSPEITOS_POR_TITULAR = """
SELECT
    e."idTitular" AS id_titular,
    e."idMunicipio" AS id_municipio,
    e."DscPorte" AS porte,
    COUNT(e."idEmpreendimento") AS qtd_empreendimentos,
    SUM(e."MdaPotenciaInstaladaKW") AS potencia_total_kw
FROM empreendimentos e
GROUP BY
    e."idTitular",
    e."idMunicipio",
    e."DscPorte"
HAVING
    (
        e."DscPorte" = 'Microgeracao'
        AND SUM(e."MdaPotenciaInstaladaKW") > 75
    )
    OR
    (
        e."DscPorte" = 'Minigeracao'
        AND SUM(e."MdaPotenciaInstaladaKW") > 3000
    )
ORDER BY e."idTitular"
"""


st.title("🔎 Radar de Fracionamento")

# Consulta os dados e interrompe a execução caso o PostgreSQL não esteja acessível.
try:
    quadro = consultar(SQL_SUSPEITOS_CATEGORIZADO)
    quadro_titulares = consultar(SQL_SUSPEITOS_POR_TITULAR)
except Exception:
    st.error("Não foi possível consultar o PostgreSQL.")
    st.info(
        "Confira se o banco está ativo, se as tabelas foram carregadas e se "
        "POSTGRES_URL em config.py aponta para o banco correto."
    )
    st.stop()

# Separa o resumo atual e o novo detalhamento em abas.
aba_categorias, aba_titulares = st.tabs(
    ["Resumo por categoria", "Suspeitos por titular e município"]
)

with aba_categorias:
    # Combina classe e subgrupo tarifário para formar as categorias dos gráficos.
    quadro["categoria"] = (
        quadro["classe_consumo"].astype(str)
        + " | "
        + quadro["subgrupo"].astype(str)
    )

    # Permite escolher Minigeração, Microgeração ou os dois portes.
    selecao_porte = st.selectbox(
        "Selecione o porte para exibição",
        options=["Ambas", "Minigeracao", "Microgeracao"],
        format_func={
            "Ambas": "Ambas",
            "Minigeracao": "Minigeração",
            "Microgeracao": "Microgeração",
        }.get,
    )
    # Traduz a escolha exibida na tela para os valores usados no banco.
    portes_selecionados = (
        ["Minigeracao", "Microgeracao"]
        if selecao_porte == "Ambas"
        else [selecao_porte]
    )
    # Mantém no resultado apenas os portes selecionados.
    quadro = quadro[quadro["porte"].isin(portes_selecionados)]

    # Cria os dois espaços de gráfico, lado a lado.
    potencia, quantidade = st.columns(2)
    # Usa o mesmo fluxo para desenhar potência e quantidade de suspeitos.
    for coluna, metrica, titulo in (
        (potencia, "potencia_total_kw", "Potência total (kW)"),
        (quantidade, "qtd_suspeitos", "Quantidade de suspeitos"),
    ):
        # Organiza categorias nas linhas e portes nas colunas para comparação.
        comparativo = quadro.pivot_table(
            index="categoria",
            columns="porte",
            values=metrica,
            aggfunc="sum",
            fill_value=0,
        )
        # Mantém a ordem dos portes e preenche com zero os que não têm registros.
        comparativo = comparativo.reindex(
            columns=[
                porte
                for porte in ["Minigeracao", "Microgeracao"]
                if porte in portes_selecionados
            ],
            fill_value=0,
        )

        # Desenha o gráfico na coluna correspondente, com uma cor por porte.
        with coluna:
            st.subheader(titulo)
            cores = {
                "Minigeracao": "#2563EB",
                "Microgeracao": "#F97316",
            }
            st.bar_chart(
                comparativo,
                horizontal=True,
                color=[cores[porte] for porte in portes_selecionados],
            )

with aba_titulares:
    # Exibe os totais de titulares suspeitos e municípios em cartões lado a lado.
    total_suspeitos = quadro_titulares["id_titular"].nunique()
    total_municipios = quadro_titulares["id_municipio"].nunique()
    quadro_suspeitos, quadro_municipios = st.columns(2)
    quadro_suspeitos.metric("Total de suspeitos", f"{total_suspeitos:,}".replace(",", "."))
    quadro_municipios.metric("Total de municípios", f"{total_municipios:,}".replace(",", "."))

    # Apresenta as linhas retornadas pela consulta detalhada.
    st.dataframe(quadro_titulares, width="stretch", hide_index=True)



