import sys
from pathlib import Path

# Pandas converte o resultado da consulta em DataFrame.
import pandas as pd
import streamlit as st
from sqlalchemy import create_engine, text
from dotenv import load_dotenv
import os


# Carregar variáveis do .env
load_dotenv()

DB_USER = os.getenv("DB_USER")
DB_PASSWORD = os.getenv("DB_PASSWORD")
DB_HOST = os.getenv("DB_HOST")
DB_PORT = os.getenv("DB_PORT")
DB_NAME = os.getenv("DB_NAME")

# Montar a URL de conexão
POSTGRES_URL = f"postgresql+psycopg2://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/{DB_NAME}"


# Define os metadados e o layout da página Streamlit.
st.set_page_config(
    page_title="Radar de Fracionamento",
    page_icon="🔎",
    layout="wide",
)


@st.cache_resource
def obter_engine():
    return create_engine(POSTGRES_URL, pool_pre_ping=True)


def consultar(sql: str) -> pd.DataFrame:
    # Executa a consulta recebida e devolve o resultado como DataFrame.
    with obter_engine().connect() as conexao:
        return pd.read_sql_query(text(sql), conexao)


# Identifica os titulares que ultrapassam os limites de potência e resume os
# resultados por porte, classe de consumo e subgrupo tarifário.
SQL_SUSPEITOS_CATEGORIZADO = """
SELECT
    u.porte,
    u.classe_consumo,
    u.subgrupo_tarifario,
    COUNT(DISTINCT t.id_titular) AS qtd_suspeitos,
    SUM(u.potencia_instalada) AS potencia_total_kw
FROM usina u
JOIN titular t ON u.id_titular = t.id_titular
JOIN municipio m ON u.id_municipio = m.id_municipio
WHERE m.estado = 'PE'
GROUP BY u.porte, u.classe_consumo, u.subgrupo_tarifario
HAVING
    (u.porte = 'Microgeracao' AND SUM(u.potencia_instalada) > 75)
    OR (u.porte = 'Minigeracao' AND SUM(u.potencia_instalada) > 3000)
ORDER BY qtd_suspeitos DESC
"""

# Lista os grupos por titular, município e porte que excedem os limites de
# potência, incluindo quantidade de empreendimentos e potência acumulada.
SQL_SUSPEITOS_POR_TITULAR = """
SELECT
    t.cpf_cnpj,
    t.nome_titular,
    u.porte,
    m.nome_municipio,
    COUNT(u.id_usina) AS qtd_usinas,
    SUM(u.potencia_instalada) AS potencia_total_kw
FROM usina u
JOIN titular t ON u.id_titular = t.id_titular
JOIN municipio m ON u.id_municipio = m.id_municipio
WHERE m.estado = 'PE'
GROUP BY t.cpf_cnpj, t.nome_titular, u.porte, m.nome_municipio
HAVING
    (u.porte = 'Microgeracao' AND SUM(u.potencia_instalada) > 75)
    OR (u.porte = 'Minigeracao' AND SUM(u.potencia_instalada) > 3000)
ORDER BY potencia_total_kw DESC
"""
SQL_SUSPEITOS_TITULARES_DETALHADO = """
SELECT t.cpf_cnpj,
       t.nome_titular,
       u.porte,
       m.nome_municipio,
       COUNT(u.id_usina) AS qtd_usinas,
       SUM(u.potencia_instalada) AS potencia_total
FROM usina u
JOIN titular t ON u.id_titular = t.id_titular
JOIN municipio m ON u.id_municipio = m.id_municipio
WHERE m.estado = 'PE'
GROUP BY t.cpf_cnpj, t.nome_titular, u.porte, m.nome_municipio
HAVING (u.porte = 'Microgeracao' AND SUM(u.potencia_instalada) > 75)
    OR (u.porte = 'Minigeracao' AND SUM(u.potencia_instalada) > 3000)
ORDER BY potencia_total DESC
"""

st.title("🔎 Radar de Fracionamento")

# Consulta os dados e interrompe a execução caso o PostgreSQL não esteja acessível.
try:
    quadro = consultar(SQL_SUSPEITOS_CATEGORIZADO)
    quadro_titulares = consultar(SQL_SUSPEITOS_POR_TITULAR)
    quadro_titulares_detalhado = consultar(SQL_SUSPEITOS_TITULARES_DETALHADO)
except Exception:
    st.error("Não foi possível consultar o PostgreSQL.")
    st.info(
        "Confira se o banco está ativo, se as tabelas foram carregadas e se "
        "POSTGRES_URL em config.py aponta para o banco correto."
    )
    st.stop()

# Separa o resumo atual e o novo detalhamento em abas.
aba_categorias, aba_titulares, aba_detalhado = st.tabs(
    ["Resumo por categoria", "Suspeitos por titular e município", "Detalhamento por titular"]
)

with aba_detalhado:
    st.subheader("Titulares com potência acima do limite em PE")

    # Exibir tabela
    st.dataframe(quadro_titulares_detalhado, width="stretch", hide_index=True)

    # Criar gráfico de barras com os maiores titulares
    top_n = quadro_titulares_detalhado.head(20)  # top 20 por potência
    st.bar_chart(
        data=top_n.set_index("nome_titular")["potencia_total"],
        use_container_width=True
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



