# BACKES-DIAMANTE-005 — Defesa de capital sem tuning retrospetivo
Congelamento pré-resultados: 2026-11-24, Europe/Zurich. **NÃO EXECUTAR TRADES**.

## Autoridade e dados fixos
- Referência: BACKES-004 PR #389, artefacto GitHub Actions #45337852543 (SHA256 ZIP `73a3e5349930d8b8d8dab46fa69fb8989a118c79cb7f6f7a59260b2f50641d7b`), `WEEKLY_DATA.json` da **Coinbase** e **Binance Spot**.
- Cada fonte: 464 semanas completas, segunda-feira–domingo UTC, de 2018-01-01 a 2026-11-22. BTC-USD/ETH-USD/ETH-BTC ou BTCUSDT/ETHUSDT/ETHBTC, diretamente negociados. SHA256 do ZIP da experiência anterior deve coincidir; o ZIP de origem é artefacto do GitHub; não mudar o histórico nem substituir fontes.
- O sinal `FROZEN002` é o que consta do código imutável `research/backes-diamante-002/rotation_backtest.py`. O `MOM8` é a regra simples de momentum 8 semanas já publicada em `research/backes-diamante-004/analyze.py`. **Todas as hipóteses são do Crypto Lab, não estratégias proprietárias de Augusto Backes.**
- A equipa já viu resultados até 2026-11-22. TODO este estudo, mesmo por janelas cronológicas, é **retrospectivo e não verdadeiramente OOS**. Nenhum GO de capital pode decorrer exclusivamente deste estudo.

## Regras congeladas antes de olhar resultados do 005
Todos os sinais calculados até ao fecho de domingo da semana t-1; exposição executada hipoteticamente na abertura de segunda-feira t. Não permitir preços de t no sinal.

**Referências:** CASH zero rendimento (sem considerar risco de custódia/USDT), BTC HOLD, ETH HOLD, MIX 50/50 rebalanço semanal, `FROZEN002` 100% BTC/ETH, `MOM8` 100% BTC/ETH.

**Defesas:** 
1. `HALF_ROT`: 50% alocado a FROZEN002, 50% CASH, reequilíbrio semanal. Controlo mecânico simples de exposição.
2. `BTC_TREND40`: 100% BTC somente quando o último fecho BTC está acima da SMA40 dos **40 últimos fechos semanais terminados**, caso contrário 100% CASH. Antes de 40 fechos, 100% CASH.
3. `ROT_TREND40`: escolher o ativo pelo FROZEN002; investir 100% no ativo selecionado só quando BTC passou o filtro SMA40; caso contrário CASH.
4. `MOM8_TREND40`: como ROT_TREND40, mas o ativo é escolhido pelo MOM8.
5. `ROT_TREND40_VOL20`: aplicar o filtro SMA40 e depois dimensionar exposição pelo alvo de volatilidade anualizada **20%**, estimada sobre as últimas **12** variações de fecho semanal do ativo selecionado, usando somente preços fechados até t-1; sem alavancagem, peso = min(1, 0.20/max(vol12, 0.10)). Complemento em CASH. Sem histórico suficiente, peso 0.
6. `MOM8_TREND40_VOL20`: mesmo filtro e alvo de vol usando MOM8.

Estas seis defesas ficam fixas; **não otimizar 40/12/20% nem escolher apenas a melhor depois de ver resultados**. A referência HALF_ROT não reduz a possibilidade de grandes percentagens de queda ao nível da parte investida.

## Custos, alocação e risco
- Cash é USD/USDT não remunerado, exposição sem alavancagem e sem posições short. Saldos positivos e custos em unidades do numerário da exchange; Coinbase USD e Binance USDT não são equivalentes sem risco de moeda, que aqui fica fora de modelo.
- Preço de operação hipotético: abertura semanal **após** fecho da semana de sinal, valorização ao open seguinte e último domingo close; comissões/slippage em cenários fixos **10,35,60,80,100 bps** por valor negociado em cada operação (não taxas exatas historicamente pagas). Modelo **direct spot netted**: buys+sales de BTC/ETH agrupados e uma troca direta BTC/ETH custa uma perna; compras ou vendas líquidas no cash também cobram a parte transacionada. Stress **two-hop USD/USDT** a 80 bps, pagando separadamente a soma de compras e vendas nas trocas de ativo. Não atribuir 10 bps ao escalão de retalho como se fosse real.
- Na carteira mista, rebalanço semanal pós-movimento gera turnover e custos; pesos transitam ajustados pelo retorno do ativo, sem reset grátis. **Sem cobrança de liquidação final**, como estudos 002 e 004, deixando esse custo pendente.
- Médias semanais e indicadores de vol usam fechos semanais observáveis. Vol12: desvio padrão amostral de 12 retornos log semanais consecutivos, anualizado por sqrt(52). Semana pré-histórica com menos observações => CASH.
- Perdas máximas: MDD sobre NAV marcado **semanalmente**; calcular também limite aproximado baseado nas mínimas OHLC da semana, **não um drawdown intradiário observado**. Gap de abertura e slippage adverso não reconstruídos.
- Investigar risco de drawdown >= **30%** como limite máximo de aceitação da experiência, não promessa de stop garantido. Exigir retorno líquido positivo e contra CASH a 80bps, melhora de MDD >= 20 pontos percentuais vs FROZEN002, e desempenho ajustado a risco (CAGR/maxDD) > BTC_TREND40 e HALf_ROT em ambas as exchanges e em pelo menos 2 de 3 regimes. Caso contrário NO-GO ou INCONCLUSIVO. Critério económico não sobrepõe risco de cauda não modelado nem validação prospetiva.
- Janelas fixas, definidas pela semana de abertura: 2018–2022, 2023–2024, 2025–2026-11-22, total 2018–2026. Reportar CAGR, retorno líquido, drawdown, pior semana, volatilidade da NAV, turnover, custos, meses/semana em cash, média exposição e Calmar; se CAGR<=0, Calmar<=0; se MDD=0, Calmar indefinido.
- Reamostragem exploratória: bootstrap temporal blocos 8 semanas, 2000 replicações com seed 5005 para excesso de retorno semanal das defesas vs CASH, BTC_TREND40 e FROZEN002. Isto não é teste prospetivo, não corrigido por múltiplas hipóteses.
- Exigir pelo menos 2 fontes independentes verificadas, sem lacunas; se faltarem, SOURCE_BLOCKED. Se houver falha do código/testes => TECH_BLOCKED, nunca inventar retorno.

## Segurança
Zero ordens, transações, compras, subscrições, trading API, alavancagem, exposição real, execução em produção, merge, alteração de estratégias 002/004 ou acesso à carteira. Todos os estudos isolados em PR Draft. Após resultados, apenas auditoria, sem otimização corretiva disfarçada de descoberta.
