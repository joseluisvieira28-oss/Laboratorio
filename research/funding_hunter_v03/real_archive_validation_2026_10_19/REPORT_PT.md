# CRYPTO LAB — FUNDING HUNTER V03: arquivos reais OKX validados

Data da auditoria: 2026-10-19. Antecessor: draft PR #254, commit a8744dbd81e7ecadf6b86860610757a3c80c37a8.

**Veredito técnico: REAL_2025_TWO_BOOKS_RECONSTRUCTED_QUOTE_ONLY.** Os dois arquivos privados do operador foram efetivamente lidos neste Windows, reconstruídos e validados até EOF. Os seis pontos congelados passaram: 400 BID + 400 ASK, sem cruzamento, idade <=2.000 ms, usando apenas eventos com timestamp <= horário-alvo.

**Veredito científico: ECONOMIC_EDGE_UNPROVEN / NO_LIVE_GO.** Estes resultados são observações históricas de livro, não negócios executados, rentabilidade de funding ou evidência independente de arbitragem.

## Protocolo e correções técnicas

O congelamento original permanece em `research/funding_hunter_v03/BEFORE_TWO_UPLOADED_2025_BTC_BOOKS_QUOTE_ONLY_FREEZE.md`, commit 53f2a66: 2025-06-02 00:05, 12:05, 23:55 UTC; nearest-past incluindo igualdade; 400 níveis por lado; idade máxima 2s. Nenhum horário, tolerância, instrumento ou gate foi ajustado depois de observar preços.

O bloqueio anterior era de runtime, antes da primeira leitura; não era prova de arquivos corrompidos. O leitor original já conseguiu obter as seis cotações neste ambiente. A inspeção real confirmou o esquema congelado `{instId,action,ts,asks,bids}`, níveis de três campos `[preço,quantidade_em_contratos,número_de_ordens]` e timestamps Unix em milissegundos. Não foi necessário adaptar o formato depois de ver preços.

A correção faz a leitura continuar depois da terceira amostra, valida a cronologia e o livro até o fim, exige um único membro TAR regular com nome exato, limita cada readline, calcula SHA256 do membro e drena GzipFile até EOF para validar CRC32/ISIZE. O TAR em modo streaming sozinho podia terminar antes de validar o trailer gzip. Contadores agora descrevem o dia inteiro; timestamps iguais são mantidos na ordem original; quantidade zero remove o nível. O campo enganador `outcomes_opened=false` foi substituído por `historical_quote_outcomes_opened=true` e `funding_outcomes_opened=false`.

## Custódia e integridade

Os SHA256 identificam os bytes locais, não são assinaturas ou digests publicados pela OKX. O nome e esquema são compatíveis com os arquivos oficiais fornecidos pelo operador; não houve download independente de uma segunda cópia para provar identidade com o servidor. Nenhum arquivo bruto nem linha L2 reconstruída foi enviado ao GitHub. Somente agregados, código, testes e hashes são publicados.

| Instrumento | Bytes gzip | Bytes .data | SHA256 gzip |
|---|---:|---:|---|
| BTC-USD-SWAP | 214247097 | 1879768143 | `4e740e424314f3a4904118af3facc02bf36956614e11e86e780a8dc9f90f9f7e` |
| BTC-USDT-SWAP | 478721192 | 3311518571 | `b9e5405d89ce84cbe6d76fa1238e55e8858e18bec5dd5a0dc11c816860b305d1` |

SHA256 dos membros descomprimidos:

- BTC-USD-SWAP.data: `85035ec5624432252232d50df09050b72456e0af87ad3b94f85f1ace3754371a`
- BTC-USDT-SWAP.data: `226976940c5e6f85cdf235a15b4b560f50fd75b4581c15a7edb7ecdb61fdf659`

## Cobertura observada do dia

| Instrumento | Primeiro evento UTC | Último evento UTC | Eventos | Snapshots | Updates | Maior intervalo ms | Iguais adjacentes | Exclusões q=0 |
|---|---|---|---:|---:|---:|---:|---:|---:|
| BTC-USD-SWAP | 2025-06-02T00:00:00.008+00:00 | 2025-06-02T23:59:59.998+00:00 | 5407466 | 1440 | 5406026 | 660 | 0 | 21498888 |
| BTC-USDT-SWAP | 2025-06-02T00:00:00.004+00:00 | 2025-06-02T23:59:59.997+00:00 | 7630944 | 1440 | 7629504 | 828 | 0 | 25134169 |

Cobertura dos probes: **6/6 (100% dos pontos previamente fixados)**. Zero livros cruzados encontrados no processamento de eventos. Não há seqId/prevSeqId/checksum nos campos destes registros; SHA/CRC e cronologia não provam ausência de mensagens perdidas antes da publicação. Não se afirma cobertura lossless, cobertura anual ou 100% do tempo negociável. O maior intervalo mede eventos adjacentes observados, não uma falha comprovada.

## BID/ASK observados e profundidade bruta

