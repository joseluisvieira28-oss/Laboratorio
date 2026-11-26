# LIQMAP-DIAMANTE-003 — AUDITORIA HISTÓRICA FINAL — 26/11/2026
**Decisão: HIPÓTESE ECONÓMICA NO-GO nos 105 dias. Fonte histórica EXATA do HyperQuant: INSUFICIENTE. LIVE TRADING: NO-GO.**

## I. Pergunta e desfecho da recuperação forense HyperQuant
Pergunta do operador: "Conseguimos recuperar mapas do HyperQuant como eram vistos 60–180 dias ANTES dos movimentos do BTC?"

**Não, pelo GitHub público investigado.**
- Repository: https://github.com/rdemb/hyperquant-data
- Auditoria GET real via GitHub Actions #45776591340, [artefacto 15095499987](https://github.com/joseluisvieira28-oss/Laboratorio/actions/runs/45776591340/artifacts/15095499987)
- GitHub REST commits filtered path=liq-map/BTC.json devolveu **1 commit em 26/11/2026 às 07:36:25 UTC, zero parents**. A README confirma que main preserva só um commit do estado atual. history tem janela móvel de ~7 dias de transações, livros e contextos (também single commit), NÃO contém o mapa liq-map/BTC.json. ledger contém previsão de OUTROS modelos, o arquivo de 25/11 tinha 1488 linhas e **0** registos completos longs/shorts/coverage. archive contém preços e funding, sem liq-map/BTC.json. Os endpoints map em history/ledger/archive responderam 404.
- Backtest de um mapa atual colocado retrospectivamente em preços antigos seria look-ahead e é PROIBIDO.

