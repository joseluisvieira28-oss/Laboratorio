# CRYPTO LAB — OPERAÇÃO DIAMANTE ESTRUTURAL
**Mandato de investigação e triagem económica | 2026-10-20 UTC | RESEARCH ONLY | SEM LIVE GO**

## 0. Mudança de pergunta
Deixar de pesquisar indicadores que parecem prever velas. Investigar apenas mecanismos em que exista uma transferência económica identificável: um participante paga funding, spread, prémio de liquidação, concessão de liquidez ou outro custo por ter de transferir risco, margem ou inventário.

**CUIDADO:** um pagamento ou uma contraparte pressionada NAO garante lucro acessível para nós. Concorrência, informação incorporada no preço, prioridade na fila, gas, execução e financiamento podem absorver toda a transferência. A expressão "forçado a financiar" identifica um potencial pagador, não uma rentabilidade demonstrada.

Cada hipótese terá obrigatoriamente seis respostas ANTES de abrir outcomes:
1. **PAGADOR** — Quem paga, em que regra de mercado/protocolo, e por que razão?
2. **TRANSFERÊNCIA** — Que dinheiro, desconto ou fluxo é efetivamente recebido por uma posição executável, em que moeda e momento?
3. **CAPTURA** — Como participaria uma posição na venue alvo, com timestamps causais e informação verdadeiramente disponível?
4. **FRICÇÃO** — Fees, bid/ask, slippage, gas/MEV, funding, FX, lotes, colateral, risco de cauda, stops, latência e oportunidade alternativa de capital.
5. **FALSIFICADOR BARATO** — Qual teste público, gratuito, read-only e de resultados ainda fechados pode invalidar depressa a tese?
6. **EVIDÊNCIA INDEPENDENTE** — Que amostra prospectiva e congelada distinguirá o mecanismo de sorte, seleção retrospetiva e sobreajuste?

Sem qualquer destas respostas, classificar MECHANISM_NOT_YET_ACTIONABLE, nunca EDGE.

## 1. Cemitério: decisões já suportadas pelas fontes
### LICP-001 — continuação de liquidação cross-venue
**CLOSED / NO_EDGE para a configuração congelada.** O PR #107 ainda contém um sumário antigo de 17/20, mas o HEAD do branch já inclui o closeout definitivo de 2026-10-14. Run 38571288601: primeiros 20 episódios independentes BTC_CONFIRMED em 6 dias, 18/20 outcomes válidos, mean base -16.37455407 bps, median base -16.47340372 bps, mean stress -32.37455407 bps, 2/18 positivos. Base/stress roundtrip 16/32 bps. Não repetir o mesmo BUY=>LONG/SELL=>SHORT BTC 60s mudando o nome, horizonte, fees ou custos após ver o resultado.
Fonte: https://github.com/joseluisvieira28-oss/Laboratorio/blob/liquidation-cascade-propagation-v0.1/research/liquidation_cascade/LICP_001_FORWARD_ECONOMIC_CLOSEOUT_2026-10-14.md

### Funding Hunter V04 — BTC OKX linear versus inverse
**NO_TRADE_UNDER_PREDECLARED_RULES**, não "não existe funding edge no mundo". Junho 2025: 28 decisões predefinidas, todas FLAT; máximo diferencial lagged observado 0.15379028 bps/h versus limiar congelado de 0.5 bps/h. Faltaram cashflows/FX/exits e não houve execução. Proibido baixar 0.5 ou escolher nova janela vendo estes resultados. Não comprar mais livros históricos para salvar este exato piloto.
Fonte: https://github.com/joseluisvieira28-oss/Laboratorio/blob/research/funding-hunter-v04-june-2025-cashflow-gate-2026-10-19/audits/FUNDING_HUNTER_V04_REAL_OKX_BTC_2025_06_28DAY_ZERO_SIGNAL_FINAL_CLOSEOUT.md

### CONVEX SOL1h e BNB4h
**ZERO ROBUST HISTORICAL PROMOTIONS**, apesar de closed cashflows históricos positivos. Amostra já conhecida antes da triagem, SOL 2025 negativo, poucos vencedores concentram ganhos, BNB só 28 closes. Sem OOS independente ou execução certificada; observadores Telegram estritamente read-only e sem crédito de lucro.
Fonte: https://github.com/joseluisvieira28-oss/Laboratorio/blob/research/convex-v07-economic-risk-calibration-2026-10-19/audits/CONVEX_V07_ECONOMIC_RISK_CALIBRATION_FROZEN_VERDICT_2026_10_19.md

