# SOL CONVEX 4h — validação prospetiva: veredito de viabilidade

20/10/2026. **INCONCLUSIVO quanto a vantagem líquida independente. Não compensa iniciar um coletor dedicado para prometer validação em meses.** Protocolo concreto congelado; investigação económica NÃO ATIVADA. A hipótese não foi rejeitada por ter poucos acertos nem por depender de grandes vencedores.

## O que foi confirmado

PR265 lido no commit `1bb31ac1a93580060a698340de856d987a7d62b7`. Reexecutado o seu script sobre os 14 ledgers originais BASE/STRESS: o blob Git do `metrics.json` reproduzido é exatamente `28ea317c9dab3955cae708d599faddc761269320`, igual ao publicado. Cinco ZIPs producer conferem com digests GitHub; RESULTs conferem com masters. Não foi feito novo backtest, seleção de thresholds nem leitura de outcomes protegidos.

| Histórico já conhecido, 2023–25 | SOL4h principal | BNB30m secundário |
|---|---:|---:|
| Trades fechados | 44 | 51 |
| Frequência aproximada / ano | 14,67 | 17,00 |
| Acertos BASE | 25,00% | 31,37% |
| Ganho/perda médio em R | 6,62 | 3,61 |
| Média líquida BASE em R/trade | +0,9575 | +0,4586 |
| Desvio padrão amostral em R | 4,7972 | 2,5934 |
| Retorno terminal BASE / STRESS | +35,90% / +35,42% | +19,67% / +18,17% |

Esses resultados incluem fees/slippage e funding PROXY do modelo, não custos reais completos. A seleção destas duas lanes foi feita depois de observar os resultados. Não há OOS independente aqui. Os cálculos da auditoria estão reproduzidos; os seus pressupostos de execução não ficam validados por isso.

## Quanto tempo uma resposta económica poderá exigir

Cálculos de planeamento Gaussianos IID, usando a dispersão e frequência do histórico selecionado. Não são um prazo garantido nem demonstração formal do tamanho suficiente; dependência e caudas podem piorá-los. Não reamostrar o passado como se fossem novos trades.

| Objetivo de planeamento | SOL4h: N / anos à frequência antiga | BNB30m: N / anos |
|---|---:|---:|
| Detetar a média histórica contra zero, potência80%, teste bilateral5% | 198 / 13,5 | 252 / 14,8 |
| Detetar metade dessa média contra zero | 789 / 53,8 | 1005 / 59,1 |
| IC95% com margem ±0,50R | 354 / 24,1 | 104 / 6,1 |
| IC95% com margem ±0,25R | 1415 / 96,5 | 414 / 24,4 |

Fórmulas: N_precisão=ceil((1,96×s/h)^2); N_potência=ceil(((1,96+0,8416)×s/(mu−mu0))^2). Para testar o SOL histórico contra uma vantagem material de +0,25R, em vez de zero, o planeamento sobe a361 trades (~24,6 anos). Um fator de dependência2 duplicaria os N de precisão. A incerteza IID estimada para apenas um ano SOL já seria cerca de ±2,46R, superior à própria média histórica +0,96R.

Porquê tolerância0,25R: ao sizing original, 1R nominal corresponde a0,8% do equity. Com ~14,7 trades/ano, 0,25R corresponde aproximadamente a2,93 pontos percentuais anuais de equity. Uma incerteza maior torna difícil distinguir uma remuneração modesta de uma remuneração economicamente irrelevante. É uma tolerância declarada de decisão, não um requisito pessoal de retorno nem um número escolhido para passar.

**O custo relevante é o tempo, mesmo que APIs sejam gratuitas.** Um ano de observação pode revelar defeitos operacionais ou perdas; não se deve prometer que certificará lucro. Não juntamos BNB, outros TFs ou mais alertas ao denominador SOL para fabricar potência.

## Freeze publicada antes da nova consulta pública

`FREEZE_V1.md`, primeira autoridade commit **f8eb19fa58c2a1d6e73cbbc204aaeeeadb38e61b**, Git timestamp **2026-10-20T13:55:28Z**. Primeiro pedido do probe **13:55:30.976Z**. SHA256 da freeze **a99bd2f14320e9d7de619faf35c13c8ca09446b59e80f3de7fd154c45161f2d5**, ligado ao receipt. Não se alterou a freeze depois das respostas.

