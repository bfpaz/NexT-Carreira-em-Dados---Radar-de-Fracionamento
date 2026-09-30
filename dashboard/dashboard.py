import sys
from pathlib import Path
import pandas as pd
import streamlit as st
from sqlalchemy import create_engine, text
from dotenv import load_dotenv
import os
import requests
import geopandas as gpd
import unidecode
import plotly.express as px
import plotly.graph_objects as go
import numpy as np
import json


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

# Query que agrega novas usinas e potência por mês e calcula acumulados.
SQL_EVOLUCAO_MENSAL = '''
-- evolução mensal de novas usinas e potência (corrigido)
WITH por_mes AS (
  SELECT
    DATE_TRUNC('month', data_atualizacao_cadastral) AS mes,
    COUNT(id_usina) AS novas_usinas_no_mes,
    SUM(potencia_instalada) AS nova_potencia_no_mes
  FROM usina
  WHERE data_atualizacao_cadastral IS NOT NULL
  GROUP BY DATE_TRUNC('month', data_atualizacao_cadastral)
)
SELECT
  mes,
  novas_usinas_no_mes,
  nova_potencia_no_mes,
  SUM(novas_usinas_no_mes) OVER (ORDER BY mes) AS total_usinas_acumulado,
  SUM(nova_potencia_no_mes) OVER (ORDER BY mes) AS potencia_acumulada
FROM por_mes
ORDER BY mes ASC;
'''

st.title("🔎 Radar de Fracionamento")

# Consulta os dados e interrompe a execução caso o PostgreSQL não esteja acessível.
try:
    quadro = consultar(SQL_SUSPEITOS_CATEGORIZADO)
    quadro_titulares = consultar(SQL_SUSPEITOS_POR_TITULAR)
    quadro_titulares_detalhado = consultar(SQL_SUSPEITOS_TITULARES_DETALHADO)
    quadro_evolucao_mensal = consultar(SQL_EVOLUCAO_MENSAL)
except Exception:
    st.error("Não foi possível consultar o PostgreSQL.")
    st.info(
        "Confira se o banco está ativo, se as tabelas foram carregadas e se "
        "POSTGRES_URL em config.py aponta para o banco correto."
    )
    st.stop()

# --- filtro global de porte na sidebar ---
portes_selecionados = st.sidebar.multiselect(
    "Filtrar por porte",
    options=["Minigeracao", "Microgeracao"],
    default=["Minigeracao", "Microgeracao"],
    format_func=lambda x: "Minigeração" if x == "Minigeracao" else "Microgeração"
)

# novo: filtrar por CNPJ apenas (ignorar registros cujo nome_titular é '***')
apenas_cnpj = st.sidebar.checkbox("Analisar apenas por CNPJ", value=False)

# aplicar filtro por "CNPJ only" conforme sua definição: ignorar linhas com nome_titular == '***'
if apenas_cnpj:
    # garantir colunas como string e remover espaços
    quadro_titulares["nome_titular"] = quadro_titulares["nome_titular"].astype(str).str.strip()
    quadro_titulares_detalhado["nome_titular"] = quadro_titulares_detalhado["nome_titular"].astype(str).str.strip()

    # filtrar: manter apenas linhas cujo nome_titular != '***'
    quadro_titulares = quadro_titulares[quadro_titulares["nome_titular"] != "***"].copy()
    quadro_titulares_detalhado = quadro_titulares_detalhado[quadro_titulares_detalhado["nome_titular"] != "***"].copy()

# Aplicar filtro global aos DataFrames usados no app
if portes_selecionados:
    quadro = quadro[quadro["porte"].isin(portes_selecionados)].copy()
    quadro_titulares = quadro_titulares[quadro_titulares["porte"].isin(portes_selecionados)].copy()
    quadro_titulares_detalhado = quadro_titulares_detalhado[quadro_titulares_detalhado["porte"].isin(portes_selecionados)].copy()

