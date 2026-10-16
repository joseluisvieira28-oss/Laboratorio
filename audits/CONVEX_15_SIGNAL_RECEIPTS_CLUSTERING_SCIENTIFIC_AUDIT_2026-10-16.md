# CONVEX — auditoria dos 15 alertas realmente registados, 15–16 outubro 2026

**Fonte:** saída sanitizada do operador de CONVEX_10_LANES_RECENT_SIGNAL_RECEIPTS_V01. Ficheiros SQLite privados não copiados para o repositório. Sem MEXC orders/positions/fees/fills, sem candles OHLC históricos desta janela e sem autorização de alterar estratégias. Esta auditoria documenta apenas metadados reduzidos, lógica do source pinned e hipóteses a testar.

## Resumo factual, do receipt local reportado

- 15 linhas de sinal encontradas: 8 V07 SOL_CONVEX_NATIVE_5M, 7 V12 BNB_CONVEX_NATIVE_5M_EXPERIMENTAL, zero V11. "V11 zero" pode ser normal numa janela limitada de consulta e NÃO demonstra defeito.
- 15/15 possuem marca local outbox_marked_sent=true. V07 8/8 apresentam telegram_message_id numérico (ACK armazenado); V12 0/7, pois V12 PR239 não persiste o message_id (mesmo com sent_ms=true). Não existe prova de 15 leituras humanas, nem de delivery exatamente uma vez; a imagem anterior corrobora especificamente dois alertas recebidos.
- Deltas locais entre signal_close_utc e sent_at_utc: SOL [11,42,69,45,9,38,12,61] segundos; BNB [27,35,28,35,42,110,35] segundos. **Atenção:** sent_at_ms é o timestamp fornecido pelo processo ANTES de concluir drain/send; isto não prova hora exata do ACK/Telegram client.
- Nenhuma duplicação por (lane,close_ms) presente neste extrato. potential_same_symbol_same_close_overlaps=[] não garante que não há exposição física sobreposta em fechos diferentes.
- Em 20:55 UTC e em 23:05, 23:10, 23:15, 23:20 UTC, os dois ativos tiveram sinal no mesmo fecho; isso não prova independência de edge (SOL/BNB podem ser altamente correlacionados).

## Agrupamento estritamente descritivo por velas consecutivas no mesmo símbolo

SOL: 20:55–21:00 UTC (2 alertas); 23:05–23:25 (5); 01:30 (1). **3 sequências**.
BNB: 20:15 (1); 20:55 (1); 23:05–23:20 (4); 01:25 (1). **4 sequências**.
**7 sequências ≠ 7 trades**: trades precisam estado de posição/stop/fill, que não existe no recibo. Devido à política original de uma exposição por ativo, quantidade de trades economicamente elegíveis pode ser menor; não derivar contagem sem replay.

## Descoberta científica — condições matematicamente redundantes no parent V5

engine/three_convex_v05/vendor/V5_PARENT_PINNED_SOURCE.py.txt:
- z=(close-sma20)/stdev20; sz=z<-2.
- sb=close < sma20 - 2*stdev20.
- stdev20 > 0 é verificada pela função. Logo, em álgebra real, **sz e sb são o mesmo teste**, salvo diferenças de floating-point na fronteira.
- score=sr+sz+sb+sv, sob regime close>sma200, score>=3. Equivalentemente, longe da fronteira de arredondamento, dispara quando close>sma200 E z<-2 E (RSI14<30 OU volume>SMA20). A lógica **não exige três confirmações estatisticamente independentes**, pois dois dos quatro votos coincidem.
- build_signals avalia flags a cada candle concluído e guarda True enquanto a condição for satisfeita. NÃO exige transição False→True nem cooldown por estado; o watcher enfileira novo signal_id ao fechar cada candle consecutivo. Isto explica estruturalmente sequências de alertas sem demonstrar que os candles locais satisfizeram efetivamente o trigger (replay por fazer).
- O parent V5 historical shadow bloqueia repetidas entradas quando já existe posição/pending no mesmo ativo; os watchers read-only não conhecem o inventário de posições manuais MEXC nem mostram signal_state ACTIVE/NEW. Portanto **15 alertas não se traduzem em 15 oportunidades de entrada**.

## Entrada, SL, TP: limites reais

- Frozen historical V5 shadow: primeira entrada proxy no OPEN do candle 5m seguinte ao fecho do sinal (close+5min). Qualquer entrada mais tardia constitui um cenário diferente e não deve ser chamada execução equivalente do backtest.
- SL inicial histórico para LONG: 4% inferior ao preço hipotético de entrada. Na prática é só um mecanismo paper; exchange native stop ACK, tick-size, slippage, liquidação e posição exata não foram provados.
- **TP fixo não existe na origem**; a saída é stop/trailing condicional 12% abaixo de peak após subida >=5% em fecho do próprio timeframe; stop NONLATCHED pode afrouxar e continua bloqueio de segurança live. Acrescentar TP/RR 2:1 ou trailing monotónico sem preregisto é alterar ciência depois de observados resultados.
- Os 5m SOL e BNB NÃO constam das 64 células da auditoria histórica comum 8ALT, que cobre apenas 15m,30m,1h,4h; não inferir PnL 5m de retornos SOL1H/BNB4H.
- Não é possível calcular preço específico SL/TP nem demonstrar lucro destes 15 registos, pois faltam OHLC de entrada, fills e regras de saída autorizadas para esses observadores. **NO-GO para converter diretamente Telegram LONG num trade real.**

## Ordem correta de provas

1. Running/read-only e receipt de outbox: **PASS restrito** pelos resultados enviados.
2. Identidade e causalidade OHLC de cada Signal ID: **PENDENTE**. Verificar o uso de candle fechado e a equivalência de score por replay de históricos coletados no PC, respeitando source boundaries.
3. Agrupar um episódio de TRUE consecutivos como regime e contar trades de forma stateful com regras já congeladas, sem atalhos de PnL post-outcome.
4. Precificar custos reais e stops exchange-hosted MEXC em simulação, sob freezes anteriores ao outcome; OOS/forward sem tuning.
5. Só depois considerar desenhos de telemetria "FIRST_TRIGGER"/"CONDITION_STILL_ACTIVE" como um fork de apresentação, preservando histórico e mensagens em produção até auditoria e autorização do operador.

**Nenhum comando novo para alterar o Windows ou as 10 canas. Repositório em branch isolada; nenhum merge main.**
