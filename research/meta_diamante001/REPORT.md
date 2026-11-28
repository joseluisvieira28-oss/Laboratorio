# META-DIAMANTE-001 · relatório científico de 28/11/2026

**Decisão económica: NO-GO.** Os três ativos e os mesmos anos permitiram comparar seleção, abstenção e CONVEX fixo. A diferença entre B e A foi inferior a um ponto percentual de um orçamento anual e mudou de sinal em stress. O ensaio independente tem zero operações liquidadas.

## Desenho e interpretação

O commit 0b6c6f8 congelou universo, variáveis, estratégia, thresholds, orçamento, custos, embargo e testes antes das métricas novas. O histórico anterior até 2025 é contaminado para confirmação. O teste spot transfere a lógica horária causal de PR81. Os verbos “reproduzir” as contas V5 e “transferir” a estratégia para spot identificam dois cálculos separados. Perpétuos incluem funding e execução em barras de 5 min. Spot usa apenas long e caixa, funding zero, execução em barras de uma hora.

A conta de 10 000 USDT é reposta em cada janeiro. Cada ativo recebe um terço do orçamento e pode aplicar 20% da sua subconta corrente numa posição. As somas de PnL cobrem três exercícios com orçamento reiniciado. O orçamento passivo inicial por ativo é o mesmo; a exposição realizada diverge porque o passivo mantém a posição. A comparação temporal cobre 1 096 dias. R01–05 usam ADX, inclinação/direção SMA200, quantil móvel de volatilidade, efficiency ratio e tendência simultânea BTC/ativo. Todos os sinais usam o fecho e a próxima abertura elegível. Os stops previamente ativos têm precedência intrabar, com gaps à abertura. O trailing histórico pode voltar a alargar. Datas de saída intrabar identificam a barra, sem hora exata de transação.

B escolhe CONVEX se pelo menos três condições estiverem ativas, ou reversão lateral se a soma for inferior a três e ADX abaixo de 25, condicionado a ocorrer o sinal subjacente. C prevê o retorno líquido por estratégia com florestas fixas, 100 árvores, profundidade 3 e mínimo de 15 por folha. Os rótulos de treino são de operações isoladas liquidadas, sem sobreposição dentro da série de cada estratégia e ativo. Embargo de 168h e novos modelos a cada janeiro, treino expansivo desde 2021. Os hiperparâmetros foram fixos, sem procura ou validação interna para escolher vencedores. Os ativos simultâneos podem partilhar risco e movimentos. O bootstrap usa os mesmos dias para todos os ativos e braços. Apenas o regressor produz uma estimativa numérica de retorno; os restantes braços usam decisões determinísticas. A probabilidade calibrada permanece indeterminada.

## Comparação histórica em USDT

| Sistema | Sinais de estratégia | Fechos / dispensados | Acerto | Ganho / perda médios | PF | Bruto | Comissões + fricção | Líquido | Stress | Manual |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| A fixo | 996 | 169 / 827 | 26,63% | 126,58 / −28,93 | 1,59 | 2461,64 | 352,99 | 2108,65 | 1712,67 | 1391,32 |
| B estatístico | 2563 | 250 / 2313 | 41,60% | 57,11 / −25,67 | 1,58 | 2706,73 | 515,02 | 2191,71 | 1688,50 | 1400,22 |
| C IA | 2563 | 156 / 2407 | 23,72% | 118,31 / −28,25 | 1,30 | 1330,72 | 314,83 | 1015,88 | 798,21 | 136,30 |
| D caixa | 2563 | 0 / 2563 | — | — | — | 0 | 0 | 0 | 0 | 0 |
| H07 abstenção CONVEX | 996 | 138 / 858 | 27,54% | 135,29 / −28,75 | 1,79 | 2554,18 | 288,26 | 2265,92 | 1942,42 | 1820,54 |

Sinais são pares sinal–estratégia; um instante pode emitir dois. A indisponibilidade de uma vaga inclui exposição já ativa. A expectativa por fecho A/B/C/H07 foi 12,48 / 8,77 / 6,51 / 16,42 USDT. A exposição média em horas das subcontas foi 54,90% / 53,32% / 51,06% / 51,46%. Em curvas diárias aditivas, drawdowns máximos de 6,56% / 6,53% / 7,89% / 6,03%. A marca diária pode omitir drawdown intradiário. Sharpe e Sortino descritivos sem taxa livre de risco, rotação, anos, regimes, ativos e concentrações estão nos CSV. O controlo de regime atrasado 168h obteve +538,12 USDT, com 310 operações. O passivo de 20% somou +9413,98 USDT, dos quais +6120,81 vieram de SOL em 2023. O passivo tem risco direcional contínuo.