# --- Agrupar por município (somar qtd_usinas e potencia_total_kw) ---
# Garante que as colunas existam e estejam com tipos numéricos
quadro_titulares["qtd_usinas"] = pd.to_numeric(quadro_titulares["qtd_usinas"], errors="coerce").fillna(0).astype(int)
# Alguns SQLs usam 'potencia_total' em vez de 'potencia_total_kw' — normalizar:
if "potencia_total" in quadro_titulares.columns and "potencia_total_kw" not in quadro_titulares.columns:
    quadro_titulares = quadro_titulares.rename(columns={"potencia_total": "potencia_total_kw"})
quadro_titulares["potencia_total_kw"] = pd.to_numeric(quadro_titulares["potencia_total_kw"], errors="coerce").fillna(0.0)

# Agrupa por nome do município (usar o nome como está no banco)
quadro_municipios = (
    quadro_titulares
    .groupby("nome_municipio", dropna=False, as_index=False)
    .agg(
        qtd_usinas=("qtd_usinas", "sum"),
        potencia_total_kw=("potencia_total_kw", "sum")
    )
)

# converter para datetime de forma robusta e remover timezone se existir
quadro_evolucao_mensal["mes"] = pd.to_datetime(quadro_evolucao_mensal["mes"], errors="coerce")

try:
    if quadro_evolucao_mensal["mes"].dt.tz is not None:
        quadro_evolucao_mensal["mes"] = (
            quadro_evolucao_mensal["mes"]
            .dt.tz_convert("UTC")
            .dt.tz_localize(None)
        )
except Exception:
    quadro_evolucao_mensal["mes"] = pd.to_datetime(quadro_evolucao_mensal["mes"].astype(str), errors="coerce")

# --- Agregar por mês para garantir rótulos únicos (evita erro de reindex) ---
# Somar novas usinas e nova potência por mês; outros acumulados serão recalculados abaixo
quadro_evolucao_mensal = (
    quadro_evolucao_mensal
    .groupby("mes", as_index=True, dropna=False)
    .agg(
        novas_usinas_no_mes=("novas_usinas_no_mes", "sum"),
        nova_potencia_no_mes=("nova_potencia_no_mes", "sum")
    )
    .sort_index()
)

# preencher meses faltantes entre min e max (índice é DatetimeIndex)
if not quadro_evolucao_mensal.empty:
    meses = pd.date_range(start=quadro_evolucao_mensal.index.min(), end=quadro_evolucao_mensal.index.max(), freq="MS")
    quadro_evolucao_mensal = quadro_evolucao_mensal.reindex(meses, fill_value=0).rename_axis("mes").reset_index()
else:
    # caso não haja dados válidos, criar DataFrame vazio com colunas esperadas
    quadro_evolucao_mensal = pd.DataFrame(columns=["mes", "novas_usinas_no_mes", "nova_potencia_no_mes"])

# recalcular acumulados em pandas (mais seguro e consistente)
quadro_evolucao_mensal["total_usinas_acumulado"] = quadro_evolucao_mensal["novas_usinas_no_mes"].cumsum()
quadro_evolucao_mensal["potencia_acumulada"] = quadro_evolucao_mensal["nova_potencia_no_mes"].cumsum()


quadro_evolucao_mensal = quadro_evolucao_mensal.sort_values("mes").reset_index(drop=True)

# preencher meses faltantes entre min e max
meses = pd.date_range(start=quadro_evolucao_mensal["mes"].min(), end=quadro_evolucao_mensal["mes"].max(), freq="MS")
quadro_evolucao_mensal = quadro_evolucao_mensal.set_index("mes").reindex(meses).rename_axis("mes").fillna(0).reset_index()

# recalcular acumulados em pandas (segurança)
quadro_evolucao_mensal["total_usinas_acumulado"] = quadro_evolucao_mensal["novas_usinas_no_mes"].cumsum()
quadro_evolucao_mensal["potencia_acumulada"] = quadro_evolucao_mensal["nova_potencia_no_mes"].cumsum()

