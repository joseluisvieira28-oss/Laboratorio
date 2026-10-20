# CONVEX V11/V12 — auditoria da assimetria económica real dos ledgers

Data: 20/10/2026. **VEREDITO: ASSIMETRIA HISTÓRICA CONFIRMADA NO MODELO / VANTAGEM LÍQUIDA INDEPENDENTE INCONCLUSIVA / ZERO DIAMANTES CANDIDATOS / SEM TRADING.**

Foram recalculados os 14 ledgers originais das sete estratégias: BASE e STRESS, período comum 2023–2025. Nenhum parâmetro de entrada/saída foi alterado; nenhum novo replay de mercado nem outcome protegido de 2026 foi aberto. V11/V12 são observadores de sinais, não versões de estratégias economicamente novas: a correspondência é V11 SOL4h/BNB30m/ETH1h e V12 BNB5m/SOL30m/BNB15m/DOGE4h.

## Resposta à pergunta do operador

Sim: o histórico destas estratégias tem o perfil de poucas vitórias grandes. A taxa de acerto não é o problema principal. Todas as sete mostram expectativa positiva depois dos custos ASSUMIDOS no modelo, tanto BASE como STRESS. Não há, contudo, demonstração independente de que essa expectativa persiste fora da amostra ou é executável na MEXC com o capital do operador.

O critério anterior «não depender dos maiores vencedores» precisa de precisão: estratégias de tendência podem legitimamente depender da cauda direita. Remover vencedores é um diagnóstico de fragilidade, não um teste universal que demonstra inexistência de edge. Respeitam-se os gates antigos das experiências; esta auditoria não os baixa, não altera os seus vereditos nem promove candidatos por um novo critério.

## Unidade, capital e método

1R = 4% do notional original de entrada (`entry_price × qty`), e não 1% do saldo, margem a 10× ou valor nominal de um stop garantido. PnL líquido/R inclui os custos do modelo. O ganho/perda abaixo é a razão entre ganho médio em R e perda média absoluta em R. A expectativa em R é a média por trade: p×ganho médio − (1−p)×perda média. Não se volta a subtrair custos já contabilizados.

Cada simulação original tinha 10 000 USDT iniciais, 20% do equity em notional por entrada, sem alavancagem e uma posição por estratégia. O risco inicial nominal era cerca de 0,8% do equity antes de custos/gaps. Esses 10 000 são capital de referência, NÃO um mínimo necessário provado. Mínimo de capital, execução fracionária e adaptação a 100 USDT/10× continuam desconhecidos. Não somar estas contas independentes para prometer retorno de uma carteira com sete lanes.

BASE = taker 8 bps + slippage adverso 2 bps POR LADO; STRESS = 8+5 bps por lado. Funding usa rates arquivadas e preço de mercado proxy, não o mark exato de liquidação de funding. Preços OHLC não são bid/ask executáveis. Spread, impacto além da hipótese de slippage, custos reais MEXC/FX, impostos aplicáveis, liquidação, indisponibilidade e stops nativos não estão certificados. Logo «líquido do modelo» não equivale a «líquido de todos os custos reais».

## Assimetria recalculada — BASE

| Grupo / estratégia | Fechados | Acertos | Ganho médio R | Perda média R | Ganho/perda | Expectativa R/trade | PF | Retorno terminal 3 anos BASE / STRESS | DD modelo |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| V11 SOL 4h | 44 | 25.00% | 7.005 | 1.058 | 6.62 | +0.957 | 2.025 | +35.90% / +35.42% | -10.45% |
| V11 BNB 30m | 51 | 31.37% | 3.703 | 1.025 | 3.61 | +0.459 | 1.601 | +19.67% / +18.17% | -10.40% |
| V11 ETH 1h | 47 | 23.40% | 5.688 | 1.076 | 5.28 | +0.507 | 1.540 | +18.77% / +18.34% | -11.06% |
| V12 BNB 5m | 72 | 23.61% | 4.500 | 1.006 | 4.48 | +0.294 | 1.345 | +17.56% / +15.92% | -15.17% |
| V12 SOL 30m | 122 | 20.49% | 5.424 | 1.055 | 5.14 | +0.273 | 1.222 | +24.67% / +22.50% | -19.28% |
| V12 BNB 15m | 65 | 23.08% | 4.318 | 1.009 | 4.28 | +0.220 | 1.239 | +11.04% / +10.49% | -15.21% |
| V12 DOGE 4h | 44 | 27.27% | 4.491 | 1.063 | 4.23 | +0.452 | 1.540 | +15.66% / +15.26% | -10.61% |

Retorno terminal inclui marcação de posições finais abertas onde existam; não se confunde com a soma dos trades fechados. Drawdown é o observado no modelo por mínimos de 5m, NÃO um limite de perda futura ou cenário extremo certificado.

