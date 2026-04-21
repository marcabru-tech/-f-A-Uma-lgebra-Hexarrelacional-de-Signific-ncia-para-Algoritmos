# Prompt para Agente de IA — Implementação da HRSP

> **Arquivo:** `docs/AI_IMPLEMENTATION_PROMPT.md`  
> **Idioma:** Português  
> **Propósito:** Instruções completas para um agente de IA implementar a HexaRelational Significance Platform a partir deste repositório.

---

## PROMPT PARA AGENTE DE IA

Você é um agente de engenharia de software sênior. Sua tarefa é implementar a **HexaRelational Significance Platform (HRSP)** a partir do repositório `marcabru-tech/algebra-hexarrelacional`, que já contém o motor matemático central (Core IPII Engine) completamente funcional e testado.

---

### 1. Contexto e Objetivos

O repositório já contém:
- **Core IPII Engine** (`core/`, `ipii/`, `gurumatrix/`, `utils/`) — completamente funcional.
- **38 testes unitários** passando (`pytest tests/ -v`).
- **Exemplo end-to-end** (`examples/semantic_transpilation.py`).

Você deve implementar sobre este núcleo uma **plataforma SaaS freemium global**, com:
- Frontend web (Next.js no Vercel).
- Backend API (Python FastAPI, containerizado).
- Integração com Stripe (pagamentos USD e BRL).
- Proteção Cloudflare (WAF, rate limit, Turnstile).
- Compliance LGPD + GDPR.
- Cripto-agility (roadmap PQC).

**Não quebre o Core IPII Engine nem os testes existentes.**

---

### 2. Arquitetura Alvo

```
Cloudflare (WAF + Rate Limit + Turnstile + DDoS)
       │
       ├─► apps/web (Next.js, Vercel) ──────────────────────────┐
       │                                                         │ REST HTTPS
       └─► apps/api (Python FastAPI, container) ◄───────────────┘
                │
                ├── Core IPII Engine (este repositório, importado como pacote)
                ├── PostgreSQL (metadados, runs, orgs, usuários)
                ├── S3-compatível (artefatos: PNG, JSON, NPY)
                └── Redis (rate limiting, fila de jobs)
```

**Princípio fundamental:** o backend Python (`apps/api`) **nunca** roda no Vercel. O Vercel hospeda apenas o Next.js (`apps/web`).

---

### 3. Requisitos Funcionais (RF)

Implemente na seguinte ordem de prioridade:

#### 3.1 MVP (R1 — primeiros sprints)
- [ ] `GET /health` — retorna versão da API e do engine.
- [ ] `POST /runs` — aceita `{code, target_lang, cf_turnstile_token?}`, valida, executa, retorna resultado.
- [ ] `GET /runs/{id}` — retorna status e resultado do run.
- [ ] Página web com textarea (código), select (linguagem-alvo), botão "Executar".
- [ ] Exibição dos resultados: f(A), Π(A), relações, imagem radar.
- [ ] Validação de tamanho: 5 KB (anônimo), 10 KB (Free logado).
- [ ] Rate limit: 2 runs/dia por IP (anônimo), 10 runs/dia por usuário (Free logado).
- [ ] Cloudflare Turnstile obrigatório para runs anônimos.
- [ ] Código bruto **jamais** persiste em logs (apenas SHA-256).

#### 3.2 Autenticação e Planos (R2)
- [ ] Login via OAuth (GitHub, Google) e e-mail/senha.
- [ ] Organizações com papéis: Owner, Admin, Member, Viewer, Auditor.
- [ ] JWT com claims de plano e org.
- [ ] Plano Free Logado: 10 runs/dia, 10 KB, 1 job simultâneo, retenção 7 dias.
- [ ] Hard limits verificados no backend (jamais confiar no frontend).

