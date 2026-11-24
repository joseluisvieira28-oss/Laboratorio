# BACKES-DIAMANTE-006 — Preflight independente, 24/11/2026

## VEREDITO
**TECH/SOURCE PASS; ECONOMIC LIVE NO-GO; FORWARD 0 semanas.** Este documento não contém qualquer rentabilidade prospetiva. O ensaio foi executado numa terça-feira 24/11, a posteriori da abertura da segunda-feira 23/11. Nunca considerar este sinal como previsão do Monday open ou como entrada executada.

## Verificações e links
- PR em draft #393 https://github.com/joseluisvieira28-oss/Laboratorio/pull/393
- GitHub Actions read-only SUCCESS https://github.com/joseluisvieira28-oss/Laboratorio/actions/runs/45375274905
- Artefacto original (preflight, livros de ordens L2, recibos, SHA256): https://github.com/joseluisvieira28-oss/Laboratorio/actions/runs/45375274905/artifacts/14909454845
- SHA256 artefacto ZIP calculado e verificado localmente: 1eb91ae1907157392b2fbb1d10f823d0dc3fb2fc9e0d89643d59192bb65985cb
- 8/8 testes PASS incluindo: nenhuma antecipação de decisões; bloqueio de pedidos prospectivos tardios; reprodução a 12 casas decimais dos pesos de 005 em prefixos semanais históricos; recibos SHA256 e 004 dados originais; book crossed/empty/insufficient depth tratados explicitamente.
- Fonte de referência BACKES004 imutável: ZIP sha256 73a3e5349930d8b8d8dab46fa69fb8989a118c79cb7f6f7a59260b2f50641d7b; arquivo semanal SHA256 4e256e2f0d4359943f96e9b1eb87e7cfe8cd6d6ca07728db7d5aa2dd4800d828.
- Dois pares de fonte pública: Binance Spot USDT e Coinbase Exchange USD. Recebidos **6/6 melhores bid/ask** após congelar os sinais e **6/6 livros de ordens nível 2** (100 níveis Binance; até ~50 Coinbase). 6 recibos SHA256 de cada fase e hora de cada GET. Zero chaves, contas, ordens, saldo, contratos ou custos pagos.

## Sinais diagnósticos (passado; segunda 23/11/2026)
Usaram-se apenas as semanas completas até domingo 22/11/2026, a partir de fontes validadas. O ficheiro de decisão marcado LATE_PREFLIGHT_ONLY indica valid_for_future_economic_sample FALSE.

| Exchange | Sinal FROZEN002 | Sinal MOM8 | BTC acima SMA40 | Vol anual BTC (12 semanas) | ROT_TREND40_VOL20 | MOM8_TREND40_VOL20 |
|---|---|---|---|---:|---|---|
| Binance | BTC | BTC | NÃO | 38.1683% | 100% CASH | 100% CASH |
| Coinbase | BTC | BTC | NÃO | 38.1927% | 100% CASH | 100% CASH |

Nenhuma compra hipotética necessária para essas duas regras na foto de 24/11. Ações reais = 0. Não permite reconstruir preços ou lucros da abertura passada de 23/11.

## Book de ordens e custos por tamanho — fotografia pontual
Os livros L1 e L2 foram obtidos em instantes consecutivos diferentes; não assumir sincronização perfeita ou execução ao preço apresentado.

- Binance L2 BTCUSDT: spread de ~0.0017bps no instante; ask disponível no melhor nível >106.6k USDT. Coinbase BTC-USD: spread ~0.0017bps e ask topo ~10.8k USD.
- Binance L2 ETHUSDT: spread ~0.0593bps; topo ask ~3.59k USDT. Coinbase ETH-USD: spread ~0.0594bps; topo ask ~1.50k USD.
- Para uma compra **estritamente hipotética** de 1,000 USD/USDT em ETH, ambas as fotografias L2 tinham profundidade e impacto estimado apenas ~0.03bps face ao mid naquele instante. Para 10,000, o impacto foi ~0.386bps Binance ETHUSDT / ~0.627bps Coinbase ETH-USD. Isto NÃO reproduz fills reais e não incorpora comissões.
- Mercado ETH/BTC direto tem spreads L2 de ~3.553bps Binance e ~2.132bps Coinbase, maior do que o de BTC vs USD; simulação de 0.01 BTC nocional ETHBTC ~1.777bps vs mid Binance / ~1.587bps Coinbase. Notional deste par em BTC, não USD/USDT.
- Custos hipotéticos de 10/35/60/80/100 bps continuam valores de cenário; os publicados para primeiro escalão Coinbase/Kraken podem ser muito superiores aos spreads observados. Sem fee tier real, conversão de base currency, risco USDT, liquidez no momento efetivo, execução por duas pernas, impostos ou stress de gap, não declarar lucro líquido real.

## Decisão operacional
- **Não há uma semana genuinamente futura na amostra** (0/8 primeiro gate de cobertura; 0/26 diagnóstico longo).
- Primeira data elegível: segunda 30/11/2026, estritamente dentro de 00:00–06:00 UTC. Compara duas exchanges e só conta fontes com 7 candles diários fechados da semana anterior e bid/ask L1/L2 recebidos depois do sinal.
- Workflow da branch permite pedido datado para aquele dia. Não está automaticamente agendado: 5/5 slots de Automations ativos; não alterámos tarefas alheias. GitHub Actions cron não dispara na branch de investigação. Nenhum acompanhamento autónomo semanal foi criado.
- Futuras entradas por request na segunda-feira devem guardar outputs imutáveis no GitHub e não colocar ordens. Preços posteriores são apenas observações, não garantia de preenchimento nem lucro.
- LIVE ECONOMIC NO-GO mantém-se até vantagem prospetiva suficientemente robusta, risco <= gate 005 e custos de conta verificáveis.

## Proveniência intelectual
FROZEN002, MOM8, trend40 e VOL20 são hipóteses do **Crypto Lab**; não são regra privada ou histórico de rentabilidade do Augusto Backes. O pré-registo da BACKES006 antes da primeira data elegível está em research/backes-diamante-006/PROTOCOL.md, commit 5570e487779abedecb333b4618a4e140562a70fa. A análise L2 foi acrescentada DEPOIS de observar limitação de quantidade no melhor nível do book — é diagnóstico operativo, não parte de uma descoberta retrospectiva pré-registada.