### Aave Base keeper — desconto de liquidação pago pelo devedor
**SOURCE_BLOCKED** na implementação de dados gratuita testada. Dois endpoints RPC separados falharam no primeiro eth_getLogs, zero observações e zero lucro demonstrado. Não relançar o mesmo scanner/fonte ou criar keeper bot. Outra fonte independente e gratuita exigiria protocolo novo antes de abrir outcomes.
Fonte: https://github.com/joseluisvieira28-oss/Laboratorio/blob/research/base-keeper-source-remediation-v02-2026-10-13/research/base_keeper/BASE_KEEPER_001_FINAL_FAST_VERDICT_2026-10-13.md

### L2 estático, vacuum e quote gap
O audit de 14 outubro refere microprice e liquidez-vacuum ainda negativos num limite otimista de perfect maker fills, e dislocação cross-venue observada inferior aos custos. Não rebatizar a mesma amostra/família de indicadores como "novo diamante".
Fonte: https://github.com/joseluisvieira28-oss/Laboratorio/blob/liquidation-cascade-propagation-v0.1/audits/EVENT_DRIVEN_EDGE_TRIAGE_NO_DUPLICATES_2026-10-14.md

## 2. Fila disciplinada — não criar 10 novos projetos

### PRIORIDADE 1 — RW-HL-EXITFLOW-001 existente: fonte/fluxo Hyperliquid
Mecanismo proposto: participantes com urgência de descarregar risco/inventário podem negociar contra liquidez; divergência de OI e funding pode ser sintoma de pressão persistente.
**Pagador exato do lucro direcional: AINDA NÃO IDENTIFICADO/PROVADO.** O funding negativo em perp normalmente significa que shorts pagam longs. Não confundir sinal de vendedor com short que recebe funding. Se não conseguirmos demonstrar transferência líquida acessível, não promover.
O protocolo G3 existente prevê observações horárias SOURCE ONLY de 2026-10-10 a 2026-10-23 (336 slots), >=320 únicos, >=14 dias e >=100 mercados; avaliação da qualidade só após 2026-10-24 00 UTC. **Não abrir retornos nem selecionar horizontes agora.** Antes do primeiro outcome G4, congelar hipótese económica exata, mercado, direção, relógio de decisão, entrada/saída, custo/funding real, controlos, métrica e regra de morte. Se G3 falhar, STOP: só remediar fonte sem tocar ciência; nunca fabricar horas/backfill.
Fonte: https://github.com/joseluisvieira28-oss/Laboratorio/pull/172

### PRIORIDADE 2 — prémio de transferência de inventário/funding de PERPS
Mecanismo legítimo em princípio: uma parte paga funding ou basis para manter exposição. O lucro só pertence ao arbitrador se conseguir posição hedged em instrumentos contratualmente compatíveis, recolher os cashflows na moeda correta e fechar as pernas com spread/lotes/margem/FX/financiamento certificados. Não pressupor delta-neutral sem medir basis, inverse contract, mark e collateral.
**Não é continuação do piloto OKX BTC V04.** Uma variante verdadeiramente independente exige novo universo/timeframe/venue JUSTIFICADO ANTES de observar rates; pré-registo de ordem fixa de teste e source gate. Sem dados completos de contratos, settlements contemporâneos e quotes de saída, SOURCE_BLOCKED. Sem margem/capital mínimo, ECONOMICALLY_INFEASIBLE. Não alterar posterior thresholds de custo.

### PRIORIDADE 3 — desconto direto de liquidação de protocolo
É mecanicamente a fonte mais clara de pagador (penalização do devedor remunerando liquidadores), mas a rota Base V0.2 está bloqueada e MEV/gas e concorrência podem absorver tudo. Só reabrir se uma fonte autenticável gratuita, diferente da rota falhada, provar censos completos e permitir estimativa de bonus efetivamente acessível; sem wallets, transações, private RPC ou capital. Estado atual: PARKED, não pipeline ativo.

### OBSERVAÇÃO DISTINTA — LCOD-001
Curva de sensibilidade de devedores Aave é prova mecânica de solvência, **não** prova de prémio capturável, evento futuro, direção nem lucro. Preservar o protocolo prospectivo já congelado; não extrair "trade signal" da curva sem novo pre-outcome freeze. Fonte: https://github.com/joseluisvieira28-oss/Laboratorio/pull/91

