# CRYPTO LAB — Diamante ou Ilusão V2

Auditoria adversarial de 21/10/2026. Research autónomo, sem ordens, capital, alterações a freezes ou acesso aos outcomes ETF Q4 2026.

**Resposta final: nenhuma das duas demonstra ainda uma vantagem economicamente explorável com perdas controladas. O ETF tem maior folga nominal para custos por trade. Isso não demonstra maior probabilidade de rentabilidade real: a incerteza é ampla, o crescimento composto a 1x é negativo no bloco observado e os custos nativos de financiamento estão incompletos. OPTIONS tem uma amostra maior, mas a execução a 8+8 bps observada nos receipts não suporta sequer a expectativa pontual de caixa antes de fricção adicional.**

## Decisão, com o âmbito de cada classificação

| Âmbito | ETF-CME-INSTFLOW-001 | OPTIONS-SPOTPERP-001-V2.1 |
|---|---|---|
| Regra científica e OOS originais | **FRAGILE**; Path2 histórico preservado | **FRAGILE**; Tier2 frágil histórico preservado |
| Execução económica nativa completa | **INSUFFICIENT**: carry, basis, short e fills não identificados | **INSUFFICIENT** para all-cost 2025 completo |
| Transferir taxa taker observada de 8+8 bps | Margem média pequena, crescimento e risco desfavoráveis | **NO-GO para esta rota**: expectativa pontual negativa antes de extras |
| SURVIVES com perdas controladas | **Não demonstrado** | **Não demonstrado** |

NO-GO da rota de custos não apaga o OOS nem afirma que o verdadeiro edge é estatisticamente zero. A classificação económica atual exige que a expectativa sobreviva aos custos da rota. Não transformámos stress20, diagnósticos de subgrupos ou critérios novos em vetos retroativos do freeze antigo.

## Fase 0 — prova recuperada e reconciliada

Li o relatório anterior, testei a integridade do ZIP e verifiquei as entradas do manifesto. As métricas-base foram reproduzidas:

| Família separada | N | Acerto líquido | Payoff | Expectativa bps/trade |
|---|---:|---:|---:|---:|
| ETF OOS 2025 | 49 | 48.98% | 1.101 | +11.636 |
| OPTIONS OOS 2025 | 363 | 47.11% | 1.200 | +5.043 |
| LICP SOL forward, apenas referência | 4 | 50,00% | 0,429 | −11,296 |

ETF: 49 posições direcionais, 50 oportunidades contando a semana flat. OPTIONS: 363 trades, exclusivamente BTCUSDT; o nome OPTIONS descreve a fonte do sinal, não operações em opções. LICP permanece separado, com quatro fechos sobrepostos, uma data completa e dois exits missing entre seis episódios. Não é amostra de confirmação de ETF/OPTIONS.

Foram lidos os freezes OOS, shadow e forward originais. O contrato ETF mantém a avaliação única após **01/01/2027 00:00 UTC**. Os novos preços de mercado lidos nesta auditoria são exclusivamente **2024–2025**. A leitura dos exports de 2026 limitou-se à auditoria de custos/cashflows das execuções conhecidas; não foi derivado nenhum outcome ETF de 2026.

## Comparação quantitativa principal

Preservam-se as unidades originais: ETF tem retorno simples semanal; OPTIONS tem retorno log assinado e ponderado diário. Cada intervalo abaixo é um diagnóstico bootstrap circular, 20.000 reamostragens, blocos de quatro, seed 20261021. Não é probabilidade posterior de existir edge.

