# POLYMARKET-DIAMANTE-006

26 de novembro de 2026 · Continuação do PR #404 · Investigação exclusivamente offline

**NO-GO para avançar com capital ou com um ensaio prospetivo de 30 dias.** Nenhuma variante taker passou a validação pré-especificada. A execução passiva/híbrida e o sinal de oráculo continuam SOURCE_BLOCKED para a amostra independente obtida.

## Reprodução de agosto

A reconstrução da DIAMANTE-005 foi novamente executada sobre os Parquets fixados. O JSON produzido coincidiu byte a byte com o do pacote anterior. Verificaram-se 21 336 165 registos, 3 553 mercados da carteira no perímetro original e +$17 271,03 líquidos modelados. O perímetro com resoluções oficiais recuperadas ficou em +$17 490,70. Sem incentivos no cálculo.

Os pares taker/taker totalizaram 1 181 563,900237 unidades e +$4 606,47, ou **+$0,0038986197 por par**. Um sobrecusto médio de 0,390 cêntimos por par bastaria para apagar o resultado agregado, mantendo as execuções originais. Os últimos três dias foram negativos no conjunto (−$368,63), mas 19 de agosto ainda foi positivo.

| Agosto UTC | Pares taker/taker | Líquido estimado |
|---|---:|---:|
| 19 | 138 385,67 | +$144,68 |
| 20 | 170 410,29 | −$215,12 |
| 21 | 190 403,73 | −$298,18 |

Esta decomposição fica condicionada às pernas efetivamente emparelhadas pela carteira. O replay desta operação inclui toda a exposição deixada por segundas pernas incompletas, mesmo se nunca houve execução do segundo lado.

## Acesso e integridade

- **Polydata5 WS**, revisão 135a5b9f8083f48b79862fb0bbb22b2bb3432246. Metadados públicos, ficheiro BTC CLOB devolveu HTTP 401 sem autenticação. O fornecedor exige conta e aceitação da partilha de informação para aceder aos ficheiros. O catálogo descreve CLOB bruto, tape, 30 s e 60 s TWAP quando presentes e cobertura geral entre 21 de agosto e 25 de novembro. A partida de cada janela pode perder 0,5 a 12 segundos. O preço de acesso não foi verificado após o gate. Gastos e subscrições zero. Não se inferiu cobertura individual de RTC/TWAP a partir do intervalo agregado.
- **PolyOrderBooks 250 ms**, revisão da05a396d41d8065dd3712ef9d6c18f1cf03e7dd. Parquet público sem login, CC BY 4.0, 198 MiB. SHA-256 c82733d9174b451919e9bd08db508af620123d2de5376f75db815be1f82b1acf. 1 719 615 linhas e 862 mercados únicos, sem duplicados no triplo mercado/token/instante amostrado nem timestamps fora da grelha. A fonte omite estados sem alterações e faz reconciliação REST de 60 em 60 segundos. Não fornece negócios individuais, sequência de eventos ou cancelamentos, nem o feed Chainlink contratual. O campo capturado é um timestamp em grelha, com informação intrabucket por verificar. Os 500 ms e 1 s são cenários de execução e não uma medição a partir do servidor.

| Abertura UTC | Mercados | Linhas | Linhas cruzadas |
|---|---:|---:|---:|
| 3 outubro, descoberta | 121 | 249 061 | 18 060 |
| 4 outubro, validação | 288 | 583 567 | 41 739 |
| 5 outubro, holdout | 288 | 572 641 | 82 803 |
| 6 outubro, holdout | 165 | 314 346 | 29 745 |

A auditoria de cobertura final leu campos estruturais do holdout e não as liquidações. O protocolo foi gravado às 11:23:53 UTC antes da descarga. SHA-256 do freeze 2c4bab724a28925cfe520191e90455f35b377423a2074d629ff94b5c78ef30e6. O resultado oficial de outubro usado no replay é a etiqueta de resolução publicada no Parquet. Não houve reconciliação Gamma independente para outubro. A amostra de confirmação contém no máximo dois dias, insuficientes para confirmação estatística neste desenho.

## Replay e auditoria adversarial

Três instantes de entrada (30/90/150 s) por hipótese, com reversão do midpoint, desequilíbrio do top-3, combinação e escolha de lado por hash como controlo. A segunda perna só é tentada quando o custo total esperado deixa pelo menos $0,005 por par. O motor reserva caixa, aplica atraso, comissões, slippage e haircut ao nível mais próximo, contabiliza IOC não preenchida e leva o inventário residual até pagar 0/1. A reutilização é simulada com 15/30 minutos adicionais depois do fecho. Entrada e cobertura (nas condições de snapshot) são separadas da liquidação, e o capital é diminuído durante a reserva. Um lote parcial pode ficar exposto mesmo com lucro na parte emparelhada. O simulador não implica que ordens virtuais teriam sido preenchidas em sessões reais. Não foram modelados mínimos oficiais, granularidade, impacto entre níveis nem custos de infraestrutura.

