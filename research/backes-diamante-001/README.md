# BACKES-DIAMANTE-001 — Auditoria adversarial de fontes públicas
Data de corte: 2026-11-23 (Europe/Zurich)
Repositório: joseluisvieira28-oss/Laboratorio
Estado: **RESEARCH ONLY / ECONOMIC NO-GO (evidência insuficiente)**
Custos realizados: **0**. Execuções reais: **0**. Compras de cursos: **0**.

## Regra científica
Esta auditoria examina **descrições públicas e capítulos** de vídeos do canal Augusto Backes, além de uma página pública de programa. **Não atesta que vídeos completos foram vistos ou transcritos**. Nenhuma frase de uma descrição, por si só, constitui regra operacional completa nem prova de resultado. Nunca apresentar um backtest criado a partir da nossa interpretação como se fosse a estratégia privada de Augusto Backes.

Os registos abaixo são uma **amostra orientada por pesquisa**, e não uma amostra aleatória de previsões. Logo, não servem para estimar a taxa de acerto global do criador sem enviesamento de seleção.

## Fontes primárias: 16 vídeos públicos rastreáveis
| # | Data de publicação | Vídeo | URL | Tema que consta da descrição/capítulos | Tipo |
|---|---|---|---|---|---|
| 01 | 2025-08-23 | Como fazer gerenciamento de risco | https://www.youtube.com/watch?v=NruRSFnJ6rs | gestão de risco | formação |
| 02 | 2026-03-17 | Vídeo sobre reversão do BTC / RSI 4H | https://www.youtube.com/watch?v=zkWWIEfqzNQ | RSI 4H, média de 200 semanas, resistência | análise condicional |
| 03 | 2026-06-16 | Bitcoin parou de cair? | https://www.youtube.com/watch?v=ZPBMHWbO2-I | DCA semanal, MVRV, SOPR, HFT | análise/metodologia |
| 04 | 2026-06-23 | Ações americanas caem e levam BTC | https://www.youtube.com/watch?v=IS-KzB4MCc4 | diversificação e proteção de capital | gestão de risco |
| 05 | 2026-07-01 | He sold all his Bitcoins and quit | https://www.youtube.com/watch?v=ojju4ia-uWo | compra de BTC perto de mínimo mensal, atenção | relato de operação |
| 06 | 2026-07-10 | Ainda dá pra comprar? | https://www.youtube.com/watch?v=5vXdRdJTn0I | lateralidade, liquidez bilateral, risco | análise |
| 07 | 2026-07-11 | The truth about altcoins | https://www.youtube.com/watch?v=E08hFAlio8U | liquidez de altcoins e crítica da altseason | tese de mercado |
| 08 | 2026-07-16 | Bitcoin finalmente atingiu o fundo? | https://www.youtube.com/watch?v=wjBMhFmoeSY | média de 8 semanas como gatilho; reversão | hipótese técnica |
| 09 | 2026-07-22 | Nem Bitcoin, nem ações | https://www.youtube.com/watch?v=p7W3coU3bps | timing, lateralidade, média 440 | análise |
| 10 | 2026-08-06 | I did not abandon Bitcoin | https://www.youtube.com/watch?v=mkMsvoLqFBk | rotação entre classes por desempenho relativo | tese |
| 11 | 2026-08-07 | Bitcoin, ouro e ações americanas | https://www.youtube.com/watch?v=Xy2EKv6F8dI | resistências BTC, compra de ETH, macro | relato + análise |
| 12 | 2026-08-18 | Money Flow: ETH/BTC e fundo ascendente | https://www.youtube.com/watch?v=M3sP2GZmpMs | ETH/BTC higher-low, triângulo BTC, baixa liquidez, compra escalonada | hipótese |
| 13 | 2026-09-03 | September will decide Bitcoin's future | https://www.youtube.com/watch?v=lCNMh79U9w4 | média de 56 semanas, 83–85k, cenário alternativo 52k | hipótese condicional |
| 14 | 2026-09-14 | Vídeo sobre ETH vs BTC | https://www.youtube.com/watch?v=b0FHJpMj-lU | possível reversão relativa ETH/BTC | tese |
| 15 | data exata não verificada | Will Bitcoin go up or down? | https://www.youtube.com/watch?v=eg8GkVQVSzw | regras pessoais de exposição e comportamento | formação |
| 16 | data exata não verificada | Bitcoin and strategies every beginner should keep an eye on | https://www.youtube.com/watch?v=GY1dwH7JnNU | dimensionamento entre small/large caps | formação |

Fonte adicional da *estrutura anunciada*, não das regras completas: https://criptoblinders.com.br/ (módulos: ação do preço, caixotes, busca de liquidez, barras de sinal/confirmação/rejeição, smart money; informação de marketing, sujeita a revisão).

