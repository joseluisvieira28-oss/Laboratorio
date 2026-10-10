# CRYPTO EDGE RADAR — AUDITORIA DE INTEGRIDADE, CIÊNCIA, ECONOMIA E AUTORIDADE
Data: 2026-10-10. Estado: PARTIAL_VERIFIED / NO_NEW_LIVE_AUTHORITY / NO_PROMOTION.

## Limites e prova
Auditoria de leitura: GitHub (branches, PRs, código, auditorias) e Supabase (consultas SQL SELECT). Nenhuma ordem, alteração de conta, credencial, merge para main, Render deploy, ajuste científico, alteração de estado do PC, lançamento de testes com exchange ou backfill. A observação Supabase é um *snapshot*, não uma prova de disponibilidade contínua nem de estado do executor Windows. O endpoint Render não foi interrogado: o workspace carece de seleção explícita. Nenhuma posição/ordem/TP-SL real da conta foi confirmada neste turno.

## Resultado executivo
**NÃO ESTÁ TUDO CERTO PARA AFIRMAR AUTO-LIVE RENTÁVEL OU MICRO-LIVE GO.** O ledger persiste observações de investigação, mas a continuidade tem lacunas substanciais; a fonte CED1D reporta 404; há divergência não resolvida entre branches/versões e a instalação Windows; a estratégia OPTIONS tem degradação económica documentada na rota MEXC; V0.4 continua DRAFT sem ACTIVE authority. Um PASS de CI/readiness não demonstra edge nem garante execução operacional.

## 1 — Ledger canónico, consulta read-only 2026-10-10 12:07:07 UTC
Projeto observado: `crypto-edge-radar-evidence-v05`, `public.radar_events`, `public.radar_event_keys`.
- 2.676 eventos; `max(id)=2676`; 2.598 event keys.
- Testes relacionais limitados: 0 orphans, 0 duplicações de `(event_type,event_key)` na tabela de keys, 0 `chain_sha256` repetidos. **Não** foi executada recomputação integral da hash chain.
- Último evento `2026-10-10T09:15:26.824892Z` (`RADAR_RUNTIME_LIVENESS`), ou 171,7 minutos sem nova evidência à hora da consulta. Não prova servidor parado; prova que esta instância do ledger não oferece prova de continuidade recente.
- Desde 2026-10-08: 121 liveness, 38 `ETF_EXEC_V2_PUBLIC_PREFLIGHT`, 17 `RADAR_RUNTIME_GAP_DETECTED`, 10 EMA6H boundary, 3 OPTIONS signal-day, 3 OPTIONS shadow-entry, 3 OPTIONS shadow-resolution, 3 OPTIONS public observations, 1 `CED1D_RENDER_SHADOW_V03_FAILURE`.
- `RADAR_RUNTIME_GAP_DETECTED` id 2673 em 2026-10-10 09:05:49Z: `RECOVERED_GAP_REVIEW_REQUIRED`, 12.841,725 s (~3h34m); outros gaps recentes: 9.192,639 s e 2.955,831 s. Necessária revisão de janelas perdidas; não presumir captura contínua.
- A última liveness id 2676 declara `CONTINUOUS`, `evidence_backend=postgres`, `live_capital_enabled=false`, `orders_created=false`; essas flags referem-se **apenas ao produtor do receipt**, não ao executor independente no PC.

## 2 — Bloqueio de fonte CED1D
`CED1D_RENDER_SHADOW_V03_FAILURE` id 2675, 2026-10-10 09:09:54Z: `GateError:FETCH_FAIL:HTTPError:404` do ficheiro oficial Binance Vision `AVAXUSDT-bookDepth-2026-10-08.zip`. Não é `NO_EDGE`: tratar como SOURCE/ARCHIVE FAILURE até arquivo válido e trilho de evidência, sem substituir a fonte ou fabricar/backfill outcomes. Progresso científico mais recente comprovado na auditoria de 08/10: 13/60 resoluções e 1/8 semanas; `WAITING_SOURCE_ARCHIVE`.

