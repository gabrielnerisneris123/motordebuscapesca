# 🎣 Motor de Busca — Pesca Esportiva Brasileira

Plataforma de coleta massiva, processamento e organização de dados sobre pesca esportiva brasileira. Construída para criar um banco de dados proprietário sem depender de APIs pagas.

---

## Arquitetura

```
motordebusca/
├── app/
│   ├── main.py               # FastAPI app principal
│   ├── config.py             # Configurações via env vars
│   ├── database.py           # Engine SQLAlchemy async/sync
│   ├── celery_app.py         # Celery + agendamento
│   ├── tasks.py              # Tasks assíncronas Celery
│   ├── models/               # Modelos SQLAlchemy
│   │   ├── fonte.py          # Fontes de dados
│   │   ├── conteudo.py       # Conteúdos coletados
│   │   ├── entidade.py       # Entidades extraídas
│   │   └── log.py            # Logs de coleta
│   ├── schemas/              # Schemas Pydantic
│   ├── api/routes/           # Endpoints FastAPI
│   │   ├── fontes.py         # CRUD de fontes
│   │   ├── conteudos.py      # Listagem e busca
│   │   ├── coleta.py         # Controle de coleta
│   │   ├── entidades.py      # Entidades extraídas
│   │   └── stats.py          # Estatísticas e logs
│   ├── crawler/
│   │   ├── discovery.py      # Descoberta automática de fontes
│   │   ├── scraper.py        # Motor de coleta HTTP + Playwright
│   │   ├── http_client.py    # Cliente HTTP com rate limiting
│   │   └── utils.py          # Utilitários
│   ├── processing/
│   │   ├── cleaner.py        # Limpeza de HTML
│   │   ├── deduplication.py  # Hash + SimHash
│   │   └── pipeline.py       # Pipeline completo
│   ├── classifier/
│   │   ├── keywords.py       # Dicionários de pesca
│   │   └── entities.py       # Extração de entidades
│   └── dashboard/static/
│       └── index.html        # Dashboard administrativo
├── workers/
│   ├── discovery_worker.py   # Worker de descoberta
│   └── scraper_worker.py     # Worker de coleta
├── scripts/
│   ├── seed_sources.py       # Seed de fontes iniciais
│   └── exportar_dataset.py   # Exportação CSV/JSONL
├── docker-compose.yml
├── Dockerfile
└── requirements.txt
```

---

## Stack

| Componente | Tecnologia |
|---|---|
| API | FastAPI + Uvicorn |
| Banco de Dados | PostgreSQL 16 |
| ORM | SQLAlchemy 2 async |
| Fila de Tarefas | Celery + Redis |
| Scraping Estático | httpx + BeautifulSoup |
| Scraping Dinâmico | Playwright (Chromium) |
| Deduplicação | SHA-256 + SimHash |
| Agendamento | Celery Beat |
| Dashboard | HTML/JS puro (sem framework) |

---

## Início Rápido

### 1. Configurar ambiente

```bash
cp .env.example .env
# Editar .env com suas configurações
```

### 2. Subir com Docker

```bash
docker-compose up -d
```

Isso inicia:
- PostgreSQL na porta 5432
- Redis na porta 6379
- API FastAPI na porta 8000
- Worker de descoberta (loop a cada 60min)
- Worker de scraping (loop contínuo)
- Celery Worker (tasks distribuídas)
- Celery Beat (agendamento automático)

### 3. Acessar

- **Dashboard:** http://localhost:8000
- **API Docs:** http://localhost:8000/docs
- **ReDoc:** http://localhost:8000/redoc

---

## Instalação Local (sem Docker)

```bash
# Criar ambiente virtual
python -m venv venv
venv\Scripts\activate  # Windows

# Instalar dependências
pip install -r requirements.txt

# Instalar Playwright
playwright install chromium

# Configurar banco
# Certifique que PostgreSQL e Redis estão rodando
cp .env.example .env
# Editar .env

# Iniciar API
uvicorn app.main:app --reload

# Em outro terminal: Worker descoberta
python -m workers.discovery_worker

# Em outro terminal: Worker scraper
python -m workers.scraper_worker

# Opcional: Seed manual de fontes
python scripts/seed_sources.py
```

---

## Endpoints da API

### Fontes
| Método | Rota | Descrição |
|---|---|---|
| GET | `/api/v1/fontes` | Lista todas as fontes |
| POST | `/api/v1/fontes` | Adiciona nova fonte |
| PATCH | `/api/v1/fontes/{id}` | Atualiza fonte |
| DELETE | `/api/v1/fontes/{id}` | Remove fonte |
| POST | `/api/v1/fontes/{id}/expandir` | Crawla links da fonte |
| POST | `/api/v1/fontes/descoberta/iniciar` | Inicia busca automática |

