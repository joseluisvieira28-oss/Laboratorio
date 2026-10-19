# Veredito — FUNDING HUNTER V01
**SOURCE_BLOCKED. Edge não demonstrada. Parar V01.**

O source gate documental falhou antes da abertura de outcomes. Não foi executado um backtest nem calculado PnL histórico. Não há candidato promovido ou recolha prospetiva ativa. Isto não demonstra ausência económica de edge.

## Resultado verificável
Protocolo congelado em [51879d805650169a338019fc2adc91646933079e](https://github.com/joseluisvieira28-oss/Laboratorio/commit/51879d805650169a338019fc2adc91646933079e), antes de qualquer payload de mercado desta missão.
Universo: BTC/ETH/SOL, perpétuos lineares USDT MEXC/Binance, janela 2025 e warmup de 31/12/2024. Datas/regras de decisão, quatro execuções, cashflows com sinal, intervalos, basis, collateral separado e critérios de rejeição constam de PROTOCOL.md.
Não existe manifesto real de settlements aprovado: falta de fonte é um bloqueio, não autorização para inventar timestamps.

A documentação atual da [MEXC](https://www.mexc.com/api-docs/futures/market-endpoints/get-funding-rate-history) acrescenta collectCycle por registo ao schema antigo. Isso ajuda a distinguir 1h/4h/8h; não resolve preços exatos de settlement, livros executáveis históricos ou acesso limitado a datas anteriores a 2026.
A [Binance](https://developers.binance.com/en/docs/catalog/core-trading-derivatives-trading-usd-s-m-futures/api/rest-api/market-data) documenta filtro temporal e markPrice associado à cobrança. Não se presume cobertura real sem payloads/recibos.

O livro [atual](https://www.mexc.com/api-docs/futures/market-endpoints/get-contract-order-book-depth) e os [últimos N snapshots](https://www.mexc.com/api-docs/futures/market-endpoints/get-the-last-n-depth-snapshots) da MEXC não demonstram uma série completa datada de 2025. [Velas de fair price](https://www.mexc.com/api-docs/futures/market-endpoints/get-fair-price-candles) não substituem esse livro nem estabelecem o preço da cobrança exata.
A pesquisa adicional por arquivo público histórico e preços de funding não encontrou uma fonte oficial gratuita que resolvesse estes requisitos; não é prova de inexistência de todas as fontes possíveis.
SOURCE_RECEIPT.json distingue fontes consultadas, lacunas, zero pedidos de payloads de mercado e ausência de hashes brutos. Não se apresenta navegação documental como teste HTTP da API.

## Economia conservadora: aritmética, não outcomes
Para N=1000 USDT por perna, E=2000 USDT imobilizados:
- 2 execuções MEXC a 6bps + 2 Binance a 5bps = 2,20 USDT.
- Reserva mínima adicional 2bps por execução = 0,80 USDT.
- Custo total mínimo = 3 USDT = 30bps de N = 15bps de E.
- Stress de execução: reserva de 7bps por execução => 5 USDT = 50bps de N.
- Exemplo hipotético de diferencial constante de 1bp por 8h: 0,30 USDT/dia, 10 dias para 3 USDT, ignorando basis e reversões. Com horizonte fixo 24h, seriam necessários 10bps por cada 8h para cobrir 30bps, nas mesmas simplificações.

São cenários assumidos e congelados; não são comissões históricas comprovadas, lucro observado ou limite universal. Fees usam notionals reais; 22bps só equivale a quatro notionals iguais. A [MEXC distingue taxas API de promoções web](https://www.mexc.co/en-GB/announcements/article/updates-to-api-futures-trading-fees-may-1-2026-17827791535194). A [Binance exemplifica taker de 5bps](https://www.binance.com/en-NG/support/faq/detail/360033544231). Falta certificar toda a aplicabilidade histórica.
As restrições de produto/geografia requerem confirmação pública datada; não se inferiu elegibilidade da timezone suíça. Sem contas ou contorno de restrições.

## Auditoria e limites
FUNDING-DISPERSION-DN-001 (637c583fd9f862dfd22960926d094eb95b29eb4b) já descrevia persistência de funding entre Bybit/OKX. Hunter é replicação MEXC/Binance mais contabilidade integral, distinta de CONVEX, sem reclamar novidade absoluta.
MFIBR (12c17e2c657dd4c23e9e707349ee548a73aa06d0) foi bloqueado por artigos de mudança de intervalos; não se repetiu seleção de eventos.
CVFB (113fc8950f02688b4e09ee24a76b401cf293fcd8) permaneceu inconclusivo por proveniência do oracle Hyperliquid; os seus diagnósticos não provam este par.
Histórico da branch funding-dispersion revisto: 637c583, 76b8279, c34ba52. Census de branches identificou também funding-cash-carry e funding-slot; não se alega auditoria exaustiva de todas as mais de mil branches.

## Verificação
20 testes locais passaram, cobrindo sinal long/short, reversão, valuation variável, quatro comissões, basis adversa, settlements assíncronos, custos/capital e rejeição de payloads vazios/incompletos, HTML, duplicados, não finitos, símbolo errado, preço ausente, intervalos inválidos e linhas de 2026.
ledger.py contém apenas primitivas offline e validação de schema; não certifica sozinho cobertura, preços ou rentabilidade. Todos os valores de teste são sintéticos.
CI limitado executa esses mesmos testes e publica relatório de teste/aritmética; não recolhe dados, negoceia ou implementa aprovação económica. Sem schedules, secrets, Render ou Windows operator. main e holdout 2026 intocados.
Condição de reabertura: fonte pública gratuita e legitimamente acessível que demonstre as lacunas, com novo protocolo antes de novos outcomes; sem baixar exigências após resultados.