## 3 — Economia MEXC OPTIONS V2.1: não confundir fees absolutas com bps
- Correção `totalFee=0` mas `takerFee>0` no [PR #158](https://github.com/joseluisvieira28-oss/Laboratorio/pull/158), não merged. Quatro execuções reais históricas: fees atribuídas 0,05378003 USDT; PnL armazenado +0,04204000 USDT; net corrigido **-0,01174003 USDT**, 1 positiva / 3 negativas. Amostra mínima e não proxy para o futuro.
- A auditoria económica [PR #156](https://github.com/joseluisvieira28-oss/Laboratorio/pull/156) estabelece referência pública taker 8 bps por lado, ~16 bps ida-volta antes de spread, slippage, funding.
- No ledger id 2660 (`OPTIONS_V21_PUBLIC_EXECUTION_OBSERVATION_V01` para signal_date 2026-10-09), proxy público de não-funding 16,012110 bps vs cenário científico BASE10: headroom -6,012110 bps. A captura pública ocorreu **5.032.477 ms** após o limite de entrada pretendido (83m52s); não é quote executável no T0. Id 2599 (signal_date 2026-10-08): proxy 16,012234 bps; o campo indica **27 321 ms = 27,321 segundos** de atraso de captura, também fora do instante T0. Estes são PROXIES, não fees cobradas à conta.
- Auditoria 08/10 do Diamond Board: 16/50 forward, mean BASE -49,74785 bps, STRESS -59,72510 bps, PF BASE 0,3282; gate **INCOMPLETO**. Não promover, não abrir mais capital e não reescrever o BASE10 antigo como se fosse executável na rota presente.
- Supabase tem 19 `OPTIONS_V21_FORWARD_RESOLUTION` até à consulta; isto não equivale à contagem oficial do Diamond Board sem reconciliação de identidade, maturação e política do gate.

## 4 — Outras famílias e firewall científica
- BNB-LAUNCHPOOL-DEMAND-001: Diamond causal 0/25; sem eventos prospectivos elegíveis depois do runtime causal, no snapshot 07/10. Histórico positivo mas frágil; operator-only sem crédito.
- ETF-CME-INSTFLOW-001: OOS 2025 NET10 +11,40 bps, NET20 +1,60 bps; Tier 2 frágil; leave-one-out FAIL, Q4 2026 protegido até 2027-01-01. Não abrir Q4 ou converter preflight público em elegibilidade live.
- HTF-DH03 12H: ao snapshot 08/10, 0 sinais, 0 saídas, WAITING_ARCHIVE_PUBLICATION. Sem juízo `NO_EDGE` e sem inventar sinal.
- CED1D: 13/60 no snapshot 08/10, agora archive failure (acima).
- LICP BTC 8/20 episódios independentes; SOL FWD-XALT-004 4 completos/1 dia, média forward negativa descritiva, ambos `FORWARD_INSUFFICIENT`. Não são slots adicionais automaticamente elegíveis.
- BTC Options VRP V2: fenómeno histórico não traduzido em trade; ACCESSIBILITY_UNRESOLVED/UNDERPOWERED_PRE; source-only.
- Fechos científicos (`NO_EDGE`, amostra insuficiente, `SOURCE_BLOCKED`) não podem ser ressuscitados por custos imaginários, redução de N, resultados OOS abertos ou promoção mecânica. Governança V2 e correção source-first PR #169 continuam separadas de execução.

Fonte: [science-only 08/10](https://github.com/joseluisvieira28-oss/Laboratorio/blob/audit/science-only-all-fronts-2026-10-08/audits/CRYPTO_LAB_SCIENCE_ONLY_ALL_FRONTS_ATTACK_2026-10-08.md).

## 5 — Autoridade, versionamento, Windows e risco
- [PR #160 — Triple Fishing V0.3](https://github.com/joseluisvieira28-oss/Laboratorio/pull/160): DRAFT, not merged, 3 lanes (BNB/OPTIONS/DH03) sob **1 único slot global**, 5x isolated, margem máxima 10 USDT/posição, notional 50, daily e 7d realized kill 5 USDT. `per_position_stop_loss=NONE` na política base: o daily kill impede novas entradas; **não protege uma posição aberta**. DH03 exige TP/SL próprio.
- [PR #165 — launcher observability](https://github.com/joseluisvieira28-oss/Laboratorio/pull/165), CI run `37771827047` job `release-invariants` **SUCCESS**; correções/diagnóstico de launcher não provam que o PC recebeu o pacote ou que já voltou a operar.
- [Auditoria PC de 08/10](https://github.com/joseluisvieira28-oss/Laboratorio/blob/audit/triple-v03-exit1-heartbeat-2026-10-08/audits/TRIPLE_V03_EXIT1_HEARTBEAT_AUDIT_2026-10-08.md): pacote operador V0.3 HOTFIX2 tem dois EXE com tamanho diferente da build validada; task exit 1, causa exata INDETERMINADA. Supervisor heartbeat antigo e `ARMED=false` relatado localmente; isto não demonstra ordem/posição real ausente. Não reiniciar cegamente.
- [Triple Fishing V0.4 draft](https://github.com/joseluisvieira28-oss/Laboratorio/blob/triple-fishing-multislot-v04-2026-10-02/crypto_edge_radar/execution/OPERATOR_FUTURES_GLOBAL_AUTHORITY_V04_DRAFT.json): **3 slots**, até 30 USDT notional agregado, 14 USDT margem inicial total, cap 10 USDT por lane e um trade por símbolo; Options 1x, BNB/DH03 5x. Explicitamente `DRAFT_PRELIVE`, `current_file_can_submit_order=false`, `armed_marker_allowed=false`, não substitui a autoridade V0.3. Não confundir V0.3 com V0.4.
- Readiness V0.3 valida overlay, clock, conta read-only, posições/ordens/TP-SL, slot, fees, sources e kill; mas `PASS_READY_TO_ARM` é **viabilidade técnica**, não uma aprovação económica/scientific promotion. Meta-layer PR #161 é shadow independente, sem alterar posições/entradas.
- Nunca desarmar/parar um executor que possa gerir saída de posição sem estado de conta confirmado. Nunca eliminar `GLOBAL_POSITION_SLOT` ou repetir blind order para recuperar um erro.

## 6 — Matriz de decisão
| Frente | Estado desta auditoria | Regra seguinte |
|---|---|---|
| Supabase ledger relacional | PARTIAL_PASS | Recomputar cadeia integral/ligação canónica só em read-only |
| Liveness/continuidade | **P0 — EVIDENCE_STALE + GAP_REVIEW_REQUIRED** | Investigar runtime/deploy/logs sem mudar serviço; identificar missed windows |
| CED1D fonte | **P1 — 404 ARCHIVE SOURCE FAILURE** | Retry oficial na regra congelada; não imputar outcome |
| OPTIONS MEXC economia | **P0 — ECONOMIC_ROUTE_NOT_VALIDATED** | Não ativar com premissa BASE10; usar histórico corrigido e custos reais |
| Triple V0.3 PC | **P0 — DEPLOYMENT/ACCOUNT_UNKNOWN** | Hashes, tasks, receipts, slot e posições/TP-SL read-only |
| V0.4 3 slots | DRAFT_NOT_LIVE | Não promover DRAFT a ACTIVE; novo closeout explícito e readiness fresca |
| BNB/DH03/ETF/CED1D scientific gate | INCOMPLETE/GATED | Prosseguir fonte/forward segundo as freezes, sem alterar parâmetros |
| Política de risco | P1 — realized kill ≠ protective stop | Explicitar exposição máxima e estado de proteções antes de qualquer live GO |

## 7 — Ordem de correção segura
1. Congelar **novas ativações/autorização LIVE**, sem interromper a gestão de posições eventualmente abertas. Não mexer em main.
2. Diagnosticar a lacuna de liveness do ledger e gaps sinalizados, verificar autoritativamente o deploy e o escritor único; não preencher dados artificialmente.
3. Verificar causa CED1D 404 e só aplicar retry source/transport conforme freeze preexistente.
4. Reconciliação read-only da execução Windows: versão/hashes, identidade da task, estado do launcher, overlay, DPAPI sem revelar credenciais, supervisores legados, slot, sinais marcados, entradas perdidas e receipts.
5. Após confirmação operacional segura, comparar conta MEXC read-only (posições/ordens/TP-SL/fees/funding) com recibos locais por IDs. Sem observação da conta, NÃO dizer que não houve trades.
6. Criar no cockpit níveis distintos: **SCIENCE**, **SOURCE HEALTH**, **ECONOMIC ROUTE**, **EXECUTION AUTHORITY**, **RUNTIME/ACCOUNT TRUTH**, **POSITION PROTECTION**. Nada de status agregado «PASS» que mascare um P0.
7. Adotar pré-trade gate de viabilidade para a rota/capital atual **sem** retunar a ciência, alterar freeze, abrir holdout selado ou tratar operator-fork como Tier3. Qualquer ativação real requer autoridade nova e explícita.

## 8 — Conclusão, confiança e bloqueios
Rigor técnico apreciável e persistência relacional intacta nos testes limitados. Porém, o Radar **não está atualmente provado como um sistema de pesca rentável e operacionalmente íntegro**. Há P0 de liveness e verdade do PC/conta, P1 de fonte, economia adversa nas OPTIONS, e V0.4 sem autoridade. `NO_EDGE` e `BLOCKED` continuam distintos.

Pendente: Render workspace explicitamente escolhido para leitura de serviços/deploys/logs; read-only PC e MEXC; recomputação total de hash-chain; revisão exata de missed windows; reavaliação de custo em cada trade futuro com recibos temporais válidos. Nenhum merge, order, capital action, deployment, live authorization ou mudança científica foi realizado por esta auditoria.
