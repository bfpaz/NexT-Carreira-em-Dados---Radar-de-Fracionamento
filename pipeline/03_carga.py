import pandas as pd
from sqlalchemy import create_engine, text
from dotenv import load_dotenv
import os


def executar_carga(caminho_csv_tratado):
    # Carregar variáveis do .env
    load_dotenv()

    user = os.getenv("DB_USER")
    password = os.getenv("DB_PASSWORD")
    host = os.getenv("DB_HOST")
    port = os.getenv("DB_PORT")
    db = os.getenv("DB_NAME")

    # Montar string de conexão
    conn_str = f"postgresql://{user}:{password}@{host}:{port}/{db}"
    engine = create_engine(conn_str)

    # Carregar CSV tratado
    neoenergia_tratado = pd.read_csv(caminho_csv_tratado, encoding="utf-8")

    # --- Inserir titulares ---
    with engine.begin() as conn:
        for _, row in neoenergia_tratado[['cpf_cnpj','nome_titular']].drop_duplicates().iterrows():
            conn.execute(
                text("""
                    INSERT INTO titular (cpf_cnpj, nome_titular)
                    VALUES (:cpf_cnpj, :nome_titular)
                    ON CONFLICT (cpf_cnpj) DO NOTHING
                """),
                {"cpf_cnpj": row['cpf_cnpj'], "nome_titular": row['nome_titular']}
            )

    # --- Inserir municípios ---
    with engine.begin() as conn:
        for _, row in neoenergia_tratado[['municipio','estado','regiao']].drop_duplicates().iterrows():
            conn.execute(
                text("""
                    INSERT INTO municipio (nome_municipio, estado, regiao)
                    VALUES (:nome_municipio, :estado, :regiao)
                    ON CONFLICT (nome_municipio, estado) DO NOTHING
                """),
                {"nome_municipio": row['municipio'], "estado": row['estado'], "regiao": row['regiao']}
            )

    # --- Inserir distribuidoras ---
    with engine.begin() as conn:
        for _, row in neoenergia_tratado[['agente']].drop_duplicates().iterrows():
            conn.execute(
                text("""
                    INSERT INTO distribuidora (nome_distribuidora)
                    VALUES (:nome_distribuidora)
                    ON CONFLICT (nome_distribuidora) DO NOTHING
                """),
                {"nome_distribuidora": row['agente']}
            )

    # --- Buscar IDs já inseridos ---
    with engine.connect() as conn:
        titulares_db = pd.read_sql(text("SELECT id_titular, cpf_cnpj FROM titular"), conn)
        municipios_db = pd.read_sql(text("SELECT id_municipio, nome_municipio, estado, regiao FROM municipio"), conn)
        distribuidoras_db = pd.read_sql(text("SELECT id_distribuidora, nome_distribuidora FROM distribuidora"), conn)

    # --- Montar DataFrame da usina com FKs ---
    usina_df = neoenergia_tratado.merge(titulares_db, on="cpf_cnpj", how="left")
    usina_df = usina_df.merge(municipios_db, left_on=["municipio","estado","regiao"],
                            right_on=["nome_municipio","estado","regiao"], how="left")
    usina_df = usina_df.merge(distribuidoras_db, left_on="agente", right_on="nome_distribuidora", how="left")

    # Selecionar colunas finais (incluindo novas)
    usina_final = usina_df[[
        "cod_empreendimento", "tipo_geracao", "classe_consumo",
        "grupo_tarifario", "potencia_instalada", "mes_referencia",
        "id_titular", "id_municipio", "id_distribuidora", "porte",
        "cep", "numero_beneficiarios", "data_atualizacao_cadastral"
    ]].rename(columns={"grupo_tarifario": "subgrupo_tarifario"})

    # --- Inserir usinas ---
    with engine.begin() as conn:
        for _, row in usina_final.iterrows():
            conn.execute(
                text("""
                    INSERT INTO usina (
                        cod_empreendimento, tipo_geracao, classe_consumo,
                        subgrupo_tarifario, potencia_instalada, mes_referencia,
                        id_titular, id_municipio, id_distribuidora, porte,
                        cep, numero_beneficiarios, data_atualizacao_cadastral
                    )
                    VALUES (:cod_empreendimento, :tipo_geracao, :classe_consumo,
                            :subgrupo_tarifario, :potencia_instalada, :mes_referencia,
                            :id_titular, :id_municipio, :id_distribuidora, :porte,
                            :cep, :numero_beneficiarios, :data_atualizacao_cadastral)
                    ON CONFLICT (cod_empreendimento) DO NOTHING
                """),
                {
                    "cod_empreendimento": row["cod_empreendimento"],
                    "tipo_geracao": row["tipo_geracao"],
                    "classe_consumo": row["classe_consumo"],
                    "subgrupo_tarifario": row["subgrupo_tarifario"],
                    "potencia_instalada": row["potencia_instalada"],
                    "mes_referencia": row["mes_referencia"],
                    "id_titular": row["id_titular"],
                    "id_municipio": row["id_municipio"],
                    "id_distribuidora": row["id_distribuidora"],
                    "porte": row["porte"],
                    "cep": row["cep"],
                    "numero_beneficiarios": row["numero_beneficiarios"],
                    "data_atualizacao_cadastral": row["data_atualizacao_cadastral"]
                }
            )
