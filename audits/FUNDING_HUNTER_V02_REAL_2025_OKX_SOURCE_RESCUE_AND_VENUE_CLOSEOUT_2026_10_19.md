# CRYPTO LAB — FUNDING HUNTER V02 SOURCE RESCUE: FIVE LIVE SOURCE TESTS — 19 OCT 2026

## Veredito resumido

**MEXC/Binance V01 = SOURCE_BLOCKED.** Sem source gate completo, portanto sem PnL económico e sem alegação de edge. A V02 procurou arquivos históricos alternativos sem abrir os outcomes de 2025, respeitando os protocolos congelados antes de cada fonte. **Binance/OKX = SOURCE_BLOCKED para execução rigorosa de 2025 no atual contrato.** Mas foi descoberta uma família própria de investigação na **OKX USDT-linear vs USD-inverse, FUTUROS-ONLY**, com arquivos de funding+livros de ordens 400 níveis referenciados oficialmente para três ativos em 2025. Estado correto **SOURCE_DISCOVERY_CANDIDATE_ONLY, AINDA NÃO TESTÁVEL ECONOMICAMENTE**. Os arquivos a que conseguimos aceder parcialmente não contêm preços exatos de settlement; não houve testes de lucro ou de preenchimentos reais.

### Ordem científica congelada