# média móvel (opcional) — parâmetro controlável na UI
window = st.sidebar.slider("Média móvel (meses)", min_value=1, max_value=12, value=3)
if window > 1:
    quadro_evolucao_mensal["novas_usinas_mm"] = quadro_evolucao_mensal["novas_usinas_no_mes"].rolling(window, min_periods=1).mean()
    quadro_evolucao_mensal["nova_potencia_mm"] = quadro_evolucao_mensal["nova_potencia_no_mes"].rolling(window, min_periods=1).mean()
else:
    quadro_evolucao_mensal["novas_usinas_mm"] = quadro_evolucao_mensal["novas_usinas_no_mes"]
    quadro_evolucao_mensal["nova_potencia_mm"] = quadro_evolucao_mensal["nova_potencia_no_mes"]

# Plot combinado: barras mensais + linha acumulada
import plotly.graph_objects as go

mostrar = st.selectbox("Mostrar", options=["Novas usinas (mês)", "Nova potência (mês)"])

x = quadro_evolucao_mensal["mes"]

fig = go.Figure()

if mostrar == "Novas usinas (mês)":
    y_bar = quadro_evolucao_mensal["novas_usinas_no_mes"]
    fig.add_trace(go.Bar(x=x, y=y_bar, name="Novas usinas no mês", marker_color="#2563EB", yaxis="y"))
    fig.add_trace(go.Scatter(x=x, y=quadro_evolucao_mensal["total_usinas_acumulado"], name="Total acumulado", mode="lines+markers", marker_color="#F97316", yaxis="y2"))
    yaxis_title = "Novas usinas / mês"
    y2_title = "Total acumulado (usinas)"
else:
    y_bar = quadro_evolucao_mensal["nova_potencia_no_mes"]
    fig.add_trace(go.Bar(x=x, y=y_bar, name="Nova potência no mês (kW)", marker_color="#2563EB", yaxis="y"))
    fig.add_trace(go.Scatter(x=x, y=quadro_evolucao_mensal["potencia_acumulada"], name="Potência acumulada (kW)", mode="lines+markers", marker_color="#F97316", yaxis="y2"))
    yaxis_title = "Potência nova (kW/mês)"
    y2_title = "Potência acumulada (kW)"

fig.update_layout(
    xaxis=dict(tickformat="%Y-%m"),
    yaxis=dict(title=yaxis_title),
    yaxis2=dict(title=y2_title, overlaying="y", side="right"),
    legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
    margin={"r":20,"t":40,"l":40,"b":40},
    bargap=0.15,
    template="plotly_white"
)

# fundo transparente opcional
fig.update_layout(paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)")

st.plotly_chart(fig, use_container_width=True)

# Separa o resumo atual e o novo detalhamento em abas.
aba_categorias, aba_titulares, aba_detalhado = st.tabs(
    ["Resumo por categoria", "Suspeitos por titular e município", "Detalhamento por titular"]
)

with aba_detalhado:
    st.subheader("Titulares com potência acima do limite em PE")

    # Exibir tabela
    # st.dataframe(quadro_titulares_detalhado, width="stretch", hide_index=True)

    # Criar gráfico de barras com os maiores titulares
    top_n = quadro_titulares_detalhado.sort_values(by='potencia_total', ascending=False).head(10)  # top 10 por potência
    fig_bar = px.bar(
        top_n,
        x="nome_titular",
        y='potencia_total',
        text='potencia_total',
        hover_data={"nome_titular": True, "nome_municipio": True, 'potencia_total': True},
        labels={'potencia_total': "Potência total (kW)", "nome_titular": "Titular"},
        color='potencia_total',
        color_continuous_scale="OrRd"
    )

    st.plotly_chart(fig_bar, use_container_width=True)

