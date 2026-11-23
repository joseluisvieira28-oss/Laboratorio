# CRYPTO LAB — REACTIVE-SHOCK-SCALP-005 R1 | TERMINAL ECONOMIC CLOSEOUT

**Data:** 2026-11-17 UTC  
**Identidade:** REACTIVE-SHOCK-SCALP-005 / `FROZEN_DISCOVERY_REPLICATION_R1`  
**Veredito congelado:** `REPLICATION_FAILS_STRICT_GATE` / `NO_LIVE_GO`.  
**Tipo:** auditoria ex-post do recibo original, apenas append-only. **Não** altera regras, sinais, custos, resultados ou holdouts.

## Cadeia de evidência

- Freeze anterior aos outcomes: `research/microstructure_scalping/REACTIVE_SHOCK_SCALP_005_REPLICATION_R1_FREEZE_V0_1.md` de 2026-09-26 na branch `microstructure-scalping-lab-v0.1`.
- Manifesto original: `research/microstructure_scalping/REACTIVE_SHOCK_SCALP_005_REPLICATION_R1_MANIFEST.json` — 14 anúncios 2023 (7 CPI, 7 NFP), sem sobreposição com os 8 da Discovery inicial.
- Runner: branch isolada `research/reactive-shock-r1-frozen-2026-11-17`; reutiliza `eval_variant` da versão original, com a correção da aritmética short; não houve retuning.
- GitHub Actions concluído: https://github.com/joseluisvieira28-oss/Laboratorio/actions/runs/44039539878 — conclusão técnica `success`, distinto do resultado económico.
- Artifact ID `14308379885`, digest ZIP SHA256 `61beeb6392a734380f7f98ce48a7dd29bb968f18541252475f0410a69573346f` **confirmado por recomputação local**.
- Único membro ZIP `reactive_shock_r1_economic_receipt.json` SHA256 `0a2cb9c9d14112bec78421fee64971f4405496657b3a9dd75bf8ace0c514062a` **recomputado**.
- Manifesto SHA256 `5a8576cdf2747dc1b3bf39a8ddedd5669848808270231655f1645c2d603fdd82` registado no recibo, sem recomputação independente do manifesto aqui.
- Receipts contêm 14 pares de SHA256 e tamanhos dos arquivos L2/trades da Bybit. **Os arquivos de mercado brutos não foram recuperados e re-hashados fora do runner** nesta auditoria.

## Reprodução estatística e económica

Recalculei todos os 12 resultados resolvidos a partir dos retornos gross, e verifiquei as identidades `net_fee_only = gross -16bps`, `net_stress10 = gross -26bps`, `net_stress20 = gross -36bps`. Reproduzi o bootstrap exato de 5.000 amostras com seed 20260926 e as 9 condições congeladas.

| Indicador | Resultado |
|---|---:|
| Anúncios fonte complete | 14/14 |
| Operações com resultado contabilizado | 12/14 |
| CPI resolvido | 5/7 |
| NFP resolvido | 7/7 |
| Eventos `NO_SIGNAL_OR_OUTCOME` | 2023-06-13 CPI; 2023-09-13 CPI |
| Média taker/taker bruta BBO (proxy Bybit) | **−7.2294484795 bps** |
| Média após 16 bps de comissão MEXC API proxy | **−23.2294484795 bps** |
| Média após comissões + 10 bps stress | **−33.2294484795 bps** |
| Mediana após stress | −16.0887456294 bps |
| Média CPI stress | −51.5774551474 bps |
| Média NFP stress | −20.1237294310 bps |
| Positivos após stress | 4/12 |
| IC95 bootstrap média stress | **[−78.1669088895, +3.6777468232] bps** |
| Gates congelados satisfeitos | **2 de 9**: n≥12 e NFP n≥6 |
| Veredito | **REPLICATION_FAILS_STRICT_GATE** |

A designação `NO_SIGNAL_OR_OUTCOME` não permite distinguir um bloqueio de sinal de um desfecho em falta; não se inventou PnL para esses dois eventos. O protocolo exigia ≥6 CPI resolvidos e faltou 1; os outros 6 critérios económicos negativos tornam o resultado inequívoco nesta implementação.

## Sensibilidade DESCRITIVA, não admissível para rescate

- Excluindo apenas a pior operação (2023-03-14 CPI, stress10 −235.288874 bps): a média dos 11 restantes ainda é **−14.8604097918 bps**.
- Excluindo as duas piores: média dos 10 restantes **−4.8221021045 bps**.
- Leave-one-out simples: a média de cada conjunto de 11 permanece negativa.
- Sem deduzir qualquer fee, o retorno gross já é negativo em média **−7.23 bps**. Trocar apenas de exchange/tarifa não torna esta regra rentável na amostra.

As exclusões são diagnósticas e não alteram o veredito congelado, a lista de eventos ou a contagem de trading.

## Limitações / firewall

- BBO histórico Bybit, **não** preço de execução real na MEXC; slippage real, latência, spread efetivo e falhas de preenchimento não foram demonstrados.
- 2023 constitui **Discovery/replicação histórica**, não validação prospetiva independente de 2025/2026.
- Não foram revalidados os 14 arquivos raw Bybit contra os hashes do runner; as verificações criptográficas aqui incidem sobre o ZIP do artifact e JSON do recibo.
- Sem trading, operações, API privada, wallets, merges, alteração de freezes ou custos.

**DECISÃO FINAL:** encerrar este identificador de scalping (`FLOWPRICE_W2`, observação 2 segundos, saída após 60 segundos) como `REPLICATION_FAILS_STRICT_GATE / NO_EDGE_AT_TESTED_DEFINITION / NO_LIVE_GO`. Não voltar a afinar horizontes, mercados, stops ou custos sobre estes outcomes já vistos; qualquer hipótese economicamente distinta exige fonte, ID e freeze próprios antes de abrir os seus outcomes.

## Continuidade: investigação adjacente, sem misturar resultados

O NFP V0.3B tem hipótese **diferente** (surpresa macro real vs consenso pré-release, 08:31→08:45, BTC/ETH spot). O master ZIP original de 16.320 bytes foi obtido do Drive, com SHA256 exato `5b0539d9a59b0a5fadd2a749d0319a0c6b9b8d4e76e58d7ae1b2405536b75c3e`, seis membros e runner congelado presentes. Porém o worklist original T02 (`NEWS_SHOCK_V03B_NFP_CONSENSUS_WORKLIST_P2_T02_V0.1.json`, dentro do tranche02 ZIP histórico SHA de referência `0751d132512f38b4f39a937a42339446cb2bea29a0dd5899d9508b29d105a381`) permanece sem bytes independentes acessíveis. Não foi substituído por lista reconstruída nem iniciada a Discovery. Estado: `T02_SOURCE_BLOCKED / DISCOVERY_NOT_RUN / NO_LIVE_GO`. Fonte V15 já documentou o mesmo bloqueio em 2026-11-16; esta passagem apenas reconfirmou os pontos acessíveis.