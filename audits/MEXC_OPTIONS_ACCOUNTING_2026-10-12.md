# MEXC OPTIONS / Triple Fishing — correção contabilística, 12 outubro 2026

Estado: **código preparado; reconciliação real das seis operações FAIL_CLOSED**.
Não existe evidência suficiente nos anexos recuperados para certificar 12 fills ou o PnL final da exchange. Nenhum valor ausente foi preenchido a partir de estimativas, taxas comerciais ou texto da conversa.

## Branch e âmbito

- Branch isolada: `fix/mexc-options-accounting-20261012`.
- Base efetiva: `triple-fishing-operator-v0.3-2026-09-30`, commit `a4539225674e0765eb5a5cb664b6cfbe43b6ba7d`.
- O `main` atual foi consultado inicialmente, mas não contém este executor. A branch isolada foi reposicionada sobre a fonte V03 antes das alterações; não houve escrita em `main` nem na branch de origem.
- Alterações: contabilidade do executor V03, validação do overlay histórico, consumo dos receipts OPTIONS pelo controlo de risco, módulo de validação offline, fixtures e testes.
- Estratégia, thresholds, leverage, sinais, autoridades, preços de proteção, rotas de execução, workflows e instalação não foram alterados. O caminho de saídas protegidas de outras estratégias permanece fora desta correção.

## Evidência preservada

Os dois ZIPs disponibilizados pela conversa foram lidos localmente. Há cópias integrais persistentes em `work/mexc-original-evidence/` no workspace do projeto, fora do repositório publicado. Os originais não foram modificados.

`crypto_edge_radar/tests/fixtures/mexc_options_audit/manifest.json` contém SHA-256 dos dois ZIPs e de todos os 75 ficheiros existentes nos arquivos. O campo `preserved_in_repository` distingue os receipts copiados byte a byte para fixtures dos restantes ficheiros existentes apenas nos ZIPs. Não foram publicados credenciais, ficheiros de ambiente ou dados de autenticação.

A evidência histórica anterior foi preservada como `prior_fee_hotfix_evidence.json`, proveniente do commit `51a808bcf70e89319e23ca1753cace47ffb963e7`, blob Git `9ffdff9838e1725bab8ff565caed3271d5fd66fe`. Esse resumo e o catálogo existente são proveniência de uma correção anterior; não são substitutos dos fills e históricos finais originais.

O auditor valida hashes das cópias preservadas e nunca altera receipts originais. Os **26 receipts copiados também tiveram os SHA-256 verificados diretamente nos blobs preparados para o commit**. A regra `.gitattributes` da fixture desativa conversão de finais de linha, preservando os bytes originais. O resultado reproduzível encontra-se em `MEXC_OPTIONS_ACCOUNTING_2026-10-12.json`.

## O que os anexos comprovam

Há seis operações fechadas nos receipts do bot: quatro históricas e duas V03. Há **oito registos explícitos de execução**, não doze: quatro entradas históricas e duas entradas/duas saídas V03. Os ACKs históricos identificam ordens, mas não contêm o detalhe dos fills de saída.

Nos oito registos disponíveis, `totalFee=0` é acompanhado por `takerFee` não zero. As taxas apresentadas nesses registos são `takerFeeRate=0.0008` e `makerFeeRate=0.0006`; o componente maker cobrado é zero. Estes números são observações dos receipts destas execuções, não taxas presumidas para outras operações.

| Sinal OPTIONS V2.1 | Fee entrada verificada no receipt (USDT) | Fee saída disponível (USDT) | Bloqueio |
|---|---:|---:|---|
| 2026-09-25 | 0.00672396 | ausente | fill saída + histórico final |
| 2026-09-26 | 0.00675228 | ausente | fill saída + histórico final |
| 2026-09-27 | 0.00675284 | ausente | fill saída + histórico final |
| 2026-09-28 | 0.00667659 | ausente | fill saída + histórico final |
| 2026-09-30 — V03 | 0.0334328 | 0.03393188 | histórico final |
| 2026-10-01 — V03 | 0.03392 | 0.03379312 | histórico final |

Os quatro IDs de saída históricos identificados no catálogo são `858980098269861888`, `859342455743534612`, `859704833945458176`, `860067222863828992`. Continuam necessários os receipts originais correspondentes. Os metadados de tamanho de contrato históricos também devem ser fornecidos explicitamente para validação completa, pois não constam dos estados históricos anexados.