## Dependência dos maiores vencedores — contabilidade estática

Valores em USDT dos ledgers BASE das contas originais. Excluir trades e os respetivos PnL líquidos não refaz a trajetória de sizing, entradas ou carteira. Valores negativos não provam que uma estratégia de tendência seja economicamente inválida.

| Estratégia | Total fechado | Sem maior vencedor | Sem 2 maiores | Sem 3 maiores | Top3 / lucro líquido total fechado |
|---|---:|---:|---:|---:|---:|
| SOL 4h | +3589.58 | +1614.25 | +502.88 | -526.02 | 114.7% |
| BNB 30m | +1927.91 | +1264.31 | +639.24 | +61.77 | 96.8% |
| ETH 1h | +1893.10 | +800.45 | -134.28 | -975.14 | 151.5% |
| BNB 5m | +1673.93 | +893.79 | +271.98 | -317.82 | 119.0% |
| SOL 30m | +2453.67 | +247.56 | -1213.34 | -2433.56 | 199.2% |
| BNB 15m | +1074.49 | +414.47 | -216.79 | -759.60 | 170.7% |
| DOGE 4h | +1566.29 | +730.77 | -17.05 | -757.13 | 148.3% |

Nenhuma das sete fica negativa retirando apenas o maior vencedor. Quatro ficam negativas retirando os dois maiores; seis ficam negativas retirando os três maiores. BNB30m conserva apenas +61,77 USDT após retirar os três, insuficiente para certificar robustez. A percentagem top3/lucro líquido pode exceder 100%; não confundir com top3/soma de todos os ganhos positivos, também presente no JSON.

## Regimes e incerteza

PnL anual por ANO DE SAÍDA, incluindo todo o PnL de cada trade fechado nesse ano; não são retornos anuais de equity nem atribuição diária de risco.

| Estratégia | 2023 USDT | 2024 USDT | 2025 USDT | Intervalo descritivo 95% da média R |
|---|---:|---:|---:|---:|
| SOL 4h | +3169.18 | +347.31 | +73.09 | [-0.119; +2.235] |
| BNB 30m | -6.48 | +1429.56 | +504.84 | [-0.213; +1.300] |
| ETH 1h | +780.85 | +502.61 | +609.64 | [-0.263; +1.521] |
| BNB 5m | +30.95 | +800.44 | +842.55 | [-0.218; +0.988] |
| SOL 30m | +4616.39 | -998.78 | -1163.95 | [-0.288; +0.891] |
| BNB 15m | +132.89 | +1102.03 | -160.44 | [-0.336; +1.017] |
| DOGE 4h | +64.26 | +977.62 | +524.41 | [-0.259; +0.954] |

Bootstrap: 12 blocos por trimestre de saída, 20 000 reamostragens, seed 20261020, média ponderada pelo número de trades de cada amostra. Todos os intervalos incluem valores negativos. Isto indica incerteza elevada; não demonstra expectativa negativa. É uma descrição de um histórico já selecionado, com poucos blocos, sem correção pela pesquisa de múltiplos ativos/timeframes, sem assegurar independência entre blocos ou estratégias. Não é probabilidade de lucrar no futuro nem OOS. Trades longos podem atravessar trimestres. Nenhuma promoção depende deste intervalo novo.

SOL30m tem todo o ganho agregado ancorado em 2023 e perdas em 2024 e 2025: é a lane de menor prioridade nesta auditoria. SOL4h tem o maior ganho/perda e expectativa histórica, mas 2023 representa cerca de 88% do PnL fechado agregado e 2025 só +73,09 USDT. ETH1h é positivo nos três anos, mas 47 observações e concentração em dois vencedores não certificam independência.

## Custos, frequência e sobrevivência

Tabela apenas dos trades FECHADOS BASE. Funding positivo é crédito recebido. Os totais globais do modelo, que podem incluir fees/funding de posição final aberta, ficam separados no JSON.

| Estratégia | Preço após slippage | Fees | Funding assinado | Líquido fechado | Mediana dias | Máximo dias | Maior sequência de perdas |
|---|---:|---:|---:|---:|---:|---:|---:|
| SOL 4h | +3961.50 | −177.22 | -194.70 | +3589.58 | 2.67 | 27.25 | 9 |
| BNB 30m | +1880.03 | −182.62 | +230.50 | +1927.91 | 6.51 | 82.19 | 7 |
| ETH 1h | +2470.66 | −170.71 | -406.85 | +1893.10 | 4.79 | 57.40 | 8 |
| BNB 5m | +1645.92 | −252.34 | +280.35 | +1673.93 | 3.98 | 74.11 | 10 |
| SOL 30m | +3229.86 | −526.45 | -249.74 | +2453.67 | 1.77 | 38.56 | 11 |
| BNB 15m | +1048.47 | −230.36 | +256.38 | +1074.49 | 5.02 | 73.54 | 16 |
| DOGE 4h | +1882.34 | −150.10 | -165.94 | +1566.29 | 1.12 | 16.00 | 9 |

