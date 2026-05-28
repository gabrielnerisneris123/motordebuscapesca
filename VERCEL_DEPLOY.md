# 🚀 Deploy no Vercel

Este guia explica como fazer deploy do Motor de Busca no Vercel (ambiente serverless).

---

## ⚠️ Limitações do Serverless

O Vercel é um ambiente **serverless**, então algumas funcionalidades são adaptadas:

| Funcionalidade | Docker (Original) | Vercel (Serverless) |
|---|---|---|
| Banco de dados | PostgreSQL | SQLite (`/tmp/motordebusca.db`) |
| Workers contínuos | ✅ Sim | ❌ Não (apenas on-demand) |
| Celery + Beat | ✅ Sim | ❌ Não (stub que loga apenas) |
| Playwright | ✅ Sim | ❌ Não (apenas HTTP simples) |
| Redis | ✅ Sim | ❌ Não |
| Scraping em background | ✅ Sim | ⚠️ Via API apenas |

> **Nota:** O banco SQLite fica em `/tmp`, que é **ephemeral** no Vercel. Os dados são perdidos a cada cold start. Para persistência, use um banco externo (Supabase, Neon, etc.) ou exporte os dados regularmente.

---

## 📋 Pré-requisitos

1. Conta no [Vercel](https://vercel.com)
2. [Vercel CLI](https://vercel.com/docs/cli) instalado (opcional)
3. Git instalado

---

## 🔧 Deploy via Dashboard (Recomendado)

### 1. Push do código para o GitHub

```bash
git add .
git commit -m "Prepara deploy no Vercel"
git push origin main
```

### 2. Importar no Vercel

1. Acesse [vercel.com/new](https://vercel.com/new)
2. Importe seu repositório do GitHub
3. Configure:
   - **Framework Preset:** `Other`
   - **Build Command:** (deixe em branco)
   - **Output Directory:** (deixe em branco)
   - **Install Command:** `pip install -r requirements-vercel.txt`

4. Adicione as **Environment Variables**:

| Variável | Valor |
|---|---|
| `DATABASE_URL` | `sqlite+aiosqlite:///tmp/motordebusca.db` |
| `DATABASE_URL_SYNC` | `sqlite:///tmp/motordebusca.db` |
| `APP_ENV` | `production` |
| `DEBUG` | `false` |

5. Clique em **Deploy**

---

## 🔧 Deploy via CLI

```bash
# Instalar Vercel CLI
npm i -g vercel

# Login
vercel login

# Deploy
vercel --prod
```

---

## 📁 Arquivos Criados/Modificados para o Deploy

```
motordebusca/
├── api/
│   └── index.py              # Entrypoint do Vercel (handler)
├── app/
│   ├── config_vercel.py      # Config com SQLite
│   ├── database_vercel.py    # Database com aiosqlite
│   ├── main_vercel.py        # App FastAPI sem seed automático
│   ├── celery_app_vercel.py  # Stub do Celery
│   ├── tasks_vercel.py       # Tasks sem background
│   └── crawler/
│       └── scraper_vercel.py # Scraper sem Playwright
├── requirements-vercel.txt   # Dependências reduzidas
├── vercel.json               # Configuração do Vercel
└── VERCEL_DEPLOY.md          # Este guia
```

---

## 🧪 Testando Localmente (modo Vercel)

```bash
# Instalar dependências do Vercel
pip install -r requirements-vercel.txt

# Rodar o app
python -c "
from api.index import app
import uvicorn
uvicorn.run(app, host='0.0.0.0', port=8000)
"
```

Acesse: http://localhost:8000

---

## 🔄 Usando PostgreSQL Externo (Recomendado para Produção)

Para persistir dados no Vercel, use um banco PostgreSQL externo:

### Opções gratuitas:
- [Supabase](https://supabase.com) — 500MB
- [Neon](https://neon.tech) — 500MB
- [ElephantSQL](https://elephantsql.com) — 20MB (Tiny Turtle)

### Configuração:

1. Crie um banco no provedor escolhido
2. Copie a connection string
3. No Vercel Dashboard, adicione:

```
DATABASE_URL=postgresql+asyncpg://user:pass@host:5432/dbname
DATABASE_URL_SYNC=postgresql://user:pass@host:5432/dbname
```

4. Re-deploy

---

## 📊 Funcionalidades Disponíveis no Vercel

✅ **API REST completa** (`/api/v1/*`)
✅ **Dashboard** (`/`)
✅ **CRUD de Fontes**
✅ **Listagem e busca de Conteúdos**
✅ **Extração de Entidades**
✅ **Estatísticas**
✅ **Exportação CSV**
✅ **Scraping on-demand** (via endpoints `/api/v1/coleta/*`)

❌ **Workers contínuos** (discovery/scraper)
❌ **Celery Beat** (agendamento automático)
❌ **Playwright** (sites JS-heavy)
❌ **Persistência de dados** (sem banco externo)

---

## 💡 Dicas

1. **Para scraping contínuo:** Use o Docker localmente para coletar dados, depois exporte para o Vercel
2. **Para persistência:** Configure um PostgreSQL externo
3. **Para sites JS-heavy:** O scraper do Vercel usa apenas HTTP simples (sem Playwright)
4. **Cold starts:** O SQLite é recriado a cada cold start — use banco externo para produção

---

## 🆘 Troubleshooting

### "Module not found"
Verifique se `requirements-vercel.txt` está no repositório e se todas as dependências estão listadas.

### "Database is locked" (SQLite)
No Vercel, o SQLite em `/tmp` pode ter concorrência. Use PostgreSQL externo para produção.

### "Timeout" ao coletar
O Vercel tem limite de 10s (Hobby) ou 60s (Pro) para serverless functions. Coletas longas podem ser interrompidas.

### Dashboard não carrega
Verifique se os arquivos estáticos estão em `app/dashboard/static/` e se a rota `/static` está configurada.
