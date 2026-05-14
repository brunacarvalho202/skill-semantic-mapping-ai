# Desafio Técnico — Data Scientist | acaso

## Contexto

Na **acaso**, o trabalho central é processar grandes volumes de dados desestruturados para mapear o quadro de colaboradores em **skills (habilidades)**. Esse mapeamento permite que empresas com milhares de funcionários entendam quais competências existem internamente, identifiquem gaps e tomem decisões mais inteligentes sobre realocação, desenvolvimento e contratação.

Para isso, a acaso mantém uma **taxonomia de skills** — uma lista estruturada de competências com nomes e descrições padronizadas.

O problema central: pessoas descrevem as mesmas skills de formas muito diferentes dependendo da empresa, do cargo e do contexto. `"Gestão de pessoas"`, `"liderança de times"`, `"people management"` e `"desenvolvimento de equipes"` podem ou não representar a mesma skill, dependendo do contexto.

---

## O Problema

Dado dois arquivos CSV, construir uma solução que faça o mapeamento de forma automatizada e confiável.

### Arquivos de entrada

#### `data/new_skills.csv`
Skills brutas extraídas de perfis de colaboradores — exatamente como foram registradas.

| Campo | Descrição |
|---|---|
| `id` | Identificador único da skill bruta |
| `skill_raw` | Texto da skill como registrado pelo colaborador |

**Amostra:**

| id | skill_raw |
|---|---|
| 1 | gestão de pessoas |
| 2 | People Management |
| 3 | SQL |
| 4 | sql avançado |
| 7 | python |
| 8 | PYTHON |
| 13 | espiritualidade |
| 28 | Alinhamento com o universo |
| 43 | modelos de embedding |
| 87 | langchain |

---

#### `data/skill_taxonomy.csv`
Taxonomia oficial com nomes padronizados e descrições de cada skill.

| Campo | Descrição |
|---|---|
| `id` | Identificador único da skill na taxonomia |
| `skill_name` | Nome padronizado da skill |
| `description` | Descrição do que a skill representa |

**Amostra:**

| id | skill_name | description |
|---|---|---|
| 1 | Gestão de Pessoas | Capacidade de liderar, desenvolver e engajar equipes... |
| 6 | Pensamento Crítico | Capacidade de analisar informações de forma sistemática... |
| 31 | Python | Desenvolvimento em Python incluindo organização de projetos... |
| 32 | SQL | Escrita de consultas SQL incluindo joins, agregações... |
| 44 | Embeddings e Busca Vetorial | Uso de modelos de embedding e bancos de dados vetoriais... |
| 83 | LangChain | Desenvolvimento de aplicações com LLMs utilizando o framework LangChain... |

---

## Entregas Esperadas

### 1. Código e/ou notebook
Código funcional que recebe os dois CSVs e gera como output o mapeamento entre `new_skills` e `skill_taxonomy`, com indicação de confiança ou qualidade do match.

Pode ser entregue como **script Python**, **Jupyter Notebook**, ou ambos. Se usar notebook, esperamos que ele documente o raciocínio e a experimentação — não apenas o resultado final.

**Output esperado:** tabela com colunas como:

| new_skill_id | skill_raw | taxonomy_id | skill_name | confidence_score | match_status |
|---|---|---|---|---|---|
| 1 | gestão de pessoas | 1 | Gestão de Pessoas | 0.97 | matched |
| 13 | espiritualidade | — | — | — | no_match |

---

### 2. Estratégia de avaliação de qualidade
Como medir a qualidade do mapeamento em produção, considerando que anotar manualmente milhares de skills é inviável.

Deve ser **tecnicamente detalhada** — pode ser em texto, no notebook ou em comentários no código.

---

### 3. Registro de decisões técnicas
Documentar as escolhas feitas:
- Por que essa abordagem e não outra
- Onde ela pode falhar
- O que seria feito diferente com mais tempo ou recursos

ATENÇÃO: A documentação é tão importante quanto o código. Queremos entender a sua linha de raciocínio e como você chegou nas suas conclusões.

---

## O Que Será Avaliado

| Critério | Peso / Observação |
|---|---|
| Clareza do raciocínio | Como o problema técnico aberto é estruturado e comunicado |
| Qualidade das decisões técnicas | Escolha de abordagem, trade-offs, consciência das limitações |
| **Estratégia de avaliação** | **Parte mais importante do desafio** |
| Organização e legibilidade do código | — |

## O Que **Não** Será Avaliado

- Perfeição no resultado final — não existe resposta certa
- Uso ou não de ferramentas de IA para auxiliar na implementação — pode usar à vontade

---

## Estrutura do Repositório

```
.
├── data/
│   ├── new_skills.csv        # ~3.030 skills brutas
│   └── skill_taxonomy.csv    # 100 skills padronizadas
├── README.md                 # Este arquivo
└── requirements.txt          # Dependências do projeto

```

---

## Como Entregar

1. Faça uma cópia deste repositório.
2. Desenvolva a sua solução.
3. Envie o link do seu repositório para o recrutador.

---

> Tempo sugerido: entre 1h e 2h. Não é esperada uma solução exaustiva.
