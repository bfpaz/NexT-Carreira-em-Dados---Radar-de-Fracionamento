# instalando e importando bibliotecas de big data
import pandas as pd

df = pd.read_csv('data/raw/20260923_230940_geracao_distribuida.csv', sep=';', header=0)


# contando quantos registros há na base
# 4_656_839

len(df)

# buscando qual o nome associado à Neoenergia Pernambuco

df['SigAgente'].unique()

# filtrando a base para analisar apenas os empreendimentos
# associados à Neoenergia PE e quanto sobra da base

neoenergia = df[df['SigAgente'] == 'Neoenergia PE']
len(neoenergia)

# investigando os diferentes portes de usinas restantes para entender
# se será necessário fazer mais algum filtro

neoenergia['DscPorte'].unique()


# buscando entender o quantos valores não-nulos há na base restante

neoenergia.info()

# buscando quais dos nulos estão associados ao cpf/cnpj ser nulo

neoenergia.loc[neoenergia.NumCPFCNPJ.isna()].info()

# R: sempre que cpf/cnpj é nulo, CodSubGrupoTarifario, CodCEP,
# SigTipoConsumidor, SigModalidadeEmpreendimento, NomSubEstacao,
# NumCoordESub, NumCoordNSub e NomTitularEmpreendimento também são nulos

# decisão: excluir os registros sem um cpf/cnpj, pois inviabiliza a análise

# excluindo todos os registros sem NumCPFCNPJ

neoeneergia_com_titular = neoenergia.dropna(axis='index', subset=['NumCPFCNPJ'])

# selecionando apenas as colunas de interesse

colunas_de_interesse = [
    # dados temporais
    'DatGeracaoConjuntoDados', 'AnmPeriodoReferencia',
    # dados da neoenergia
    'SigAgente',
    # dados de localização
    'SigUF', 'NomRegiao', 'NomMunicipio', 'CodCEP',
    # dados da usina
    'DscClasseConsumo', 'DscSubGrupoTarifario', 'CodEmpreendimento',
    'DthAtualizaCadastralEmpreend', 'QtdUCRecebeCredito',
    'SigTipoGeracao', 'DscPorte', 'MdaPotenciaInstaladaKW',
    # dados do titular
    'NomTitularEmpreendimento', 'NumCPFCNPJ'
]

# restringindo os dados apenas para as colunas de interesse

neoenergia_colunas_interesse = neoeneergia_com_titular[colunas_de_interesse]

# contando o número de registros com o mesmo cpf/cnpj

registros_mesmo_titular = neoenergia_colunas_interesse[['NumCPFCNPJ', 'CodEmpreendimento']].groupby(['NumCPFCNPJ']).count()
registros_mesmo_titular.sort_values(by='CodEmpreendimento', ascending=False)

# modificando o nome das colunas

novas_colunas = {
    'DatGeracaoConjuntoDados': 'data_geracao',
    'AnmPeriodoReferencia': 'mes_referencia',
    'SigAgente': 'agente',
    'SigUF': 'estado',
    'NomRegiao': 'regiao',
    'NomMunicipio': 'municipio',
    'CodCEP': 'cep',
    'DscClasseConsumo': 'classe_consumo',
    'DscSubGrupoTarifario': 'grupo_tarifario',
    'CodEmpreendimento': 'cod_empreendimento',
    'DthAtualizaCadastralEmpreend': 'data_atualizacao_cadastral',
    'QtdUCRecebeCredito': 'numero_beneficiarios',
    'SigTipoGeracao': 'tipo_geracao',
    'DscPorte': 'porte',
    'MdaPotenciaInstaladaKW': 'potencia_instalada',
    'NomTitularEmpreendimento': 'nome_titular',
    'NumCPFCNPJ': 'cpf_cnpj'
}

neoenergia_tratamento = neoenergia_colunas_interesse.rename(columns=novas_colunas)

# entendendo a nova estrutura da base de dados

neoenergia_tratamento.info()

# transformando os tipos de dados para o mais adequado

# colunas do tipo data
datas = ['data_geracao', 'mes_referencia', 'data_atualizacao_cadastral']

# um tratamento especial para a coluna mes_referencia por ter um formato diferente (mm/YYYY)
neoenergia_tratamento['mes_referencia'] = pd.to_datetime(neoenergia_tratamento['mes_referencia'], format='%m/%Y')

for data in datas:
    neoenergia_tratamento[data] = pd.to_datetime(neoenergia_tratamento[data])

# transformando os dados de potência instalada para float com ponto separando as casas decimais
neoenergia_tratamento['potencia_instalada'] = neoenergia_tratamento['potencia_instalada'].str.replace(',', '.', regex=False).astype(float)

neoenergia_tratamento.info()

# focando no tratamento de nulos em tipo_geração:
# entendendo se há possíveis candidatos entre os
# registros sem tipo de geração

possiveis_candidatos = neoenergia_tratamento.loc[neoenergia_tratamento['tipo_geracao'].isna(), ['cpf_cnpj', 'tipo_geracao', 'potencia_instalada']].groupby(['cpf_cnpj']).sum()

possiveis_candidatos[possiveis_candidatos['potencia_instalada'] > 75]

# contando quantos são os registros de cada tipo_geração
# para compreender como tratar os nulos

neoenergia_tratamento[['tipo_geracao', 'cpf_cnpj']].groupby(['tipo_geracao']).count()

# decisão: assumir que os nulos são de UFV, pois não afeta a proporção
# de UFV do total e o tipo de geração não é relevante para a análise,
# além de alguns nulos pertencerem a possíveis candidatos

# inputando UFV nos valores nulos de tipo_geracao

neoenergia_tratamento.loc[neoenergia_tratamento['tipo_geracao'].isna(), 'tipo_geracao'] ='UFV'

# consultando os diferentes estados relacionados à neoenergia PE

neoenergia_tratamento.estado.unique()

# conferindo se o código do empreendimento se repete na base de dados (não)

len(neoenergia_tratamento.cod_empreendimento.unique()) - len(neoenergia_tratamento)

# verificando os ceps e número de empreendimentos por cpf/cnpj
# confirmou a hipótese de que os ceps só são acessíveis por cnpj

emp_cep_contagem = neoenergia_tratamento[['cep', 'cpf_cnpj', 'cod_empreendimento']].groupby(['cpf_cnpj', 'cep']).count().sort_values(by=['cod_empreendimento'], ascending=False)
emp_cep_contagem

neoenergia_tratamento.to_csv('neoenergia_tratado.csv', index=False)  