O funding armazenado pelo V03 é `0.006` e `0.0047` USDT. É uma observação pré-fecho e não prova que esses sejam os lançamentos finais. A soma do PnL V03 armazenado é aproximadamente `-0.5896278` USDT. O valor `-0.58765` mencionado na conversa não foi certificado aqui: faltam os exports oficiais que sustentariam a diferença. A correção não substitui esses valores por números retirados do resumo da conversa.

## Comportamento corrigido

1. Componentes maker/taker cobrados têm precedência sobre o placeholder `totalFee=0`. Um total não zero conflitante provoca bloqueio. Valores ausentes, inválidos, não finitos ou em moeda diferente de USDT não se transformam em zero.
2. As quantias e as duas taxas observadas ficam associadas à identidade de cada registo de execução. A validação compara fee com preço × volume × tamanho do contrato × taxa. Ordens agregadas com componentes maker e taker simultâneos ficam bloqueadas até existirem fills individuais que demonstrem a repartição. Rebates maker negativos mantêm o sinal.
3. Funding é uma rubrica independente, com sinal, obtida do histórico final da posição; não se usa o snapshot pré-fecho para certificar o net.
4. Gross, fees e net são comparados com `closeProfitLoss`, `totalFee` e `realised` do histórico final, com tolerância absoluta de `0.00000001` USDT. Identidade da posição, símbolo, lado, volume e duplicados também são validados.
5. Os receipts brutos de saída e o histórico recebido são guardados antes da decisão contabilística. Sem prova suficiente, o executor devolve `EXIT_RECONCILIATION_REQUIRED`, não escreve um receipt de sucesso, não marca o estado como CLOSED e não liberta o slot. A entrada também conserva o receipt bruto antes de validar fees desconhecidas.
6. Um overlay histórico exige os receipts de entrada/saída e o histórico final. Hash de um receipt e IDs em ACKs, por si só, não autorizam a substituição do PnL. O controlo de risco revalida os artefactos OPTIONS e bloqueia evidência incompleta.

## Validação

Os testes correm offline. Clientes e transportes usados nos testes do executor são mocks: nenhuma conta, ordem ou bot real foi utilizado.

**94 testes passaram** na execução final. Incluem os testes de contabilidade novos e os grupos de regressão definidos na auditoria de release V03: engine, risco, overlay, slot global (incluindo concorrência entre processos), dispatcher, clientes/transportes simulados, sinais OPTIONS, DH03 e readiness Triple Fishing. `git diff --check` também passou. A pasta temporária dos testes foi colocada dentro do workspace devido às restrições de escrita do ambiente Windows.

Cobertura específica: oito receipts reais com `totalFee=0`; valores ausentes/não finitos; conflitos entre fees; rebates; zero explicitamente comprovado; taxas divergentes; volume parcial; duplicados; lados e identidades errados; funding final diferente do pré-fecho; sucesso contabilístico com histórico sintético; retenção do slot sem histórico; overlay completo e rejeição de catálogo isolado; preservação de bytes.

**Os históricos finais usados nos testes de sucesso são sintéticos e estão identificados no código. Não foram gravados como evidência oficial na fixture nem usados para certificar estas seis operações.** O auditor dos anexos devolve FAIL_CLOSED para todas as seis.

Reprodução a partir de `crypto_edge_radar`, com `PYTHONPATH=.`:

```text
python -m unittest tests.test_mexc_options_accounting tests.test_operator_futures_engine_v02 tests.test_operator_risk_v02 tests.test_build_options_v21_pnl_correction_overlay_v01
python scripts/audit_mexc_options_accounting.py --root tests/fixtures/mexc_options_audit --out audit-local.json
```

## Bloqueios e limites operacionais

- Faltam quatro registos históricos de saída e os históricos finais/export oficiais da exchange para as seis posições, incluindo funding final e resultado realizado. Não houve acesso a contas para obter esses dados.
- O executor histórico OPTIONS V02 reside noutra branch; o seu programa não foi importado nem reinstalado nesta branch V03. Os seus receipts e overlays são tratados como evidência incompleta até verificação independente.
- Se a exchange ainda não disponibilizar o histórico final imediatamente após o fecho, a posição fica contabilisticamente pendente e o slot reservado. Esta mudança não acrescenta reenvio automático nem desbloqueio automático após um reinício; a recuperação exige evidência final e reconciliação controlada.
- Fills mistos maker/taker agregados e diferenças superiores à tolerância ficam bloqueados; não se presume uma repartição ou arredondamento.
- Não foram feitos testes em conta real, ordens, ativação, deploy, merge ou gastos. A publicação da branch é entrega de código para revisão; não é aprovação operacional para usar o bot.
