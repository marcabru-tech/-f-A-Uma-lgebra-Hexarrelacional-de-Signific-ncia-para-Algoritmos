# PRD — HexaRelational Significance Platform (HRSP)

> **Status:** Aprovado para implementação  
> **Versão:** 1.0  
> **Data:** Abril 2026  
> **Repositório:** `marcabru-tech/algebra-hexarrelacional`

---

## 1. Visão e Objetivo

### 1.1 Nome do Produto
**HexaRelational Significance Platform (HRSP)**

### 1.2 Proposta de Valor
Plataforma SaaS/freemium global que expõe o pipeline IPII (Interação Paramétrica Iterativa por Interoperabilidade) e a Álgebra Hexarrelacional de Significância como serviço web — permitindo análise semiótica, transpilação semântica iterativa e geração de relatórios de qualidade de código via GuruMatrix 5D.

- **B2B:** apoio a modernização de código, migrações, auditorias de qualidade semântica e redução de risco em pipelines de desenvolvimento.
- **B2G:** apoio a programas de legado, conformidade, transparência e padronização de software em órgãos públicos.

### 1.3 Alcance Geográfico e Compliance
- **Global** com foco inicial em Brasil e mercados GDPR.
- Compliance obrigatório: **LGPD** (Lei nº 13.709/2018) + **GDPR** (Reg. UE 2016/679).
- Leis aplicáveis adicionais: Marco Civil da Internet (Brasil), ePrivacy Directive (UE).

---

## 2. Personas e Casos de Uso

| Persona | Perfil | Caso de uso principal |
|---------|--------|-----------------------|
| Dev/Arquiteto (B2B) | Engenheiro de software em empresa | Medir "distância semântica" ao migrar módulos Python → Rust/JS/Go |
| Líder de Engenharia/CTO (B2B) | Tomador de decisão técnico | Relatórios comparáveis por equipe/projeto, auditoria e rastreabilidade |
| Analista de TI/Gestor (B2G) | Órgão público, contrato TI | Evidências formais, trilha de auditoria, controle de dados, governança |
| Pesquisador/Educação | Academia ou hobbyista | Uso free para aprender, validar hipóteses, publicar resultados |

---

## 3. Planos e Preços

### 3.1 Free — Anônimo Limitado
- **Autenticação:** nenhuma (por IP/device).
- **Turnstile:** obrigatório (Cloudflare).
- **Limites:** 2 runs/dia por IP/device.
- **Input:** até 5 KB de código-fonte.
- **Retenção:** sem retenção de dados — download imediato recomendado.
- **Artefatos:** JSON + PNG disponíveis por sessão, sem persistência.
- **LLM:** desabilitado.
- **Share link:** não disponível.

### 3.2 Free — Logado
- **Autenticação:** conta registrada (OAuth ou e-mail).
- **Limites:** 10 runs/dia por usuário + teto por organização.
- **Input:** até 10 KB de código-fonte.
- **Jobs:** 1 job simultâneo por vez.
- **Timeout:** 10 segundos por execução.
- **Retenção:** 7 dias (metadados + JSON + PNG/SVG; código bruto não persiste).
- **LLM:** desabilitado.
- **Share link:** não disponível (recurso pago Pro+).

### 3.3 Pro — US$ 19 / R$ 79 por usuário/mês
- Runs ilimitados (dentro de fair use).
- Input até 50 KB.
- Timeout estendido: 30s.
- Retenção: 90 dias.
- Exportação JSON/PNG/SVG.
- Share link privado.
- API token para CI.
- LLM opcional (con consentimento por org).

### 3.4 Team — US$ 99 / R$ 399 por mês (até 5 usuários)
- Tudo do Pro.
- Até 5 usuários; usuários adicionais: US$ 15/R$ 60 por usuário/mês.
- RBAC básico (Owner, Admin, Member, Viewer).
- Retenção: 180 dias.
- Dashboard de equipe e comparação de runs.

### 3.5 Enterprise/Gov — Contrato (a partir de US$ 12.000/ano; R$ 60.000/ano referência)
- SSO/SAML.
- RBAC avançado + papel Auditor.
- Retenção customizada (até 7 anos para Gov).
- SLAs contratuais (ex.: 99.5%+ uptime).
- BYOK (Bring Your Own Key) para LLM.
- "LLM Off" ou LLM interno/privado para Gov.
- Possibilidade de deployment dedicado (VPC/on-prem).
- Relatórios formais para auditoria.
- Suporte prioritário.

### 3.6 Revisão de Preços
- Preços revisados trimestralmente.
- Moedas: USD e BRL (preços fixos em cada moeda; sem conversão em tempo real).
- Sem trial gratuito.

---

## 4. Pagamentos

- **Provedor:** Stripe.
- **Moedas suportadas:** USD e BRL.
- **Sem trial.**
- **Cobrança:** mensal (Pro/Team) ou anual (Enterprise/Gov, com desconto).
- Upgrade/downgrade a qualquer momento; cobrança proporcional.

---

## 5. Arquitetura Alvo (Resumo)

