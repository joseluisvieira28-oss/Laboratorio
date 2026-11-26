# LIQMAP-DIAMANTE-004 — EVENT STUDY DE CASCATAS REAIS
**Pré-registo 26/11/2026, ANTES de consultar resultados históricos. READ-ONLY.**

## Hipótese
Depois de uma hora com liquidações efetivamente executadas anormalmente intensas, BTC e ETH tendem a continuar ou reverter o movimento forçado nas quatro horas seguintes? Hipótese distinta dos mapas anteriores (LIQMAP-003 NO-GO). Não valida o algoritmo proprietário do Neuron.

## Fonte, período
- Fonte grátis, sem chave: Ironflow (ironflow.sh) datasets HF ironflow/hyperliquid-liquidations (tabela EVENTS = 1 por posição liquidada, NÃO fills por execução parcial) + ironflow/hyperliquid-candles-1h (velas da MESMA exchange Hyperliquid).
- Período rigidamente pré-fixado 2026-07-01 00:00 UTC até 2026-11-01 00:00 UTC EXCLUSIVO, 123 dias, BTC-PERP e ETH-PERP nativos (não HIP-3). Não misturar Binance, ETH spot ou preços de outra exchange.
- Dados mensais EVENTS e OHLCV 1h, hashes SHA256 dos bytes e OIDs LFS, URL e timestamps de obtenção; cobertura integral 4 meses, timestamps alinhados, nenhuma hora fictícia, sem forward-fill, sem vazios inventados. Eventual linha duplicada deve ser tratada por ID original; sem ID inequívoco, SOURCE_UNTRUSTED. Não guardar endereços pessoais nos outputs.
- Conteúdo publicado livre antes de 10/11/2026 conforme licença declarada CC BY 4.0 (citar Ironflow). Confirmar na fonte. Limitar transferências a ficheiros públicos gratuitos; se bloquear, SOURCE_BLOCKED, zero pagamentos.

## Sinal congelado
- Somar por hora UTC notional USD das liquidações reais LONG/SHORT e contagem, por ativo. A fonte deve permitir inferir inequívocamente o lado da posição liquidada; se não, SOURCE_BLOCKED, nunca adivinhar com retorno de preço posterior.
- Cascata se total da hora t >0, count>=3 e >= percentil 95% dos totais da janela das **336 horas anteriores t-336..t-1** (inclusive zeros), com quantil de ordem sorted(ref)[ceil(.95*len(ref))-1]. NÃO inclui própria hora t na determinação do threshold.
- Direção classificada só quando >=65% de notional da hora de liquidação corresponde a LONG (venda forçada DOWN) ou SHORT (compra forçada UP); caso contrário NEUTRAL contado sem entrada.
- Hipótese A CONTINUA: segue direção forçada. Hipótese B REVERTE: oposta. Ambas pré-registadas e avaliadas com correção para múltiplos testes; nunca escolher vencedora após ver os resultados.
- Uma decisão apenas no fim da hora t, exposição hipotética ao OPEN da hora t+1 e saída no CLOSE da hora t+4, **quatro velas fechadas após o sinal**. Sinais com horizonte sobreposto são ignorados até t+4 (registar contador). 1h/12h/24h apenas descritivos não económicos se existirem dados suficientes; nunca escolher janela vencedora ex post.
- Excluir períodos de warmup, missing OHLC e fontes com preços incoerentes. Não usar OHLC de t+1 para calcular o sinal.

## Controlos rigorosos
- MOM4: mesmo evento e exatas horas de entrada/saída, direção dada close_t vs close_(t-4), mesmas despesas e magnitude. Contrafactual a posteriori NÃO criado por escolher períodos ganhadores; placebo sem cascata da mesma hora UTC e mesmo dia-da-semana no histórico anterior 336h, exposição/vol24 da mesma metade da distribuição trailing, caso exista. Se placebo não comparável, CONTROL_BLOCKED sem inventar desempenho.
- Comparar direção e retorno ao longo de JUL, AGO, SET, OUT; mediana/notional, 4h retorno, fracção de trades simulados vencedores, pior evento, drawdown NAV sequencial (não inclui intra-hora), turnovers, concentração de eventos, sensibilidade a custos e CASH zero.
- Custos de 10,35,80 e 100 bps **por lado** +5bps de slippage **por lado**; custos redondos 30/80/170/210 bps; hipótese de perp unlevered, sem funding, margem, custo/impacto real de ordens, mark-price/liquidação do trader e impostos.
- Bootstrap 2000 réplicas em blocos por semana ISO seed 4004, intervalo bilateral 97.5% da média de retorno líquido após 80bps e da diferença vs MOM4 para corrigir dois candidatos; relatório sem combinar BTC+ETH como independentes.

## Gates económicos
- Fonte e amostra científica suficientes se >=100 sinais independentes totais e >=40 por moeda, com quatro meses de price data. Menos => INCONCLUSIVE (não descartar hipótese como falhada).
- CANDIDATE_SHADOW_ONLY se UMA mesma hipótese A ou B atingir em BTC e ETH: >=40 eventos cada, retorno médio líquido após 80bps/lado+5bps >0, CI97.5 inferior >0, excesso emparelhado vs MOM4 CI97.5 inferior >0, retorno líquido médio positivo em >=3/4 meses em ambas moedas e MDD sequencial superior a -30%. Caso contrário NO-GO económico se amostra suficiente, INCONCLUSIVE se não.
- Mesmo CANDIDATE_SHADOW_ONLY não é GO dinheiro real: precisa experiência prospetiva nova, execução e funding reais, capacidade e risco de cauda. O passado Jul-Out foi visto em outras investigações e NÃO é out-of-sample independente.
- Sem mudar thresholds/fees/ativo/janela após resultados, nem criar novos bots.

## Segurança
ZERO trades, dinheiro, ordens, leverage, chave de exchange, compra de dados, subscrições, pagamentos, produção, merges, contacto com contas/indivíduos ou alterações à LIQMAP-002 (que permanece ativa).