Preços lineares em USDT/BTC; inversos em USD/BTC. Quantidades abaixo são contratos nativos, sem comparação direta entre instrumentos. Spread = 10.000 × (ASK−BID)/mid. O JSON também preserva a definição legada 10.000 × (ASK/BID−1), com denominador BID.

| Instrumento | UTC | Último evento UTC | Idade ms | BID | ASK | Spread bps | Q BID topo | Q ASK topo | Q BID 400 níveis | Q ASK 400 níveis |
|---|---|---|---:|---:|---:|---:|---:|---:|---:|---:|
| BTC-USD-SWAP | 00:05 | 2025-06-02T00:04:59.998+00:00 | 2 | 105643.2 | 105643.3 | 0.00946582 | 2036.00 | 865.00 | 234171.00 | 115918.00 |
| BTC-USD-SWAP | 12:05 | 2025-06-02T12:05:00.000+00:00 | 0 | 104034.1 | 104034.2 | 0.00961223 | 180.00 | 995.00 | 104280.00 | 131479.00 |
| BTC-USD-SWAP | 23:55 | 2025-06-02T23:54:59.998+00:00 | 2 | 105872.8 | 105872.9 | 0.00944529 | 791.00 | 1948.00 | 151769.00 | 133735.00 |
| BTC-USDT-SWAP | 00:05 | 2025-06-02T00:04:59.994+00:00 | 6 | 105588.6 | 105588.7 | 0.00947071 | 235.77 | 530.17 | 14052.47 | 16117.23 |
| BTC-USDT-SWAP | 12:05 | 2025-06-02T12:04:59.997+00:00 | 3 | 103990.8 | 103990.9 | 0.00961623 | 652.69 | 1294.69 | 18044.60 | 17253.84 |
| BTC-USDT-SWAP | 23:55 | 2025-06-02T23:54:59.997+00:00 | 3 | 105815.2 | 105815.3 | 0.00945043 | 1406.01 | 191.16 | 14076.90 | 13529.71 |

O receipt JSON inclui ainda o preço mais distante de cada lado dos 400 níveis. Os livros completos são reconstruídos em memória a partir do snapshot e dos incrementais; não são publicados nem persistidos como linhas L2.

## Comparação entre instrumentos

| UTC | Mid linear USDT | Mid inverso USD | Prêmio numérico inverso/linear bps | Diferença temporal entre eventos ms |
|---|---:|---:|---:|---:|
| 00:05 | 105588.65 | 105643.25 | 5.17101033 | 4 |
| 12:05 | 103990.85 | 104034.15 | 4.16382788 | 3 |
| 23:55 | 105815.25 | 105872.85 | 5.44344979 | 1 |

Esta razão usa duas moedas diferentes: não foi corrigida por USD/USDT contemporâneo. Os livros são alinhados causalmente ao mesmo relógio, mas seus últimos eventos não são simultâneos. Não se toma essa diferença como lucro disponível.

## Unidades contratuais: o que está e não está comprovado

