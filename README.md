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
- Potência instalada e data de conexão;
- Fonte, subgrupo e unidade beneficiária.

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
3. Qual potência está associada aos casos identificados?
4. Quais municípios concentram mais indícios?
5. Quais fontes, classes e subgrupos apresentam maior concentração de casos?

## Equipe

| Integrante | Papel | Responsabilidades principais |
| --- | --- | --- |
| **Bruno** | PO / Engenharia de Dados | Backlog, requisitos, prioridades e pipeline de ingestão, transformação e carga. |
| **Danilo** | SM / Análise de Dados | Organização das sprints, remoção de impedimentos, análise exploratória e regras de negócio. |
| **Márcio** | QA de Dados / Análise de Dados | Qualidade dos dados, testes da pipeline, validação dos resultados e análises. |
| **Felipe** | Modelagem, Banco e Visualização de Dados | Modelagem, estruturação do banco, indicadores, dashboards e visualizações. |

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

- Um mesmo titular pode constar com grafias diferentes, exigindo normalização;
- Nomes semelhantes podem gerar agrupamentos incorretos;
- O limiar de potência deve ser definido e validado com a demandante;
- Os resultados são indícios e requerem avaliação humana;
- Dados de titulares devem ser tratados com atenção, evitando exposição desnecessária de informações pessoais;
- Informações individuais não devem ser publicadas quando não forem necessárias.

## Próximos passos

- [ ] Organizar o backlog e a arquitetura inicial;
- [ ] Baixar e explorar a base pública;
- [ ] Definir a estratégia de normalização dos titulares;
- [ ] Validar o limiar de potência da regra;
- [ ] Implementar ingestão, tratamento e testes de qualidade;
- [ ] Modelar o banco e implementar as regras de identificação;
- [ ] Desenvolver o ranking, dashboard e documentação final.

## Resultado esperado

Uma solução de dados que transforme uma base pública volumosa em informações organizadas e priorizadas, apoiando a Neoenergia Pernambuco na identificação de casos que merecem análise humana.

---

**CESAR Next — Carreira em Dados | Projeto Final 2026**