## Inferência e vereditos

Nove comparações direcionais utilizam a correção Bonferroni e 2000 amostras bootstrap circulares de 30 dias. O limite inferior unilateral corrigido foi negativo nas nove. IC de 95% citados são bilaterais descritivos sem ajuste. A fração de réplicas com ganho ≤0 não é uma probabilidade posterior de a hipótese ser falsa. A amostra de três anos, os eventos de cauda e a escolha prévia de ativos reduzem o poder. Os intervalos condicionam nos modelos já treinados e nas hipóteses de execução.

| Hipótese | Amostra | PnL / incremento | Incerteza e robustez | Custos / execução | Veredito |
|---|---|---|---|---|---|
| H01 tendência | 996 sinais CONVEX, 114–155 negócios por filtro | R01 −242, R02 −492, R03 +156, R04 −322, R05 −540 face a A | R03 IC −353 a +602; estabilidade insuficiente | Spot BASE simulado | INSUFFICIENT_EVIDENCE |
| H02 reversão lateral | 233 fechados | −710,28; +463,33 face a MR permanente | Negativa nos três anos e três ativos, bruto −252,24 | 458,1 de custos aproximados | NO_EDGE |
| H03 macro | 0 eventos elegíveis neste ensaio | Indeterminado | News Shock documenta falta de consenso anterior ao anúncio para os campos obrigatórios | Execução não estimável | SOURCE_BLOCKED |
| H04 liquidez | 0 entradas META sincronizadas | Indeterminado | PRs 331/353/369/376/400 com protocolos distintos. LIQMAP-004 documentou NO-GO próprio | Três livros atuais; não liquidam sinais históricos | INSUFFICIENT_EVIDENCE |
| H05 seleção estatística | 250 vs 169 | +83,06 vs A | IC −642 a +735; B−A em 2025 −87,33 | Stress −24,17 vs A | INSUFFICIENT_EVIDENCE |
| H06 IA incremental | 156 vs 250 | −1175,83 vs B | IC −2355 a −166; inferior também em stress e manual | Inferência local, custo incremental monetário assumido zero | NO_EDGE |
| H07 abstenção | 138 vs 169 | +157,27 vs A | IC −501 a +723; inferior em BNB; inferior corrigido −734 | Simulação, execução empírica em falta | HISTORICAL_CANDIDATE |
| H08 transferência | Três ativos e três anos | H07−A BTC +88,74; SOL +101,04; BNB −32,51 | Falha o critério entre ativos; todos estes mercados eram conhecidos | Mesmos custos BASE | INSUFFICIENT_EVIDENCE |

## Reprodução dos perpétuos originais

A listagem de artefactos devolveu zero para os quatro runs pedidos e para os três runs-fonte adicionais. Reconstruímos a partir de arquivos mensais oficiais com o código V5 fixado em Git e verificação de checksum antes de interpretar preços, volumes e funding. O PR #81 contém uma variante com período e capital diferentes. O valor BTC de 11 507,44 vem da matriz V5 canónica de 5 minutos agregada a 1h. Misturar as duas séries geraria uma reprodução incorreta.

* BTC 1h, 2021–25: 10 000 → 11 507,4361 marcado; 77 fechos, 78 entradas e uma posição aberta. Houve 635 barras com sinal, 557 ignoradas por posição ocupada. O PnL líquido dos fechos foi +1527,15. O financiamento modelado foi −1154,26 USDT.
* BTC F2: BASE 588 fechos e −22,18865%; STRESS 592 e −27,13426%. Cinco anos negativos. Sobre os mesmos fills BASE, retirar fees e funding ainda deixa o preço após slippage negativo em cerca de 545 USDT. Encerrar a versão congelada.
* SOL 1h: 84 fechos BASE, líquido +5930,21, ano 2025 −577,72, três maiores ganhos / líquido 76,46%. BNB 4h: 28 fechos, +2737,79, ano 2023 −28,89, concentração 82,35%.
* Nos sete braços V11/V12, os 14 CSV BASE/STRESS regenerados têm exatamente os hashes preservados na auditoria anterior. Acerto BASE 20,49%–31,37%, relação ganho/perda média em R 3,61–6,62. Seis em sete ficam negativos sem os três maiores ganhos. Os sete contam com 445 fechos BASE, com sobreposições entre estratégias. A reconciliação compara preço menos fees mais funding por negócio.

