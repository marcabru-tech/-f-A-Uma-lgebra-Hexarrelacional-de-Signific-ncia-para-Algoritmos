# Defesa de Receita — HexaRelational Significance Platform (HRSP)

> **Versão:** 1.0 | **Data:** Abril 2026  
> Documento de referência para regras de negócio, controles técnicos e metering.

---

## 1. Modelo de Receita

### 1.1 Planos e Limites

| Plano | Preço | Runs/dia | Input max | Timeout | Retenção | Share link | API token | LLM |
|-------|-------|----------|-----------|---------|----------|:----------:|:---------:|:---:|
| Free Anônimo | Grátis | 2/IP/device | 5 KB | 10s | Nenhuma | ❌ | ❌ | ❌ |
| Free Logado | Grátis | 10/usuário | 10 KB | 10s | 7 dias | ❌ | ❌ | ❌ |
| Pro | US$19/R$79 por usuário/mês | Ilimitado¹ | 50 KB | 30s | 90 dias | ✅ | ✅ | Opcional |
| Team | US$99/R$399 por mês (5 users) | Ilimitado¹ | 50 KB | 30s | 180 dias | ✅ | ✅ | Opcional |
| Enterprise/Gov | Contrato | Contratual | Contratual | Contratual | Contratual | ✅ | ✅ | BYOK/Off |

¹ *"Ilimitado" sujeito a fair use policy; suspensão por abuso grave.*

### 1.2 Revisão de Preços
- Revisão trimestral; mudança notificada com 30 dias de antecedência.
- Moedas: USD e BRL fixos (sem conversão em tempo real).
- Sem trial; pagamento antes de ativar plano pago.

---

## 2. Hard Limits (Técnicos, Invioláveis)

Implementados no backend (`apps/api`); **não** podem ser sobrescritos pelo frontend.

```python
HARD_LIMITS = {
    "anonymous": {
        "max_input_bytes": 5 * 1024,       # 5 KB
        "max_runs_per_day_per_ip": 2,
        "max_concurrent_jobs": 0,           # sem persistência
        "timeout_seconds": 10,
        "retention_days": 0,                # sem retenção
        "turnstile_required": True,
    },
    "free_logged": {
        "max_input_bytes": 10 * 1024,       # 10 KB
        "max_runs_per_day_per_user": 10,
        "max_concurrent_jobs": 1,
        "timeout_seconds": 10,
        "retention_days": 7,
        "turnstile_required": False,
    },
    "pro": {
        "max_input_bytes": 50 * 1024,       # 50 KB
        "max_runs_per_day_per_user": None,  # ilimitado (fair use)
        "max_concurrent_jobs": 5,
        "timeout_seconds": 30,
        "retention_days": 90,
    },
    "team": {
        "max_input_bytes": 50 * 1024,
        "max_runs_per_day_per_user": None,
        "max_concurrent_jobs": 10,
        "timeout_seconds": 30,
        "retention_days": 180,
    },
}
```

---

## 3. Metering (Contagem e Rastreamento)

### 3.1 O que é medido
- **Runs:** contador diário por usuário (Redis, TTL 24h) e contador total por org (DB).
- **Compute time:** tempo de execução do engine em segundos por run (registrado no DB).
- **Storage:** tamanho total de artefatos por org (calculado na expiração).
- **LLM tokens:** tokens de entrada e saída por run (quando LLM ativo).

### 3.2 Implementação do contador de runs

```python
# Pseudo-código — implementação real em apps/api/src/metering.py
async def check_and_increment_run_counter(
    user_id: str,
    plan: str,
    ip: str,
    redis: Redis,
    db: AsyncSession,
) -> None:
    """Verifica e incrementa o contador de runs. Lança LimitExceededError se atingido."""
    limit = get_run_limit(plan)
    if limit is None:
        return  # ilimitado

    key = f"runs:{user_id or ip}:{date.today().isoformat()}"
    count = await redis.incr(key)
    if count == 1:
        await redis.expire(key, 86400)  # TTL 24h

    if count > limit:
        await redis.decr(key)  # desfaz o incremento
        raise LimitExceededError(f"Daily run limit ({limit}) reached")
```

### 3.3 Expiração de artefatos

- Job diário verifica `runs.expires_at` e exclui artefatos do S3 + marca run como `expired`.
- Usuário pode solicitar deleção imediata (direito ao esquecimento — LGPD/GDPR).

---

## 4. Abuse Scoring

### 4.1 Sinais de abuso
| Sinal | Peso | Descrição |
|-------|------|-----------|
| Velocidade de cadastro por IP | Alto | Muitas contas em pouco tempo no mesmo IP |
| Mesmo IP com múltiplas contas ativas | Médio | Provável evasão de limite Free |
| Payload sempre no limite máximo | Médio | Comportamento de bot/scraper |
| Taxa de erro Turnstile alta | Alto | Bypass de Turnstile falhando |
| Runs todos idênticos (mesmo hash) | Médio | Replay/scraping |
| Padrão de horário anômalo | Baixo | Acesso 100% automatizado, sem variação |