with aba_categorias:
    st.subheader("Titulares com potência acima do limite em PE")

    # Exibir tabela
    # st.dataframe(quadro_titulares_detalhado, width="stretch", hide_index=True)

    # Criar gráfico de barras com os maiores titulares
    top_n = quadro_titulares_detalhado.sort_values(by='potencia_total', ascending=False).head(10)  # top 20 por potência
    # criar gráfico Plotly com hover customizado

    fig_bar = px.bar(
        top_n,
        x="nome_titular",
        y='potencia_total',
        text='potencia_total',
        hover_data={"nome_titular": True, "nome_municipio": True, 'potencia_total': True},
        labels={'potencia_total': "Potência total (kW)", "nome_titular": "Titular"},
        color='potencia_total',
        color_continuous_scale="OrRd"
    )

    st.plotly_chart(fig_bar, use_container_width=True)
    

with aba_categorias:
    # controle local de exibição (aplica só a esta aba)
    modo_exibicao_local = st.radio(
        "Exibir por",
        options=["Ambos", "Classe de consumo", "Subgrupo tarifário"],
        index=0,
        horizontal=True
    )

    # criar coluna 'categoria' conforme modo de exibição selecionado
    if modo_exibicao_local == "Classe de consumo":
        quadro["categoria"] = quadro["classe_consumo"].astype(str)
    elif modo_exibicao_local == "Subgrupo tarifário":
        quadro["categoria"] = quadro["subgrupo_tarifario"].astype(str)
    else:  # "Ambos"
        quadro["categoria"] = (
            quadro["classe_consumo"].astype(str)
            + " | "
            + quadro["subgrupo_tarifario"].astype(str)
        )

    # título descritivo conforme modo
    titulo_suffix = {
        "Classe de consumo": "por classe de consumo",
        "Subgrupo tarifário": "por subgrupo tarifário",
        "Ambos": "por categoria (classe | subgrupo)"
    }[modo_exibicao_local]

    # Mantém o filtro global de portes já aplicado anteriormente
    # Montar os dois gráficos lado a lado (potência e quantidade)
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
        # opcional: ordenar categorias pelo total (descendente) para melhorar leitura
        comparativo["__total__"] = comparativo.sum(axis=1)
        comparativo = comparativo.sort_values("__total__", ascending=False).drop(columns="__total__")

        # desenhar gráfico
        with coluna:
            st.subheader(f"{titulo} — {titulo_suffix}")
            cores = {"Minigeracao": "#2563EB", "Microgeracao": "#F97316"}
            st.bar_chart(
                comparativo,
                horizontal=True,
                color=[cores[porte] for porte in comparativo.columns],
                use_container_width=True
            )