| Regra / custo | Expectativa bps | IC 95% bps | PF | Acerto | Payoff | Perdas consecutivas máximas |
|---|---:|---|---:|---:|---:|---:|
| ETF / FROZEN_BASE10 | +11.636 | [-128.64; +138.83] | 1.057 | 48.98% | 1.101 | 5 |
| ETF / OBSERVED_TAKER16_TRANSFER | +5.636 | [-134.64; +132.83] | 1.027 | 46.94% | 1.161 | 5 |
| ETF / FROZEN_STRESS20 | +1.636 | [-138.64; +128.83] | 1.008 | 46.94% | 1.139 | 5 |
| OPTIONS / FROZEN_BASE10 | +5.043 | [-14.68; +25.45] | 1.069 | 47.11% | 1.200 | 7 |
| OPTIONS / OBSERVED_TAKER16_TRANSFER | -0.788 | [-20.52; +19.63] | 0.990 | 46.01% | 1.161 | 7 |
| OPTIONS / FROZEN_STRESS20 | -4.676 | [-24.42; +15.76] | 0.940 | 45.45% | 1.128 | 7 |

Blocos 1 e 8 também foram calculados e os intervalos continuam a incluir zero. O bootstrap não corrige descoberta prévia, seleção entre estratégias, não estacionariedade ou erros de execução. Nenhum intervalo é uma nova prova confirmatória.

## Contabilidade económica: não confundir média com crescimento

Reproduzimos sem alterações o runner antigo. Em paralelo, fizemos uma ponte de caixa identificada separadamente:

`retorno_caixa = peso × [lado × (P_saida/P_entrada − 1) − fee_entrada − fee_saida × P_saida/P_entrada − custo_extra]`

Fees incidem sobre o notional respetivo de entrada e saída. O capital é atualizado por `Eseguinte = Eanterior × (1 + retorno_caixa)`. Funding e basis nativos não observados não foram inventados; zero é uma hipótese explícita deste diagnóstico.

| Família / fees ida e volta | Crescimento composto de caixa | DD MTM fecho 1 minuto | DD marca adversa intraminuto |
|---|---:|---:|---:|
| ETF / 10 bps | -0.85% | -34.29% | -34.39% |
| ETF / 16 bps | -3.73% | -34.66% | -34.71% |
| ETF / 20 bps | -5.60% | -34.90% | -34.94% |
| OPTIONS / 10 bps | +6.79% | -33.04% | -33.09% |
| OPTIONS / 16 bps | -13.59% | -39.89% | -39.94% |
| OPTIONS / 20 bps | -24.97% | -44.08% | -44.12% |

**ETF BASE10:** a média aritmética positiva coexiste com crescimento composto de caixa de cerca de −0,85% no bloco. A dispersão dos retornos torna relevante o efeito de capitalização. Não há contradição com +5,70 pontos percentuais de soma aditiva do relatório anterior.

**OPTIONS BASE10:** os +20,09% do runner são `exp(soma(log-retornos assinados × peso − custo)) − 1`, não um ledger de caixa financiado. A ponte de caixa no mesmo caminho produz cerca de +6,79% antes de funding/basis. Aos 16 bps observados transferidos, passa a **−13,59%**. Não reclassificámos silenciosamente o resultado antigo nem apresentamos estes números como fills MEXC.

As marcas de 1 minuto vêm de Binance spot. O DD adverso usa low para long e high para short relativamente aos picos observados nos fechos; a ordem intraminuto dos extremos não é conhecida. Não é DD contínuo exato, liquidação, execução de stop ou mark nativo MEXC. Mesmo nesta aproximação, perdas de ~35–40% não demonstram controlo de perdas.

## Ataque ao ETF: distribuição, concentração e estabilidade

Os 49 trades completos, lado, peso, datas, preços, regime causal e retornos estão em `results/all_412_trades.csv`, filtrando apenas a coluna `family=ETF`. Nenhum trade foi eliminado da estimativa principal.

| Distribuição líquida BASE10 | ETF bps | OPTIONS bps |
|---|---:|---:|
| Mediana | -36.28 | -5.28 |
| Pior trade | -1019.86 | -802.27 |
| Melhor trade | +1161.51 | +900.65 |
| Percentil 5% | -885.87 | -311.25 |
| Percentil 95% | +909.91 | +362.03 |
| Média da cauda inferior 5% | -993.00 | -436.76 |