#### 3.3 Billing (R3)
- [ ] Integração Stripe Checkout para Pro (US$19/R$79) e Team (US$99/R$399).
- [ ] Webhooks Stripe: `checkout.session.completed`, `customer.subscription.deleted`, `invoice.payment_failed`.
- [ ] Share link (Pro+): UUID expiráveis, revogáveis ao rebaixar plano.
- [ ] API token (Pro+): scoped, revogável.

#### 3.4 RBAC e Dashboard (R4)
- [ ] Dashboard com histórico de runs por projeto/org.
- [ ] Comparação de runs lado a lado.
- [ ] Exportação de artefatos (JSON, PNG, SVG).
- [ ] Painel de consumo (runs usados / limite).

#### 3.5 Enterprise/Gov (R5)
- [ ] SSO/SAML.
- [ ] Papel Auditor com exportação de trilha de auditoria.
- [ ] "LLM Off" e BYOK por org.
- [ ] Retenção customizável.
- [ ] Relatório de auditoria em PDF.

---

### 4. Requisitos Não Funcionais (RNF)

#### 4.1 Segurança
- **RNF-SEC-01:** Código bruto nunca em logs — apenas `SHA-256(code)`.
- **RNF-SEC-02:** Secrets apenas em variáveis de ambiente do runtime (nunca em código ou imagem Docker).
- **RNF-SEC-03:** JWT assinado com RS256 ou ES256; verificado em cada request autenticado.
- **RNF-SEC-04:** Verificação de ownership em todos os endpoints de run (`run.org_id == requester.org_id`).
- **RNF-SEC-05:** Webhook Stripe verificado com HMAC antes de processar.
- **RNF-SEC-06:** CORS restrito ao domínio do frontend.
- **RNF-SEC-07:** Headers de segurança obrigatórios: `Strict-Transport-Security`, `X-Content-Type-Options`, `X-Frame-Options`, `Content-Security-Policy`.
- **RNF-SEC-08:** Dependências fixadas com lock file; sem dependências com CVEs conhecidas críticas.
- **RNF-SEC-09:** Cripto-agility — abstrair todos os algoritmos criptográficos atrás de interfaces configuráveis.

#### 4.2 Performance
- **RNF-PERF-01:** P95 de tempo de resposta ≤ 10s para runs Free logado.
- **RNF-PERF-02:** Validação de payload (tamanho, Turnstile) antes de executar o engine.
- **RNF-PERF-03:** Engine executado com timeout configurável; processo/thread encerrado no timeout.

#### 4.3 Observabilidade
- **RNF-OBS-01:** Logs estruturados (JSON) com campos: `request_id`, `user_id`, `org_id`, `run_id`, `duration_ms`, `status`.
- **RNF-OBS-02:** Métricas expostas (latência, erros 4xx/5xx, runs por plano).
- **RNF-OBS-03:** `engine_version` registrado em cada run (reprodutibilidade).

#### 4.4 Compliance
- **RNF-COMP-01:** Toda base legal de tratamento documentada.
- **RNF-COMP-02:** Consentimento para LLM externo registrado com timestamp por org.
- **RNF-COMP-03:** Endpoint de deleção de conta (`DELETE /users/me`) exclui todos os dados em cascata.
- **RNF-COMP-04:** Exportação de dados pessoais (`GET /users/me/export`).

---

### 5. Regras de Negócio (Planos, Paywalls, Limites)

#### 5.1 Free Anônimo
```python
MAX_INPUT = 5 * 1024        # 5 KB
MAX_RUNS_PER_DAY = 2        # por IP/device
TURNSTILE_REQUIRED = True   # obrigatório
RETENTION_DAYS = 0          # sem retenção
TIMEOUT_SECONDS = 10
```

#### 5.2 Free Logado
```python
MAX_INPUT = 10 * 1024       # 10 KB
MAX_RUNS_PER_DAY = 10       # por usuário
MAX_CONCURRENT = 1          # 1 job por vez
RETENTION_DAYS = 7
TIMEOUT_SECONDS = 10
SHARE_LINK = False          # paywall Pro+
API_TOKEN = False           # paywall Pro+
LLM_ENABLED = False
```