## Triagem adversarial
### H1 — BTC / filtro de tendência com SMA de 56 semanas
* Evidência publicada: o vídeo #13 menciona a importância da média de 56 semanas como região de decisão.
* **Regra de teste concebida pelo laboratório (NÃO atribuída ao autor):** BTC spot long quando fecho semanal > SMA56 e inclinação da SMA56 positiva; execução apenas na abertura da semana seguinte; sair quando fecho semanal < SMA56. Sem alavancagem.
* Comparadores pré-definidos: buy-and-hold BTC, filtro SMA52 e SMA200 dias com execução equivalente; observar sensibilidade aos parâmetros.
* Dados requeridos: OHLCV BTCUSDT com timestamps e proveniência, desde pelo menos 2017, idealmente 2015; custos e slippage de entrada/saída.
* Status: **HYPOTHESIS ONLY**. Sem registos históricos verificáveis nesta auditoria; nenhum PnL calculado.

### H2 — Rotação ETH/BTC após fundo relativo ascendente
* Evidência publicada: vídeos #12 e #14 descrevem a possível recuperação de ETH face ao BTC e a necessidade de higher low.
* **Regra de teste nossa:** pivô em semana k só é conhecido depois de três semanas futuras; entrada na ETH na próxima abertura semanal APÓS a confirmação de dois fundos ascendentes em ETH/BTC, se retorno relativo 4 semanas > 0; de resto, alocação BTC; impedir qualquer uso de pivô antes da sua confirmação.
* Comparadores: BTC-only, ETH-only, rebalancing 50/50, momentum relativo de 4 semanas sem pivôs.
* Entrada com comissões, slippage, diferencial de preço e tributação fora de escopo (não presumir taxa fiscal).
* Status: **HYPOTHESIS ONLY**. Não há edge comprovado.

### H3 — Reversão BTC com média móvel 8 semanas
* Evidência publicada: vídeo #08 refere a média de 8 semanas como gatilho.
* **Regra nossa:** fecho semanal acima da EMA8 e EMA8 ascendente => BTC spot long a partir da abertura da semana seguinte; saída na primeira quebra de fecho. Testar EMA/SMA e 6/8/10 semanas como estabilidade, não escolher vencedor retroativamente.
* Status: **HYPOTHESIS ONLY**.

### H4 — Acumulação on-chain MVRV / SOPR
* Evidência publicada: vídeo #03 nomeia MVRV e SOPR.
* Requer séries **point-in-time**, datas de cálculo e revisões; se não houver dados com histórico de disponibilidade, **SOURCE_BLOCKED**.
* Status: **SOURCE_BLOCKED**.

### H5 — Baixa liquidez e entradas escalonadas
* Evidência publicada: vídeo #12 descreve baixa liquidez e compras escalonadas.
* **Não há especificação pública suficiente nesta amostra** para definir qual percentil de volume, timeframe, fracionamento, stops e condição de saída.
* Status: **RULE_BLOCKED**. Não inventar regras e atribuí-las ao criador.

## Protocolo económico congelável ANTES de olhar para resultados
1. Disponibilidade de dados: OHLCV de fonte original, fuso UTC, arquivo original com SHA256, intervalos sem lacunas e asset mapping ETHBTC/BTCUSDT/ETHUSDT.
2. Calendário: treino 2018–2022, validação 2023–2024, teste cronológico 2025–2026-11-22. O período anterior ao início do produto de trading usado deve respeitar restrições de mercado e instrumentos; não misturar mercados sem justificação.
3. Sinal só pode usar barras *fechadas*; execução na próxima barra, nunca ao fecho que gerou o sinal. Preservar *delisting*, *survivorship bias*, e reajustes quando aplicável.
4. Custos de investigação (cenários, NÃO taxas reais verificadas): fricção por lado de 5, 10, 20, 35 bps, incluindo comissão + slippage; cenários de choque de 100 bps; spread/volume e liquidez verificáveis antes de simulação realista.
5. Métricas: retorno geométrico líquido anual, drawdown máximo, exposição, turnover, número de operações, mediana por trade, expectativa com incerteza, diferenças contra benchmarks e probabilidade de subdesempenho.
6. Inferência: bootstrap de blocos no tempo, testes por regime, walk-forward, sensibilidade de parâmetros; correção de múltiplos testes se testar variantes.
7. Gate GO económico só com diferença líquida positiva contra benchmark apropriado, margem robusta a fricções, amostra independente e futura; sem dependência de único evento/regime. Caso contrário NO-GO ou INCONCLUSIVO.
8. **Não executar trades, pagamentos, compra de cursos, subscrições ou contacto automático.**

## Limites do que foi verificado (2026-11-23)
* **16/16** URLs públicas identificadas por pesquisa; **0/16** transcrições completas validadas palavra a palavra.
* **0** regras proprietárias obtidas dos cursos. **0** backtests executados com série histórica BTC/ETH verificada nesta operação.
* **0** retornos líquidos medidos. É proibido inferir percentagem de acerto do criador a partir desta amostra selecionada.
* Os materiais consultados falam muitas vezes de *condições e cenários alternativos*, não de ordens inequívocas. Nunca classificar uma previsão como falhada/acertada sem definir antes horizonte, preço, lado, invalidadores e exceções.
* Veredito: **GO para aquisição e validação de dados e regras; NO-GO para capital/trading e para alegar vantagem económica.**