| Família BASE10 / melhores removidos | Contribuição para PnL positivo | Contribuição / PnL líquido total | Expectativa dos restantes bps |
|---|---:|---:|---:|
| ETF / 1 | 11.02% | 203.72% | -12.320 |
| ETF / 3 | 30.10% | 556.27% | -56.552 |
| ETF / 5 | 44.54% | 823.20% | -93.711 |
| OPTIONS / 1 | 3.18% | 49.20% | +2.569 |
| OPTIONS / 3 | 8.63% | 133.40% | -1.698 |
| OPTIONS / 5 | 12.99% | 200.78% | -5.153 |

A melhor operação ETF corresponde a **203,7% do lucro líquido total**; remover essa operação torna a média negativa. Em OPTIONS, remover uma mantém a média positiva; remover as três melhores torna-a negativa. Contribuição superior a 100% do net significa que perdas consumiram parte dos vencedores, não erro de denominador. Remoções são apenas diagnósticos de concentração, nunca novas regras.

Regimes definidos com informação anterior à entrada: close anterior vs SMA200 e RV20 anterior vs mediana expansiva de RV20, com aquecimento desde janeiro de 2024. Não são filtros. A definição do regime é nova e retrospectiva, sem crédito confirmatório. Todos os lados, regimes e interseções são publicados, incluindo os negativos:

| Família / grupo | Estado | N | Média canónica após 16 bps |
|---|---|---:|---:|
| ETF / side | -1 | 24 | +3.348 |
| ETF / side | 1 | 25 | +7.832 |
| ETF / trend | ABOVE_SMA200 | 36 | +31.612 |
| ETF / trend | BELOW_SMA200 | 13 | -66.299 |
| ETF / volatility | HIGH_RV20 | 13 | -57.134 |
| ETF / volatility | LOW_RV20 | 36 | +28.302 |
| OPTIONS / side | -1 | 273 | -4.277 |
| OPTIONS / side | 1 | 90 | +9.793 |
| OPTIONS / trend | ABOVE_SMA200 | 267 | +6.255 |
| OPTIONS / trend | BELOW_SMA200 | 96 | -20.378 |
| OPTIONS / volatility | HIGH_RV20 | 105 | -5.878 |
| OPTIONS / volatility | LOW_RV20 | 258 | +1.283 |

O ETF depende do contexto observado acima da SMA200 e de menor volatilidade; em tendência abaixo da SMA200 e volatilidade alta a média é negativa. OPTIONS também deteriora nesses estados; os shorts têm média negativa à taxa transferida. **Não há autorização para excluir shorts, crises ou regimes perdedores.** Trimestres e cruzamentos completos estão em `diagnostic_groups.csv`.

## Custos reais e limites de transferência

Os três exports oficiais locais (Trade History, Position History e Capital Flow) foram verificados por SHA256 e comparados linha a linha com a cópia previamente analisada. Para os seis trades atribuídos à execução alternativa OPTIONS, as identidades de gross, fees, funding e net coincidem com a reconciliação certificada.

- São **12 fills taker a 8 bps por lado**, não fees zero nem maker comprovado.
- As seis execuções têm média líquida de **−25,88 bps sobre notional de entrada**, com funding favorável médio de +1,115 bps. Amostra pequena, todos shorts, executada noutra implementação; não é a expectativa da estratégia spot em 2025.
- O histórico BTC do export contém **145 fills**: taxas taker variáveis entre 0 e 8 bps e 47 maker fills a zero em períodos anteriores. Não se atribuem todos estes fills à estratégia. A cronologia agregada está em `observed_fee_history.csv`.
- A cotação maker de 6 bps encontrada nos receipts não prova fill maker. Maker a zero cobrado noutras datas também não prova elegibilidade atual.
- O endpoint público de contrato observado em 21/10/2026 indica defaults maker 0 e taker 2 bps. A própria MEXC remete para o histórico real e avisa que taxas podem variar por evento/região. **O default público não substitui a taxa da conta/rota.**

