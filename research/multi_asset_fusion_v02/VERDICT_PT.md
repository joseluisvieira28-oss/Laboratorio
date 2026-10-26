# Fusion Multi-Asset V0.2 Source Recovery

**Veredito: source gate PASS; replay executado; edge não certificado. Descoberta exploratória, não OOS.**

Protocolo congelado no commit `9c2e9456877093ecb4f74cdd8a63aabae21de0ce`, antes de leitura/cálculo de resultados económicos desta execução. Lacunas e plano de recuperação já conhecidos: não é pré-registo independente. V0.1 preservada em `ac6e9d22328c2b91a46b7b16bfdcb9a577aa6d6d`.

## Integridade e execução

319/319 ZIPs mensais e CHECKSUMs coincidem com a auditoria original e foram novamente validados. Os oito meses incompletos permanecem inalterados. 20/20 ZIPs diários oficiais e CHECKSUMs recuperam apenas os 10 D1 e 240 H1 permitidos. Nenhuma observação existente foi substituída; a diferença de timestamps é exatamente a whitelist. API USD-M: 250/250 candles iguais nos primeiros 11 campos numéricos. OHLCV D1 igual à agregação H1 nos dez dias/ativo.

As capturas anteriores da API foram encontradas localmente, conferidas com o manifesto SHA256 e recibos públicos de pedidos, e incluídas no pacote; não são apresentadas como novos pedidos à API. A primeira captura continha timeout em SOL H1 fevereiro; o recibo retry contém a resposta integral. Os arquivos mensais locais foram conferidos com os hashes da versão exata do GitHub. A cópia local inicial da auditoria diferia byte a byte e foi substituída apenas no diretório V0.2 pela referência exata antes do PASS.

Código de saída do gate e replay: **0**. Duas execuções independentes geraram report, ledger, manifest, provenance e source_gate byte a byte idênticos. **26/26 testes de regressão e 8/8 de recuperação aprovados**. As primeiras tentativas de testes falharam por permissões de limpeza no diretório temporário do Windows; repetidos com temporários no workspace, passaram sem alteração da estratégia. Falhas iniciais e logs preservados.

## Resultados por custo

Cesta descritiva com peso igual nos cinco ativos, AVAX excluído. Médias por todos os 730 dias; bps aditivos, sem capitalização, não são retornos de carteira executável.

| Custo roundtrip (bps) | Fusion bps/dia | Baseline bps/dia | Diferença bps/dia |
|---:|---:|---:|---:|
| 0 | 7.822076 | 6.688621 | 1.133455 |
| 4 | 4.742624 | 2.690813 | 2.051811 |
| 8 | 1.663172 | -1.306995 | 2.970167 |
| 14 | -2.956006 | -7.303708 | 4.347702 |
| 20 | -7.575184 | -13.300420 | 5.725236 |

## Ativos — cenário 14 bps

| Ativo | Fusion bps/dia | Baseline bps/dia | Diferença | p Holm25 |
|---|---:|---:|---:|---:|
| SOLUSDT | 4.695911 | -1.746422 | 6.442333 | 0.052895 |
| ETHUSDT | -7.158683 | -10.158052 | 2.999369 | 0.212779 |
| BNBUSDT | -4.720255 | -7.251860 | 2.531605 | 0.545945 |
| XRPUSDT | -5.921447 | -11.180400 | 5.258954 | 0.212779 |
| LINKUSDT | -1.675557 | -6.181804 | 4.506247 | 0.393561 |

Todos os 25 testes primários, intervalos e p-valores estão em `replay-final/report.json`. A 14 bps nenhum dos cinco testes tem p Holm25 < 0,05. A 20 bps SOL e BNB têm p Holm25 < 0,05 para a diferença face ao baseline; isso é uma comparação relativa condicionada ao custo, não certificação de rentabilidade ou edge. A melhoria com custo maior decorre também da redução de operações. Nenhum cenário foi selecionado ou otimizado após os resultados.

## Robustez e limitações

O relatório JSON inclui todos os ativos/custos por ano e direção, remoção dos 1/3/5 maiores ganhos, correlação diária, leave-one-out, bootstrap pareado estratificado por ano L30 com 10.000 réplicas seed 271 e Holm25, preservados do código V0.1. A referência AVAX é exposta e fica fora dos 25 testes e da cesta.

A 14 bps, todos os leave-one-out mantêm média Fusion negativa (entre -4,869 e -1,905 bps/dia). Correlações fora da diagonal: 0,530–0,722. Cesta Fusion: total aditivo -2157,885 bps; removendo os 1/3/5 maiores ganhos: -2637,961 / -3468,244 / -4133,625 bps. Logo, melhoria sobre baseline não equivale a rentabilidade líquida.

Persistem seleção de sobreviventes, investigação prévia, ativos correlacionados, multiplicidade histórica desconhecida, revisões atuais dos arquivos e opens OHLC como proxies de execução. Os IC e p-valores seguem exatamente o método exploratório V0.1; não constituem confirmação independente. Sem holdout ou validação de fills.

2024–2026 permaneceu fechado. Sem interpolação, exclusão de datas/ativos, tuning, ordens, live/paper trading, contas, APIs privadas, wallets, deploy, despesas, alteração de main, PR #271/#272 ou merge.

## Evidências

- `protocol.json`: contrato congelado; `run.py` e `reference_replay.py`: gate e replay.
- `replay-final/manifest.json`: 339 pares com URLs e SHA256.
- `replay-final/provenance.json`: exatamente 250 inserções; zero substituições.
- `recovery_inputs.zip`: 20 ZIPs diários, CHECKSUMs, oito corpos API e recibo retry.
- `replay-final/report.json` e `daily.csv`: resultados completos e ledger de 4380 linhas.
- `reproducibility.json`, logs de testes e `SHA256SUMS.json`: reprodução e hashes.