with aba_titulares:
    # Exibe os totais de titulares suspeitos e municípios em cartões lado a lado.
    total_suspeitos = quadro_titulares["id_titular"].nunique()
    total_municipios = quadro_titulares["id_municipio"].nunique()
    quadro_suspeitos, quadro_municipios = st.columns(2)
    quadro_suspeitos.metric("Total de suspeitos", f"{total_suspeitos:,}".replace(",", "."))
    quadro_municipios.metric("Total de municípios", f"{total_municipios:,}".replace(",", "."))

    # Apresenta as linhas retornadas pela consulta detalhada.
    # st.dataframe(quadro_titulares, width="stretch", hide_index=True)

    # --- caminho do arquivo local ---
    GEOJSON_LOCAL = os.path.join(os.path.dirname(__file__), "geojson_pe", "geojs-26-mun.json")

    # --- carregar GeoJSON local (fallback para IBGE/mcp_brasil se não existir) ---
    def carregar_malha_local(caminho):
        if os.path.exists(caminho):
            with open(caminho, "r", encoding="utf-8") as f:
                geojson = json.load(f)
            gdf = gpd.GeoDataFrame.from_features(geojson["features"])
            # garantir coluna codarea (id IBGE) e nome do município a partir das properties
            if "codarea" not in gdf.columns:
                try:
                    gdf["codarea"] = [str(feat["properties"].get("id") or feat["properties"].get("codarea") or "") for feat in geojson["features"]]
                except Exception:
                    gdf["codarea"] = ""
            if "nome_municipio_malha" not in gdf.columns:
                try:
                    gdf["nome_municipio_malha"] = [feat["properties"].get("name") or feat["properties"].get("nome") or feat["properties"].get("description") or "" for feat in geojson["features"]]
                except Exception:
                    gdf["nome_municipio_malha"] = ""
            gdf["codarea"] = gdf["codarea"].astype(str)
            gdf["nome_municipio_malha"] = gdf["nome_municipio_malha"].astype(str)
            return gdf, geojson
        return None, None

    mapa, mapa_geojson = carregar_malha_local(GEOJSON_LOCAL)

    mapa["nome_chave"] = mapa["nome_municipio_malha"]
    quadro_municipios["nome_chave"] = quadro_municipios["nome_municipio"]

    # Merge left para manter todos os polígonos
    mapa_dados = mapa.merge(quadro_municipios, on="nome_chave", how="left", suffixes=("_malha", "_dados"))

    # Selecionar parâmetro e construir mapa
    parametro = st.selectbox("Selecione o parâmetro para o mapa", options=["potencia_total_kw", "qtd_usinas"], width=225)

    # Garantir colunas numéricas
    mapa_dados["qtd_usinas"] = pd.to_numeric(mapa_dados.get("qtd_usinas", 0), errors="coerce")
    mapa_dados["potencia_total_kw"] = pd.to_numeric(mapa_dados.get("potencia_total_kw", 0), errors="coerce")

    mask_dados = mapa_dados[parametro].notna()

    fig = go.Figure()

    # Determinar featureidkey correto
    featureid = "properties.id" if "id" in mapa_geojson["features"][0]["properties"] else "properties.codarea"

    # Camada base: todos os municípios em cinza claro
    fig.add_trace(
        go.Choropleth(
            geojson=mapa_geojson,
            locations=mapa_dados["codarea"],
            z=[0] * len(mapa_dados),
            featureidkey=featureid,
            colorscale=[[0, "#f0f0f0"], [1, "#f0f0f0"]],
            showscale=False,
            marker_line_width=0.5,
            marker_line_color="black",
            hoverinfo="none",
            name="base"
        )
    )

    # Camada de dados: apenas municípios com valores
    if mask_dados.any():
        mapa_com_dados = mapa_dados[mask_dados].copy()
        mapa_com_dados[parametro] = pd.to_numeric(mapa_com_dados[parametro], errors="coerce").fillna(0)
        fig.add_trace(
            go.Choropleth(
                geojson=mapa_geojson,
                locations=mapa_com_dados["codarea"],
                z=mapa_com_dados[parametro],
                featureidkey=featureid,
                colorscale="OrRd",
                colorbar_title=parametro,
                marker_line_width=0.5,
                marker_line_color="black",
                hovertemplate=(
                    "<b>%{customdata[0]}</b><br>"
                    "Qtd usinas: %{customdata[1]}<br>"
                    "Potência total (kW): %{customdata[2]:,.1f}<extra></extra>"
                ),
                customdata=np.stack([
                    mapa_com_dados["nome_municipio_malha"].fillna(""),
                    mapa_com_dados["qtd_usinas"].fillna(0).astype(int),
                    mapa_com_dados["potencia_total_kw"].fillna(0.0)
                ], axis=-1),
                name="dados"
            )
        )
    else:
        st.info("Nenhum município com dados para o parâmetro selecionado.")

    fig.update_geos(fitbounds="locations", visible=False)
    fig.update_layout(margin={"r":0,"t":40,"l":0,"b":0}, title_text=f"Mapa de calor - {parametro.replace('_',' ').title()}")

    # deixar fundo do gráfico transparente
    fig.update_layout(
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)"
    )
    # garantir que a área do mapa também seja transparente
    fig.update_geos(bgcolor="rgba(0,0,0,0)")

    
    st.plotly_chart(fig, use_container_width=True)



