# apps/api — HRSP Backend API

Backend Python (FastAPI) da HexaRelational Significance Platform.

## Estrutura

```
apps/api/
├── src/
│   ├── main.py          # FastAPI app entry point
│   ├── models.py        # Pydantic request/response models
│   ├── engine.py        # Integration with Core IPII Engine
│   ├── limits.py        # Plan limits and rate limiting
│   └── security.py      # Turnstile verification, JWT helpers
├── pyproject.toml
└── README.md            # Este arquivo
```

## Pré-requisitos

- Python 3.10+
- Dependências do Core Engine (numpy, matplotlib, rich)

## Instalação local

```bash
# A partir da raiz do repositório:
python -m venv .venv
source .venv/bin/activate

# Instalar o core engine + dependências da API
pip install -r requirements.txt
pip install -r requirements-dev.txt
cd apps/api
pip install -e ".[dev]"
```

## Executar localmente

```bash
# A partir de apps/api/ (com o venv ativo e o core instalado)
uvicorn src.main:app --reload --port 8000
```

Ou a partir da raiz do repositório:

```bash
uvicorn apps.api.src.main:app --reload --port 8000
```

## Endpoints

| Método | Path | Descrição |
|--------|------|-----------|
| GET | `/health` | Health check (versão da API e do engine) |
| POST | `/runs` | Executa o pipeline IPII e retorna resultado |
| GET | `/runs/{id}` | Retorna status/resultado de um run |

## Variáveis de Ambiente

Copie `.env.example` para `.env` e preencha os valores:

```bash
cp ../../infra/env/.env.example .env
```

| Variável | Descrição | Obrigatório |
|----------|-----------|:-----------:|
| `CF_TURNSTILE_SECRET_KEY` | Chave secreta Cloudflare Turnstile | Prod |
| `DATABASE_URL` | URL do PostgreSQL | Prod |
| `REDIS_URL` | URL do Redis | Prod |
| `JWT_SECRET` | Secret para assinar JWT | Prod |
| `ENGINE_VERSION` | Versão do engine (default: da lib) | Não |
| `OPENAI_API_KEY` | Chave OpenAI (modo LLM; opcional) | Não |

## Smoke Test

```bash
# Health check
curl http://localhost:8000/health

# Run simples (anônimo, modo MVP sem Turnstile)
curl -X POST http://localhost:8000/runs \
  -H "Content-Type: application/json" \
  -d '{"code": "def f(n):\n    return n * 2", "target_lang": "javascript"}'
```

## Testes

```bash
# Testes do core engine
pytest ../../tests/ -v

# Smoke test da API (requer servidor rodando)
curl -f http://localhost:8000/health
```