A freeze fixa blobs do sinal/V11, entrada C+300s, LONG, stop−4%, ativação+5%, trail12% NONLATCHED original, sizing20%-equity, uma posição por símbolo/lane, contratos arredondados para baixo, gaps, dados ausentes, censura, BASE/STRESS, método estatístico e regras de decisão/recursos. BNB é comparação descritiva, não hipótese com promoção automática. O stop que pode afrouxar foi preservado como problema de implementação, não corrigido mudando ciência.

A data condicional de source start é21/10/2026 00:00Z; proteger 2026 impede carregar prehistória arbitrária. O feed V11 original exige12 576 barras5m; só com dados futuros o primeiro fecho SOL elegível seria03/12/2026 16:00Z. Isto é fidelidade ao buffer original, não um atraso novo de rentabilidade. Deadline absoluto21/10/2027 00:00Z, checkpoint de fontes ao dia90. **Nenhuma dessas datas significa que haja um coletor ativo.** O gate de viabilidade já falhou antes da ativação; não se abre uma espera de um ano disfarçada de experiência em curso. Uma futura reabertura precisaria de uma razão económica nova e freeze separada, sem herdar resultados observados como frescos.

Critério de candidato é exigente e explícito: evidência independente, custos/execução/acesso e caudas verificáveis, amostra efetiva/precisão suficientes, limite inferior95% BASE e STRESS acima de+0,25R. Os1 415 closes independentes-equivalentes decorrem do cálculo de precisão, não de uma meta redonda. Retirar grandes vencedores é só diagnóstico. No prazo máximo, dados insuficientes fecham como INCONCLUSIVO; não se baixa o gate nem se prolonga indefinidamente.

## Execução: documentação, observações e desconhecidos

Foram lidas fontes oficiais listadas em `evidence/OFFICIAL_SOURCES.json`; cada facto documental está separado do probe real.

| Elemento | Evidência disponível | Limite que impede certificar líquido |
|---|---|---|
| Instrumento | Estudo Binance USD-M; alvo MEXC USDT perpetual SOL/BNB | Bolsas/contratos distintos; basis, funding e triggers não equivalentes por pressuposto |
| Entrada | Original só permite candle fechada, witness>=1s, entrada5m depois | Nenhum sinal/quote elegível novo observado; preço executável depois do sinal desconhecido |
| Bid/ask/profundidade | API documenta livro com timestamp/version e volumes em contratos | Nenhum livro JSON utilizável neste probe; VWAP para20/200/2000USDT e mínimo=null |
| Contrato/rounding | Schema atual inclui contractSize,minVol,volUnit,priceUnit,maxVol e limitações | Nenhuma especificação SOL/BNB atual certificada neste ambiente; não usar exemplos da documentação como dados reais |
| Latência | Receipt mede RTT dos pedidos, incluindo erros | Isto não mede C→deteção→entrada, nem latência de broker; pares de quotes sincronizados inexistentes |
| Fees | Tabela oficial API efetiva01/06/2026: taker0,08%/lado; sem descontos | A conta não foi consultada. Exemplo antigo no próprio anúncio diverge da tabela; prevalece a tabela efetiva. Taxa aplicável atual continua condicionada à publicação e pode mudar |
| Funding | Oficial: valor liquidado usa fairPrice do settlement | History schema não fornece esse fairPrice; rate atual não é cashflow liquidado. Nada substituído por zero ou Binance open |
| Stops | FAQ oficial admite slippage de market stops e não-fill de limit stops | Não existe ACK nativo, trigger path ou preço de saída real; stops/gaps não garantem1R |
| Acesso suíço | Suíça ausente da lista nominal proibida nos termos atualizados13/10/2026 | Lista não exclusiva e restrições de produto/API podem aplicar-se; plausível, não certificado por conta ou parecer legal |

