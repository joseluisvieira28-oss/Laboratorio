# LIQMAP-DIAMANTE-002 — Protocolo prospectivo congelado em 26/11/2026

OBJETIVO: testar se o preço BTC visita primeiro o lado da maior concentração de posições em risco de liquidação visível naquele momento. NUNCA atribuir esta regra ao Neuron, à CoinGlass ou ao Augusto Backes. ZERO TRADING / PAGAMENTOS.

## Fonte e cobertura
Fonte única: https://raw.githubusercontent.com/rdemb/hyperquant-data/main/liq-map/BTC.json, mapa agregado de posições de BTC-PERP observadas no Hyperliquid via clearinghouseState. Dados externos limitados e incompletos: cobertura de OI ~48.8% na fotografia inicial e posições parcialmente antigas; não é o universo de posições abertas. Dados auxiliares status.json e liquidação-tape só diagnósticos. Capturar hora UTC início/fim de GET, asOf interno, SHA256 dos bytes, coverage.share, idade ponderada notional, markPx e nível agregado. Não publicar carteiras.

Aceitar somente asOf no passado com idade <=20min e futuro permitido <=60seg, coverage.share >=0.30, idade notional P50 <=15min, >=30 bandas válidas e preço positivo. Fonte inválida => SOURCE_BLOCKED; não repetir recolha depois de conhecer outcome. Data do marcador deve igualar data UTC real entre 27/11/2026 e 26/01/2027, uma captura única por dia, não mais tarde do que 15 UTC. Agendar via automação separada, porque cron GitHub Actions em branch Draft não corre. Todos os 61 dias contam, inclusive falhas.

## Sinal congelado, nenhum tuning
Bandas longs abaixo e shorts acima de markPx, com px>0 e ntlUsd>0; valores inválidos/side inconsistent excluídos. Agrupar em classes largura 0.005 de log-preço. Selecionar SOMENTE níveis com distância absoluta de log-preço [0.005,0.05] ao markPx. Score de banda = soma ntlUsd monitorizado * exp(-distância/0.03). Vencedor maior score, desempate preço mais baixo. Sem bandas => NO_SIGNAL.
Escolha UP se alvo acima do mark, DOWN se abaixo. Barreira oposta é markPx**2/target: MESMA distância logarítmica no sentido contrário. Nenhuma previsão fora do preço e do mapa presente.

Baseline MOM24: diferença entre último close de vela BTC-PERP 1h já fechada antes da decisão e close 24h antes; API pública Hyperliquid POST /info candleSnapshot, sem autenticação; baseline indisponível => CONTROL_BLOCKED. 50/50 de direção é nulo mais fraco, não um indicador rival suficiente.

## Liquidação futura
Hora decisória é o fim da captura e gravação do sinal, nunca asOf do mapa. Outcome: 24 candles completos e consecutivos de BTC-PERP 1h, começando na primeira fronteira de hora APÓS a decisão. Carregar apenas DEPOIS de o último candle encerrar. Primeira barreira tocada (em high/low) => TARGET_FIRST / MIRROR_FIRST, ambas na mesma vela AMBIGUOUS, nenhuma NEITHER; registar TODOS e NO_SIGNAL. Os candles futuros nunca podem entrar na seleção de alvo. Comparação MOM24 usa exatamente as mesmas duas barreiras e preços.

Stress futuro apenas hipotético: LONG/SHORT BTC-PERP no open da primeira vela, saída na barreira ou último close, PnL com custos 10/35/80bps por lado +5bps slippage por lado, ambiguidades pessimistas, sem funding, margin, market impact, liquidação do trader, taxas de conta ou fills reais. Nunca chamar a isto lucro executado.

## Veredito pré-congelado
Primeiro checkpoint 8 observações válidas. Checkpoint científico 30 tentativas de calendar days. Final após 61 capturas/até 60 outcomes maturados; não afirmar 30-60 dias antes de passarem. Requer >=50 observações com uma única barreira tocada, Wilson95 inferior >50%, superioridade pareada >+5pp vs momentum 24h, mean pseudo-PnL líquido após 80bps/side >0, bootstrap semanal 2000 amostras seed 2002 lower95 de excesso vs MOM24 >0, vantagem em >=2 blocos mensais. Se insuficiente => INCONCLUSIVE; se suficiente e falhar => NO-GO ECONÓMICO; se cumprir => candidato a investigação apenas. Sempre NO-GO para trading REAL sem execução, robustez em outras fontes e custos reais verificados.

Dados agregados da fonte pública com SHA256 e snapshots de resultados imutáveis na branch research, PR Draft. Nunca alterar main, fazer merges, contas reais, chaves privadas, subscrições, gastos, ordens, trades ou alavancagem.
