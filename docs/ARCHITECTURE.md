# Arquitetura — HexaRelational Significance Platform (HRSP)

> **Versão:** 1.0 | **Data:** Abril 2026

---

## 1. Visão Geral

```
┌──────────────────────────────────────────────────────────────────┐
│                    Cloudflare Edge                                │
│   WAF · Rate Limit · Turnstile · Bot Fight · DDoS · TLS 1.3      │
└────────────────────────┬─────────────────────────────────────────┘
                         │
          ┌──────────────┴──────────────┐
          │                             │
    ┌─────▼──────┐               ┌──────▼──────┐
    │  apps/web  │               │  apps/api   │
    │  Next.js   │──── REST ────►│  FastAPI    │
    │  Vercel    │               │  (container)│
    └────────────┘               └──────┬──────┘
                                        │
                    ┌───────────────────┼───────────────────┐
                    │                   │                   │
              ┌─────▼─────┐    ┌───────▼──────┐    ┌──────▼──────┐
              │ PostgreSQL │    │ Object Store │    │ Job Queue   │
              │ (metadata) │    │ (S3-compat.) │    │ (Redis/SQS) │
              └─────┬──────┘    └──────────────┘    └─────────────┘
                    │
              ┌─────▼──────┐
              │ Core IPII  │
              │ Engine     │
              │ (Python)   │
              └────────────┘
```

---

## 2. Componentes

### 2.1 `apps/web` — Frontend (Next.js no Vercel)

**Stack:** Next.js 14+ (App Router) · TypeScript · Tailwind CSS

**Responsabilidades:**
- UI para submissão de código e seleção de linguagem-alvo.
- Exibição de resultados: métricas f(A), Π(A), relações, radar PNG.
- Autenticação via NextAuth.js (OAuth GitHub/Google + credenciais).
- Painel de histórico de runs e projetos.
- Painel de billing e planos (integrado ao Stripe Customer Portal).
- Placeholder para login e paywall de share link.
- Integração com Cloudflare Turnstile (widget embutido).

**Deploy:** Vercel (serverless; sem workloads Python no Vercel).

**Variáveis de ambiente (sem segredos no repo):**
```
NEXT_PUBLIC_API_URL=https://api.hrsp.app
NEXT_PUBLIC_CF_TURNSTILE_SITE_KEY=<site-key-publica>
NEXTAUTH_URL=https://hrsp.app
NEXTAUTH_SECRET=<secret>          # apenas no runtime do Vercel
```

---

### 2.2 `apps/api` — Backend (Python FastAPI, containerizado)

**Stack:** Python 3.12 · FastAPI · Pydantic v2 · SQLAlchemy · Alembic

**Responsabilidades:**
- Endpoint `GET /health` — health check.
- Endpoint `POST /runs` — aceita código + target, valida, enfileira/executa.
- Endpoint `GET /runs/{id}` — retorna status e resultado do run.
- Validação de tamanho de payload (5 KB anônimo / 10 KB logado / 50 KB Pro).
- Verificação de Cloudflare Turnstile token.
- Autenticação JWT e verificação de plano.
- Integração com o Core IPII Engine.
- Geração de artefatos em memória e upload para object storage.
- Webhook Stripe (`POST /webhooks/stripe`).
- Metering e contagem de runs por plano.

**Deploy:** Container Docker em qualquer host que suporte workloads Python (Fly.io, Render, Railway, AWS ECS, GCP Cloud Run, etc.).

**Variáveis de ambiente (sem segredos no repo):**
```
DATABASE_URL=postgresql://...
REDIS_URL=redis://...
S3_BUCKET=hrsp-artifacts
S3_ENDPOINT_URL=...
AWS_ACCESS_KEY_ID=...
AWS_SECRET_ACCESS_KEY=...
STRIPE_SECRET_KEY=...
STRIPE_WEBHOOK_SECRET=...
CF_TURNSTILE_SECRET_KEY=...
JWT_SECRET=...
ENGINE_VERSION=0.1.0
```

---

### 2.3 Core IPII Engine

**Localização:** Pacote Python neste repositório (`core/`, `ipii/`, `gurumatrix/`, `utils/`).

**Integração:** `apps/api` importa diretamente:
```python
from ipii.transpiler import SemanticTranspiler
from gurumatrix.tensor import GuruMatrix, TargetLanguage
from core.operator import pi_radical_significance
from utils.visualization import plot_significance_profile
```

**Versão do engine:** registrada em `pyproject.toml` e exposta via `GET /health` para reprodutibilidade de runs.

**Timeout e isolamento:** execução do engine em thread pool com timeout configurável; para isolamento maior (futuro): subprocess com RLIMIT.

---

### 2.4 Banco de Dados (PostgreSQL)

**Modelo conceitual de entidades:**

```
Organization
  ├── id, name, slug, plan, stripe_customer_id
  ├── created_at, updated_at
  └── members (via OrgMember)

OrgMember
  ├── org_id, user_id, role (owner/admin/member/viewer/auditor)
  └── invited_at, joined_at

User
  ├── id, email, name, oauth_provider, oauth_sub
  ├── daily_run_count, last_run_date
  └── created_at

Project
  ├── id, org_id, name, description
  └── created_at

Run
  ├── id (UUID), org_id, user_id, project_id
  ├── target_lang, input_hash (SHA-256 do código; jamais o código bruto)
  ├── input_size_bytes, engine_version
  ├── status (queued/running/done/failed/timeout)
  ├── f_A, pi_A, iterations, distance
  ├── relation_scores (JSONB)
  ├── artifact_json_key, artifact_png_key (keys no S3)
  ├── created_at, completed_at, expires_at
  └── mode (heuristic/llm)
```

