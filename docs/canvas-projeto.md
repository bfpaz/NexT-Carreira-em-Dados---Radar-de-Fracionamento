# Canvas do Projeto — M6 Experiência Prática

**Como usar:** copie este arquivo para `docs/canvas-projeto.md` no repositório da equipe e preencha durante o E2 (qua 16/09). O canvas é validado pelo mentor ao fim do E2: aprovado, aprovado com ajustes, ou devolvido com pendências claras (pendências resolvidas até o E3). O canvas aprovado fica versionado no repositório — ele é a referência dos checkpoints: as perguntas daqui são as que o CP1 verifica (critério 1.4) e as que a análise e o dashboard precisam responder (critérios 2.1 e 2.2).

Lembre da regra do E2: **não existe viabilidade sem amostra baixada e aberta.**

---

## Identificação

| | |
|---|---|
| **Nome da equipe** | Energia Legal |
| **Integrantes** | Bruno Paz, Danilo, Felipe |
| **Mentor** | Eric, Marcio, João Pedro |
| **Tema** | Radar de Fracionamento |
| **Repositório GitHub** | https://github.com/bfpaz/NexT-Carreira-em-Dados---Radar-de-Fracionamento |

---

## 1. Problema de negócio

Escreva em 2–4 frases. Tema não é problema: o problema diz **quem decide, o que decide, e com que informação decidiria melhor**. Evite "analisar X" — prefira "a organização Y precisa decidir Z, mas hoje decide sem W".

> _Exemplo: "A secretaria estadual de saúde de PE precisa decidir onde reforçar equipes antes da próxima temporada de dengue, mas hoje decide sem histórico consolidado de internações por município."_

```
A Neoenergia PE precisa decidir sobre quais as organizações geradoras de energia renovável distribuiída estão fracionando a sua potência gerada para burlar a legislação que classifica o tamanho da geração e a empresa não possui um sistema automatizado para identificar os candidatos a serem fiscalizados
```

---

## 2. Público / decisor

Quem usa o dashboard e toma a decisão? Cargo ou papel concreto (secretário, gerente de logística, comandante de policiamento), não "a sociedade". É para essa pessoa que o pitch "vende a solução".

```
Equipe de incorporação de mercado da Neoenergia PE
```

---

## 3. Perguntas analíticas

No mínimo 3, respondíveis com os dados escolhidos. Uma pergunta respondível tem recorte claro (onde, quando, o quê) e o dado necessário existe na fonte. O CP1 verifica que ao menos 3 continuam respondíveis com os dados **reais**.

| # | Pergunta | Que decisão ela informa? | Respondível com os dados? (verificado na amostra) |
|---|---|---|---|
| 1 | Quais/quantos são os empreendimentos do mesmo titular que ultrapassam o limite da ANEEL? | Possíveis suspeitos de fracionamento | CPF/CNPJ do titular, município, potência gerada... |
| 2 | Quais destes possíveis suspeitos têm empreendimentos posteriores à data de promulgação da legislação em questão? | Prováveis suspeitos de fracionamento | Data de referência |
| 3 | Quais fontes, classes de consumo e subgrupo concentram os casos suspeitos? | Quais tipos de geração focar | Fonte, Classe, Subgrupo |
| 4 (opcional) | Quanta potência está sob suspeita em PE? | Por onde começar a fiscalização | Potência gerada |
| 5 (opcional) | | | |

---

## 4. Fontes de dados

Uma linha por fonte. A amostra precisa ter sido **baixada e aberta hoje** — coluna a coluna. Lembrete: se a fonte tiver API, a coleta usa API (requisito do M3). Troca de fonte é livre até o E3 (21/09); depois, só com a coordenação.

| Fonte | Link | Formato | Volume estimado | Licença/acesso | Amostra baixada e aberta? (sim/não) | Colunas-chave confirmadas na amostra |
|---|---|---|---|---|---|---|
| ANEEL | https://dadosabertos.aneel.gov.br/dataset/relacao-de-empreendimentos-de-geracao-distribuida/resource/3fabb9e8-668a-4f94-8f0e-ed9cd2682979 | CSV | 1,48gb | Aberta | | |
| | | | | | | |

---

## 5. Escopo e entregáveis — a regra do fatiável

Defina primeiro a fatia mínima: o menor recorte que ainda exercita o ciclo completo (banco → pipeline → análise → dashboard). Ela é o compromisso da equipe. As extensões só entram se a fatia mínima estiver pronta — e nada entra após o congelamento de escopo (05/10).

**Fatia mínima (compromisso):**

```
Ranking de suspeitos de fracionamento em PE, anual 2020-2026, com quadro de indicadores de evolução de potência sob suspeita
```

**Extensões desejáveis (apenas se sobrar tempo):**

```
Ampliar monitoramento para os outros estados, agrupando por região
```

**Fora de escopo (o que decidimos NÃO fazer):**

```
Classificação por machine learning em potencial suspeito para previnir fracionamento
```

---

## 6. Riscos e mitigação

Ao menos 3 riscos do **seu** projeto (não genéricos). Consulte a tabela de riscos comuns no [`guia-do-projeto.md`](guia-do-projeto.md).

| Risco | Sinal precoce | Mitigação | Responsável por monitorar |
|---|---|---|---|
| Dependência de especialista técnico em geração distribuiída | Dúvidas conceituais quanto aos dados | Consultar especialistas (ex.: professor universitário) | Scrum Master |
| Carência de informação da necessidade do cliente | Discordância sobre o objetivo decisório | Consultar mentores quanto à regra de negócio | Product Owner |
| Dashboard saturado de informações | Número de gráficos e análises feitas na exploração de dados | Revisar o objetivo de negócio periodicamente para verificar a utilidade das análises | Visualização de dados |

---

## 7. Divisão de papéis

Todos codificam — papéis distribuem responsabilidade de acompanhamento, não exclusividade de execução. Cada papel tem uma pessoa sombra (backup). Em equipes de 4, coordenação acumula com outro papel; em equipes de 5–6, dados/pipeline e análise podem ser duplicados.

| Papel | Titular | Sombra |
|---|---|---|
| Coordenação de projeto | Bruno Paz | Danilo Cesar |
| Dados / pipeline | Luis Felipe | Bruno Paz |
| Análise | Danilo Cesar | Luis Felipe |
| Visualização / pitch | Danilo Cesar | Luis Felipe |

**Canal de comunicação da equipe (fora do horário de aula):**

```
grupo no WhatsApp + board no GitHub Projects
```

---

## Validação do mentor (preenchida pelo mentor no E2)

| | |
|---|---|
| **Status** | ( ) Aprovado ( ) Aprovado com ajustes ( ) Devolvido com pendências |
| **Data** | |
| **Amostra baixada e aberta verificada?** | ( ) Sim ( ) Não |
| **Pendências (com prazo até o E3 — seg 21/09)** | |
