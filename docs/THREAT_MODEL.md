# Modelo de Ameaças — HexaRelational Significance Platform (HRSP)

> **Versão:** 1.0 | **Data:** Abril 2026  
> **Referência:** STRIDE, OWASP Top 10, NIST CSF 2.0

---

## 1. Escopo e Ativos

### 1.1 Componentes no Escopo
- `apps/web` — Frontend Next.js (Vercel)
- `apps/api` — Backend FastAPI (containerizado)
- Core IPII Engine (Python, neste repositório)
- Cloudflare (edge: WAF, rate limit, Turnstile, DDoS)
- Banco de dados (PostgreSQL) — metadados, runs, usuários, orgs
- Object Storage (S3-compatível) — PNG/SVG/JSON/tensor
- Fila de jobs (Redis/Queue)
- Stripe webhook endpoint
- GitHub Actions (CI/CD)

### 1.2 Ativos Críticos
| Ativo | Criticidade | Motivo |
|-------|-------------|--------|
| Código-fonte dos usuários | Alta | PII/propriedade intelectual; não deve vazar |
| Chaves de API (Stripe, LLM, DB) | Crítica | Comprometimento gera impacto financeiro/operacional |
| Dados de runs e artefatos | Alta | Confidencialidade por plano e LGPD/GDPR |
| Registros de auditoria | Alta | Obrigatório para B2G; integridade não pode ser comprometida |
| Credenciais de usuários/OAuth tokens | Crítica | Comprometimento permite acesso à conta |

---

## 2. Superfície de Ataque

```
Internet ──► Cloudflare Edge ──► apps/web (Vercel)
                                        │
                                        │ HTTPS/REST
                                        ▼
                               apps/api (container)
                                   │         │
                              Core Engine   DB/Storage
                                             │
                                        Stripe webhook
```

Pontos de entrada:
- POST /runs (payload de usuário — maior risco)
- GET /runs/{id} (acesso a artefatos)
- Webhooks Stripe (autenticidade deve ser verificada)
- OAuth callback (CSRF, state forgery)
- Interface web (XSS, CSRF)

---

## 3. Ameaças por Categoria (STRIDE)

### 3.1 Abuso de Freemium (Bots, Multi-contas, Scraping)

| Ameaça | Vetor | Impacto | Controle |
|--------|-------|---------|---------|
| Bot farms criando contas para burlar limites Free | Automação de cadastro OAuth | Custos de compute, degradação de serviço | Cloudflare Turnstile (runs anônimos); verificação de e-mail; detecção de padrões de abuso |
| Multi-contas (um usuário cria N contas) | Cadastro manual ou automatizado | Bypass do limite de 10 runs/dia | Abuse scoring (velocidade de cadastro, similaridade de IPs, fingerprinting de dispositivo) |
| Scraping via API Free | Automação de GET/POST sem Turnstile | Extração de dados públicos | Rate limit por IP (Cloudflare); autenticação obrigatória para dados persistidos |
| Replay de runs caros | Re-send de requests idênticos | Amplificação de custo | Idempotency key + deduplicação por hash do payload |

**Controles principais:**
- Cloudflare Turnstile obrigatório para runs anônimos.
- Rate limit em múltiplas camadas: edge (CF), API (middleware).
- Abuse scoring: detectar anomalias de frequência, IPs compartilhados, fingerprinting.
- Limite de 1 job simultâneo por usuário Free logado.

---

### 3.2 Bypass de Paywalls

| Ameaça | Vetor | Impacto | Controle |
|--------|-------|---------|---------|
| Chamada direta à API sem passar pelo frontend | Manipulação de headers/JWT | Uso de features pagas sem pagar | Validação de plano no backend (nunca confiar no frontend); JWT com claims de plano |
| Manipulação de token/plano no JWT | JWT forjado ou alterado | Acesso a features Pro/Enterprise | Assinatura do JWT com chave privada do servidor; verificação em cada request |
| Compartilhamento de share link por conta Pro | Link enviado para usuários Free | Bypass do paywall de share | Share links expiráveis; vinculados à conta do criador; revogar ao rebaixar plano |
| Exploração de condição de corrida nos contadores | Envio paralelo de runs | Burst acima do limite | Contador atômico (Redis/DB com lock); verificação antes e depois do run |

---

### 3.3 DoS / Custos de Compute

