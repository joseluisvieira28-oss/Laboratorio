# Crypto Lab — 3 Canas × 10× — 100 USDT (PRELIVE) — 14/10/2026

**Autoridade: NENHUMA. Este pacote NÃO faz trading, NÃO inicia tarefas automáticas, NÃO pede API keys e NÃO faz login na MEXC.** O output é sempre `NO_LIVE_GO`, incluindo quando os testes sintéticos passam. Não o confundas com o Windows Operator LIVE.

## O que foi confirmado, e o que NÃO foi comprovado
O operador humano declarou **100 USDT disponíveis na conta MEXC Futures** e **zero posições abertas**. Não verificámos nenhum destes factos independentemente, porque não fizemos pedidos autenticados nem consultámos a conta. Isto resolve apenas a falta da declaração de `EQUITY_USDT`, não a prova do estado da corretora.

## Três estratégias ORIGINAIS (sem early-half)
1. `SOL_CONVEX_NATIVE_5M` LONG `SOL_USDT` futures, sinal original fonte PR #217, SHA `af82deefd5634a77a7b49e7acec61ca21eb44a49`.
2. `SOL_CONVEX_1H` LONG `SOL_USDT` futures, original fonte PR #215, SHA `42d6748864dd78b911b5f1fc775ff1950b556d2b`.
3. `BNB_CONVEX_4H` LONG `BNB_USDT` futures, original fonte PR #215, SHA `42d6748864dd78b911b5f1fc775ff1950b556d2b`.
Cada uma tem stop original modelado **4% ABAIXO do preço de entrada** e trailing original V5 (12% do pico ativado quando a vela do timeframe fecha >=+5%). O trailing original **NÃO É monotónico** e pode afrouxar quando desativa. Não o alterámos nesta preparação; uma política que o impeça é um novo fork económico que necessita de avaliação própria. Nunca afirmar que a estratégia original dispõe de um stop que não afrouxa.

## Configuração de risco APENAS PROPOSTA
- Capital *declarado* 100 USDT, alavancagem *pretendida* 10× e modo ISOLATED.
- Risco de perda projetada até ao stop por estratégia: **0,50 USDT** incluindo hipótese BASE 8bps taker/lado +2bps slippage/lado +5bps reserva de funding; total projetado até 1,50 USDT; orçamento de risco SOL até 1,00 USDT.
- Na conta de 100 USDT, 20% de notional da estratégia histórica seriam 20 USDT, com stop preço -4% => 0,80 USDT de perda APENAS DO PREÇO, antes das comissões. Por isso NÃO herdamos automaticamente os 20% notional do backtest para este orçamento de 0,50: precisamos de redimensionamento, que também altera economicamente a estratégia.
- A 10×, o stop de preço -4% representa cerca de **-40% da margem inicial** antes de custos e da dinâmica de liquidação. Isso NÃO é 40% da banca; o risco à banca depende do tamanho das posições. Um stop não garante perda máxima em gaps, outages, deslizamento e mark-liquidation.
- Os cálculos sintéticos usam SOL ask=110 USDT, contrato=0,1 SOL; BNB ask=750 USDT, contrato=0,01 BNB. São **números fabricados apenas para teste de funções**, não cotações ou specs da MEXC. A atual quantidade mínima, tamanho do contrato, step, preço, fee do utilizador e modo de conta NÃO foram consultados.
- Os dois sinais de SOL partilham o mesmo símbolo `SOL_USDT`. Em modo one-way podem ser uma única posição netted; múltiplas ordens/stops independentes NÃO são presumidos. Até prova do broker, permitir apenas **uma posição SOL física em simultâneo**. Existem três slots de sinais, mas no máximo **duas exposições físicas simultâneas (SOL e BNB)** neste desenho PRELIVE. Não prometer três posições independentes.

## Usar no Windows
Extrair o ZIP para uma pasta. Confirmar que `VERIFICAR_PRELIVE.ps1`, `preflight_risk_only.py` e `prelive_100usdt_configuration.json` estão juntos na pasta. Abrir PowerShell nessa pasta e executar:

```powershell
powershell -NoProfile -ExecutionPolicy Bypass -File .\VERIFICAR_PRELIVE.ps1
```

Alternativa sem PowerShell:

```powershell
py -3 .\preflight_risk_only.py --config .\prelive_100usdt_configuration.json --synthetic-only
```

Procurar `result: NO_LIVE_GO`, `execution_authority: NONE`. Exemplos de quantidades são hipotéticos. NENHUMA linha produz ordens. Partilhar o output sem segredos para discussão.

## Gates ainda em falta para LIVE GO
1. Sinais originais reproduzidos causalmente com dados presentes da MEXC (não basta Binance 2023–25).
2. Livros bid/ask e contrato MEXC atualizados, timestamp/latência, preços, tamanho de contrato, lot/step, notional mínimo, amplitude stop e limites de leverage confirmados.
3. Banca, fees reais da conta Futures, posições abertas, modos de posição, margem e resting orders verificados read-only depois de ligação explícita autorizada; a declaração de 100/zero NÃO é uma resposta autenticada.
4. Stop inicial real nativo da corretora com ACK associado ao position ID, quantidade, direção e trigger (mark/last/index). O operador tem de provar o que acontece em preenchimentos parciais, mudanças, cancel/replaces sem janela nua, desconexão e crash.
5. Limites de exposição conjunta, stops num símbolo agregado SOL, reconciliação após reinício, nenhum duplicate order on timeout e monitor de falha de feed. Stop distante de liquidação *verificada*, sem auto add, sem cross margin e sem martingale.
6. Shadow independente e contemporâneo **depois de todas as alterações de sizing/stop/venue**, com custos e funding da rota, para determinar se existe expectancy líquida positiva; os resultados históricos de 2023–25 não se transferem automaticamente.
7. Aprovação operacional final após recibos completos e autorização distinta para qualquer teste real que gaste capital. Este ZIP não produz essa autorização.

## Repositório e prova
Repo `joseluisvieira28-oss/Laboratorio`; branch `prelive/three-canas-100usdt-10x-risk-gate-2026-10-14`. Research-only, sem alterações a `main`, sem keys, sem ordens, sem deployment ou tarefas automáticas. Testes em CI são apenas unitários/sintéticos. Qualquer API privada ou alteração real à conta continua bloqueada.
