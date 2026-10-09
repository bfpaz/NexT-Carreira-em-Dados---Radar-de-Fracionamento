# 🔎 Radar de Fracionamento

## Projeto Final — CESAR Next | Carreira em Dados

Projeto desenvolvido na experiência prática do curso **CESAR Next — Carreira em Dados**, para apoiar uma demanda da **Neoenergia Pernambuco**.

## Sobre o projeto

O Radar de Fracionamento identifica, a partir de dados públicos da ANEEL, possíveis indícios de fracionamento de empreendimentos de geração distribuída. A análise busca titulares com múltiplos empreendimentos no mesmo município cuja potência instalada total ultrapasse o limiar definido pela regra de negócio.

> **Importante:** os resultados são indícios priorizados para análise humana; não representam confirmação nem acusação de fraude.

## Objetivo

Construir uma pipeline de dados capaz de:

- Coletar dados públicos da ANEEL;
- Filtrar, limpar e transformar os dados relevantes;
- Normalizar informações dos titulares;
- Agrupar empreendimentos por titular e município;
- Aplicar a regra de identificação de indícios;
- Gerar um ranking priorizado para análise;
- Disponibilizar indicadores e visualizações de apoio à decisão.

O escopo inicial contempla a **Neoenergia Pernambuco**, empreendimentos de **fonte solar**, agrupamento por **titular e município** e análise da potência instalada.

## Fonte de dados

Os dados são provenientes da base pública da **ANEEL — Agência Nacional de Energia Elétrica**, em especial da relação de empreendimentos de Mini e Micro Geração Distribuída.

Principais campos utilizados:

- Titular e empreendimento;
- Município e distribuidora;
- Potência instalada;
- Fonte, subgrupo e classe de consumo.

## Pipeline de dados

```text
Dados públicos da ANEEL
          ↓
Ingestão (download e carga)
          ↓
Tratamento (limpeza e normalização)
          ↓
Modelagem e armazenamento
          ↓
Regra de identificação de indícios
          ↓
Análise, ranking e priorização ──→ Dashboard
          ↓
Lista para análise humana/fiscalização
```

## Perguntas de análise

1. Quais titulares possuem múltiplos empreendimentos no mesmo município, com potência total acima do limiar definido?
2. As conexões desses empreendimentos ocorreram próximas no tempo?
3. Qual potência total está associada aos casos identificados?
4. Quais municípios concentram mais indícios?
5. Quais fontes, classes e subgrupos apresentam maior concentração de casos?

## Equipe

| Integrante | Papel | Responsabilidades principais | Contato |
| --- | --- | --- | --- |
| **Bruno** | PO / Engenharia de Dados / QA de dados | Backlog, requisitos, prioridades e pipeline de ingestão, transformação e carga. |  |
| **Danilo** | SM / Análise de Dados / Viz. de Dados | Organização das sprints, remoção de impedimentos, análise exploratória e regras de negócio. | danilo.vitorino@ufpe.br |
| **Felipe** | Modelagem, Banco e Visualização de Dados | Modelagem, estruturação do banco, indicadores, dashboards e visualizações. |  |

## Mentores

O projeto contou com a orientação dos mentores **Erick**, **Marcio** e **João Pedro**.

## Entregas esperadas

- Pipeline funcional para coleta e tratamento da base pública;
- Dados normalizados e estruturados para análise;
- Regra documentada de identificação de indícios;
- Ranking de titulares e casos para análise humana;
- Indicadores, visualizações e dashboard;
- Documentação do processo, regras e limitações.

## Cuidados e limitações

- [x] Um mesmo titular pode constar com grafias diferentes, exigindo normalização;
- [x] Nomes semelhantes podem gerar agrupamentos incorretos;
- [x] O limiar de potência deve ser definido e validado com a demandante;
- [x] Os resultados são indícios e requerem avaliação humana;
- [x] Dados de titulares devem ser tratados com atenção, evitando exposição desnecessária de informações pessoais;
- [x] Informações individuais não devem ser publicadas quando não forem necessárias.

## Passo a passo para utilização desta ferramenta

```text
Baixar este repositório em um ambiente local
          ↓
Instalar requirements.txt
          ↓
Criar um banco de dados no postgres utilizando o arquivo sql/schema.sql
          ↓
Editar o arquivo pipeline/.env com as informações pertinentes à conexão do seu banco
          ↓
Rodar o aquivo pipeline/_main.py
          ↓
Replicar o ambiente anterior no arquivo dashboard/.env
          ↓
Rodar o comando streamlit run dashboard.py no terminal dentro da pasta dashboard
          ↓
Utilizar o dashboard livremente
```

## Resultado esperado

Uma solução de dados que transforme uma base pública volumosa em informações organizadas e priorizadas, apoiando a Neoenergia Pernambuco na identificação de casos que merecem análise humana.

---

**CESAR Next — Carreira em Dados | Projeto Final 2026**