#### 5.3 Pro (US$19/R$79 por usuário/mês)
```python
MAX_INPUT = 50 * 1024       # 50 KB
MAX_RUNS_PER_DAY = None     # ilimitado (fair use)
MAX_CONCURRENT = 5
RETENTION_DAYS = 90
TIMEOUT_SECONDS = 30
SHARE_LINK = True
API_TOKEN = True
LLM_ENABLED = True          # com consentimento por org
```

#### 5.4 Team (US$99/R$399 por mês, até 5 usuários)
```python
MAX_INPUT = 50 * 1024
MAX_RUNS_PER_DAY = None
MAX_CONCURRENT = 10
RETENTION_DAYS = 180
TIMEOUT_SECONDS = 30
SHARE_LINK = True
API_TOKEN = True
LLM_ENABLED = True
EXTRA_USER_PRICE_USD = 15   # por usuário/mês adicional
EXTRA_USER_PRICE_BRL = 60
```

#### 5.5 Regras de Paywall
- Share link **nunca** disponível em Free (anônimo ou logado).
- API token **nunca** disponível em Free.
- Verificação sempre no backend; frontend apenas exibe estado.
- Ao rebaixar plano: revogar share links e tokens imediatamente.
- Sem trial; pagamento obrigatório antes de ativar recursos pagos.

#### 5.6 Moedas e Pagamentos
- Stripe com suporte a USD e BRL.
- Preços fixos em cada moeda (sem conversão em tempo real).
- Revisão trimestral com notificação 30 dias antes.

---

### 6. Compliance LGPD / GDPR

#### 6.1 Regras de implementação
1. **Código bruto nunca em logs** — logar apenas `sha256(code)`.
2. **Artefatos expiram** automaticamente conforme `retention_days` do plano.
3. **Deleção sob demanda** — `DELETE /users/me` deve excluir tudo em cascata.
4. **Exportação** — `GET /users/me/export` retorna todos os dados em JSON.
5. **Consentimento LLM** — registrado com timestamp, revogável; sem LLM sem consentimento explícito.
6. **Bases legais documentadas** — cada tipo de dado deve ter base legal clara no código (comentário ou constante).
7. **Privacy by Design** — dados mínimos necessários; sem coletar além do essencial.

#### 6.2 Campos proibidos em logs
```python
SENSITIVE_FIELDS = {"code", "source_code", "password", "token", "api_key", "secret"}
# Usar redact_sensitive(data) antes de logar qualquer dict
```

#### 6.3 Tabela de bases legais
| Dado | Base legal (LGPD art.) | Base legal (GDPR art.) |
|------|----------------------|----------------------|
| E-mail/nome | Art. 7º, V (contrato) | Art. 6(1)(b) |
| IP e logs de acesso | Art. 7º, IX (interesse legítimo) | Art. 6(1)(f) |
| Código enviado | Art. 7º, V (contrato) | Art. 6(1)(b) |
| Hash do código | Art. 7º, IX (interesse legítimo) | Art. 6(1)(f) |
| Consentimento LLM | Art. 7º, I (consentimento) | Art. 6(1)(a) |
| Dados de pagamento | Art. 7º, V (contrato; controlador: Stripe) | Art. 6(1)(b) |

---

### 7. Cloudflare e Turnstile

#### 7.1 Configuração obrigatória no Cloudflare
```yaml
# infra/cloudflare/waf_rules.yaml (referência)
rate_limits:
  - path: /runs
    method: POST
    rate: 10/min  # por IP (Free)
    action: block
  - path: /auth
    rate: 20/min  # por IP
    action: challenge
waf:
  ruleset: owasp_core
  level: medium
turnstile:
  mode: managed  # transparente para o usuário
bot_fight_mode: true
ddos_protection: true
```

