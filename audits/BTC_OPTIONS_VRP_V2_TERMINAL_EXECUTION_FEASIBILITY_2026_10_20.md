# CRYPTO LAB — BTC OPTIONS VRP V2 | AUDITORIA ADVERSARIAL FINAL DE EXECUÇÃO
**UTC 2026-10-20 • evidência existente / read-only • nenhuma abertura de outcomes novos • revisão independente do branch `btc-options-vrp-v2-forward-2026-10-07`**

## VEREDITO EXECUTIVO — CLARO E TERMINAL PARA OS DESENHOS ATUAIS

**`NO_DEPLOYABLE_EXECUTABLE_EDGE_PROVEN / EXECUTION_SOURCE_INSUFFICIENT / UNDERPOWERED_PRE / NO_LIVE_GO`.**

**DECISÃO DE RECURSOS:** **STOP** na construção de um robô, integração privada, compra de dados, opções reais ou novos clones. Os **dois métodos históricos de execução (7D e 30D)** têm source gate insuficiente; o **desenho inverso com poder estatístico corrigido** é inviável em horizonte de investigação realista; o **forward BTC_USDC 0,01** tem evidência técnica de quotes, mas **nenhum ledger semanal canónico encontrado neste branch em 20 Oct**, nenhum PnL independente, nenhuma prova de fill e nenhum teste de poder robusto já aprovado para esta escala. A meta antiga N=36/N_eff>=30 FOI REVOGADA pre-outcome para o problema anterior de normalização, e não pode ser recuperada como se bastasse.

Isto não implica `VRP_PHENOMENON_NO_EDGE`: o fenómeno histórico de prémio de risco sobrevive; não há prova que o operador consiga convertê-lo num sistema económico positivo. **STOP é uma decisão sobre viabilidade da execução e alocação de recursos AGORA, não falsificação universal da literatura ou ausência de retorno esperado em qualquer conta.**

