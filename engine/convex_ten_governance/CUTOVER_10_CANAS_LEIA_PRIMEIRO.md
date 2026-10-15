# CRYPTO LAB — CUTOVER DE 10 CANAS (read-only; one at a time)

**Data:** 15 outubro 2026. **Objetivo:** preservar exatamente 10 sinais (V07 3 + V11 3 + V12 4) e recuperar robustez da observação, não autorizar trading.

## Estado atual confirmado pelo operador
- V07, V11, V12 anteriormente **Running com relatórios frescos**. Há interrupção V07 documentada anteriormente, recuperada pelo operador.
- V07 instalado SHA256 `6c1173cdb678629552424c5074035b44f81be2af6331084fb7742f4381b7004c`; V11 `057812c1cb3164347bdf7afe01b419dd3fcbfe921b5013ba5bce219e938426e9`.
- PR237 corrigido V2 tem SHA EXE V07 `99d06384268d649b2224a10fa9d231ad8ce78fb6ced8aaee4389f12d86e12e84` e V11 `8143e21de4cefb59c896fbb706d59def525ff9d459cdb36e182bf0bdd33db3bc`. V2 pacote manifest commit `d31a4be82c8eed8d08cd9fba54567573b9153391`. O operador passou `VERIFICAR_PACOTE.ps1`, ambas EXE --self-test PASS. **Instalação V2 ainda não feita.**
- PR239 V12 source-isolation + clock correction CI 14 tests Windows/Linux + standalone build PASS. Usar APENAS [artefacto corrigido PR239 #12000715498](https://github.com/joseluisvieira28-oss/Laboratorio/actions/runs/38792104517/artifacts/12000715498), NÃO a primeira versão V12 original.
- OPTIONS watcher antigo `CryptoLab-OPTIONS-V21-Telegram-Watcher` foi desativado pelo operador. Não alterar MEXC Futures executores/stop supervision.
- Saúde, zero pendientes e Running NÃO provam sinal real→ Telegram.

## Limites
- Um único observador substituído por operação, nunca três simultaneamente.
- **Não apagar/copiar DPAPI secrets**, não alterar as 10 estratégias nem parent-V5.
- **Sem ordens MEXC, sem live trading, sem merge `main`**; nenhum scripts novos fazem requests HTTP. Watchers durante operação mantêm comportamento read-only original.
- Backup SQLite **só depois** da tarefa parar e de não existirem processos EXE, capturando WAL e metadados. Backups sob `%LOCALAPPDATA%\CryptoLab\CONVEX10_BACKUPS\<V07|V11|V12>\<UTC>` contêm histórico de sinais e POSSIVELMENTE dados de conta; **não enviar backups para ChatGPT/GitHub**.
- Se ocorrer entrega Telegram durante uma execução que falhe, o rollback **mantém o SQLite atual** para evitar repetir mensagens já enviadas. Restaurar os DBs antigos indiscriminadamente poderia repetir eventos.
- Desligar o watcher durante atualização pode perder definitivamente sinais dentro da janela científica de 180 segundos; downtime reportado; nunca tratar período sem observação como NO_SIGNAL.
- Se falha externa persistente impedir `sources_ok`, corte reverte executável mas não apaga o ledger/outbox. Inspecionar status e tarefas posteriormente. Não prometer zero perdas ou exactly-once.

## Descarga de 3 pacotes separados
1. [Pacote corrigido V07 + V11 PR237](https://github.com/joseluisvieira28-oss/Laboratorio/actions/runs/38754922098/artifacts/11983865584). Extrair ZIP do GitHub numa pasta A. Tem `BUILD_MANIFEST.json`, `V07_AUDIT_PREVIEW.exe`, `V11_AUDIT_PREVIEW.exe`.
2. [Pacote corrigido V12 PR239](https://github.com/joseluisvieira28-oss/Laboratorio/actions/runs/38792104517/artifacts/12000715498). Extrair ZIP do GitHub E o ZIP interno numa pasta B. Tem `V12_FinalFour_Signals.exe`, `RUN_V12.ps1`, `SHA256_EXE.txt` e o inventário Telegram.
3. [Este pacote de scripts operacional](link do workflow da branch — publicado na CI). Extrair numa pasta C. Não contém EXEs MEXC nem quaisquer chaves.

## PASSO 0 — Só preflight, sem mutações
No PowerShell na pasta C, definir caminhos REAIS da tua máquina:
```powershell
$V2 = 'C:\CAMINHO\PARA\PASTA_A'
$V12 = 'C:\CAMINHO\PARA\PASTA_B'
powershell.exe -NoProfile -ExecutionPolicy Bypass -File .\ATUALIZAR_UMA_CANA_READONLY.ps1 -Version V07 -PackageDir $V2 -Mode Preflight
powershell.exe -NoProfile -ExecutionPolicy Bypass -File .\ATUALIZAR_UMA_CANA_READONLY.ps1 -Version V11 -PackageDir $V2 -Mode Preflight
powershell.exe -NoProfile -ExecutionPolicy Bypass -File .\ATUALIZAR_UMA_CANA_READONLY.ps1 -Version V12 -PackageDir $V12 -Mode Preflight
```
O resultado esperado de cada uma: `PREFLIGHT_PASS_NO_CHANGES`. Se pacote não encontrar os EXEs porque existe ZIP dentro de ZIP, extrair essa camada. **Se qualquer uma falhar, parar.**

## PASSO 1 — Aplicação controlada, UMA de cada vez, somente após preflight PASS
```powershell
powershell.exe -NoProfile -ExecutionPolicy Bypass -File .\ATUALIZAR_UMA_CANA_READONLY.ps1 -Version V07 -PackageDir $V2 -Mode Apply -Approval CONFIRMO_10_CANAS_READONLY
```
Exigir `CUTOVER_PASS` com nova fonte OK e backup. Depois verificar `ESTADO_10_CANAS_READONLY.ps1`, e só então aplicar V11:
```powershell
powershell.exe -NoProfile -ExecutionPolicy Bypass -File .\ATUALIZAR_UMA_CANA_READONLY.ps1 -Version V11 -PackageDir $V2 -Mode Apply -Approval CONFIRMO_10_CANAS_READONLY
```
Verificar de novo, depois V12:
```powershell
powershell.exe -NoProfile -ExecutionPolicy Bypass -File .\ATUALIZAR_UMA_CANA_READONLY.ps1 -Version V12 -PackageDir $V12 -Mode Apply -Approval CONFIRMO_10_CANAS_READONLY
```
**Não executar 2 comandos Apply em simultâneo.** V07 ainda faz MEXC GET de observação, não POST privado. V11/V12 não exigem credenciais MEXC.

## PASSO 2 — Recibo após três fases
```powershell
powershell.exe -NoProfile -ExecutionPolicy Bypass -File .\ESTADO_10_CANAS_READONLY.ps1
```
Verificar `all_three_monitors_healthy: true`, V07/V11 `matches_audit_v2: true` e V12 `total_inventory: 10`, bem como OPTIONS antigo `Disabled`.
Ainda faltará uma prova REAL `signal_id→Telegram message_id→mensagem visível`, sem sintetizar sinais em produção.

## Fallo e rollback
`CUTOVER_FAIL_CLOSED` informa `Recovery`. O script tenta repor executável e runner originais e reiniciar apenas a tarefa escolhida, conservando SQLite atual para não reabrir sinais enviados. Se `Recovery` não confirmar `ORIGINAL_EXE_RESTART_REQUESTED...`, interromper operações e investigar; **não tentar Apply repetidamente**.
O backup da pasta data é para recuperação manual orientada, nunca restaurá-lo automaticamente após envio. Se for necessária recuperação manual, auditar primeiro outbox/ACK/estado dos três monitores.

## Limitação
CI Windows testa sintaxe, contratos estruturais e fixture de falha fechada para os scripts, não Windows Scheduled Tasks reais nem DPAPI do operador. O cutover será evidenciado apenas pela saída PowerShell no PC e verificações pós-atualização. Nenhuma entrega real Telegram é simulada como prova.