#### 7.2 Verificação do Turnstile no backend
```python
# apps/api/src/security/turnstile.py
import httpx

async def verify_turnstile(token: str, ip: str) -> bool:
    """Verifica token Cloudflare Turnstile com a API da CF."""
    async with httpx.AsyncClient() as client:
        resp = await client.post(
            "https://challenges.cloudflare.com/turnstile/v0/siteverify",
            data={
                "secret": settings.CF_TURNSTILE_SECRET_KEY,
                "response": token,
                "remoteip": ip,
            },
        )
    result = resp.json()
    return result.get("success", False)
```

---

### 8. Stripe (USD + BRL, sem trial)

#### 8.1 Criar sessão de checkout
```python
# apps/api/src/billing/stripe_client.py
import stripe

async def create_checkout_session(
    org_id: str,
    plan: str,
    currency: str,  # "usd" ou "brl"
    success_url: str,
    cancel_url: str,
) -> str:
    price_id = PRICE_IDS[plan][currency]  # mapeado de env vars
    session = stripe.checkout.Session.create(
        mode="subscription",
        line_items=[{"price": price_id, "quantity": 1}],
        success_url=success_url,
        cancel_url=cancel_url,
        metadata={"org_id": org_id},
        # Sem trial: trial_period_days=0 (ou não incluir)
    )
    return session.url
```

#### 8.2 Verificar webhook Stripe
```python
# apps/api/src/billing/webhook.py
import stripe
from fastapi import Request, HTTPException

async def handle_stripe_webhook(request: Request):
    payload = await request.body()
    sig = request.headers.get("stripe-signature")
    try:
        event = stripe.Webhook.construct_event(
            payload, sig, settings.STRIPE_WEBHOOK_SECRET
        )
    except stripe.error.SignatureVerificationError:
        raise HTTPException(status_code=400, detail="Invalid signature")
    # Processar evento...
```

---

### 9. Cripto-Agility

#### 9.1 Princípio de design
Todos os algoritmos criptográficos devem ser **configuráveis** e **substituíveis** sem refatoração:

```python
# apps/api/src/security/crypto.py
from typing import Protocol

class HashProvider(Protocol):
    def hash(self, data: bytes) -> str: ...

class SignatureProvider(Protocol):
    def sign(self, data: bytes, key: bytes) -> bytes: ...
    def verify(self, data: bytes, sig: bytes, key: bytes) -> bool: ...

# Implementação padrão (SHA-256 + HMAC)
class SHA256HashProvider:
    def hash(self, data: bytes) -> str:
        import hashlib
        return hashlib.sha256(data).hexdigest()

# No futuro: trocar por ML-KEM ou SLH-DSA sem mudar a interface
```

#### 9.2 Roadmap PQC
- **Fase 1 (atual):** Cripto-agility — interfaces abstratas implementadas.
- **Fase 2:** Monitorar NIST FIPS 203/204/205 nos providers (Cloudflare, AWS, GCP).
- **Fase 3:** Migração híbrida (clássico + PQC) em TLS quando disponível.
- **Fase 4:** Migração completa quando ecossistema maduro.

---

### 10. Critérios de Aceite

#### 10.1 MVP aceito quando:
- [ ] `pytest tests/ -v` passa (38/38 testes).
- [ ] `GET /health` retorna `200 OK` com versão do engine.
- [ ] `POST /runs` com código válido retorna resultado em < 10s.
- [ ] `POST /runs` com payload > 5 KB (anônimo) retorna `413 Payload Too Large`.
- [ ] `POST /runs` sem Turnstile token (anônimo) retorna `403 Forbidden`.
- [ ] Frontend exibe radar PNG e métricas corretamente.
- [ ] Logs não contêm código bruto (apenas hash).
- [ ] CI/CD verde (GitHub Actions).

#### 10.2 R2 aceito quando:
- [ ] Login OAuth (GitHub/Google) funciona end-to-end.
- [ ] Free logado: 11º run no mesmo dia retorna `429 Too Many Requests`.
- [ ] Free logado: código > 10 KB retorna `413`.
- [ ] JWT inválido retorna `401 Unauthorized`.
- [ ] Cross-tenant: usuário A não acessa run de usuário B.

