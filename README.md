# Skill Mapping Intelligence: Relatório Técnico de Solução

Este repositório contém uma solução inicial para o mapeamento automatizado de habilidades (*skills*) brutas para uma taxonomia padronizada, utilizando uma arquitetura de IA híbrida para superar barreiras linguísticas e ambiguidades semânticas.

---

# 1. O que é a Solução Construída

A solução é um pipeline de Processamento de Linguagem Natural (NLP) que recebe uma lista de competências em texto livre e as vincula a uma categoria oficial.

O objetivo principal é transformar dados brutos e desestruturados em inteligência de inventário de talentos, permitindo que organizações entendam seus gaps de competências com precisão.

---

# 2. Arquitetura Escolhida e Funcionamento

A arquitetura utiliza o conceito de **Retrieve & Re-rank** (*Recuperar & Re-ranquear*), dividida em três camadas de decisão:

## Camada de Atalho (Fuzzy Match)

Utiliza a biblioteca `rapidfuzz` para identificar correspondências quase exatas (ex: `"Python"` vs `"PYTHON"`).

Se o *match* for superior a `95%`, a IA é poupada para otimizar custo e tempo.

## Camada de Recuperação (Bi-Encoder)

Utiliza o modelo `intfloat/multilingual-e5-base`.

Esta camada converte a taxonomia inteira em vetores densos (*embeddings*) e realiza uma busca por similaridade de cosseno, selecionando os 5 candidatos mais prováveis em milissegundos.

## Camada de Refinamento (Cross-Encoder)

O modelo `cross-encoder/mmarco-mMiniLMv2-L12-H384-v1` analisa o par:

- Skill Bruta
- Descrição da Taxonomia

simultaneamente.

Diferente do Bi-Encoder, ele consegue captar nuances contextuais profundas, sendo o responsável pelo veredito final do mapeamento.

---

# 3. Estrutura de Código do Projeto

A solução foi desenhada seguindo princípios de modularidade, separando:

- responsabilidade de processamento de dados
- motor de inferência de IA
- camada de avaliação de qualidade

---

## 📂 Componentes do Sistema

### `main.py` — Orquestrador do Pipeline

É o ponto de entrada da aplicação.

Gerencia o fluxo de dados entre os módulos, desde a carga inicial até a geração dos artefatos de auditoria e relatórios finais.

Garante que o processo seja executado de forma sequencial e segura.

---

### `data_processor.py` — Camada de Tratamento de Dados

Responsável pela ingestão e normalização da taxonomia e das novas competências.

#### Destaque Técnico

Implementa um tratamento robusto para arquivos CSV, lidando com diferentes codificações (`utf-8-sig`) e separadores, garantindo que as descrições ricas da taxonomia sejam preservadas sem truncamento.

---

### `mapper_engine.py` — Motor de Inteligência e Mapeamento

Onde reside a inteligência da solução.

Implementa o padrão **Retrieve & Re-rank**:

#### Fuzzy Match

Resolve rapidamente termos idênticos ou com variações simples de escrita.

#### Bi-Encoder (`multilingual-e5`)

Realiza a busca vetorial para encontrar os 5 candidatos mais similares em um espaço latente de alta dimensão.

#### Cross-Encoder (`mMiniLMv2`)

Atua como o decisor final, comparando o par:

- Skill
- Descrição

para atribuir o score de confiança definitivo.

---

### `evaluator.py` — Módulo de Diagnóstico e Qualidade

Transforma os resultados brutos em inteligência de negócio.

Gera:

- métricas de cobertura
- identificação da "Zona Cinzenta"
- análise de gaps
- histogramas de confiança

---

# 4. Registro de Decisões Técnicas

## Abordagem Híbrida

A escolha de combinar Bi-Encoders e Cross-Encoders foi porque:

- Bi-Encoders sozinhos ignoram o contexto cruzado
- Cross-Encoders são lentos demais para processar milhares de combinações

A busca `top-k` resolve esse *trade-off*.

---

## Modelo Multilíngue

A migração para modelos *multilingual* foi decidida após observarmos que competências técnicas em inglês (ex: `"Data Science"`) não eram mapeadas corretamente para categorias em português em modelos monolíngues.

---