A [documentação oficial da API](https://www.okx.com/docs-v5/en/) identifica quantidades de derivativos em contratos; o terceiro campo do arquivo é contagem de ordens, não BTC nem USD. As próprias fontes históricas aqui lidas não contêm ctVal, ctValCcy, lotSz, minSz ou tickSz.

O [anúncio oficial de 17/01/2025](https://www.okx.com/en-sg/help/okx-to-adjust-the-minimum-order-quantities-of-spots-and-futures), com alteração prevista para 22/01/2025, relaciona BTC/USDT perpetual: lote/mínimo 0,01 contrato = 0,0001 BTC, implicando face de 0,01 BTC/contrato. É evidência documental anterior ao dia estudado e explica as quantidades fracionárias observadas. O [anúncio anterior de abril de 2024](https://www.okx.com/en-au/help/okx-to-adjust-the-minimum-order-quantities-for-several-futures-24-04-19) tinha lote 0,1 contrato; usar essa regra mais antiga sem atualização seria incorreto.

A [explicação oficial dos contratos](https://www.okx.com/en-us/help/what-is-the-difference-between-contracts), publicada em 2023 mas atualizada em agosto de 2026, descreve BTCUSD com face de 100 USD e liquidação/colateral em BTC, e BTCUSDT linear em USDT. A revisão posterior **não comprova**, por si só, os parâmetros exatos vigentes em 02/06/2025. Não se abriu conteúdo de preços/funding do holdout 2026; datas 2026 nestas páginas são revisões documentais.

Conclusão: unidade nativa validada; prova histórica parcial para o linear; conjunto completo de face/lote/tick de ambos em 02/06/2025 ainda não certificado. A ausência de mudanças intermediárias também não foi provada. Pelo gate congelado, não convertemos profundidade em BTC/USD, não certificamos tamanho de 1 BTC e não calculamos VWAP/impacto monetário. A precisão observada de 0,1 no preço não é prova independente de tick contratual. Fórmulas documentais: linear BTC = contratos × ctVal; inverso USD nominal = contratos × ctVal e equivalente BTC depende do preço. Não aplicadas aqui como execução histórica verificada.

## Custos possíveis: observação versus hipótese

Cada spread acima é observado. Se um tamanho já validado coubesse integralmente no topo e o livro ficasse imóvel, comprar no ASK e vender no BID no mesmo instante produziria um custo bruto de spread de aproximadamente 0,0094–0,0096 bps do mid por instrumento. Isso é apenas a diferença algébrica entre cotações, **não um preenchimento**. A entrada de uma perna custa aproximadamente meio spread em relação ao mid; um roundtrip imóvel custa o spread completo. Para dois roundtrips de pernas com mesmo notional normalizado, o componente estático seria s_linear+s_inverso, ao qual se somariam quatro taxas taker, impacto e outros custos. Não é o custo medido de uma operação de 24 horas; o spread da saída futura é desconhecido.

Sem quantidade e lote historicamente certificados para ambos, não se calcula execução por varredura, slippage ou VWAP. Nenhuma taxa de conta privada foi consultada e nenhuma taxa atual foi tratada como taxa histórica. A [FAQ oficial de taxas](https://www.okx.com/en-gb/help/trading-fee-rules-faq) explica cobrança linear em USDT e inversa em cripto; exemplos de tarifas nessa página não certificam a tarifa aplicável ao operador em 2025. Os pressupostos anteriores de custos do V01 não foram recalibrados para baixo a partir destes spreads. Seus pisos de 30/50 bps sobre o notional de uma perna pertencem à configuração MEXC/Binance; não são tarifas históricas nem estimativas certificadas desta dupla OKX. Maker sem fila, preenchimento ou rebate comprovado não foi presumido.

Permanecem desconhecidos: quatro comissões efetivas de abertura/fecho, latência e cancelamentos entre observação e ordem, posição na fila maker, liquidez oculta, impacto de mercado, funding e marcas de liquidação exatos, FX USD/USDT, financiamento do colateral BTC, requisitos de margem e rebalanceamento da exposição inversa. Profundidade pública observada não é garantia de disponibilidade quando uma ordem hipotética chega.

## Testes e reprodução

- 14/14 testes sintéticos locais PASS: clocks congelados, nearest-past e igualdade, idade, símbolos, primeiro snapshot, cruzamento, exclusão por zero, identidade de arquivo, erro posterior ao terceiro probe, contagem de ordens inválida, TAR extra, CRC corrompido e gzip truncado.
- O primeiro comando de testes falhou por permissão do diretório temporário padrão do sandbox. Reexecutado com TEMP/TMP apontando para work/ autorizado: PASS; não houve relaxamento de asserções.
- Replay real integral: ambos os arquivos originais, todos os eventos, CRC/ISIZE até EOF, um único membro TAR, tamanho e SHA do membro. Resultado no receipt sanitizado.
- Leitor independente sem importar o principal, usando Decimal para preços/quantidades: 6/6 timestamps, BID/ASK, tamanhos de topo e somas de ambos os lados reconciliados; tolerância de agregação float <= max(1e-8, |valor|×1e-12). O JSON Decimal preserva somas exatas.
- As seis amostras do leitor original e do corrigido coincidem em todos os campos comuns. A mudança de contadores decorre de processar o resto do dia, não de recalcular horários.
- git diff --check: PASS. Testes executados localmente em Windows; não se reivindica nova validação Linux/CI nesta continuação.

Reprodução local (Python 3, sem dependências obrigatórias e sem rede):

```text
python -m unittest research.funding_hunter_v03.test_dual_btc_400l2_private_replay -v
python -m research.funding_hunter_v03.dual_btc_400l2_private_replay --linear <Downloads>/BTC-USDT-SWAP-L2orderbook-400lv-2025-06-02.tar.gz --inverse <Downloads>/BTC-USD-SWAP-L2orderbook-400lv-2025-06-02.tar.gz --out <local>/V03_full_archive_receipt.json
python -m research.funding_hunter_v03.verify_real_receipt_decimal --receipt <local>/V03_full_archive_receipt.json --archive-dir <Downloads> --out <local>/V03_decimal_crosscheck.json
```

No Windows sandbox deste operador, definir TEMP e TMP para um diretório gravável em work/ antes dos testes. Os arquivos brutos devem ficar em Downloads, fora do repositório.

## Limite científico e encerramento

O bloqueio de leitura real foi resolvido; a fonte local e os seis livros foram comprovados nos limites descritos. Não há teste de rentabilidade de funding neste V03. O terceiro horário 23:55 é diagnóstico; o fecho de 24h do protocolo original exigiria **03/06/2025 00:05**, ausente dos dois arquivos. Um dia e três probes não fornecem frequência, estabilidade, PnL líquido, amostra anual ou OOS independente.

Não se abriram resultados de funding, contas privadas, chaves, ordens ou holdout protegido 2026. Não houve compra de dados, instalação de serviços, dinheiro gasto ou mudança/merge em main. Este trabalho permanece em branch de investigação e draft PR sobre o branch V03 anterior. Novos dados e especificações históricos podem remover os bloqueios restantes, mas os resultados vistos não autorizam retunar ou promover uma estratégia.