## 3. Funil que um "diamante" terá de passar
**G0 — ECONOMIC_PAYER_IDENTIFIED:** prova da regra contratual/protocolo e beneficiário; sem pagador ou concessionário concretos, STOP.

**G1 — FREE_SOURCE_AVAILABLE:** endpoints públicos/arquivos com licença e schema verificados; timestamp de disponibilidade, sequência/cobertura, idade, hashes, custos e ausência de olhar para outcome. Faltas => SOURCE_BLOCKED, não NO_EDGE.

**G2 — COST_CEILING:** demonstrar teto bruto da transferência com dados fonte independentes e comparar com custo executável realista + versão stress. Se o teto otimista não cobre custos, fechar família exata ANTES de programar bot. Nenhum fee=0 salvo contrato/prova real. Incluir concorrência, queue position, gas e funding na moeda efetiva.

**G3 — PRE_OUTCOME_FREEZE:** especificar tamanho e seleção da amostra, deduplicação, direção, clock, mercado, entry/exit bid/ask, no-lookahead, benchmark nulo, teste estatístico e riscos sem abrir resultados do mesmo experimento.

**G4 — PROSPECTIVE_INDEPENDENT_NET:** outcomes recolhidos só depois da freeze, sem tuning nem resgate de subgrupos. Net após fees, funding, slippage e custos de todas as pernas. Critérios relevantes incluem média/mediana, distribuição de cauda, regimes e incerteza amostral, não apenas trades vencedores.

**G5 — REAL_EXECUTION_SAFETY (futuro e separado):** só depois de G4 promissor; quotes de tamanho exequível, limites de capital, colateral, stops com ACK, recuperação de crash e reconciliação. Nenhum G4 aprova dinheiro real automaticamente.

Estados de saída distintos: REJECTED_MECHANISM, SOURCE_BLOCKED, FORWARD_INSUFFICIENT, BLOCKED_DATA_QUALITY, NO_EDGE, ECONOMICALLY_INFEASIBLE, PROVISIONAL_CANDIDATE. GREEN CI ou TRUE SIGNAL nunca equivalem a economic GO.

## 4. Próximas datas e instruções operacionais (sem promises)
- **2026-10-20 a 23:** apenas confirmar integridade/fonte do G3 Hyperliquid existente e mapear pagador, contratos, fees e capacidade com fontes oficiais; sem outcomes de G3 nem tuning.
- **A partir de 2026-10-24 00 UTC:** ler somente o veredito de qualidade do G3; se PASS, antes de ver qualquer outcome criar G4 de resultados pre-congelados. Se FAIL, fonte corrigível ou STOP, sem inferir lucro.
- **Após G4 válido:** aguardar amostra independente suficiente, sem janela artificial de "30 dias = dinheiro". Se nada sobreviver, registar honestamente ZERO EDGE.
- **Em paralelo só source-only:** inventariar protocolo de prémio funding/inventário novo se existir um pagador verificável e fonte gratuita materialmente distinta do V04. Nenhuma seleção pela rentabilidade já conhecida.
- **Custo/segurança:** zero gastos, zero wallets, zero login, zero contas, zero ordens, zero exchange mutation, zero live trading, zero Render, zero deploy, zero merge main. Holdout científico 2026 pré-existente continua selado; só forward permitido por freezes já válidas.
- Não clonar/duplicar automações ou collectors já operacionais. Zero "novas canas" sem encerramento/triagem de existentes.

## 5. Entregável e critério de sucesso desta missão
Este documento é uma **decisão de prioridade e governance**, não backtest novo, nem G4, nem prova de edge. Mantém um cemitério exato e um único próximo marco económico verificável. Um verdadeiro "diamante" terá: pagador identificado + fonte credível + surplus líquido exequível + resultado prospectivo independente robusto + segurança operacional. Qualquer elo não demonstrado mantém NO LIVE GO.

**Veredito em 2026-10-20: ZERO ESTRATÉGIAS DE LUCRO LÍQUIDO INDEPENDENTE COMPROVADO. PRIORIDADE IMEDIATA: G3 HYPERLIQUID E ECONOMIA DO PAGADOR, NÃO MAIS INDICADORES.**