Não temos uma série fiável, específica da rota/conta e contemporânea de **fees, spread, slippage, basis e funding de cada um dos 363 trades de 2025**. Portanto, a expectativa all-cost histórica real é **não identificada**. A matriz de 16 bps é transferência contrafactual de uma taxa real observada em 2026, não custos efetivamente realizados em 2025.

| Limite de custos totais a notional completo | ETF semanal | OPTIONS diário |
|---|---:|---:|
| Break-even no modelo original | 21.636 bps | 15.189 bps |
| Break-even na ponte de caixa, fees simétricas | 21.633 bps | 14.104 bps |
| Fees taker observadas, apenas transferência | 16 bps | 16 bps |

O limite é partilhado por fees, spread, slippage e financiamento; não é orçamento separado para cada rubrica. Depois de 16 bps, ETF conserva só ~5,63 bps por semana, ou ~0,80 bps/dia para todo o carry e fricção remanescentes. Com mais 2 bps de fricção, sobram ~0,52 bps/dia. OPTIONS já está negativo antes de extras. Funding credit dos seis shorts não pode ser extrapolado para os 273 shorts e 90 longs de 2025.

Cenários de maker, todos sem garantia de fill, na ponte de caixa e antes de spread/slippage/funding:

| Execução / fees por lado | ETF bps/trade | OPTIONS bps/trade |
|---|---:|---:|
| Maker/maker cotado, 6+6 | +9.634 | +2.045 |
| Maker/taker cotado, 6+8 | +7.633 | +0.101 |
| Taker/taker observado, 8+8 | +5.633 | -1.843 |
| Default público, 0+2 não certificado | +19.635 | +11.764 |

Em OPTIONS, a média de maker/taker a 6+8 é apenas +0,10 bps antes de todos os extras. Maker/maker a 6+6 tem +2,04 bps, também sem prova de probabilidade de fill ou adverse selection. Não é fundamento para afirmar que colocar limites torna a estratégia rentável. A matriz completa inclui custos adicionais de 0/1/2/5/10 bps.

## Atrasos de execução, sem escolher o melhor atraso

Perturbámos os preços de entrada e/ou saída para a abertura da barra Binance de 1/5/15/60 minutos após o horário original. Mantivemos sinais e pesos. São proxies de preço, sem BBO ou profundidade históricos MEXC; não certificam latência real. O caso de ambos atrasados preserva o horizonte; os casos de um só lado encurtam/alongam o hold apenas como diagnóstico.

| Atraso em ambos os lados | ETF, caixa após 8+8 bps | OPTIONS, caixa após 8+8 bps |
|---|---:|---:|
| 0 min | +5.633 | -1.843 |
| 1 min | +5.474 | -1.831 |
| 5 min | +3.187 | -1.962 |
| 15 min | +0.636 | -1.995 |
| 60 min | -1.017 | -2.859 |

Não existe resgate por atraso: os cinco resultados são apresentados e nenhuma variante é promovida. Em particular, uma hora de atraso torna também a média ETF negativa no cenário de fees transferidas.

## Sequências de perdas e incerteza

A probabilidade de pelo menos uma sequência de k perdas foi calculada por programação dinâmica sob Bernoulli IID estacionário, com taxa de perda estimada da própria amostra. O segundo modelo reamostra blocos circulares de quatro trades, preservando parte da dependência de curto prazo. Ambos são condicionais à amostra, não previsões nem probabilidades do verdadeiro edge.

| Caixa com 8+8 bps, no respetivo bloco OOS | ETF: 49 trades semanais | OPTIONS: 363 trades diários |
|---|---:|---:|
| Fração bootstrap com perda terminal | 53.21% | 65.61% |
| Fração com >=5 perdas seguidas | 50.41% | 99.59% |
| Fração com >=10 perdas seguidas | 1.77% | 8.41% |
| Fração com DD de fechos pior que 20% | 80.16% | 96.38% |

Os IC 95% da expectativa de caixa aos 8+8 bps, blocos de quatro, são: ETF [-134.53; +132.85] bps; OPTIONS [-21.61; +18.56] bps. São demasiado amplos para alegar um edge robusto.