| Ameaça | Vetor | Impacto | Controle |
|--------|-------|---------|---------|
| Payload de código muito grande | POST /runs com megabytes de código | Memória/CPU exaustão no engine | Limite de tamanho: 5 KB (anônimo), 10 KB (Free logado), 50 KB (Pro); rejeição imediata |
| Código com AST exponencial | Input especialmente construído (deep recursion) | Timeout/crash do engine | Timeout por execução (10s Free, 30s Pro); subprocess isolado com RLIMIT |
| Flood de runs | Muitos requests simultâneos | Custo de infraestrutura | Rate limit por IP e por conta; fila com limite de workers |
| Abuso de LLM (modo Inferir) | Envio massivo de requests para OpenAI | Custo de API LLM | LLM apenas em planos pagos; limite de tokens por run; timeout de chamada LLM |

---

### 3.4 Vazamento de Dados (Código do Usuário, Logs)

| Ameaça | Vetor | Impacto | Controle |
|--------|-------|---------|---------|
| Código bruto em logs de aplicação | Logging inadvertido de corpo do request | Violação de LGPD/GDPR; exposição de IP do cliente | Redact automático: apenas hash do código em logs; jamais logar o campo `code` |
| Acesso cross-tenant a artefatos | IDOR em GET /runs/{id} | Vazamento de código/relatórios de outro usuário | Verificação de ownership: run.org_id == requester.org_id |
| Artefatos em storage público por engano | Misconfiguration de bucket S3 | Exposição pública de dados privados | Bucket privado por padrão; URLs pré-assinadas com expiração curta |
| Exposição de variáveis de ambiente | `.env` no repositório ou container | Comprometimento de chaves | Segredos apenas em variáveis de ambiente do runtime; `.env` no `.gitignore`; secrets scanning |
| Logs de LLM contendo código do usuário | Prompt enviado ao LLM inclui código | Dados do usuário em sistemas de terceiros | Consentimento explícito por org antes de ativar LLM; opção "LLM Off" para Gov |

---

### 3.5 Supply Chain e Dependências

| Ameaça | Vetor | Impacto | Controle |
|--------|-------|---------|---------|
| Dependência maliciosa no PyPI/npm | Typosquatting ou compromisso de maintainer | Execução de código arbitrário na infraestrutura | Lock files (pip lock / package-lock.json); revisão de dependências novas; Dependabot |
| Imagem base de container vulnerável | CVEs em Python ou sistema base | RCE ou privesc | Imagem base minimal (python:3.12-slim); Trivy scan em CI |
| Actions de terceiros comprometidas | Uso de `uses: terceiro/action@main` | Exfiltração de secrets de CI | Fixar Actions por SHA; mínimo de Actions de terceiros |
| Atualização de dependência com breaking change | NumPy/FastAPI atualização major | Quebra do engine ou da API | Lock files + testes de regressão + renovate/dependabot com aprovação |

---

### 3.6 Riscos de LLM (Roadmap)

| Ameaça | Vetor | Impacto | Controle |
|--------|-------|---------|---------|
| Prompt injection via código do usuário | Código com strings que manipulam o prompt | Resposta inesperada ou vazamento de system prompt | Sanitização do código antes de incluir no prompt; separação clara de contextos |
| Data exfiltration via LLM | Código de um usuário visto pelo LLM e "memorizado" | Vazamento indireto | Consentimento explícito; opção de LLM interno (BYOK/privado) para Enterprise |
| Custo descontrolado de tokens | Usuário envia payloads grandes para o LLM | Bill choque | Limite de tokens por run; circuit breaker por custo |
| Dependência de disponibilidade do LLM | OpenAI API down | Degradação do modo Inferir | Fallback automático para scorer heurístico (já implementado) |

---

### 3.7 Requisitos Cloudflare/Turnstile e Rate Limiting

**Configuração obrigatória:**

```
Cloudflare Zone:
  - WAF rules: OWASP Core Ruleset (nível medium ou higher)
  - Rate limiting:
      - /runs: 10 req/min por IP (Free); 60 req/min por IP (Pro)
      - /auth/*: 20 req/min por IP
      - /*: 1000 req/min por IP (DDoS threshold)
  - Turnstile:
      - Widget obrigatório no formulário de POST /runs (modo anônimo)
      - Verificação do token no backend (apps/api valida com CF API)
  - Bot Fight Mode: ON
  - DDoS protection: ON (L3/L4 e L7)
  - Cache: evitar cachear respostas de runs (dados dinâmicos)
```

