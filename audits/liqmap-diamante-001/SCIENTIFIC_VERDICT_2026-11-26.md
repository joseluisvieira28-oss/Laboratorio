# LIQMAP-DIAMANTE-001 — AUDITORIA CIENTÍFICA E VEREDITO
Data: 26/11/2026. **LIVE ECONOMIC NO-GO; scientific INCONCLUSIVE. No trades, subscriptions or spending.**

## O que o vídeo demonstra e não demonstra
O vídeo promocional do Neuron enviado pelo operador (~71 s) apresenta barras azuis/laranja e texto sobre zonas de liquidação BTC. Não mostra previsões arquivadas ANTES dos movimentos, exportação histórica pontual, código do modelo, posições individuais verificadas, preços de entrada ou PnL com custos. Logo não é evidência de edge.
A CoinGlass esclarece nas páginas oficiais que intensidade do mapa é ESTIMATIVA de modelo e não montante efetivo liquidado, valor monetário garantido ou resting order. A API de heatmap/mapa CoinGlass requer Professional+ e chave. Não houve tentativa de subscrever ou comprar nada.

## Experiência 001A — proxy sintético com dados oficiais Bybit (SOURCE_BLOCKED)
- PR Draft #399 https://github.com/joseluisvieira28-oss/Laboratorio/pull/399
- Fonte: Bybit public v5 hourly price/OI para BTCUSDT e ETHUSDT, período congelado 2026-11-01..2026-11-25 UTC, 576 horas por ativo, controles OI/candle e preço causal.
- Pre-registo ANTES de resultados: research/liqmap-diamante-001/PROTOCOL.md commit fb83db8f0fbc27a8796fbfc85b3524b8b3e28fd1. 
- Execução GitHub Actions #45763751823 https://github.com/joseluisvieira28-oss/Laboratorio/actions/runs/45763751823. Testes offline PASS; GET públicos Bybit BTC/ETH devolvem HTTP 403 Forbidden e foram documentados como SOURCE_BLOCKED. Arquivo fonte bloqueada artifact 15091166802 SHA256 ZIP 2bd1eb90b21eeec1bba7869b43c43da0c86c38d6234a7cef40cae055c3c33f3d.
- Zero preços/OI da Bybit imputados, zero taxa de acerto para 001A. Não confundir FAIL de acesso com NO-GO económico.

## Fonte gratuita independente — positions e liquidações efetivamente registadas
LiquidVision free sample público https://huggingface.co/datasets/liquidvision/crypto-derivatives-sample
- Metadados auditados numa execução GitHub Actions #45764070350 https://github.com/joseluisvieira28-oss/Laboratorio/actions/runs/45764070350; arquivo SHA256 ZIP fb0004b258cff63a7def3879a75b033b19e9f58d554807b3e372265c15a1ee5f.
- 76,224 linhas de posições de grandes contas Hyperliquid, com preço de liquidação reportado pela exchange (campo liq_px) e preço mark_px, mas **só 28 timestamps entre 2026-11-08 00:10:44 UTC e 21:39:19 UTC**. 48,272 BTC, 20,675 ETH e 7,277 SOL rows, repetidos por tempo/carteira e não independentes.
- 105,256 eventos observados de liquidação, BTCUSDT 44,283, ETHUSDT 45,745 e SOLUSDT 15,228, entre **2026-11-02 00:00 UTC e 2026-11-08 23:59 UTC**. São liquidações que JÁ ocorreram, não o mapa histórico de risco prospetivo. Proveniência desta amostra anunciada pelo terceiro, sem auditagem de completude do universo.
- Nenhum identificador de carteira/conta foi republicado. Dados originais não republicados no artefacto, apenas contagens, checksums e resultados agregados.