#### 10.3 R3 aceito quando:
- [ ] Stripe Checkout cria assinatura corretamente (USD e BRL).
- [ ] Webhook `customer.subscription.deleted` rebaixa para Free e revoga share links.
- [ ] Share link de Pro funciona; Free tenta acessar e recebe paywall.
- [ ] Webhook com assinatura inválida retorna `400`.

---

### 11. Recomendações de Etapas (Milestones)

#### Milestone 1 — Scaffold e API mínima (1–2 semanas)
1. Criar `apps/api/` com FastAPI + Pydantic + pyproject.toml.
2. Implementar `GET /health` e `POST /runs` (stub + integração engine).
3. Criar `apps/web/` com Next.js, textarea, select, botão.
4. Conectar frontend ao backend (fetch + exibir resultado).
5. CI verde (pytest + smoke test da API).

#### Milestone 2 — Segurança básica e rate limiting (1 semana)
1. Validação de tamanho de payload no backend.
2. Cloudflare Turnstile obrigatório para anônimos.
3. Rate limiting por IP (Redis).
4. Logs sem código bruto (redact automático).
5. CORS configurado.

#### Milestone 3 — Autenticação e planos (2 semanas)
1. NextAuth.js no frontend (OAuth GitHub/Google).
2. JWT no backend com claims de plano.
3. Hard limits por plano verificados no backend.
4. Organizações e papéis básicos (Owner, Member).

#### Milestone 4 — Billing Stripe (1–2 semanas)
1. Stripe Checkout para Pro e Team.
2. Webhooks Stripe verificados.
3. Share link e API token para Pro+.
4. Painel de consumo e upgrade.

#### Milestone 5 — Hardening e compliance (1 semana)
1. Headers de segurança completos.
2. Criptografia em repouso (DB + storage).
3. Endpoint de deleção de conta (LGPD/GDPR).
4. Exportação de dados pessoais.
5. Documentação de bases legais.

#### Milestone 6 — Enterprise/Gov (3–4 semanas)
1. SSO/SAML.
2. Papel Auditor e exportação de trilha de auditoria.
3. "LLM Off" e BYOK por org.
4. SLA e suporte prioritário.

#### Milestone 7 — PQC e cripto-agility (roadmap)
1. Abstrações criptográficas implementadas (já devem estar desde M1).
2. Monitorar suporte PQC nos providers.
3. Migração híbrida quando disponível.

---

### 12. Referências Úteis no Repositório

| Arquivo | O que faz |
|---------|-----------|
| `core/operator.py` | Operador Π(A) = [f(A)]^(1/π) |
| `core/modes.py` | Cinco modos operativos (𝕆 ℙ 𝔻 𝕀 ℕ) + LLMScorer |
| `core/relations.py` | Seis relações de significância (ρ₁–ρ₆) |
| `ipii/transpiler.py` | `SemanticTranspiler.transpile(code, target_lang)` → `TranspilationResult` |
| `ipii/ast_parser.py` | `parse_and_enrich_ast(code)` |
| `gurumatrix/tensor.py` | `GuruMatrix`, `TargetLanguage`, `calculate_language_distance` |
| `utils/visualization.py` | `plot_significance_profile(scores, filepath=...)` → PNG/SVG |
| `examples/semantic_transpilation.py` | Demo end-to-end completo |
| `tests/` | 38 testes unitários que devem sempre passar |
| `docs/ARCHITECTURE.md` | Arquitetura alvo detalhada |
| `docs/THREAT_MODEL.md` | Modelo de ameaças e controles |
| `docs/REVENUE_DEFENSE.md` | Regras de negócio e metering |
| `docs/PRD.md` | Requisitos completos aprovados |

---

**Boa implementação. Priorize segurança e compliance desde o início — é muito mais fácil do que retrofit.**
