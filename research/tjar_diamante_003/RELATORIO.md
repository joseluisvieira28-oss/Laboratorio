# TJAR-DIAMANTE-003 — Veredito económico
**27 de novembro de 2026 | B — lucro pontual demonstrado, NO-GO para capital e automação.**

## O resultado que muda a investigação

Em 9 de novembro às 08:26:45 UTC, no bloco 109917234 da Robinhood Chain, um operador distinto do endereço dominante recebeu **0,004017730291234839 ETH** no final de uma conversão HOOKR. A taxa observada foi **0,000014161088512 ETH**, incluindo a componente publicada pelo explorador (poster fee zero nesta transação). O saldo líquido da transação foi **0,004003569202722839 ETH**, equivalente a **US$8,54** à taxa histórica indicativa do explorador de 2.132,138072 USD/ETH. A valorização em USD é informativa. O lucro realizado foi em ETH e inclui as trocas e o financiamento liquidados dentro da transação. Custos externos, falhas anteriores e relação entre endereços ficam indeterminados.

- [Transação](https://robinhoodchain.blockscout.com/tx/0x099a35d0fcf4f5717d88658b91c89d6bb4c99b0653a2b5b3bb92f9519d4720d8)
- [Logs](https://robinhoodchain.blockscout.com/api/v2/transactions/0x099a35d0fcf4f5717d88658b91c89d6bb4c99b0653a2b5b3bb92f9519d4720d8/logs)
- [Trace paginado](https://robinhoodchain.blockscout.com/api/v2/transactions/0x099a35d0fcf4f5717d88658b91c89d6bb4c99b0653a2b5b3bb92f9519d4720d8/internal-transactions?index=49&transaction_index=1&block_number=109917234&include_zero_value=true)
- [Crédito de ativos no bloco 109914729](https://robinhoodchain.blockscout.com/tx/0xfd6f854e0da60c90a7e085a86a65cd9dfb4fad6d132c6021ea8fc460e0f26507)

| Fluxo observado | Valor |
|---|---:|
| WETH mobilizado com flash loan Morpho | 0,018167505232651224 WETH (~US$38,74) |
| HOOKR comprado na rota | 2.059,995436623926181615 |
| HOOKR queimado | 2.000 |
| HOOKR recebido do jar | 390,573524414251908218 |
| USDG recebido do jar | 17,052382 |
| ETH nativo recebido do jar pelo contrato | 0,010143382786388646 |
| WETH equivalente obtido nas duas vendas de saída | 0,012041852737496417 |
| Repagamento do principal | 0,018167505232651224 WETH |
| Crédito ETH ao remetente no trace 88 | 0,004017730291234839 ETH |
| Gas publicado | 0,000014161088512 ETH |
| Resultado líquido por transação | **0,004003569202722839 ETH** |

O tamanho observado cabe nominalmente em US$100, US$250 e US$500, incluindo gas observado. Em cada orçamento, a alternativa pré-financiada fica **INCONCLUSIVA**: faltam execução histórica antes da chegada, custos de preparação/manutenção de saldo e validação das permissões e dos estados da rota para o novo operador. A estratégia efetivamente usada contou com financiamento atómico. A reconciliação não presume acesso a essa infraestrutura.

## A duração do saldo e a duração económica

Às 08:22:26 UTC, a última entrada HOOKR/USDG antes do release creditou 390,573524414251908218 HOOKR e 2,158420 USDG. Entre esse bloco e a execução passaram **259 segundos**, com **2.505 blocos** de diferença. O release recolheu 17,052382 USDG, incluindo saldo anterior, e ETH nativo. Os 259 segundos medem o tempo após o último crédito ERC-20 identificado. Sem a série histórica de ETH nativo no jar e ofertas executáveis das pools, o início, a continuidade e a duração da janela com lucro ≥ US$1 são desconhecidos. Contagem causal a 1 bloco, 5/15/30/60 s, 5/30 min: **ND**. O replay a +5/+15/+30/+60 s fica SOURCE_BLOCKED; chegada após o vencedor implica oportunidade capturada e, com nonce antigo enviado, custo de tentativa/revert. Frequência de falhas e PnL de carteira são ND.

A sensibilidade pontual usa a execução vencedora, sem crédito causal. Com gas duplicado e redução dos recebimentos combinada com aumento igual do custo de aquisição, a margem indicativa fica em US$8,08 a 0,5%, US$7,65 a 1% e US$6,79 a 2%. Choques de liquidez carecem de reconstrução de pools. Retirar todas as saídas vendidas do caso, mantendo apenas o ETH nativo do jar e o custo de compra observado, deixa cerca de **−US$17,14** após gas. Liquidez e rota importam para o resultado.

## Recorrência e concorrência

O ledger HOOKR cobre os 20 eventos de nonce 0–19 observados de 6 a 26 de novembro e as respetivas transações e transferências ERC-20. Três remetentes distintos. Um remeteu **18/20 (90%)**. O intervalo entre o último crédito HOOKR e o release foi **0–1 segundo em 19/20**, à resolução dos timestamps. Essa métrica mede o crédito mais recente e admite saldos prévios. O máximo foi **10 releases brutos** em 7 dias móveis. Dois períodos completos de sete dias, 13–19 e 20–26 nov. UTC, tiveram **8 e 6 releases brutos**. Esta estratificação descreve resultados já vistos e não é uma validação OOS. A amostra tem um lucro realizado isolado reconciliado e zero oportunidades que tenham sido demonstradas como recorrentes e executáveis causalmente durante ≥30 s. PnL acumulado, mediana, pior caso e custos operacionais de radar para uma carteira nova: ND. Não há base para projetar receita.

## Censo da Factory oficial

Factory **0xfAc70EEEE259F2140CBbB8e3157b75A52ce39fee**. Seis exploradores devolveram 18 eventos JarDeployed sem cursor adicional. A amostra é delimitada pelo índice de cada explorador. Nos 18 pares, o histórico do jar mostrou um único ReleaserSet e os limiares abaixo vêm de ConfigSet. Endereços iguais são distintos por rede. O âmbito é a Factory TJAR, que difere dos contratos legados de protocol fees usados nos agregados Dune.

| Rede | Jar (prefixo) | Releaser (prefixo) | Limiar | Releases | Veredito no âmbito observado |
|---|---|---|---:|---:|---|
| Base | 0x9efd11e1 | 0x3cd1b0e0 | 500 USDC | 0 | NO-GO observado, limiar esgota o orçamento nominal a paridade |
| Base | 0xfee5fee5 | 0x3031b304 | 5.000 USDC | 0 | NO-GO pré-financiado |
| Arbitrum | 0x9efd11e1 | 0xf4c16d3e | 500 USDC | 0 | NO-GO observado, limiar esgota o orçamento nominal a paridade |
| Arbitrum | 0xfee5fee5 | 0x40b9127d | 1.000 USDC | 0 | NO-GO pré-financiado |
| Optimism | 0x9efd11e1 | 0xab51e57a | 500 USDC | 0 | NO-GO observado, limiar esgota o orçamento nominal a paridade |
| Optimism | 0xfee5fee5 | 0x41433c7a | 1.000 USDC | 0 | NO-GO pré-financiado |
| Polygon | 0x9efd11e1 | 0x859f7ad7 | 500 USDC | 0 | NO-GO observado, limiar esgota o orçamento nominal a paridade |
| Polygon | 0xfee5fee5 | 0x1eb597c5 | 1.000 USDC | 0 | NO-GO pré-financiado |
| Ethereum | 0x9efd11e1 | 0x5b21d477 | 500 USDC | 0 | NO-GO observado, limiar esgota o orçamento nominal a paridade |
| Ethereum | 0xfee5fee5 | 0x4e5da24a | 10.000 USDG | 2 | NO-GO pré-financiado, financiamento atómico observado |
| Ethereum | 0x13fa9511 | 0x73d0d811 | 1 FLAY | 1 | NO-GO de recorrência observada, PnL realizado ND |
| Robinhood | 0x9efd11e1 | 0x6dc5b1ae | 500 USDG | 0 | NO-GO observado, limiar esgota o orçamento nominal a paridade |
| Robinhood | 0xfee5fee5 | 0x0f414f29 | 5.000 USDG | 20 | NO-GO pré-financiado, financiamento atómico observado |
| Robinhood | 0x6425a789 | 0xd22e2282 | 2.000.000 RHIABLO | 1 | NO-GO de recorrência observada, custo executável ND |
| Robinhood | 0xb4c20b82 | 0xd4a9faaa | 2.000 HOOKR | 20 | NO-GO para promoção, lucro pontual realizado |
| Robinhood | 0x6cd7aaaa | 0x90c37da9 | 0,01 WETH | 0 | INCONCLUSIVO, sem release observado |
| Robinhood | 0xa424b595 | 0xa0912293 | 0,045 WETH | 0 | INCONCLUSIVO, sem release observado |
| Robinhood | 0xf98e5afb | 0x595ee610 | 100 USDG | 0 | INCONCLUSIVO, sem release observado |
| BNB Chain | — | — | — | ND | SOURCE_BLOCKED para o censo |

As conclusões por rede são NO-GO no conjunto observado em Base, Arbitrum, Optimism, Polygon, Ethereum e Robinhood. BNB fica SOURCE_BLOCKED. O teste de orçamento de stablecoins usa paridade indicativa. O limiar de 500 unidades implica necessidade adicional de gas; não demonstra impossibilidade em todos os preços de mercado. Os vereditos de financiamento prévio não invalidam arbitragem financiada, que exige prova própria.

- [Factory e redes oficiais](https://developers.uniswap.org/docs/protocols/tjar/deployments)
- [Factory Robinhood](https://robinhoodchain.blockscout.com/api/v2/addresses/0xfAc70EEEE259F2140CBbB8e3157b75A52ce39fee/logs)
- [Releaser HOOKR](https://robinhoodchain.blockscout.com/api/v2/addresses/0xd4a9faaaBF5baF38390852627Bd980782d83e75/logs)
- [Release de 1 FLAY por 10 USDC e 0,5 LINK depois de 0,000065851207748415 ETH de gas](https://eth.blockscout.com/tx/0x8f3215a5f17b7f485f47fd2db5570e127a6f068400989a9879b79c9960c37dbc)
- [Release Robinhood com 5.000 USDG de custo nominal](https://robinhoodchain.blockscout.com/tx/0xf3f09687cfc9e49be1ca087a1af58572d2a2570c7e829fb8b4cbc15addb9d4e2)

## Auditoria dos dados anteriores

A Dune 9072754 seleciona como destinatário o endereço com mais transferências de saída num hash. Isso pode ser um contrato intermédio e mistura mais de um jar no mesmo hash. A 9072761 junta valores ao jar apenas pela rede, podendo multiplicar releases quando há vários jars por rede; usa limiar nominal, preço diário e imputa gas ausente como zero. O preço diário pode incorporar negócios posteriores. Para uma reexecução, ligar chain id + endereço de jar + hash + índice de release e atribuir cada transferência na ordem de execução. Usar valores exigidos no evento, traces de ETH nativo, taxas efetivas e estado de pool anterior à decisão. A auditoria não reproduziu os agregados históricos 849/25/5/2 nem a média de custos por operador. Esses números não foram usados no veredito. Rubicon fica fora de promoção. Dune cobra execução e recuperação pela API nas modalidades indicadas. Não houve execução paga. Substreams documenta os módulos públicos e requer autenticação para extração. As alegações Jarvest não ficaram verificadas. Nenhum pagamento, depósito, assinatura, aprovação ou transação real foi feito.

- [SQL de metadados Dune](https://dune.com/queries/9072754)
- [SQL de PnL dos operadores](https://dune.com/queries/9072761)
- [Condições da Dune](https://dune.com/apis-and-connectors)
- [Substreams Arbitrum](https://substreams.dev/packages/uniswap-database-changes-tjar-arbitrum-one/v0.0.1)
- [Substreams Robinhood](https://substreams.dev/packages/uniswap-database-changes-tjar-robinhood/latest)

## Decisão

**B. Encerrar a linha para alocação e automação.** O lucro pontual realizado é verificável. O conjunto observado falha em demonstrar dez oportunidades causais semanais que durem 30 segundos, com US$1 líquidos e capital próprio até US$500. A ausência de estados históricos para replay, dados de falhas e a lacuna BNB delimitam a conclusão. Uma estimativa estática de margem positiva no bloco vencedor não abre um GO.