## Experiência 001B — Replay de UM DIA com preços de liquidação reportados (INCONCLUSIVE)
- Protocolo separado congelado antes dos outcomes: research/liqmap-diamante-001/PROTOCOL_REAL_POSITIONS_SAMPLE.md commit fddf9e9434a8634913237e472c553904cefa3594.
- A cada instantâneo, agrega valor_usd de posições grandes por banda de 0.5% do preço de liquidação EXCHANGE-REPORTED; seleciona maior concentração a distância log 0.5-5% do preço corrente, penalizada pela distância. NÃO é o modelo do Neuron nem o modelo da CoinGlass.
- Medida: posição do preço mark em instantâneo futuro >=60 min <=120 min depois, comparada com direção de preço indicada pela zona. Controlo: momentum em instantâneo >=60 <=120min ANTES. Decisões espaçadas >=2h; um evento de cada vez, sem overlap. É direção do preço no próximo checkpoint, NÃO a sequência de first touches no interior da hora. Sem fills, sem PnL.
- GitHub Actions #45764254759 SUCCESS https://github.com/joseluisvieira28-oss/Laboratorio/actions/runs/45764254759. Artefacto 15090514212, ZIP SHA256 ea991a5866d3e0c6160b54a6ea1c19203d76eb7cd72e8e13647eb296a2c182dd.
- BTC: 28 instantâneos, 7 decisões pontuais emparelhadas; **zona 1/7 (14.29%)** vs MOM 7/7 (100%); Wilson95 para a zona [2.57%, 51.31%].
- ETH: 28 instantâneos, 6 decisões emparelhadas; **zona 2/6 (33.33%)** vs MOM 1/6 (16.67%); Wilson95 [9.68%,70.00%].
- SOL: 28 instantâneos, 6 decisões emparelhadas; **zona 4/6 (66.67%)** vs MOM 3/6 (50%); Wilson95 [30.00%, 90.32%].
- Menos que 20 decisões por ativo pre-registadas como mínimo exploratório; todas falham. Intervalos largos, única data, amostragem de contas grandes, preços discretos, dependência entre ativos e ausência de livros/execution fills => não permitem testar retorno líquido ou validar generalização.
- RESULTADO: nenhum achado robusto; a aparente vantagem em SOL e momentum BTC são episódios de UM DIA com n baixo. Nunca selecionar SOL como vencedor porque o vimos agora.

## Fontes e trabalhos externos verificados
- https://docs.coinglass.com/reference/liquidation-map : modelo de intensidade, não liquidações garantidas.
- https://docs.coinglass.com/reference/endpoint-overview : API professional maps.
- https://bybit-exchange.github.io/docs/v5/websocket/public/all-liquidation : eventos executados em stream não mapa futuro.
- https://github.com/bendizziesmith/liqmap : mapa estimado de fonte pública, com parâmetros arbitrários de alavancagem, OI e decaimento; não prova edge.
- https://huggingface.co/datasets/liquidvision/crypto-derivatives-sample : amostra livre com posicoes, marcas e liquidações reportadas.
- https://www.coinglass.com/prime : visualização paga é diferente de API histórica auditável.
- Estudos de cascatas de liquidações demonstram potencial de reflexividade/impacto, mas NÃO demonstram capacidade de os mapas direcionais anteciparem o próximo movimento ou o seu PnL realizável.

## Conclusão económica e próxima porta científica
**SOURCE BLOCKED** para 001A Bybit; **TECH/SOURCE PASS mas SCIENTIFIC INCONCLUSIVE** para 001B um único dia. **ECONOMIC NO-GO** para capital real, comprar Neuron com intenção de rentabilidade, ou bot de sinais.
Próximo gate útil: >=30 dias de mapas snapshotados ao vivo com relógio/hashe de fonte, >=2 meses idealmente e vários regimes, zonas congeladas antes de preços futuros, direção/tempo até primeiro toque vs placebo de igual distância e MOM, calibração de liquidação real, fees/slippage/funding, teste de latência e drawdown; não criar promessas de captação automática sem tarefa funcional. Antes de pagar qualquer plataforma perguntar (1) API ou export de pontos com timestamp observável, (2) histórico point-in-time e correções/revisões, (3) fórmulas e cobertura por exchange, (4) custo TOTAL R$99 x número de parcelas + cancelamento e (5) prova auditável de performance económica.
**Zero trades, gastos, subscrições, ordens, produção ou merges. PR Draft.**