## Onde Pode Falhar

A solução pode apresentar dificuldades em:

- termos extremamente genéricos (ex: `"Comunicação"`)
- termos sem vizinhança semântica relevante na taxonomia atual

---

## Futuras Melhorias

Com mais recursos, implementaríamos:

- Estágio de LLM judicante para explicar o "porquê" de cada *match*
- *fine-tuning* dos embeddings com dados específicos do domínio de RH/Tecnologia
- Enriquecimento de contexto para a descrição das habilidades na taxonomia
- No filtro do pipeline adicionar uma etapa de possibilidade para jogar a skill nova a ser mapeada em um llm para enriquecer o contexto dela e diminuir a dificuldade de busca semântica (casos seja uma skills que exista na taxonomia)
- Melhorar como a taxonomia é organizada: adicionar categorias macros e subcategorias, melhorando hierarquia (ex: hardskills > linguagem de programação > python)
- Além de usar o nome e a descrição da habilidade, o pipeline poderia considerar metadados adicionais, como o nível de senioridade exigido ou a área de atuação da empresa, para desempatar casos onde uma skill pode pertencer a taxonomias diferentes.

Em termos de melhoria de código:

- Colocaria em um formato de API para ser consumível.
- Implementaria mais formas de avaliações no ambiente de desenvolvimento, um pipeline automático com investigações a depender dos indícios de produção.
- Melhoraria a modularização das funções do projeto, como a função de mapeamento para transformar as etapas em módulos.
- Melhoraria a estruturação dos resultados.
- Criação de .env para melhor gerenciamento dos modelos usados e outras futuras variáveis
- Implementação de testes unitários

---

# 5. Qualidade das Decisões e Trade-offs

## Performance Híbrida: Velocidade vs. Precisão

Para equilibrar a alta precisão sem comprometer o tempo de resposta, usei uma arquitetura de dois estágios (Retrieve & Re-rank).

Usar apenas o Cross-Encoder em toda a base seria computacionalmente caro e lento. O processamento em batch (lote) permite que o modelo processe múltiplos candidatos simultaneamente na CPU, otimizando o uso de memória. 

Isso garante que a precisão superior da IA chegue ao usuário final sem gerar gargalos de escalabilidade.

---

## Calibragem de Threshold (Limiar de Confiança)

Defini um ponto de corte de 0.4 para o modelo MS-Marco após rodar testes de sensibilidade.

Um valor mais baixo aumentaria a cobertura (maior volume de matches), mas traria mais "falsos positivos".

Escolhi um limiar que favorece a descoberta, mas que exige uma camada de observabilidade dedicada para monitorar a "Zona Cinzenta" — garantindo que decisões com confiança moderada sejam sinalizadas para análise

---

## Consciência de Limitações e Gestão de Incertezas

Modelos de linguagem podem apresentar alucinações ou incertezas em termos muito específicos. Por isso, a solução não é uma "caixa-preta".

O sistema isola automaticamente casos com confiança incerta no arquivo 

```bash
auditoria_necessaria.csv
```

Isso transforma a IA em um copiloto, permitindo que especialistas foquem apenas nos casos onde a máquina não teve certeza absoluta, aumentando a eficiência do processo de curadoria em até 80%.

---

# 6. Medição de Qualidade no ambiente de desenvolvimento

A qualidade é aferida através do módulo `evaluator.py`, que gera um diagnóstico automático baseado em:

## Taxa de Cobertura

Porcentagem de skills que superaram o *threshold* de confiança.

---

## Volume em Zona Cinzenta

Identificação de *matches* com score entre `0.5` e `0.75`, sinalizando potencial ambiguidade.

---

## Análise de Gaps

Identificação das 10 skills mais frequentes que não encontraram *match*, orientando a expansão da taxonomia.

---

## Distribuição de Scores

Gráficos de densidade (*histogramas*) que mostram se o modelo está:

- "decidido" → concentração em scores altos
- "confuso" → concentração em scores baixos

---

# 7. Estratégia de Avaliação em Produção

Avaliar um mapeamento semântico em produção exige uma abordagem de **Observabilidade de ML**, focada em:

- métricas de confiança
- amostragem inteligente

já que a revisão manual total é inviável.