A adenda foi registada após o primeiro resumo spot e antes de cruzar as entradas originais com o regime. Na atribuição estática H07 a BTC manteve 61/77 entradas, 46/60 perdas e os três maiores vencedores; PnL retido +2196,19. SOL manteve 58/84, 40/60 perdas e os três maiores; +6040,59. Em BNB 27/28 tinham histórico suficiente, H07 reteve 17, 11 perdas e dois dos três maiores; +1482,40 contra +2698,78 das 27 classificáveis. As quantidades originais foram mantidas para atribuição. A trajectória de uma conta reexecutada pode ser diferente.

## Capital, custos e execução

Spot BASE usa 10 bp de comissão e 5 bp de fricção adversa por lado, stress 10+15, manual 10+25 com uma hora adicional de atraso nas decisões discricionárias e stop pré-existente. A fricção agrega spread, slippage e impacto como cenário. Funding spot sem empréstimo é zero. Nenhum braço usa maker; não há desconto maker nem pressuposto de prioridade na fila. Um snapshot atual verificou filtros de quantidade, mínimo de 5 USDT nos três símbolos e topo vendedor suficiente para os seis tamanhos nesse instante. Os limites e a profundidade históricos permanecem desconhecidos. O mínimo fixado no ensaio foi 10 USDT por entrada; como o notional inicial é capital/15, o mínimo aritmético inicial foi 150 USDT; 250 foi o menor escalão simulado com operações. O risco de fills parciais, falhas de stop, tick histórico, latência intrahorária, spread em cascata, seleção adversa e diferenças de venue não foi resolvido. Não há estimativa certificada de capacidade. O custo de infraestrutura real ou de tempo humano pode dominar uma pequena conta.

| Capital USDT | H07, três anos | Após 1 USDT/mês | Incremento H07−A antes de custo fixo |
|---:|---:|---:|---:|
| 100 | 0 | −36 se serviço ligado | 0 |
| 250 | 56,65 | 20,65 | 3,93 |
| 500 | 113,30 | 77,30 | 7,86 |
| 1000 | 226,59 | 190,59 | 15,73 |
| 5000 | 1132,96 | 1096,96 | 78,63 |
| 10000 | 2265,92 | 2229,92 | 157,27 |

## WHAT COULD WE BE WRONG ABOUT?

Os filtros podem apenas selecionar beta de tendência: o controlo passivo ganhou mais, sobretudo num ativo/ano. A cauda positiva é plausível para trailing, mas os IC permitem perda incremental. C teve 106% do seu próprio PnL nos três maiores ganhos. Aumentar acerto em B reduziu a expectativa por trade. O uso duplo de z-score e Bollinger herdado de PR81 torna dois votos quase equivalentes. O filtro pode reconhecer persistência já realizada sem antecipar nova expansão.

Os dados spot têm 14 horas ausentes em cada série entre 2021–25, uma em 2023. A execução primária usa a próxima barra publicada. Exigir 745 observações consecutivas antes de novas entradas reduziu a vantagem H07−A de +157,27 para +20,44. Duas posições de cada braço verificado atravessam a hora em falta e o caminho do stop continua desconhecido. A sensibilidade dos blocos de 7, 60 e 90 dias manteve os IC H07−A e B−A dos dois lados de zero. A simulação não observa fills recusados e o relógio da barra não comprova o atraso do operador. Os três ativos sobreviventes foram escolhidos pelo histórico do laboratório; os testes não estimam retorno sobre todas as moedas listadas. Um universo mais amplo não foi retroativamente procurado.

## Estado independente

A fotografia pública das 12:11:41 UTC de 28/11/2026 contém cinco níveis por lado para BTC, SOL e BNB. Zero operações prospetivas fechadas. Barras admitidas exclusivamente depois das 13:00 UTC de 28/11 para aquecimento; avaliação anual começa 01/01/2027. A floresta futura está congelada para as 32 combinações de flags, utilizando apenas trades já liquidados até ao embargo de dezembro de 2025. A liquidação anual usa o último fecho menos custos; durante o exercício, posições ainda abertas contam como marca provisória. Mínimo de 365 dias pontuados e 100 fechos, mais estabilidade, custos, evidência independente de execução e limites inferiores positivos. A réplica de candles futura poderá testar previsibilidade; por si só não certificará execução.

A recolha inicial foi executada; o agendamento diário foi recusado devido às cinco tarefas ativas da conta. As candles futuras são recuperáveis pela data original sob a regra congelada. A continuidade de snapshots contemporâneos de profundidade requer um agendamento em funcionamento. Não há run próprio de GitHub Actions desta operação. Os links originais de workflows estão no inventário e nos closeouts, e os novos resultados foram calculados localmente.