Uma aproximação de potência normal IID, a 5% unilateral e 80% de potência, precisaria de **~10.829 trades OPTIONS** para distinguir um edge de 5 bps usando a dispersão observada. Dependência e incerteza dos custos pioram a situação. Não é um plano de esperar 30 anos nem estimativa exata, mas demonstra que 20/50 operações adicionais não provam uma vantagem tão pequena. Um piloto curto pode falsificar execução cara, não confirmar lucro sustentável.

## Capital de 100, 250, 500 e 1.000 USDT

O contrato público atual é 0,0001 BTC, mínimo um contrato e passo um contrato; minLeverage indicado 1. Aplicámos apenas estas quantizações às entradas históricas de 2025. Não consultámos preço atual, margin da conta ou ticker. Os mínimos atuais podem ser diferentes dos de 2025 e não certificam elegibilidade da conta, minNotional não publicado ou capacidade de short.

A simulação abaixo usa exposição máxima de 1x, fees 8+8 bps, mais 2 bps de fricção, funding zero explicitamente desconhecido. Arredonda sempre para baixo e reserva fees; não usa alavancagem para contornar o mínimo. É uma nova ponte operacional de sizing, não o OOS congelado nem uma previsão:

| Capital inicial USDT | PnL ETF simulado | PnL OPTIONS simulado |
|---|---:|---:|
| 100 | -4.86 USDT | -18.37 USDT |
| 250 | -11.66 USDT | -48.08 USDT |
| 500 | -22.22 USDT | -96.67 USDT |
| 1000 | -48.86 USDT | -194.75 USDT |

O mínimo de contrato permite discretização nestes capitais neste replay; isso é apenas compatibilidade aritmética. Com 100 USDT, um contrato já representa vários pontos percentuais de exposição e a quantização altera o peso. Aumentar capital reduz erros relativos de lotes, mas não corrige expectativa negativa. Reduzir risco depois de ver o resultado não foi usado para fabricar uma curva vencedora. Sem orçamento de perda fornecido e sem prova de stop/financiamento executável, não afirmamos perdas controladas.

## Bloqueios concretos

1. Não há custos all-cost, basis e financiamento nativos MEXC 2025 trade a trade; é impossível certificar expectativa histórica realmente realizável.
2. A taxa atual específica da conta/rota não foi consultada. Históricos e default público divergem; a cotação geral não resolve a divergência.
3. Não há histórico BBO/L2 da MEXC correspondente às 363 entradas/saídas para medir spread, profundidade e adverse selection. Atrasos Binance não substituem isso.
4. Fills maker, posição na fila, probabilidade de não execução e impacto na seleção dos trades são desconhecidos.
5. Os seis trades reais pertencem a uma execução alternativa em futuros, com scientific credit falso; não se transferem as conclusões para o pai spot.
6. Ambos os IC incluem zero; concentração, regimes e DD não satisfazem prova de robustez. Nenhuma triagem técnica é prova de rentabilidade.
7. A cobertura forward completa de OPTIONS sob o banco original não foi reconstituída aqui. Não há nova promoção por misturar os seis receipts com o OOS.
8. ETF Q4 2026 permanece inacessível até à data congelada; não é um bloqueio a contornar.

## Próxima experiência independente mais eficiente

**Primeiro resolver custos, sem arriscar capital.** Se a rota continua a cobrar 8+8 bps, não há fundamento económico para ativar OPTIONS nessa rota com base nesta evidência. Verificar a taxa específica da rota por comprovativo datado e certificar custos executáveis é mais barato e informativo do que acumular resultados simulados assumindo maker gratuito.

Ficou gravado `PROSPECTIVE_EXECUTION_PROTOCOL.json`, uma **nova hipótese condicional de execução de baixo custo**, separada do pai e não ativada. O limite de 8 bps all-cost é um novo orçamento prospectivo que deixa margem; não é um critério antigo reduzido. A condição inicial ainda **não está satisfeita**.