### 4.2 Ações automáticas por score

```
Score 0–30:   Normal — sem ação
Score 31–60:  Warning — monitorar; CAPTCHA adicional possível
Score 61–80:  Throttle — reduzir limite para 1 run/dia; alertar admin
Score 81–100: Block — bloquear IP/conta temporariamente; notificar admin
```

### 4.3 Revisão manual
- Bloqueios automáticos revisados em até 48h por equipe de trust & safety.
- Usuários podem contestar via e-mail de suporte.

---

## 5. Regras de Paywall

### 5.1 Share Link
- **Somente Pro+.**
- Share link gerado com UUID único e vinculado ao `run_id` + `org_id`.
- Link expira em 30 dias ou ao rebaixar o plano.
- Ao rebaixar plano (Pro → Free), todos os share links são revogados.
- Link público exibe apenas métricas (f(A), Π(A), relações) e PNG — jamais o código bruto.

### 5.2 API Token
- **Somente Pro+.**
- Tokens gerados por organização (até 5 tokens ativos por org no Pro).
- Token revogado imediatamente ao cancelar plano.
- Tokens têm permissão de scope limitado (ex.: `runs:create`, `runs:read`).

### 5.3 Modo LLM
- **Somente Pro+ com consentimento explícito.**
- Consentimento registrado por org com timestamp.
- Enterprise/Gov: pode escolher "LLM Off" ou BYOK.
- Consentimento pode ser revogado a qualquer momento (desativa LLM imediatamente).

---

## 6. Integração Stripe

### 6.1 Fluxo de assinatura
```
1. Usuário escolhe plano na UI
2. Frontend redireciona para Stripe Checkout (session criada pelo backend)
3. Após pagamento, Stripe emite webhook `checkout.session.completed`
4. Backend verifica assinatura HMAC do webhook (STRIPE_WEBHOOK_SECRET)
5. Backend atualiza org.plan no DB
6. Usuário redirecionado para dashboard com plano ativo
```

### 6.2 Webhooks Stripe monitorados
| Evento | Ação |
|--------|------|
| `checkout.session.completed` | Ativar plano |
| `customer.subscription.updated` | Atualizar plano (upgrade/downgrade) |
| `customer.subscription.deleted` | Rebaixar para Free; revogar share links e tokens |
| `invoice.payment_failed` | Notificar usuário; suspender após N tentativas |

### 6.3 Segurança do webhook
- Sempre verificar `Stripe-Signature` header com `stripe.Webhook.construct_event`.
- Usar HTTPS endpoint; rejeitar HTTP.
- Idempotência: registrar `stripe_event_id` no DB para evitar processamento duplicado.

---

## 7. Compliance LGPD / GDPR

### 7.1 Bases legais de tratamento
| Dado | Base legal | Observação |
|------|-----------|-----------|
| E-mail e nome (conta) | Contrato | Necessário para prestação do serviço |
| IP e metadados de acesso | Interesse legítimo | Segurança e prevenção de abuso |
| Código-fonte enviado | Contrato | Processado para o serviço; não persiste em logs |
| Dados de pagamento | Contrato | Gerenciado pelo Stripe (controlador independente) |
| Hash do código | Interesse legítimo | Deduplicação e auditoria; não permite reconstrução |
| Consentimento para LLM externo | Consentimento explícito | Opt-in por org; revogável a qualquer tempo |

### 7.2 Direitos dos titulares
- **Acesso:** usuário pode exportar todos os seus dados via painel.
- **Retificação:** e-mail e nome editáveis no painel.
- **Exclusão:** deleção de conta exclui todos os runs e artefatos em até 30 dias.
- **Portabilidade:** exportação de runs em JSON.
- **Revogação de consentimento:** desativa LLM imediatamente.

### 7.3 Medidas técnicas
- Código bruto jamais persiste em logs (apenas SHA-256).
- Artefatos expiram automaticamente.
- Criptografia em repouso e em trânsito.
- Acesso ao DB restrito ao serviço `apps/api` (não exposto externamente).
- DPO designado para Enterprise/Gov (contratual).

---

## 8. Fair Use Policy

Para planos "ilimitados" (Pro/Team):
- Limite implícito de bom senso: uso para fins profissionais legítimos.
- Suspensão por abuso detectado (abuse score > 80).
- Runs de teste automatizados em CI: permitidos e incentivados.
- Scraping sistemático para fins comerciais não relacionados: proibido.

---

*Revisar regras de negócio trimestralmente junto com revisão de preços.*
