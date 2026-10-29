# MEXC Event Futures: primeiro replay histórico — veredito (29/10/2026)

**Autoridade:** GitHub Actions [run #40851732517](https://github.com/joseluisvieira28-oss/Laboratorio/actions/runs/40851732517), job #123372612587, head `6f818b21449cd9b6b6459adb39a663ba4b1b9963`, artifact #12887113270.

**SOURCE PASS / HISTORICAL INDEX PROXY ONLY / NO NEW EDGE / NO LIVE GO.**

## Fonte e período
- API pública MEXC standard-futures **INDEX** Min5. BTCUSDT/ETHUSDT: 4320 + 4320 candles recuperados. Raw source SHA-256 nos oito blocos, abaixo.
- Janela de decisões: **2026-04-01** até **2026-04-14** UTC; fonte começa 2026-03-31 (warm-up). Este período já foi explorado pelo V0.4; não é OOS independente.
- 3 regras fixas anteriormente estudadas (UP_ALWAYS, ROC3_CONT, ROC3_REV) × 10/30/60 minutos × BTC/ETH = 18 células. Nenhum tuning posterior nem seleção de vencedoras.
- Índice OPEN(t) versus OPEN(t+H), como proxy otimista; **NÃO** se provou igualdade com preços reais de abertura/liquidação de Event Futures.

## Resultados

| Ativo | Horizonte | Regra | N | W | L | Acerto | EV q80 | EV q85 |
|---|---:|---|---:|---:|---:|---:|---:|---:|
| BTC_USDT | 10m | UP_ALWAYS | 2015 | 994 | 1019 | 49.38% | -0.1111 | -0.0864 |
| BTC_USDT | 10m | ROC3_CONT | 2013 | 998 | 1013 | 49.63% | -0.1066 | -0.0818 |
| BTC_USDT | 10m | ROC3_REV | 2013 | 1013 | 998 | 50.37% | -0.0932 | -0.0680 |
| BTC_USDT | 30m | UP_ALWAYS | 671 | 344 | 326 | 51.34% | -0.0757 | -0.0501 |
| BTC_USDT | 30m | ROC3_CONT | 670 | 334 | 335 | 49.93% | -0.1012 | -0.0763 |
| BTC_USDT | 30m | ROC3_REV | 670 | 335 | 334 | 50.07% | -0.0985 | -0.0735 |
| BTC_USDT | 60m | UP_ALWAYS | 335 | 176 | 159 | 52.54% | -0.0543 | -0.0281 |
| BTC_USDT | 60m | ROC3_CONT | 335 | 163 | 172 | 48.66% | -0.1242 | -0.0999 |
| BTC_USDT | 60m | ROC3_REV | 335 | 172 | 163 | 51.34% | -0.0758 | -0.0501 |
| ETH_USDT | 10m | UP_ALWAYS | 2015 | 1007 | 1006 | 50.02% | -0.0995 | -0.0745 |
| ETH_USDT | 10m | ROC3_CONT | 2013 | 979 | 1032 | 48.68% | -0.1236 | -0.0993 |
| ETH_USDT | 10m | ROC3_REV | 2013 | 1032 | 979 | 51.32% | -0.0762 | -0.0506 |
| ETH_USDT | 30m | UP_ALWAYS | 671 | 340 | 330 | 50.75% | -0.0864 | -0.0611 |
| ETH_USDT | 30m | ROC3_CONT | 671 | 311 | 359 | 46.42% | -0.1642 | -0.1411 |
| ETH_USDT | 30m | ROC3_REV | 671 | 359 | 311 | 53.58% | -0.0355 | -0.0087 |
| ETH_USDT | 60m | UP_ALWAYS | 335 | 174 | 161 | 51.94% | -0.0651 | -0.0391 |
| ETH_USDT | 60m | ROC3_CONT | 335 | 162 | 173 | 48.36% | -0.1296 | -0.1054 |
| ETH_USDT | 60m | ROC3_REV | 335 | 173 | 162 | 51.64% | -0.0704 | -0.0446 |

**Economia simulada:** 0/18 células com EV positivo tanto a q=0.80 como q=0.85; pagamento hipotético e simétrico, NÃO payout histórico real MEXC. Os pagamentos reais variam com momento, lado e ciclo; nenhum foi recuperado historicamente neste estudo. Melhor acerto: ETH 30m ROC3_REV 53.58%, abaixo de break-even teórico 55.56% a q80 ou 54.05% a q85. Ties rendem zero.

## Hashes de fonte pública (SHA256 das respostas)

| Ativo | Chunk desde UTC | Nº linhas | Raw SHA-256 |
|---|---|---:|---|
| BTC_USDT | 2026-03-31 | 1152 | `83fecc0e1146923467553167fd4fb10de68b90cca1fabda1d5444cb0dcfdc9dc` |
| BTC_USDT | 2026-04-04 | 1152 | `4f31d54089fa44a4fa5813f5a72d5ac7e80b94002a5c9e0b1af6deaa5a635797` |
| BTC_USDT | 2026-04-08 | 1152 | `7385e3e5e198fa174e0d3cafd6e9afad8dcae28714915cec12c44fa3f1ac86db` |
| BTC_USDT | 2026-04-12 | 864 | `eab781a0282d74e228ac572bf59c5b91a208c31da7773566b6b452c2a7cd8b28` |
| ETH_USDT | 2026-03-31 | 1152 | `6ee86f19bcc4fbd3737f19a05c2a8aea11b643f410bfacc8e40318b2fd3f9696` |
| ETH_USDT | 2026-04-04 | 1152 | `315394e1865b7fe02169e9717d471fd304ec3ad3b9a7c6d322481b9ed5c0ca5f` |
| ETH_USDT | 2026-04-08 | 1152 | `368d89258dfa1299246feda3b8adbc64ccd175e8939ebf83dd9564fbf06f8da5` |
| ETH_USDT | 2026-04-12 | 864 | `3e491cfaae704f0a5cafcf15393b19cb651088dc59a5ac7341bac6e6db986f81` |

## Restrições
- Sem conta, dinheiro, ordens, endpoints privados, login, wallet, main merge ou histórico protegido de setembro de 2026.
- 0/18 significa apenas **nenhum EV positivo nas 18 configurações e cenários calculados neste período**, não NO_EDGE universal para trading de evento.
- Não repetir o mesmo teste com novos parâmetros escolhidos após o resultado para procurar falsos vencedores. A próxima hipótese terá de ser economicamente distinta, com freeze pré-resultados e validação independente.