- Protocolo V01 e PR [#252](https://github.com/joseluisvieira28-oss/Laboratorio/pull/252) mantidos intocados; nenhuma remarcação dos resultados MEXC.
- V02 `SOURCE_METADATA_PRE_QUERY_FREEZE_2026_10_19.md` commit `e3d1ea42`, antes dos 2025 catálogos oficiais.
- V02B `V02B_ONE_FUNDING_ZIP_TRANSPORT_AND_BINANCE_HEAD_FREEZE_2026_10_19.md` commit `bc4d67ba`, antes de qualquer arquivo de funding.
- V02C `V02C_OKX_USDC_USDT_DUAL_MARGIN_SOURCE_FAMILY_FREEZE_2026_10_19.md` commit `d59e60fc`, antes de USDC histórico.
- V02D `V02D_USD_INVERSE_AND_USDT_LINEAR_3ASSET_FUNDING_SOURCE_FREEZE_2026_10_19.md` commit `632a442b`, antes de USD-inverse histórico.
- V02E `V02E_INVERSE_BTC_FUNDING_ZIP_HEADER_ONLY_FREEZE_2026_10_19.md` commit `8892b7ff`, antes do original arquivo 2025 BTC-USD funding. O primeiro V02E retornou erro técnico AttributeError em fonte schema (lista tratada como dicionário), **não foi mascarado**. Corrigido no commit `d5bfe5fe`, repetição GitHub Actions **39228639247** fonte passa.

## Resultados reais, não testes sintéticos

**#39227262012** [metadata original Binance-alternative OKX](https://github.com/joseluisvieira28-oss/Laboratorio/actions/runs/39227262012), 4 pedidos GET públicos (HTTP200/código0): oficial 2025-06 funding mensal `BTC-USDT,ETH-USDT,SOL-USDT`: **3 ZIP URLs em static.okx.com**; arquivo 400-L2 UTC 2025-06-02 `BTC-USDT,ETH-USDT,SOL-USDT`: **3 TAR.GZ URLs**. Validação: **6/6 metadados de fonte encontráveis**. Nada prova ainda os bytes brutos 400-L2 e o instrumento dentro de cada arquivo, nem cobertura diária de ano completo.

**#39227800228** [byte/header + Binance HEAD](https://github.com/joseluisvieira28-oss/Laboratorio/actions/runs/39227800228):
- 2025-06 `BTC-USDT-SWAP` funding ZIP HTTPS `static.okx.com` efetivamente **descarregado**, 1,322 bytes; SHA256 da cópia local `7d9c0081d864be097539ee6021ace42709fdadce148cd5cabde12ee3603b9a2a`; único membro 4,333 bytes descomprimidos; cabeçalho CSV exato `instrument_name,funding_rate,funding_time`. Nenhuma taxa/payout/preço foi lida.
- Binance Data Vision `BTCUSDT-bookTicker-2025-06-02.zip` **HTTP404** em HEAD. Confirmar histórico comunitário com comentário de colaborador oficial na issue binance-public-data #334 (historical bookTicker descontinuado em 2024); isto prova a falha nessa data, não impossibilidade universal.
- Binance Data Vision `BTCUSDT-bookDepth-2025-06-02.zip` **HTTP200** em HEAD. Este esquema `timestamp,percentage,depth,notional` é profundidade agregada por banda de preço, não preço/quantidade exato de melhor BID/ASK para um fill. Importante: issues do repositório reportam divergências neste agregado.

**#39228085134** [OKX USDC same-venue fonte](https://github.com/joseluisvieira28-oss/Laboratorio/actions/runs/39228085134):
- BTC-USDC: funding ZIP e L2 TAR.GZ encontrados;
- ETH-USDC: funding ZIP e L2 TAR.GZ encontrados;
- **SOL-USDC: funding sem arquivo no catálogo e L2 de 02/06/2025 sem arquivo.**
- Total 4/6: `USDC_SOURCE_INCOMPLETE` para universo pré-congelado BTC+ETH+SOL; não retirar SOL a posteriori nem substituir por outro símbolo e fingir o mesmo protocolo.

**#39228295401** [OKX USD-inverse perp](https://github.com/joseluisvieira28-oss/Laboratorio/actions/runs/39228295401):
- Junho 2025 funding mensal **BTC-USD, ETH-USD, SOL-USD**: 3 ZIP históricos oficiais catalogados;
- Dia 2025-06-02 L2 400 níveis **BTC-USD, ETH-USD, SOL-USD**: 3 TAR.GZ oficiais catalogados;
- Metadados **6/6**, HTTP200/código0, domínio static.okx.com, ainda sem livros 2025 ingeridos/sem qualidade ou contrato exacto verificados.

**#39228639247** [USD inverse ZIP transport real](https://github.com/joseluisvieira28-oss/Laboratorio/actions/runs/39228639247):
- BTC-USD-SWAP junho 2025 funding ZIP original descarregado **1,295 bytes**, SHA256 cópia local `383fd84f431caf75470c1efce95577e2c8dfcc67bb80bf381112ccd32c4984b0`; membro 4,206 bytes, cabeçalho `instrument_name,funding_rate,funding_time`; nenhum funding histórico pago lido.
- Este arquivo não contém coluna de preço efetivo do mark usado no settlement. Logo, mesmo com taxas verificadas, os fluxos exatos das duas pernas não foram provados.

## Fonte económica: por que não podemos já declarar GO?

O anúncio e mecânica official [OKX perp funding](https://www.okx.com/en-ae/help/perps-funding-fee-mechanism) distingue fundamentalmente:
- **USDT perp linear:** valuation em USDT = contratos * ctVal * markPx.
- **USD inverso crypto-margin:** valor/cobrança em moeda cripto = contratos * faceUSD / markPx; PnL inverso não-linear em cripto. Long/short linear/inverso **não cria um hedge USD delta-neutral gratuito** devido a FX do colateral, contract multiplier, margem isolada/cross, moeda de funding, diferença de base e risco de liquidação.
- Aquele CSV de funding não inclui o markPx exato de settlement (3 colunas apenas). Substituir arbitrariamente mid, candle 1m ou preço do livro é uma nova hipótese de execução/valor que exige congelamento de limite adverso ANTES de avaliar outcomes; a V02 não o fez.
- Dos 365 dias de 2025 exigidos por V01, só existe prova **de 1 mês de catálogo e 1 dia de L2** para a rota alternativa; nenhum manifesto anual completo ou source raw verificado por instrumento. Fontes de contrato, fees e regras de margem no instante de 2025 não foram verificadas.
- Restrição de elegibilidade de produtos suíços nunca deve ser inferida só a partir de localização; confirmar em documentação aplicável antes de aplicação real.

## Vereditos objetivos separados

| Rota | Source gate nesta missão | Lucro após custos | Ação |
|---|---|---|---|
| MEXC/Binance 2025 V01 | `SOURCE_BLOCKED`, sem arquivo histórico completo | **DESCONHECIDO** | ENCERRAR V01, não retro-ajustar |
| Binance/OKX 2025 linear | `SOURCE_PARTIAL`: OKX real; Binance bookTicker 2025 amostrado HTTP404 e bookDepth agregado | **DESCONHECIDO** | NÃO correr backtest fingindo fills |
| OKX USDT vs USDC linear BTC+ETH+SOL | `SOURCE_BLOCKED_SIX_FILES` (4/6) | **DESCONHECIDO** | NÃO excluir SOL para fabricar PASS |
| **OKX USDT-linear vs USD-inverse**, BTC+ETH+SOL | `SOURCE_DISCOVERY_CANDIDATE_ONLY` (12 referências metadados combinadas; BTC inverse/linear arquivos funding efetivamente transferidos para teste de cabeçalho) | **DESCONHECIDO** | Fonte PENDENTE de formato/cobertura/mark, hipótese de pesquisa nova, não GO |

Nenhuma rota tem lucro/risco histórico real ou forward calculado. Número de trades/episódios económicos **ZERO**, 2026 holdout intocado, no money, accounts, orders, exchange mutations, main merge, Render/Windows trading operator.

## Próximo ataque racional da alternativa de fonte

1. Antes de abrir rates ou preços, freeze de um piloto técnico de dois instrumentos BTC-USDT-SWAP vs BTC-USD-SWAP numa única data 2025, com contrato/collateral inverso, output schema, e critérios de FAIL; descarregar no portal OKX **manualmente** apenas os dois 400-level L2 BTC de 2025-06-02 se o transporte do GitHub for bloqueado. Os dados brutos nunca devem ser commitados ou redistribuídos.
2. Para exata valorização de funding, tentar obter markPx no settlement (ponto no tempo) para ambos instrumentos através de fonte histórica oficial; se impossível, freeze *conservador limit-bounded* antes de abrir outcomes, com invalidação se erro exceder margem bruta.
3. Demonstrar fees e contratos exatos 2025, tick/lot/collateral, base USDT vs USD, liquidação independentemente. Só então congelar regras econômicas novas e abrir outcomes 2025 com análise causal after-fee. Protegido 2026 permanece fechado.
4. Se nenhum piloto source passa, fechar nova hipótese em `SOURCE_BLOCKED`; não gastar tempo a adaptar parâmetros a um ano conhecido.

**VEREDITO GLOBAL V02:** ORIGINAL MEXC BLOCKED; Binance/OKX não tem executable 2025 BBO provado; USDT/USDC 3-asset incomplete; **OKX inverse vs linear é uma hipótese nova de fontes legítimas mais viáveis, mas NÃO um candidato rentável certificado, nem autorização para live.**