---

### 2.5 Object Storage (S3-compatível)

**Armazenamento:**
- `{org_id}/{run_id}/report.json` — resultado estruturado completo.
- `{org_id}/{run_id}/profile.png` — radar de significância.
- `{org_id}/{run_id}/profile.svg` — radar em SVG (Pro+).
- `{org_id}/{run_id}/tensor.npy` — GuruMatrix aprendida (Enterprise).

**Acesso:** URLs pré-assinadas com expiração curta (ex.: 1 hora).  
**Política:** bucket privado; sem acesso público direto.

---

### 2.6 Fila de Jobs (Redis / SQS / Celery)

**Propósito:** execução assíncrona de runs para não bloquear a API.

**Fluxo:**
```
POST /runs → valida → enfileira → retorna run_id com status=queued
Worker → pega job → executa engine → atualiza DB + upload artefatos → status=done
GET /runs/{id} → retorna status atual (queued/running/done)
```

**MVP:** execução síncrona em thread pool (sem fila externa) — adequado para carga baixa.  
**Produção:** Celery + Redis (ou AWS SQS) para escalar workers independentemente.

---

### 2.7 Multi-tenant e RBAC

**Isolamento de tenant:**
- Toda query ao DB filtra por `org_id` do token JWT.
- Artefatos no storage organizados por `org_id/`.
- Nenhum dado de uma org é acessível a outra.

**Papéis (Role-Based Access Control):**

| Papel | Pode criar runs | Pode ler runs | Pode gerenciar membros | Pode exportar auditoria |
|-------|:-:|:-:|:-:|:-:|
| Owner | ✅ | ✅ | ✅ | ✅ |
| Admin | ✅ | ✅ | ✅ | ✅ |
| Member | ✅ | ✅ | ❌ | ❌ |
| Viewer | ❌ | ✅ | ❌ | ❌ |
| Auditor | ❌ | ✅ | ❌ | ✅ |

---

### 2.8 Versão do Engine e Reprodutibilidade

- Toda execução registra `engine_version` (ex.: `0.1.0`) no Run.
- `GET /health` expõe a versão atual do engine.
- Para reexecução de run histórico com versão diferente: registrar divergência esperada nos metadados.
- Dependências fixadas via lock files para garantir determinismo.

---

## 3. Segurança por Camada

| Camada | Controle |
|--------|---------|
| Edge (Cloudflare) | WAF, rate limit, Turnstile, DDoS, TLS 1.3 |
| Frontend (web) | CSP, HSTS, SameSite cookies, CSRF token (NextAuth) |
| API (FastAPI) | JWT validation, payload size limit, CORS, IDOR check, Stripe webhook HMAC |
| Engine | Timeout, no code execution (apenas parsing estático), sandbox futuro |
| Storage | Bucket privado, URLs pré-assinadas, criptografia em repouso |
| DB | Credenciais rotacionáveis, TLS, row-level isolation por org |
| CI/CD | Actions fixadas por SHA, secrets scanning, Trivy scan |

---

## 4. Fluxo de Dados — POST /runs

```
1. Usuário preenche código + target na UI (apps/web)
2. Frontend verifica Turnstile (se anônimo) e obtém token
3. Frontend faz POST /runs com {code, target, cf_turnstile_token}
4. apps/api:
   a. Valida tamanho do payload (5/10/50 KB por plano)
   b. Verifica Turnstile token com Cloudflare API (se anônimo)
   c. Verifica JWT e plano (se logado)
   d. Verifica rate limit e cota de runs
   e. Calcula SHA-256 do código (para deduplicação e log)
   f. Cria Run(status=queued) no DB
   g. Envia para fila (ou executa sincronamente no MVP)
5. Worker executa SemanticTranspiler.transpile(code, target)
6. Artefatos gerados em memória → upload S3
7. Run atualizado: status=done, métricas, artifact_keys
8. Frontend polling GET /runs/{id} até status=done
9. Frontend exibe resultados + URL pré-assinada para PNG
```

---

## 5. Decisões de Design

| Decisão | Escolha | Motivo |
|---------|---------|--------|
| Python fora do Vercel | FastAPI em container separado | NumPy/matplotlib incompatíveis com Vercel serverless |
| Código bruto não persiste | Apenas SHA-256 em logs | LGPD/GDPR + privacidade por design |
| Turnstile obrigatório (anônimo) | Cloudflare Turnstile | Proteção anti-bot sem fricção excessiva |
| JWT no backend | RS256/ES256 | Não expor segredos de assinatura ao frontend |
| URLs pré-assinadas para artefatos | S3 pre-signed URLs | Acesso temporário sem expor bucket público |
| Fila assíncrona | Celery/Redis | Desacopla API de workloads pesados |
| Cripto-agility | Interface abstrata para cripto | Permite migração PQC sem refatoração |

---

*Documento de referência para implementação. Revisar a cada release major.*
