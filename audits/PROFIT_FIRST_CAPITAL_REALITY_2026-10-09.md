# OPERAÇÃO LUCRO REAL — PRIORIDADE DE CAPITAL, NÃO MAIS BACKTESTS

Data/hora observada: **2026-10-09 03:35–03:40 UTC**, Frankfurt Render canonical `crypto-edge-radar-v05-canary`, serviço `srv-dalqkpu1egvs73fhiehg`, deployed commit `b9d8e28ff0ec0fe8a67cc9e1970e8c1050c2fa36`. Base Supabase `jqzdvgjeuveiktftyrlz` consultada **read-only**.

**Operador quer lucro líquido efetivo e perdas pequenas, não chegar artificialmente a +40% em apenas uma minoria das vitórias.**

## Decisão imediatamente aplicável

1. **ZERO capital novo** para estratégias sem aprovação económica + execução causal. Isto não é paralisar pesquisa: é evitar trocas de dinheiro real por esperança.
2. **CED1D-0031** é a única entre as três linhas verificadas hoje com médias BASE/STRESS de execução provisoriamente positivas e dados prospetivos acumulados. Mantê-la a recolher shadow **SEM PROMOVER**; falta 46/60 eventos, 7/8 semanas e o gate de concentração. **Não** tratar como rendimento disponível.
3. **OPTIONS-SPOTPERP-001-V2.1**: 18/50, BASE descritivo **−20.120348 bps**, STRESS **−30.100124 bps**, PF BASE **0.69433**, embora integridade do subconjunto reportada PASS. Resultado **não autoriza** trading; a freeze proíbe veredito económico antecipado.
4. **TFG-DONCHIAN-REGIME-ADAPTATION-V1**: 12 trades resolvidos com −12R na telemetria, **mas dados de execução causal contaminados** (entrada simulada anterior ao receipt e posições overlapping conforme `audits/TFG_DONCHIAN_REGIME_V1_FORWARD_CAUSALITY_CLOSEOUT_2026-10-08.md` no branch forense). **EXECUTION_INTEGRITY_FAIL**, não provar `NO_EDGE` limpo e não reiniciar a mesma hipótese com retune.
5. **BTC-CONVEX/Quant Trailing**: mesma família, evidência seed +40% pouco frequente e custos completos indisponíveis (PR draft #166 `research/margin_payoff_audit/README_PT.md`). Não alavancar a seed para inventar rendimento.

## Risco escondido em CED1D

Read-only `public.radar_events` com `event_type=CED1D_RENDER_SHADOW_V03_EVENT`, `payload_json::jsonb->'event'->>'reference_base_lower_bps'` ordenado por `signal_day` entrega os **14** valores já resolvidos entre 2026-09-22 e 2026-10-05. São resultados de referência **após custos BASE definidos no congelamento** (não resultados de uma conta pessoal):

```
2026-09-22 -904.7633571872224
2026-09-23  -82.3396703157782
2026-09-24 +456.81172207780963
2026-09-25 +144.0883777923428
2026-09-26  +26.26408973827207
2026-09-27 -286.8087725178937
2026-09-28 +758.975056162407
2026-09-29 -451.53028963568715
2026-09-30  +31.043501257432492
2026-10-01 -190.49253515803107
2026-10-02 +292.65011375278254
2026-10-03  -42.316762493255524
2026-10-04   +7.443912359309294
2026-10-05 +422.9148713721414
```

**Verificação:** 8 positivas, 6 negativas; soma **+181.9402572 bps**, média **+12.99573266 bps** (+0.12996% notional), maior ganho **+758.9751 bps**, maior perda **−904.7634 bps**. Se se excluírem **só as duas maiores vitórias** (diagnóstico de concentração, não regra de trading nem alteração da amostra original), média dos restantes 12 = **−86.15387675 bps**. PF BASE ~**1.0929** (telemetria). O motor reporta 12/50 pares de execução, média BASE +21.13880051 bps e STRESS +19.13880051 bps, PF BASE ~1.1549. **Execução é proxy pública com notional de pesquisa, não ganho realizável garantido.**

Para notional de 100 USDT por trade (exemplo apenas), +12.9957 bps são +0.12996 USDT médios e a pior perda observada corresponde a ~9.05 USDT de perda; a melhor operação a ~7.59 USDT. Multiplicar por alavancagem amplifica ambos os lados, não gera edge. O histórico **não sustenta** a promessa de perder sempre só 10% da margem quando se tenta ganhar 40% nela.

**Nota de causalidade:** os receipts de CED1D são reconstruídos após o fecho do dia via arquivos verificáveis, segundo mecanismo já congelado. Não são ordens e não são execução ao vivo. O presente documento é *diagnóstico de risco sem veredito científico antecipado*: preservar a autoridade Tier1 (60 eventos/8 semanas) e não selecionar/excluir dias adversos.

## Bloqueio exato de source, não bug comprovado

Em 2026-10-09T03:39:45Z, Render reporta `ced1d_render_shadow.status=WAITING_SOURCE_ARCHIVE` para `latest_mature_signal_day=2026-10-06`, `latest_required_path_day=2026-10-08`, com HTTP **404** da fonte congelada:
`https://data.binance.vision/data/futures/um/daily/klines/AVAXUSDT/1m/AVAXUSDT-1m-2026-10-08.zip`.
Métricas anteriores até `2026-10-05` foram conservadas. A lógica `latest_mature_signal_day(today)=today-3days` e `latest_required_path_day=signal_day+2` está no código do watcher. Não contornar 404 com velas incompletas, não inserir dados artificiais e não converter ausência de arquivo em trade. O watcher pode retentar sem mutação de trading quando o arquivo fonte existir. Arquivo futuro ainda indisponível é um impedimento externo **SOURCE_WAIT**, não motivo para alterar ciência.

## Plano de ganho real, em vez de maquilhar capital

A. **Aproveitar** observações independentes que de fato já estão a passar integridade, custos, concentração e capacidade de ordens. Exigir **probabilidades, perdas cauda, liquidação/margem, net PnL absoluto e capital necessário** para cada candidato, não só retorno %.
B. **Suspender novas otimizações em seeds conhecidas.** Investigar mecanismo económico novo apenas se tiver uma cadeia causal mensurável distinta e fontes públicas de baixo custo; fazer freeze antes dos resultados posteriores e jamais chamar backfill de forward.
C. Se o objetivo é **renda agora**, nenhuma das três estratégias foi demonstrada como fonte de rendimento previsível. O laboratório não pode legitimamente substituir receita de trabalho/serviço enquanto estes gates não estiverem preenchidos.

## Reprodução read-only

```sql
SELECT e.payload_json::jsonb->'event'->>'signal_day' AS signal_day,
       e.payload_json::jsonb->'event'->>'status' AS status,
       e.payload_json::jsonb->'event'->>'reference_base_lower_bps' AS base_reference_lower_bps
FROM public.radar_events AS e
WHERE e.event_type = 'CED1D_RENDER_SHADOW_V03_EVENT'
ORDER BY e.event_ts;
```

Para os números, correr `python -m unittest audits.test_profit_first_capital_reality_2026_10_09 -v`; os testes verificam somente aritmética determinística e não tocam na base de dados.

**Autoridade:** research-only, fail-closed. No deploy, orders, account reads, paid services, mutation, merge, margin/leverage selection from outcomes or automatic promotion. Não é recomendação de investimento nem promessa de lucro.