## II. Alternativas grátis e gating
- Hydromancer/hyperliquid-reservoir no Hugging Face anuncia apenas **13 datas** de snapshots de posições, 26 ficheiros account_values/positions (metadados do primeiro inventário). Isto NÃO atende ao mínimo de 60 mapas.
- Blocklens meta API sem chave respondeu HTTP 401; docs oficiais exigem chave mesmo no escalão Free, que só libera 30 dias, Pro todo o histórico. Não foi criada conta nem pago nada.
- **Alternativa que passou:** [ProbioticFarmer/hyperliquid-augmented-copytrading](https://huggingface.co/datasets/ProbioticFarmer/hyperliquid-augmented-copytrading) no Hugging Face, snapshots_perp: **391 Parquet correspondentes a 390 datas de 2025-07-29 a 2026-10-13**, ~6.06GB anunciado pela API de metadados. Trata-se de um **OUTRO fornecedor**, não o mapa original HyperQuant e não o Neuron. Ver [inventário Actions #45776746721](https://github.com/joseluisvieira28-oss/Laboratorio/actions/runs/45776746721).
- Duas datas extremas de fonte original foram descarregadas E seus SHA256 validados contra LFS OIDs: 2025-07-29 (175551 posições em todos os mercados, 16434 BTC) e 2026-10-13 (314708 todos, 37815 BTC). Colunas: user, market, size, notional, entry_price, **liquidation_price**, leverage_type, leverage etc. **NÃO EXISTE coluna de timestamp por linha**; hora e data são inferidas apenas do nome dos ficheiros e do fornecedor. Nenhuma carteira/endereço é republicado no output.
- [Actions schema #45777109720](https://github.com/joseluisvieira28-oss/Laboratorio/actions/runs/45777109720), 2/2 SHA256 LFS e schema PASS.

## III. Teste de hipótese histórica SEPARADA (não HyperQuant, não Neuron)
Protocolo congelado antes de consultar os 105 outcomes em research/liqmap-diamante-003/BACKTEST_PROTOCOL.md (commit 865dbc9201facae023d179e3d337086a92708ff8).
- Janela determinada: TODOS os dias 2026-07-01 a 2026-10-13, **105 dias calendário**, sem escolher datas vencedoras.
- Cada snapshot fonte pública Parquet com preço liq BTC da posição, tamanho e side. Referência de preço = mediana robusta |notional/size| das posições BTC, confrontada com candle pré-snapshot de BTC-PERP na API oficial Hyperliquid, tolerância <=5%; não inventar mark posterior.
- Níveis com long abaixo, short acima, bin log 0.005 (0.5%), distancia log [.005,.05] e mass=abs(size)*liquidation_price, score soma mass*exp(-dist/.03); alvo escolhido e barreira oposta simétrica em log-preço. Mesmos parâmetros LIQMAP002, sem tuning após ver resultados. Não imputar fontes/dias.
- MOM24 do preço BTC-PERP em horas FECHADAS anteriores ao suposto instante snapshot; resultado FIRST_TOUCH nas próximas 24 velas 1h COMPLETAS a partir da primeira hora que começa APÓS o suposto as-of; mesma barra dupla = AMBIGUOUS; sem-toque NEITHER. O algoritmo não utiliza futuro para construir alvos.
- PnL hipotético SHORT/LONG BTC perp, entrada no primeiro open, saída na barreira ou último close, 10/35/80bps POR LADO +5bps slippage POR LADO. Ignora funding, liquidez real, mark-price triggers, margin, impostos e fills.
- Fonte de preços independente: API oficial Hyperliquid POST /info candleSnapshot, **2616 velas 1h completas e sem lacunas**. Recibo request SHA256 6b6b497f90e63ab3d2c1364047be02f7ec76325944c3c2e26647e919473be117 e resposta SHA256 22612cffd945d75add40a42d95e17c362573d81c2bc7b675c05d3ef231311c0d.
- 104/105 dias passaram checks de fonte e preço; 1 dia **23/08/2026 SOURCE_BLOCKED** por timestamp reclamado do ficheiro fora da janela fixada (mais de 12h UTC / claim não verificável). Não houve substituição.
- Em 104/104 eventos aceites, SHA256 dos bytes Parquet coincide com o LFS original, a data claimed pertence à data de arquivo, target × mirror = mark² com erro relativo <=2.3e-16; as rotas de custos variam exactamente 50bps entre 10 e 35, e 90bps entre 35 e 80 por transação de duas pernas. Nenhum endereço/ID de wallet guardado.
- [Run completo SOURCE PASS #45777543433](https://github.com/joseluisvieira28-oss/Laboratorio/actions/runs/45777543433) job historical-105-day-BTC SUCCESS, **8/8 testes offline**; [artefacto 15096069230](https://github.com/joseluisvieira28-oss/Laboratorio/actions/runs/45777543433/artifacts/15096069230). ZIP SHA256 b86222c7324fcd47dd03da361650fbc6a91fbc190b7088c1501b91fcd6ed0069.

## IV. Veredito estatístico
**104/105 dias com observação/futuro válido; 53 eventos com uma barreira atingida primeiro; 51 NEITHER; 0 ambiguous.**

| Campo | Mapa hipotético | MOM24 |
|---|---:|---:|
| Acertos entre 53 eventos resolvidos | **29/53 = 54.72%** | **28/53 = 52.83%** |
| Diferença emparelhada | **+1.887pp** | comparação |
| Intervalo Wilson95 da taxa mapa | **41.45% – 67.34%** | — |
| Média por oportunidade no stress 10bps/side +5bps slippage/side | **-27.911bps** | -33.056bps |
| Média por oportunidade no stress 35bps/side +5bps slippage/side | **-77.911bps** | -83.056bps |
| Média por oportunidade no stress 80bps/side +5bps slippage/side | **-167.911bps** | -173.056bps |
| Diferença média de PnL 80bps vs MOM24 (cancela custo igual) | **+5.145bps** | — |
| Intervalo 95% bootstrap em blocos semanais da diferença PnL | **[-38.235, +47.811]bps** | inclui 0 |

Regimes por mês (80bps/side, com slippage):
- Julho: 31 dias, 14 resolvidos, **5 mapa vs 9 momentum**, PnL médio mapa **-239.2bps**.
- Agosto: 30 dias, 13 resolvidos, **8 vs 8**, PnL médio **-133.0bps**.
- Setembro: 30 dias, 17 resolvidos, **12 vs 7**, PnL médio **-131.7bps**.
- Outubro 1–13: 13 dias, 9 resolvidos, **4 vs 4**, PnL médio **-161.9bps**.
Não selecionar Setembro ex post como estratégia: foi escolhido por ser favorável APÓS a avaliação e não muda veredito.

**Portas económico-científicas pré-congeladas:** >=60 fontes PASS; >=50 resolvidos PASS; Wilson95 low >50% **FAIL**; +5pp vs MOM24 **FAIL**; mean net80bps positiva **FAIL**; bootstrap lower95 excesso>0 **FAIL**; >=2 meses positivos no excesso PnL PASS (insuficiente). **Resultado HYPOTHESIS_NO_GO**.

## V. Limites adversariais
1. **Sem as-of per-row**: a hora do nome do ficheiro é uma afirmação do fornecedor, não um recibo criptográfico de que cada posição foi capturada e publicada ANTES dos movimentos. LFS SHA256 garante bytes recebidos hoje, não o instante histórico de existência. A análise é RETROSPETIVA e NÃO ponto-no-tempo comprovado.
2. Outra cobertura/seleção de posições e método de mark face ao scanner HyperQuant; resultados NÃO validam nem refutam o Neuron ou a heurística exata do HyperQuant.
3. Eventos diários são temporalmente dependentes e a comparação usa janelas de 24h. O bootstrap semanal amostra dependência, não prova independência nem corrige hipótese humana.
4. Ganho 54.7% condicional a 53 eventos tocados; **51 não tocaram qualquer barreira** e não podem ser excluídos do cálculo PnL. As taxas podem aparentar edge se se ignorar indevidamente NEITHER e custos.
5. Trading em perp teria funding, livro real, taxas efectivas, risco de liquidação do TRADER e short, todos não simulados. Nunca declarar lucro ou taxa de execução.
6. Repetir parâmetros na mesma amostra para procurar vencedores seria data snooping. Protocolo 002 prospectivo mantém-se inalterado, sem alteração de automação.

## Decisão prática
- **HyperQuant exact 60–180d historical map replay: SOURCE NOT AVAILABLE** pelo GitHub público.
- **Hipótese original sobre níveis de liquidação calculados de posições reais de outro arquivo: ECONOMIC NO-GO** neste teste histórico, porque a vantagem vs baseline é trivial e incerta e net after-cost negativa.
- **NEURON product claimed edge: NOT TESTED / NO EVIDENCE**, não comprar pela alegação de performance.
- **Real capital trading: NO-GO.** Manter somente LIQMAP-002 já iniciada para observação prospectiva com snapshots verdadeiramente congelados e timestamps; nenhum trade ou gasto realizado.