Se existir rota barata comprovável, o protocolo mantém sinal/lado/horizonte/peso originais e recolhe shadow de profundidade por capital, contabilizando todos os intents, missing e custos. Maker fica secundário e sem crédito de fill garantido. Os primeiros 20 servem apenas para custos/execução. A avaliação económica é única, após 365 sinais elegíveis ou cutoff fixo, sem extensão após conhecer perdas. Para preservar o firewall ETF, o novo bloco de preços só pode começar em **02/01/2027**. Não se iniciou recolha, monitor, bot ou automação.

Os critérios novos exigem média de caixa com limite inferior positivo, PF>1, DD MTM <=10% sem rescaling retroativo e concentração controlada. São difíceis e podem falhar; 365 trades não garantem potência para um edge de 5 bps. O primeiro50 gate original permanece independente e não pode receber crédito deste fork. Para ETF, a próxima experiência legítima já existe: aguardar o termo e aplicar exatamente o contrato Q4 2026 uma única vez.

## Provas, reprodução e âmbito

- `validation.json`: 1252 verificações numéricas de reconciliação, timestamps, preços diário/minuto e identidades. Não são provas de lucro.
- `phase0_zip_validation.json`: hash do ZIP original e verificação de todos os ficheiros do manifesto.
- `source_manifest.json`: 36 arquivos oficiais Binance, de 2024–2025, com hashes e checksums. Zero preço de mercado de 2026 solicitado.
- `data/observed_costs.json`: evidência agregada de custos com hashes dos exports. UID, identificadores da conta e exports brutos não são publicados.
- `ANALYSIS_PLAN.json`: decisões fixadas antes de produzir os novos diagnósticos; não é preregistração independente de outcomes já conhecidos.
- `analyze.py`: reconstrói distribuição, custos, regimes, delays, MTM, capital e probabilidades condicionais. `extra_diagnostics.py`: IC de caixa e cronologia agregada de fees. `requirements.txt`: ambiente.
- `acquire_sources.py`: obtém exclusivamente os arquivos permitidos e verifica hashes; preserva a especificação de contrato datada. Depois executar `python analyze.py` e `python extra_diagnostics.py` nesta pasta. Os exports privados são opcionais apenas para repetir a auditoria de custos da conta; a ausência não transforma missing em zero.

Fontes principais:

- [ETF OOS e source gate](https://github.com/joseluisvieira28-oss/Laboratorio/actions/runs/34815006815)
- [OPTIONS V2.1 OOS](https://github.com/joseluisvieira28-oss/Laboratorio/actions/runs/35231711508)
- [Auditoria de contabilidade MEXC, commit original](https://github.com/joseluisvieira28-oss/Laboratorio/blob/c99f99bb6965b93c961d8b4f8878e021d846b015/audits/MEXC_OPTIONS_ACCOUNTING_2026-10-12.md)
- [MEXC fees: consultar histórico real; taxas variáveis](https://www.mexc.com/fee)
- [MEXC: especificação do contrato](https://mexcdevelop.github.io/apidocs/contract_v1_en/#get-the-contract-information)
- [Binance public data: formato, timestamps e checksums](https://github.com/binance/binance-public-data)

O snapshot inicial de main é `75fb36c8337c3221b7551c513e049cd472dad231`. A entrega remota usa exclusivamente uma branch de auditoria e caminhos `research/diamond_illusion_v2_20261021/`, com CI omitido no commit. Nenhum freeze antigo, executor, ordem ou wallet foi alterado.

**Veredito:** o ETF tem maior folga teórica de custos, mas ainda não uma probabilidade demonstrável de lucro com risco controlado. OPTIONS é mais fácil de falsificar economicamente e a rota taker observada deve ser descartada para deployment com a evidência atual. Nenhuma merece SURVIVES. Custos comprovadamente inferiores e nova validação independente seriam necessários; maker presumido, capital maior e tuning de regimes não resolvem as falhas.
