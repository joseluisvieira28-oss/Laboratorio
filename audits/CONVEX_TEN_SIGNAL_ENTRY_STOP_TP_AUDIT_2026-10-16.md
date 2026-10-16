# CRYPTO LAB — auditoria dos sinais CONVEX, entrada/SL/TP e risco
**Data:** 2026-10-16 UTC. **Regime:** research-only, sem alteração às estratégias, não executa ordens, não modifica `main` nem os três monitores Windows.

## Base verificada
- 10/10 lanes read-only nas versões instaladas V07 V2 (`99d06384...`), V11 V2 (`8143e21d...`), V12 PR239 (`0aa45a02...`), segundo receipts do operador de 15 outubro 20:52 UTC. Isso prova fontes e runtime, não lucros.
- Imagem Telegram fornecida pelo operador mostra SOL_CONVEX_NATIVE_5M (V07) e BNB_CONVEX_NATIVE_5M_EXPERIMENTAL (V12) LONG potencial, fechados 2026-10-15T20:55:00Z; outras mensagens recebidas em 16 outubro não foram ainda fornecidas para avaliação individual.
- Sinais LONG são registos de observação de um indicador extremo de tendência/pullback, não ordens, nem fills. A ligação causal de candles específicos aos dois IDs está pendente da auditoria forense [PR #241](https://github.com/joseluisvieira28-oss/Laboratorio/pull/241).

## Regra original cientificamente congelada — NÃO transplantar para novos observadores automaticamente
- Fonte: `engine/three_convex_v05/signals.py`, `shadow.py`, README; parent V5 pinned Git blob 19c8b8e2363f253458db42111b6701f3a3ef1f4b.
- Indicador: SMA200 regime, RSI14 Wilder <30, z-score <-2, fechamento abaixo da BB inferior 2std, volume>SMA20 com >=3/4 componentes; apenas vela completa.
- Entrada histórica simulada: abertura do primeiro candle 5m **depois** do fecho da vela de sinal, timestamp `signal_close_ms + 300000`. Se esse instante falha, não perseguir preço em vela posterior. Preço usado no shadow é Binance 5m OPEN, não ASK executável MEXC.
- SL inicial histórico: `entry * (1 - 0.04)` em LONG (não arredondado); risco realizado pode exceder stop por gap/slippage/liquidação.
- **TP fixo: inexistente no original.** O parent mantém posição sob stop; quando fecho do seu timeframe tem ganho >=5%, stop condicional = `max(initial_stop, peak_5m_high * (1 - 0.12))`; em contrário reverte para initial stop. Esta regra NONLATCHED pode afrouxar a proteção. Alterar para trailing monotónico ou acrescentar TP 1:2 é novo modelo, não validado pelo backtest original.
- Shadow demonstrou por testes a regra, não demonstrou ordens broker native SL/TP. Os monitores V07/V11/V12 **não calculam nem aplicam** stops a posições na MEXC.
- Simulação de exposição V05: 1 contrato mínimo usuário reportado = SOL 0.1 SOL ou BNB 0.01 BNB em 14 Outubro, posição isolada 10×, orçamento modelado 0.50 USDT por trade e <=1.50 USDT agregado, custos ilustrativos 8bps taker/side +2bps slip/side+5bps funding reserva. **Não usar quotes datados de 14 Outubro para ordens em 16 Outubro**; specs/fees/ticks/equity reais não foram revalidados.

## Matriz individual — o que o histórico específico realmente sustenta
Base comum source-validated Binance 2023–2025, 20% equity notional, 1×, base 8bps taker +2bps slippage por lado, funding proxy. É retrospectiva, não OOS independente, nem fill MEXC da atual topologia, nem rentabilidade futura.

| Lane | Monitor | Histórico net marcado 2023–25 (base) | SL/TP operativo no watcher | Veredito |
|---|---|---:|---|---|
| SOL 5m | V07 | Não consta no 8ALT 15m–4h | Não | Apenas sinal, estudar fonte própria 5m separada |
| SOL 1h | V07 | +59.39% | Não | Hipótese histórica mais forte; OOS não provado |
| BNB 4h | V07 | +27.38% | Não | Hipótese com PF e DD modelados mais defensáveis, amostra pequena |
| SOL 4h | V11 | +35.90% | Não | Dependência dos 3 maiores vencedores |
| BNB 30m | V11 | +19.67% | Não | Residual após top-3 fraco |
| ETH 1h | V11 | +18.77% | Não | Dependência da cauda direita |
| BNB 5m | V12 | Não consta no 8ALT 15m–4h | Não | **Alerta observado, sem prova económica comparável neste quadro** |
| SOL 30m | V12 | +24.67% | Não | Histórica retrospetiva, forward não provado |
| BNB 15m | V12 | +11.04% | Não | Histórica retrospetiva, forward não provado |
| DOGE 4h | V12 | +15.66% | Não | Top-3 removal negativo, frágil |

Fonte histórica específica: `audits/CONVEX_8ALT_4TF_COMMON_2023_25_FINAL_CLOSEOUT_2026_10_13.md` no branch `research/convex-sol1h-bnb4h-economic-source-gates-2026-10-13`. **Não misturar estes retornos 1× com o capital alavancado 10× nem chamar estes resultados testes de stop manual MEXC.**

## Implicações práticas dos novos Telegram alerts
1. O Signal ID dá só lane e timestamp do fecho. Falta o preço executável MEXC na entrada programada, fill, quantidade, tick-size, margem, posição já existente e verificação do stop exchange-hosted.
2. Para os dois alertas visíveis das 20:55 UTC, primeiro candle de abertura no modelo às 21:00 UTC; este é um timestamp de pesquisa, não autorização de entrada. Qualquer trade feito mais tarde é uma estratégia distinta.
3. O modelo original não tem preço TP fixo, logo não existe um 'número de TP correto' a colocar manualmente com base apenas no Telegram.
4. Se sinais de SOL em V07/V11/V12 forem simultâneos/sobrepostos, não assumir que são operações long independentes; uma posição física MEXC pode ficar agregada e os stops não vinculados a estratégias individuais.
5. V12 não conserva Telegram API message_id na SQLite; V07 e V11 V2 podem conservar, mas receipt individual requer dados locais. Não inventar evidência de ACK.
6. Nenhuma das 10 famílias provou forward robusto costed na venue MEXC, nem stops reais atómicos ou execução/risco completos; o veredito atual é **NO-GO para converter os sinais Telegram diretamente em operações alavancadas**.

## Próximo passo mínimo sem contas/ordens
Recolher dos três SQLite locais **só** os Signal IDs e UTC closes com o novo `tools/convex_signal_forensics/recent_signals.py` (`mode=ro`, sem rede, sem preços privados). Depois validar os candles causais, o preço de abertura 5m e comparar o exit original contra saídas explicitamente pré-congeladas **em dados futuros intocados**, sem escolher SL/TP olhando o movimento já ocorrido. Não pedir bases SQLite, tokens ou credenciais ao operador.

**NO MERGE / NO LIVE GO / NO POST-OUTCOME TUNING.**