### Conteúdos
| Método | Rota | Descrição |
|---|---|---|
| GET | `/api/v1/conteudos` | Lista conteúdos com filtros |
| GET | `/api/v1/conteudos/{id}` | Detalhe do conteúdo |
| POST | `/api/v1/conteudos/{id}/processar` | Reprocessa conteúdo |
| GET | `/api/v1/conteudos/exportar/csv` | Exporta CSV |

### Coleta
| Método | Rota | Descrição |
|---|---|---|
| POST | `/api/v1/coleta/iniciar/{fonte_id}` | Coleta uma fonte |
| POST | `/api/v1/coleta/iniciar-todas` | Coleta todas as fontes |
| POST | `/api/v1/coleta/processar-pendentes` | Processa pendentes |
| POST | `/api/v1/coleta/descobrir-sitemap/{id}` | Descobre sitemap |
| GET | `/api/v1/coleta/status` | Status geral |

### Entidades
| Método | Rota | Descrição |
|---|---|---|
| GET | `/api/v1/entidades` | Lista entidades |
| GET | `/api/v1/entidades/tipos` | Contagem por tipo |
| GET | `/api/v1/entidades/top/{tipo}` | Top entidades de um tipo |

### Estatísticas
| Método | Rota | Descrição |
|---|---|---|
| GET | `/api/v1/stats` | Estatísticas gerais |
| GET | `/api/v1/stats/logs` | Logs recentes |
| GET | `/api/v1/stats/crescimento` | Crescimento diário |

---

## Banco de Dados

### Tabelas Principais

**fontes** — Fontes de dados descobertas
- `id`, `url`, `dominio`, `status`, `score_relevancia`
- `paginas_coletadas`, `ultima_coleta`, `tem_sitemap`, `tem_rss`

**conteudos** — Conteúdo coletado
- `id`, `fonte_id`, `url`, `titulo`, `conteudo_texto`
- `hash_conteudo` (SHA-256 para dedup exata)
- `hash_simhash` (SimHash para dedup aproximada)
- `score_relevancia`, `num_palavras`, `tags`, `categorias`

**entidades** — Entidades extraídas automaticamente
- Tipos: `especie`, `ingrediente`, `tecnica`, `equipamento`, `local`, `evento`, `aroma`
- `frequencia` — quantas vezes apareceu nos textos

**conteudo_entidades** — Relação N:N com contexto
- Permite buscar "quais conteúdos falam sobre carpa-comum"

**logs_coleta** — Histórico de operações

---

## Agendamento Automático (Celery Beat)

| Task | Frequência | Descrição |
|---|---|---|
| Descoberta de Fontes | A cada 6h | Busca DuckDuckGo + Bing |
| Coleta de Conteúdos | A cada 30min | Coleta fontes ativas |
| Processamento | A cada 15min | Processa pendentes |
| Limpeza de Logs | Diário às 2h | Remove logs antigos |

---

## Exportação de Dataset

```bash
# Exporta CSV e JSONL com conteúdos processados
python scripts/exportar_dataset.py
```

Gera:
- `dataset_pesca.csv` — formato tabular
- `dataset_pesca.jsonl` — formato para treinamento de LLMs

---

## Escalabilidade

- **Múltiplos workers Celery** — aumentar `--concurrency`
- **Múltiplas instâncias do scraper_worker** — basta subir mais containers
- **Rate limiting por domínio** — respeita robots.txt automaticamente
- **SimHash** — detecta conteúdos ~similares (duplicação parcial)
- **PostgreSQL** — suporta milhões de registros com índices apropriados
- **Playwright** — suporte automático a sites dinâmicos (JS)

---

## Variáveis de Ambiente

| Variável | Padrão | Descrição |
|---|---|---|
| `CRAWL_DELAY_MIN` | 1.0 | Delay mínimo entre requests (seg) |
| `CRAWL_DELAY_MAX` | 4.0 | Delay máximo entre requests (seg) |
| `MAX_CONCURRENT_REQUESTS` | 10 | Máximo de requests simultâneos |
| `MAX_PAGES_PER_DOMAIN` | 500 | Limite de páginas por domínio |
| `SCRAPER_WORKERS` | 4 | Workers paralelos |
| `BATCH_SIZE` | 50 | URLs por ciclo de coleta |
| `DISCOVERY_INTERVAL_MINUTES` | 60 | Intervalo do worker de descoberta |