---

## 4. Controles por Camada

### 4.1 Edge (Cloudflare)
- WAF com OWASP ruleset.
- Rate limiting por IP, rota e método.
- Turnstile para formulários públicos.
- DDoS mitigation automática.
- Bot Fight Mode.
- TLS 1.3 enforced.

### 4.2 Aplicação (apps/api)
- Validação de tamanho de payload na entrada (antes de processar).
- Autenticação JWT com verificação de assinatura e expiração.
- Autorização por plano e org em cada endpoint.
- Verificação de ownership de runs (anti-IDOR).
- Timeout de execução com subprocess isolado.
- Redact de código bruto em logs.
- Validação de webhook Stripe (assinatura HMAC).
- CORS restrito ao domínio do frontend.
- Headers de segurança: CSP, HSTS, X-Frame-Options, X-Content-Type-Options.

### 4.3 Infraestrutura
- Segredos em variáveis de ambiente do runtime (nunca em código ou imagem).
- Bucket S3 privado; URLs pré-assinadas para artefatos.
- DB com conexão autenticada via credencial rotacionável.
- Container minimal (sem shell desnecessário em produção).
- Rede interna (apps/api não exposta diretamente à internet; tráfego via Cloudflare).
- Trivy/Grype scan de imagem em CI.

### 4.4 Dados
- Código bruto nunca persiste em logs — apenas SHA-256 do conteúdo.
- Artefatos expiram automaticamente conforme plano.
- Deleção sob demanda (direito ao esquecimento — LGPD/GDPR).
- Criptografia em repouso (DB e storage).
- Criptografia em trânsito (TLS 1.3).
- Cripto-agility: algoritmos abstrados via interface, substituíveis sem refatoração.

---

## 5. Cripto-Agility e Criptografia Pós-Quântica (PQC)

### 5.1 Situação Atual
- TLS 1.3 com ECDHE (X25519) para troca de chaves.
- AES-256-GCM para criptografia em repouso.
- HMAC-SHA256 para assinaturas de webhook.
- JWT com RS256 ou ES256.

### 5.2 Roadmap PQC
- **Fase 1 (Cripto-agility):** abstrair todos os algoritmos criptográficos atrás de interfaces — nenhum algoritmo hard-coded; configurável por variável de ambiente/configuração.
- **Fase 2:** Monitorar adoção de NIST FIPS 203 (ML-KEM), FIPS 204 (ML-DSA), FIPS 205 (SLH-DSA) pelos provedores de plataforma (Cloudflare, AWS, GCP).
- **Fase 3:** Migração híbrida (clássico + PQC) quando suporte de TLS PQC estiver disponível em produção (ex.: X25519Kyber768 no TLS 1.3).
- **Fase 4:** Migração completa para PQC quando ecossistema maduro.
- **Requisito de design atual:** toda decisão criptográfica deve ser documentada e revisável. Nenhuma chave ou algoritmo deve estar hard-coded no código-fonte.

---

## 6. Matriz de Risco Residual

| Ameaça | Prob. | Impacto | Risco inerente | Controles | Risco residual |
|--------|-------|---------|----------------|-----------|----------------|
| Abuso de freemium por bots | Alta | Médio | Alto | Turnstile + rate limit + abuse scoring | Médio |
| Bypass de paywall via API | Média | Alto | Alto | JWT verificado no backend + claims de plano | Baixo |
| DoS por payload grande | Alta | Alto | Crítico | Limite de tamanho + timeout | Médio |
| Vazamento de código em logs | Média | Alto | Alto | Redact automático | Baixo |
| Supply chain (dependência maliciosa) | Baixa | Crítico | Alto | Lock files + Dependabot + revisão | Médio |
| IDOR em runs/{id} | Média | Alto | Alto | Verificação de ownership | Baixo |
| Prompt injection (LLM) | Média | Médio | Médio | Sanitização + consentimento | Baixo |
| Vazamento de segredos no repo | Baixa | Crítico | Alto | .gitignore + secrets scanning | Baixo |

---

*Revisar este documento a cada release major ou mudança significativa de arquitetura.*