Fontes principais: [fees API](https://www.mexc.com/announcements/article/updates-to-api-futures-trading-fees-jun-1-2026-17827791535742), [contratos](https://www.mexc.com/api-docs/futures/market-endpoints/get-contract-info), [livro](https://www.mexc.com/api-docs/futures/market-endpoints/get-contract-order-book-depth), [funding history](https://www.mexc.io/api-docs/futures/market-endpoints/get-funding-rate-history), [cálculo de funding/PNL](https://www.mexc.co/support/article/mexc-futures-calculation-guide-312060306409668608), [stops](https://www.mexc.co/support/article/mexc-futures-take-profit-and-stop-loss-faq-350096811661177856), [termos](https://www.mexc.com/terms). Não foi usado produto pago de guaranteed SL; a própria FAQ desse produto também admite falhas de triggering/execução em exceções.

## Resultado real do source gate

Um único probe,17 GET públicos allowlisted, entre **13:55:30.976 e13:56:28.216UTC de20/10/2026**:

- **0/17 JSON utilizáveis**;7 respostas HTTP200 eram HTML “Site Unavailable”, não dados de mercado.
-8 timeouts e2 HTTP451 da Binance. Sem repetir requests nem aumentar orçamento para produzir um PASS.
-0 especificações atuais certificadas,0 quotes executáveis,0 medições de slippage/basis,0 funding settlements,0 posições/PnL prospetivos.

Classificação: **SOURCE_BLOCKED_THIS_RUNTIME**. Não se conclui que MEXC/Binance estejam globalmente indisponíveis, nem que a estratégia falhe economicamente. Uma resposta HTTP200 sem JSON não é SOURCE_PASS. Bytes devolvidos, content types, SHA256 e timestamps são preservados em `evidence/source_probe_v1/`.

**Recolha real:** terminou apenas esta verificação de fontes. Existe um script one-shot de source probing, não um coletor económico preparado. Nenhum daemon, cron, automation, Windows task ou GitHub scheduler novo. Não existe acompanhamento contínuo nem promessa de aviso. As restantes canas e alertas não foram alterados.

## Capital e sobrevivência

1R=.04×notional. Na referência10k/20% exposição, 1R nominal=80USDT e risco nominal0,8% do equity antes de custos. Margem aritmética a10× seria200USDT para2k exposição, mas uma queda10% já representa200USDT de perda de preço; margem não limita perda a80USDT nem prova distância à liquidação. Esta validação não muda a referência para10×.

Cenários ilustrativos sem probabilidades: quedas/gaps10/30/50/100% na exposição2k implicam perdas de preço200/600/1000/2000USDT, mais custos/funding; risco de venue pode atingir todo o collateral. DD e maior sequência histórica não são limites futuros. Estes cenários quantificam impacto, não a probabilidade de eventos extremos nem a solvência real de uma conta. O primeiro franco continua sem justificação.

## Evidência que mudaria a decisão

Seriam necessários, conjuntamente: novos sinais com proveniência exata e sem contaminação; entrada posterior à disponibilidade do sinal; livros/quantidades/contratos que suportem sizing; caminho de stop verificável sem preencher gaps com preços teóricos; taxas e funding liquidados pelo período completo; sobrevivência sob eventos extremos; e amostra independente com precisão económica, contabilizando dependência e todos os episódios perdidos/censurados. Acesso público a um livro por si só não valida edge nem proteção de uma conta.

**Conseguimos obtê-la a custo razoável?** Uma qualificação pontual de fontes poderia ser barata noutro runtime autorizado, mas está bloqueada aqui e não resolve a baixa frequência. Com o histórico disponível, não defenderia um coletor dedicado para certificar esta única lane: meses de dados não justificam a promessa e anos de investigação têm elevado custo de oportunidade. Preservar a hipótese/alertas existentes custa pouco; inventar uma promoção ou construir mais infraestrutura custa demasiado.

Próximo veredito legítimo entregue agora: **INCONCLUSIVO / VANTAGEM INDEPENDENTE POR PROVAR / SOURCE_BLOCKED NESTE AMBIENTE / FEASIBILITY_FAIL PARA CONFIRMAÇÃO EM UM ANO / NO LIVE GO.**

## Reprodução e limites

`precision.py --sol-ledger <artifact11831078628/4h_BASE_TRADES.csv> --bnb-ledger <artifact11830584859/30m_BASE_TRADES.csv> --out precision.json` usa só ledgers antigos. `test_protocol.py` verifica isolamento público, unidades, tamanho mínimo, rounding, livro inválido e proibição de fills sem profundidade. Estes testes não validam retorno. `source_probe.py --out <nova pasta>` faz17 GET sem credenciais e exige nova saída; **não o voltar a executar como continuação desta freeze**, cujo orçamento já foi gasto.

Census completo de AGENTS.md: nenhum nos trees não truncados de PR265, PR215 pin ou main inspecionado, nem nos quatro ancestrais locais, conforme `identity.json`. Limites do utilizador e freezes originais mantêm-se. Apenas ficheiros de investigação novos; sem main/merge, mercados privados, ordens, wallets, capital ou Render. Sem parâmetros alterados após outcomes.