O protocolo fixo exigiu dois livros válidos publicados na mesma grelha durante os dez segundos anteriores à entrada. Isso deixou 4–9 mercados utilizáveis por instante na descoberta e 20–27 na validação. A melhor variante base em $500, reversão aos 90 s, marcou +$41,02 em apenas quatro entradas, duas parcialmente emparelhadas. O limiar era 30 execuções de validação e pelo menos 50 livros elegíveis por fase. Nenhum candidato passou. O holdout ficou fechado.

Após ver o problema de cobertura, executei uma **sensibilidade exploratória** usando o último snapshot publicado de cada token com idade máxima de 1 s, sem consultar o holdout. Mantive os thresholds, os horários e os dois cenários. Isto elevou a cobertura de validação para 166–182 mercados utilizáveis por instante. O preenchimento IOC continua aproximado, porque a ausência de atualização e as caixas temporais não provam que a ordem original permaneceu disponível. O máximo de 1 s pode favorecer o preenchimento; por isso esta sensibilidade não serve de confirmação independente.

| Regra exploratória, $500 | Descoberta base | Validação base | Descoberta stress | Validação stress |
|---|---:|---:|---:|---:|
| Reversão 30 s | +$31,20 | +$3,08 | +$42,88 | −$57,38 |
| Reversão 90 s | −$101,34 | +$117,72 | −$58,64 | +$62,70 |
| Desequilíbrio 90 s | −$82,79 | −$80,54 | −$41,11 | −$91,02 |
| Combinação 90 s | −$32,73 | +$98,29 | −$9,61 | +$54,93 |
| Controlo 90 s | −$79,88 | −$206,92 | −$58,17 | −$140,09 |

O desequilíbrio isolado perdeu em todos os horários na validação exploratória, em base e stress. A reversão e a combinação aos 90 s mudaram de sinal entre fases. Aos 150 s a reversão perdeu $168,24 na validação base. A hipótese de divergência do oráculo não foi executada sem referência compatível. Efeitos de fila não puderam ser distinguidos de cancelamentos com a fonte aberta. Nenhum fill maker foi imputado. Por isso a comparação maker/taker/híbrido termina com taker simulado e maker/híbrido SOURCE_BLOCKED. O WS gated pode habilitar testes de prioridade conservadora, condicionados a uma auditoria de tape, timestamps e TWAP.

### Capital reduzido

Reversão a 90 s, sensibilidade exploratória. Em $500, 46 primeiras pernas em validação base. 18 totalmente cobertas, 19 parciais, 9 sem cobertura. Ficaram 854,64 contratos residuais. Estes números incluem os custos das pernas sem hedge. Cada coluna fase parte do saldo indicado, sem transferência de PnL entre fases.

| Capital | Descoberta base | Validação base | Validação stress | Pico reservado em validação base | Pior mercado em validação base |
|---|---:|---:|---:|---:|---:|
| $100 | −$19,94 | +$4,70 | −$6,87 | $16,94 | −$4,52 |
| $250 | −$54,31 | +$45,63 | +$21,93 | $43,53 | −$11,95 |
| $500 | −$101,34 | +$117,72 | +$62,70 | $86,46 | −$24,34 |
| $1 000 | −$167,79 | +$241,65 | +$46,76 | $127,28 | −$49,12 |
| $5 000 | −$292,39 | +$123,42 | +$2,77 | $257,04 | −$153,95 |

## Decisão

- **Taker e vantagem independente:** NO-GO para as regras testadas. A variante congelada falhou a cobertura e o mínimo de execuções, e nenhuma variante da sensibilidade teve PnL positivo em ambas as fases e cenários.
- **Maker, híbrido e oráculo:** SOURCE_BLOCKED nesta amostra. O modelo precisa de negócios por token e relógio de receção verificável para estimar fila, ou do feed contratual de referência para divergência.
- **Capital pequeno e experiência de 30 dias:** NO-GO para avançar. Sem sobreviventes à validação e sem resultados de holdout abertos.
- O resultado rejeita a promoção económica das regras especificadas. Permanece inconclusiva a existência de outras regras ou sinais privados da carteira.

## Reprodução

Obter btc.parquet no revision pin da05a396d41d8065dd3712ef9d6c18f1cf03e7dd e verificar evidence.sha256. Python 3.12 e DuckDB 2.0.1. Executar replay.py e replay.py --asof a partir da pasta do pacote. O programa separa a validação da leitura de desfechos do holdout. Com --asof, recusa explicitamente --holdout. summary.json contém todos os agregados nos cinco capitais, com histórico agosto e síntese dos dois replays. O ZIP contém também cada operação simulada. O objeto Parquet pode ser recuperado gratuitamente do fornecedor sem necessidade de duplicar o ficheiro bruto no arquivo de investigação.

- [PolyData5 WS](https://huggingface.co/datasets/polydata5/polymarket-updown-5m-ws)
- [PolyOrderBooks 250 ms](https://huggingface.co/datasets/polyorderbooks/polymarket-crypto-btc-5min-250ms-l2)
- [DIAMANTE-005, PR #404](https://github.com/joseluisvieira28-oss/Laboratorio/pull/404)