```
Cloudflare (WAF + Rate Limit + Turnstile)
       │
       ▼
apps/web  ← Next.js no Vercel (frontend)
       │
       │  REST / fetch
       ▼
apps/api  ← Python FastAPI (containerizado, fora do Vercel)
       │
       ├── Core IPII Engine (este repositório)
       ├── DB (PostgreSQL) — metadados, runs, orgs
       ├── Object Storage (S3-compatível) — PNG/JSON/tensors
       └── Fila de jobs (Redis/Queue) — execução assíncrona
```

Ver `docs/ARCHITECTURE.md` para detalhes completos.

---

## 6. Segurança e Compliance

### 6.1 LGPD / GDPR
- Base legal documentada para cada processamento.
- Consentimento explícito para uso de LLM externo.
- Direito ao esquecimento (deleção sob demanda).
- Data Protection Officer (DPO) designado para Enterprise/Gov.
- Registro de atividades de tratamento (ROPA).
- Privacy by Design: código bruto não persiste em logs; apenas hashes e metadados.

### 6.2 Cloudflare
- WAF (Web Application Firewall) obrigatório.
- Rate limiting por IP e por conta.
- Turnstile obrigatório para runs anônimos (Free sem login).
- Bot management.

### 6.3 Criptografia Pós-Quântica (Roadmap / Cripto-Agility)
- Requisito atual: **cripto-agility** — algoritmos criptográficos devem ser substituíveis sem refatoração estrutural.
- Roadmap: migração progressiva para algoritmos PQC (NIST FIPS 203/204/205 — ML-KEM, ML-DSA, SLH-DSA) à medida que suporte de plataformas madurecer.
- Referência: NIST Post-Quantum Cryptography Standardization (2024).

### 6.4 Política de Dados
- Código bruto não persiste em logs (apenas hashes + metadados).
- Compartilhamento público só mediante opção explícita do usuário.
- Artefatos expiram conforme limite do plano.
- Enterprise/Gov: controle de retenção customizável.

---

## 7. Requisitos Funcionais

| ID | Descrição |
|----|-----------|
| RF-01 | Login via OAuth (GitHub/Google) + e-mail |
| RF-02 | Organizações com papéis: Owner, Admin, Member, Viewer, Auditor |
| RF-10 | Enviar código-fonte + selecionar linguagem-alvo |
| RF-11 | Executar pipeline IPII, retornar f(A), Π(A), relações, distância |
| RF-12 | Gerar artefatos: radar PNG/SVG, tensor NPY, JSON |
| RF-13 | Dashboard com histórico e comparação de runs |
| RF-20 | Criar Projetos dentro de organizações |
| RF-21 | Cada run versionado com metadados completos |
| RF-22 | Reexecução de run anterior com mesmos parâmetros |
| RF-30 | API pública (planos pagos) para integração com CI |
| RF-40 | Alternar modo heurístico vs LLM por org |
| RF-50 | Painel de consumo e limites por plano |
| RF-51 | Bloqueio automático ao atingir cota (com opção de upgrade) |
| RF-52 | Gestão de API tokens por organização |

---

## 8. Requisitos Não Funcionais

| ID | Descrição |
|----|-----------|
| RNF-01 | Isolamento de tenant (org) e controles de acesso por papel |
| RNF-02 | Criptografia em trânsito (TLS 1.3) e em repouso |
| RNF-03 | Segredos somente no backend (nunca expostos ao frontend) |
| RNF-04 | No code execution: apenas parsing/análise/transpilação estática |
| RNF-05 | Retenção configurável com deleção sob demanda |
| RNF-10 | Disponibilidade: best-effort (Free); SLA contratual (Enterprise/Gov) |
| RNF-11 | P95 de tempo de resposta: ≤ 10s para runs Free logado |
| RNF-12 | Execuções assíncronas com fila para jobs longos |
| RNF-20 | Logs estruturados + métricas (latência, erros, consumo) |
| RNF-21 | Trilha de auditoria exportável (B2G) |
| RNF-22 | Versão do engine explícita por run (reprodutibilidade) |
| RNF-30 | CI obrigatório (tests + lint) em todo PR |
| RNF-31 | Dependências fixadas com lock file |
| RNF-32 | Documentação pública (quickstart + API docs) |

---

## 9. Critérios de Aceite do MVP

1. Demo pública roda com estabilidade (modo heurístico) e gera relatório + PNG.
2. Autenticação básica (OAuth) e separação por organização funcionando.
3. Limites Free corretamente aplicados (tamanho/timeout/rate limit).
4. Código bruto não persiste em logs.
5. Cloudflare Turnstile ativo para runs anônimos.
6. CI verde (tests + smoke test da API).
7. Documentação de uso público (README + política básica).

---

## 10. Roadmap de Releases

| Release | Foco | Prazo estimado |
|---------|------|----------------|
| R0 (atual) | Core IPII engine + testes unitários | ✅ Concluído |
| R1 | Scaffold monorepo + API FastAPI + UI Next.js mínima | Sprint 1–2 |
| R2 | Auth (OAuth) + Free logado + limits + Cloudflare Turnstile | Sprint 3–4 |
| R3 | Stripe billing + Pro plan + share link | Sprint 5–6 |
| R4 | Team plan + RBAC + dashboard | Sprint 7–8 |
| R5 | Enterprise/Gov + SSO/SAML + auditoria | Sprint 9–12 |
| R6 | PQC cripto-agility + hardening | Roadmap |

---

*Documento revisado e aprovado. Números e decisões são referência e sujeitos a ajuste trimestral.*