## 1. Evidência científica original preservada
- Parent Discovery: 192 observações semanais 2021–24; sinal da diferença volatilidade implícita menos realizada positivo em ~74,5%, média +10,43 pontos de volatilidade; intervalos HAC/bootstrap da média VRP acima de 0. Isso **não é lucro de vender opções**.
- Fonte: `research/btc_options_vrp_v2/V2_RESEARCH_CLOSEOUT_2026-10-07.md` no branch original; [PR #163](https://github.com/joseluisvieira28-oss/Laboratorio/pull/163).
- Risco da contraparte: compradores pagam pelo seguro/convexidade; vendedores absorvem grandes perdas de crash/squeeze/volatilidade e hedge/liq. Nem premium bruto nem IV−RV provam PnL líquido depois de skips, spread, fees, funding, hedge, gaps e colateral.

## 2. PROVA DE FALHA DE VIABILIDADE DE ENTRADA HISTÓRICA
### A. Execução 30D / manter até vencimento
Freeze original: `research/btc_options_vrp_v2/USDC_30D_EXPIRY_SOURCE_GATE_FREEZE_V0.1.md`.
- Pre-frozen 52 Thursdays 2025, janela 08–12 UTC, 25–35 DTE, call e put BTC_USDC com mesmo strike, >=0,01 e trade direction SELL em ambas.
- Fonte e closeout: [run #37663564452](https://github.com/joseluisvieira28-oss/Laboratorio/actions/runs/37663564452), artifact 11502211371.
- Resultado: **0/52 entradas source-qualifying** contra mínimo **24**. `SOURCE_ENTRY_INSUFFICIENT`, **não** NO_EDGE.
- Teste menos exigente de existência de duas pernas negociadas, independentemente de agressor: **1/52**, conforme V2 closeout. Isto prova atividade insuficiente nesta proxy; não prova a impossibilidade de obter fills passivos.

### B. Execução semanal 7D / recompra de ambas as pernas
- Seis janelas públicas: **380 trades em 203 contratos**, 100% cobertura de campos; mas **nenhum par call+put qualificado com entry SELL e posterior BUY no mesmo instrumento**.
- Fonte: `research/btc_options_vrp_v2/USDC_7D_TRADEPRINT_SOURCE_CLOSEOUT_V0.1.md`, [run #37662838078](https://github.com/joseluisvieira28-oss/Laboratorio/actions/runs/37662838078), artifact 11500783018.
- `7D_TRADEPRINT_EXECUTION_SOURCE_INSUFFICIENT`. Não é PnL nem NO_EDGE.

### C. Execução inversa antiga e margin
- Deribit inverse mínimo antigo 0,1 BTC-equivalent each leg; cálculo ponto-no-tempo para ATM short call+put **~0,03655 BTC IM**, na altura cerca **USD 3 mil** antes da margem/perda da cobertura. NÃO foi verificada conta, elegibilidade, limite de perda ou capital utilizável.
- [SOURCE_HEALTH_RECEIPT_2026-10-07.json](../research/btc_options_vrp_v2/SOURCE_HEALTH_RECEIPT_2026-10-07.json) prova BBO fonte (74/74 instrumentos; 0 erro), mas para fonte, não preenchimento de ordens.

## 3. Prova de execução nova BTC_USDC de tamanho 0,01: apenas SOURCE HEALTH
- Deribit BTC_USDC linear listado e mínimo técnico **0,01**: o acesso à cotação pública está demonstrado em one-shot, não em execução real.
- [run #38036299950](https://github.com/joseluisvieira28-oss/Laboratorio/actions/runs/38036299950) documentado no source-ready report de 10 Oct: um par 0,01 com DTE ~20, margem standard inicial estimada **~298,65 USDC** antes de coberturas e custos de capital. Fricção instantânea roundtrip, bid/ask + fees **~1,9927 USDC**, modelo de uma fotografia, não execução.
- **Nova conta estritamente descritiva desta auditoria**: 1,9927/298,65 ≈ **0,667%** da margem inicial de referência, comparado com hurdle **~0,183%/7 dias** de 10% annual-compounded. Fricção pontual ~3,65× o hurdle semanal *se* ambos denominadores fossem aplicáveis à mesma experiência e no mesmo risco. NÃO converta isto em expected PnL nem NO_EDGE: um pagamento de prémio pode exceder custos; hedge, spread futuro, gamma, funding, capital e perdas de cauda permanecem sem prova.
- Pior, a fotografia de sábado não qualifica para um Thursday source-bank (regra 08:00–08:15 UTC).
- A fonte não prova bid/ask consistente em vencimento, bid fill com tamanho real, ask de fecho executável, hedge ao minuto pretendido, stop native, haircuts/liquidation buffers ou stress de gap.

## 4. Erro de desenho estatístico já provado e NÃO remediado
- Freeze `V2_FORWARD_POWER_ACCESSIBILITY_FREEZE.md`: primeira análise utilizava 1 BTC de colateral artificial e N_eff 30 / 36 cohorts; foi **formalmente revogada ANTES de resultados** no `ACCESSIBILITY_COST_RECEIPT_2026-10-07.md`.
- Correção para o modelo **inverso antigo 0,1 BTC**: SD semanal em função da margem ~6,2%; comparar um alvo de 10% annual com alternativa 20% annual exigia **~8.617 efetivas observações semanais**, perto de 165,7 anos a uma por semana sem falhas. Isto é planning, não um theorem de impossibilidade nem power estimate aplicável sem ajuste ao 0,01 BTC_USDC linear.
- `PREOUTCOME_GATE_V2.json` mantém n_eff_estimate **0**, status `UNDERPOWERED_PRE`, planned_n_eff **8617**, no forward PnL. O contrato 0,01 e o design 30D são economicamente e estatisticamente distintos; não se pode aplicar 8617 mecanicamente nem fingir que a meta N=36 é válida.
- Não existe **nova** freeze de economic estimand/risk-capital e power para o filho linear 0,01 com outcomes protegidos ainda selados. Sem isso, qualquer cálculo de PnL seria retrospetivo não autorizado.

## 5. Fonte operacional prospectiva: workflow NÃO autónomo / ledger canónico ausente no branch
- Código `labs/BTC_OPTIONS_VRP_001/usdc_forward_entry_bank_v01.py` somente admite Quinta 08:00–08:15 UTC, BTC_USDC 0,01 call+put e testemunha BTC_USDC-PERPETUAL, source BBO <=30 s, grava append-only e proíbe settlement/PnL.
- Workflow `.github/workflows/btc-options-vrp-v2-usdc-forward-entry-bank.yml` dispara **apenas** push do ficheiro `research/btc_options_vrp_v2/TRIGGER_WEEKLY_CAPTURE.txt` no próprio branch. Não é cron.
- Nesta auditoria (20 Oct) GET dos seguintes caminhos canónicos no HEAD do branch original devolveu **404 NOT_FOUND**:
  - `data/vrp_usdc_forward/entry_source_bank.jsonl`;
  - `receipts/vrp_usdc_forward/2026-10-15.json`;
  - `research/btc_options_vrp_v2/TRIGGER_WEEKLY_CAPTURE.txt`.
  Isto permite apenas afirmar que **NÃO FOI DEMONSTRADO ledger canónico neste branch**. Não extrapolar "não existem outros recibos" sem auditar todos os workflows/artifacts externos.
- Os **40** testes CI de integridade de fonte [38047244412](https://github.com/joseluisvieira28-oss/Laboratorio/actions/runs/38047244412) passaram, mas certificam código sintético e não fornecem uma observação semanal autêntica. O relatório `USDC_FORWARD_BANK_OPERATIONAL_READY_2026_10_10.md` diz explicitamente que source capture não é automático e snapshots de sábado não contam.

## 6. Qualidade da evidência / obstáculos que invalidam LIVE GO
**Invioláveis até qualquer promoção:**
1. Mecanismo histórico VRP positivo ≠ estratégia concreta positiva;
2. BID/ASK visto ≠ fill recebido, muito menos exit/worst-case fill;
3. Margin inicial pública ≠ margem final / capital livre / risco extremo;
4. One-shot 0,01 BTC_USDC ≠ amostra powered; tese de lucro líquido exige ex-ante estimand, blind power design e muitos resultados verdadeiramente independentes;
5. Venda de volatilidade tem risco de cauda não limitado ao prémio; hedge estático não limita perdas e stop/gap pode superar capital;
6. Amostras que falharam gates congelados não são resgatadas escolhendo ativo, vencimento, custos, agressor ou janela pós-outcome.

## 7. DECISÃO TERMINAL DE ALOCAÇÃO — 20 OUT 2026
**`NO_LIVE_GO / NO_DEPLOYABLE_EXECUTION_EDGE / CURRENT_TEST_DESIGNS_CLOSED_FOR_PROMOTION`.** Encerrar gasto de engenharia, automações extra e expectativas de rendimento na estratégia BTC Options VRP. Manter património histórico e pré-resultados congelados; não apagar, editar ou inverter vereditos do parent. Não iniciar ordens reais, short straddle, conta, autenticação, gasto, integração ou main.

É cientificamente ilegítimo escrever `NO_EDGE` para o mercado VRP inteiro. O nosso veredito é **não provar execução rentável sob as regras e dados atuais** — prova suficientemente concreta para **não alocar capital nem novos ciclos grandes de engenharia**. Reabertura só com **evidência nova não selecionada por outcomes**, provando para um novo desenho quantidade real BID/ASK/execução, saída, funding/hedge, capacidade/cauda e um plano estatístico exequível pre-outcome. Isso seria um projeto novo, não continuação de resultados vistos.

**NENHUM outcome novo consultado**, nenhum holdout 2026 aberto, main e ciência intactos, sem ordens, conta, exchange mutation, wallet, Render ou despesa.

### Evidência direta
- V2 canonical closeout: `research/btc_options_vrp_v2/V2_RESEARCH_CLOSEOUT_2026-10-07.md`.
- No forward capture: `research/btc_options_vrp_v2/USDC_FORWARD_BANK_OPERATIONAL_READY_2026_10_10.md`.
- Recorded costs/margin: `research/btc_options_vrp_v2/USDC_BANK_CANONICAL_INTEGRITY_TECH_PATCH_2026_10_10.md`.
- Power correction: `research/btc_options_vrp_v2/ACCESSIBILITY_COST_RECEIPT_2026-10-07.md`.
- Preoutcome JSON `research/btc_options_vrp_v2/PREOUTCOME_GATE_V2.json`.
- 30D source outcome-blind closeout: `research/btc_options_vrp_v2/USDC_30D_EXPIRY_SOURCE_CLOSEOUT_V0.1.md`.
- 7D source outcome-blind closeout: `research/btc_options_vrp_v2/USDC_7D_TRADEPRINT_SOURCE_CLOSEOUT_V0.1.md`.

**This report is source-evidence adjudication, not a new economic experiment or live profitability measurement.**