A sequência histórica de até 16 perdas é compatível com a baixa taxa de acerto; não é um limite máximo futuro. Há apenas 44–122 trades por lane em TRÊS ANOS, com posições que duraram até 82 dias. BNB5m não é um scalp de cinco minutos nem uma fonte de rendimento diário. O risco de gap, stop enfraquecido, mercado correlacionado e falha de venue não foi quantificado como distribuição de perdas extremas. Sem isso, nenhum franco de capital real é defendido aqui.

O original usa stop inicial LONG −4%, SEM TP fixo, e trailing 12% abaixo do pico condicionado por ganho >=5% em fecho do próprio TF, NONLATCHED. O stop pode voltar a afrouxar; os observadores Telegram não demonstram aceitação de stop pelo broker. Impor agora alvo 2R, trailing monotónico, tomada parcial ou cooldown mudaria a experiência. Não foi feito.

## Decisões

- **SOL4h, BNB30m, ETH1h, BNB5m, BNB15m e DOGE4h: INCONCLUSIVO quanto a edge líquido independente.** Há assimetria positiva histórica; faltam validação não contaminada e execução/custos completos. Podem permanecer como hipóteses/controlo sob regras existentes. Não justifica novas variantes ou infraestrutura.
- **SOL30m: DESPRIORIZAR para novos recursos**, por duas perdas anuais consecutivas e concentração em 2023, sem declarar que jamais poderá ganhar.
- **Nenhuma das sete é DIAMANTE CANDIDATO. Nenhuma é rejeitada apenas por ter poucos acertos ou por depender de caudas.** Não há prova para trading real, nem renda previsível, nem extrapolação com 10×.
- Se se mantiver uma investigação estritamente sobre V11/V12, SOL4h e BNB30m são comparadores históricos descritivos úteis, não vencedores de seleção OOS. O próximo recurso só compensa se produzir evidência prospectiva independente já autorizada e preços executáveis do caminho completo. Repetir os mesmos 2023–25 ou gerar mais variantes não fecha a lacuna.

Não existe um pagador estrutural identificado nestes ledgers. O mecanismo observado é captura de grandes movimentos longos após pullbacks; isto não prova prémio económico persistente, arbitragem ou remuneração contratual por fornecer proteção/liquidez. Portanto esta auditoria também não satisfaz sozinha a missão payer-first.

## Evidência e reprodução

- Originais 4TF: [PR215](https://github.com/joseluisvieira28-oss/Laboratorio/pull/215), producer run [38432883246](https://github.com/joseluisvieira28-oss/Laboratorio/actions/runs/38432883246), master artifact 11831602875.
- Original native5m: [PR217](https://github.com/joseluisvieira28-oss/Laboratorio/pull/217), producer run [38435206427](https://github.com/joseluisvieira28-oss/Laboratorio/actions/runs/38435206427), master artifact 11833106063.
- 4TF source artifacts usados: SOL 11831078628; DOGE 11831058673; ETH 11831023679; BNB 11830584859. Native5m BNB 11832357900.
- Taxonomia observadores e regras: [PR242](https://github.com/joseluisvieira28-oss/Laboratorio/pull/242), commit 5eff9d6209ea5b2a0dc432cf7950c700e2d62599. Sinais Telegram não são trades fechados; não se contou cada alerta como nova operação.
- 5/5 ZIPs producer SHA256 idênticos ao digest GitHub; 5/5 RESULT.json idênticos aos hashes dos masters; 14/14 ledgers reconciliados trade a trade: preço − fees + funding = net, N/wins/PF/anos/top3 concordam com RESULT. A conferência valida custódia/contabilidade, não os pressupostos de mercado nem rentabilidade.
- `AUDIT_SCOPE.md` declara explicitamente que os resumos históricos já tinham sido vistos. Não se apresenta este trabalho como freeze pré-outcome. `metrics.json` contém métricas completas dos dois custos e hashes dos ledgers.
- Para reproduzir: colocar os sete ZIPs nas pastas `source/`, extrair cada producer em `source/ARTIFACT_ID/`, os masters em `source/4tf/` e `source/5m/`, guardar os metadados GitHub dos producers em `source/artifacts_38432883246.json` e `source/artifacts_38435206427.json`, instalar NumPy e executar `python audit.py`. O script não faz pedidos de rede nem importa motores/brokers.

**Limite final: auditoria independente do cálculo sobre dados antigos, não validação independente de vantagem económica. Main, Windows, alertas, parâmetros e holdouts preservados.**
