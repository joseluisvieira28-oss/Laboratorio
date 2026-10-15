# CONVEX V07/V11 — continuação operacional V2

Esta revisão continua a auditoria do PR #237. O [relatório inicial](CONVEX_V07_V11_INDEPENDENT_AUDIT_2026-10-15.md) e os receipts originais ficam preservados. Sem rollout Windows, alterações de tarefas, credenciais, ordens, merge main ou abertura de holdouts.

## Reparações adicionais

1. **Isolamento de fontes**: V07 e V11 guardam sinais válidos por símbolo antes de tentar o próximo. Falha BNB deixa de eliminar sinal SOL validado. Status distingue `source_status` por símbolo; V11 reporta `V11_DEGRADED_READONLY` se alguma fonte/Telegram falhar. Alterámos explicitamente o teste antigo que exigia supressão global para exigir preservação da fonte saudável. Nenhuma regra de sinal foi mudada.
2. **Cobertura persistente**: SQLite recebe tabelas `observer_coverage`, `observer_gaps`, `observer_lane_health`. Fecho UTC por lane fica classificado como SIGNAL_QUEUED, NO_SIGNAL, SOURCE_FAILED, WARMUP_INSUFFICIENT, EXPIRED_CLOSE, NOT_AT_TF_BOUNDARY ou UNVERIFIED_HISTORY. Intervalos não visitados entre ciclos são registados compactamente; reinício preserva gaps. Uma falha posterior não apaga decisão já comprovada no mesmo fecho. `latest_close_state` distingue a decisão preservada da última tentativa/falha. Esta cobertura começa na ativação original gravada: não reabre outcomes nem inventa dados retroativos. Fechos não observados não são chamados sinais perdidos, porque não sabemos se teriam sinal.
3. **Releitura de relógio após recolha**: produção usa nova leitura pública Binance antes de avaliar sinais e antes de drenar filas. Se recolha demorar além da elegibilidade de 180s, não promove o fecho antigo a sinal fresco. `collection_elapsed_ms` mostra o tempo decorrido desde o snapshot de recolha (cumulativo por símbolo em V11). Não equivale a latência real ACK: essa métrica ainda requer receipt no PC.
4. **Telegram e continuidade V11**: deteção persiste novos sinais mesmo quando Telegram falha; tentativa de envio acontece depois da deteção e erro fica no relatório. Não existe guarantee de envio exatamente uma vez no intervalo ACK/crash.
5. **Estado V07**: falha Telegram/SQLite/WatchHalt substitui JSON anterior por receipt de falha com UTC e pendentes; não deixa apenas um sucesso antigo com aspeto saudável.
6. **Empacotamento com execução real offline**: ambos entrypoints têm `--self-test` sem data-dir/credenciais. O próprio EXE carrega parent V5, produz fixture positiva nas três lanes respetivas, rejeita vela aberta e verifica fila/deduplicação em SQLite temporária e mensagem NÃO É ORDEM. Workflow exige sucesso desse teste além de --help. O pacote inclui verificador SHA256 e o receipt Windows de leitura. Zero requests/envios reais nesses testes.

## Prova local

180 testes: 50 V05 + 75 V06 + 22 V07 + 12 V11 + 21 auditoria. [Log](evidence/convex-v07-v11-2026-10-15/CONTINUATION_V2_LOCAL_TESTS.txt). Os dois self-tests passaram em Python local; o CI Windows valida posteriormente os EXEs empacotados. Testes novos incluem falha parcial por ativo, falha Telegram durante recolha, gap persistente após reinício, preservação de decisão NO_SIGNAL perante falha posterior e atraso de fetch que expira sinal antes da avaliação.

## Pacote e próximo passo local

O artifact `CONVEX_AUDIT_PREVIEW_NOT_INSTALLED` inclui dois EXEs isolados, BUILD_MANIFEST.json, VERIFICAR_PACOTE.ps1, WINDOWS_READONLY_RECEIPT.ps1 e instruções. O manifesto identifica o commit e hashes de EXEs/scripts/documentação; não é uma assinatura digital independente. `VERIFICAR_PACOTE.ps1` apenas verifica o pacote e executa testes offline temporários; não instala nem altera os monitores ativos.

Não iniciar estes previews sobre as SQLite ativas. Primeiro comparar o receipt Windows instalado com o artifact original. Troca efetiva exige plano de backup/rollback e confirmação para parar/substituir tarefas existentes, conforme limite original do operador. Nenhuma confirmação nova é necessária para testar o pacote offline.

## Limites mantidos

- Internet/PC indisponível >180s pode impedir deteção elegível. Esta revisão torna buracos visíveis; não alarga ciência, não gera sinais retroativos e não mantém hardware ligado.
- Fila é durável e deduplicada, mas aceitação Telegram seguida de crash antes de commit pode duplicar. ACK não prova leitura humana.
- Loop continua sequencial; recolha muito lenta e leituras de conta V07 podem atrasar ciclos. A releitura de relógio protege frescura e regista o problema, não cria SLA.
- Feed REST vs arquivo original e RSI com warmup móvel não têm paridade externa integral provada. Histórico favorável continua sem OOS/forward económico independente para MEXC.
- SQLite modificada apenas em fixtures locais/CI. Instalação real, lifecycle DPAPI/Task, hashes instalados e sinal real→ACK Telegram continuam NÃO VERIFICADOS neste trabalho.

**Veredito: a garantia universal continua NÃO. O preview corrigido tem mais cobertura auditável e testes, mas não está instalado no PC e não constitui GO operacional/económico.**

## Receipt final V2

- Código: `d31a4be82c8eed8d08cd9fba54567573b9153391`.
- [CI 38754922098](https://github.com/joseluisvieira28-oss/Laboratorio/actions/runs/38754922098): Windows job `116490702076` e Linux job `116490702246` SUCCESS. Logs lidos: **180 testes por OS**. Os dois EXEs passaram `--self-test`; verificador do pacote também passou em Windows CI. Nenhum secret, request MEXC ou envio Telegram real usado.
- [Pacote V2 11983865584](https://github.com/joseluisvieira28-oss/Laboratorio/actions/runs/38754922098/artifacts/11983865584): descarregado independentemente; hashes de ambos EXEs, scripts e README conferidos com manifesto. [Receipt](evidence/convex-v07-v11-2026-10-15/V2_ARTIFACT_HASH_VERIFIED.json).
- SHA256 ZIP: `c32017479528fd2b73899567f51fb4e7f096a3a8ca4222db64b5e83538663c27`.
- V07 preview EXE SHA256: `99d06384268d649b2224a10fa9d231ad8ce78fb6ced8aaee4389f12d86e12e84`.
- V11 preview EXE SHA256: `8143e21de4cefb59c896fbb706d59def525ff9d459cdb36e182bf0bdd33db3bc`.
- Prova local adicional: simulação de TelegramHalt no loop V07 confirmou saída 2 e substituição de OLD_SUCCESS por NO_TRADE_MONITOR_BLOCKED com checked_at_utc. Sem rede.

Para verificar no PC, extrair o pacote numa pasta nova e executar nessa pasta:

```powershell
powershell -NoProfile -ExecutionPolicy Bypass -File .\VERIFICAR_PACOTE.ps1
powershell -NoProfile -ExecutionPolicy Bypass -File .\WINDOWS_READONLY_RECEIPT.ps1
```

Primeiro comando valida apenas pacote e fixtures temporárias. Segundo lê os monitores atuais. Nenhum instala, pára tarefas, altera secrets ou envia Telegram. A saída sanitizada do segundo é a prova pendente para comparar hashes/estado local; não é necessário fornecer qualquer token ou chave.