Em produção, não conhecemos previamente a categoria correta para cada nova skill, e a taxonomia é um organismo vivo que cresce constantemente.

Precisamos de sinais que indiquem a qualidade do processo e como ela reage a novas atualizações.

Para isso, estruturamos nossa observabilidade em torno de perguntas fundamentais e estratégias de extração de indícios.

---

# I. Perguntas Fundamentais de Saúde do Modelo

## Nível de Assertividade

O modelo está encontrando similaridades fortes ou está "chutando" com scores baixos?

---

## Ambiguidade

A solução tem dificuldade de decidir entre duas ou mais categorias (*Zona Cinzenta*)?

---

## Aderência e Lacunas

As categorias atuais são suficientes ou existem novas habilidades surgindo que a taxonomia não cobre?

---

## Granularidade e Estrutura

As categorias estão muito genéricas ou específicas demais?

Existem redundâncias ou necessidade de organização hierárquica?

---

## Consistência Temporal

O mesmo termo recebe o mesmo *match* e score hoje que recebia ontem, ou há instabilidade (*Drift*)? ⏱

---

## Robustez da Decisão

A margem entre a 1ª e a 2ª opção é grande o suficiente para ser confiável?

---

# II. Estratégias de Avaliação (Indicadores de Observabilidade)

## Distribuição de Confiança

### Como funciona

Monitoramento do histograma de scores em tempo real:

- Verde → `> 0.8`
- Cinza → `0.4 - 0.7`
- Vermelha → `< 0.4`

### O que indica

Se a massa de dados migra para a esquerda, há sinal de:

- *Data Drift*
- taxonomia defasada

---

## Margem de Confiança (Top-1 vs Top-2)

### Como funciona

Cálculo da diferença entre o score da 1ª e da 2ª melhor opção encontrada.

### O que indica

Margens pequenas indicam sobreposição na taxonomia.

---

## Métricas Recall@K e Precision@K (Golden Set Dinâmico)

### Como funciona

Avaliação do "funil" de busca e da relevância das sugestões do topo aplicadas a um conjunto de dados de referência.

### O que indica

Um Recall baixo indica que a categoria correta não está sendo sequer cogitada na fase de busca inicial.

---

## Clusterização de Gaps

### Como funciona

Agrupamento semântico (`K-Means` / `DBSCAN`) dos casos classificados como `insufficient_confidence`.

### O que indica

Revela lacunas reais na taxonomia.

Clusters densos de falhas sinalizam necessidade de criar novas categorias específicas.

---

## Análise de Entropia

### Como funciona

Medição da concentração de *matches* entre as diversas categorias existentes.

### O que indica

Categorias com volume excessivo indicam que estão muito abrangentes.

---

## Golden Set Dinâmico

### Como funciona

Teste automático em um conjunto "blindado" de pares validados por especialistas humanos.

### O que indica

Garante não-regressão entre versões do modelo.

---

## Silver Labeling

### Como funciona

Auditoria amostral automática utilizando uma IA judicante superior.

### O que indica

Fornece um "termômetro" de precisão constante sem depender de revisão humana para cada caso.

---

# III. Protocolos de Investigação e Tomada de Decisão

## A. Queda no Score ou Aumento da Zona Cinzenta

### Investigação

Análise de proximidade em amostra de 50 registros.

### Decisão

- Fundir categorias semelhantes
- Refinar descrições
- Atualizar embeddings
- Atualizar taxonomia

---

## B. Baixo Recall ou Precision no Golden Set

### Investigação

Identificar se o erro ocorre:

- no estágio de busca (Bi-Encoder)
- no estágio de refinamento (Cross-Encoder)

### Decisão

- Ajustar estratégia de indexação
- Calibrar threshold

---

## C. Alta Concentração em Categorias Genéricas

### Investigação

Análise detalhada seguida de clusterização não supervisionada.

### Decisão

Decompor categorias em níveis mais granulares.

Exemplo:

```text
Linguagens → Python, Java, Go, Rust...
```

---

## D. Agrupamento Denso de "No-Matches"

### Investigação

Analisar o centróide do cluster de falhas para identificar o tema comum.

### Decisão

Expandir a taxonomia para cobrir novas tendências de mercado.