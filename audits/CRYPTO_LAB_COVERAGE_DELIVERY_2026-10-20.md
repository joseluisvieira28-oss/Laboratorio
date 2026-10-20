# Crypto Lab — veredito de 20/10/2026

## Veredito
LEGACY_COVERAGE_DEBT_CONFIRMED / CURRENT_OBSERVATION_HEALTHY_AT_SNAPSHOT / UNIVERSAL_DELIVERY_NOT_PROVEN.
Inspeção Windows real, somente leitura, 18:19–18:21 UTC (20:19–20:21 Paris). Não se inferiu instalação a partir do GitHub. Nenhuma tarefa, instalação, credencial, flag, ordem ou destino Telegram alterado. Nenhum PR merged; main preservada.

## Origem exata de 135 e 2
`Coverage.record` de PR237 cria `observer_gaps` entre activation/última observação e o fecho observado. `summary` soma `(last-first)/step+1`; não conta candles em falta no cache REST nem mensagens Telegram. Intervalos persistem após restart; não são apagados por uma fonte saudável. Não há backfill de decisões históricas.

| Lane | Gaps | Primeiro fecho UTC | Último fecho UTC |
|---|---:|---|---|
| SOL 5m |124|15/10 10:25|15/10 20:40|
| SOL 1H |9|15/10 11:00|15/10 19:00|
| BNB 4H |2|15/10 12:00|15/10 16:00|

As duas linhas unresolved são BNB 4H e SOL 1H, ambas fecho **15/10 20:00 UTC**, estado EXPIRED_CLOSE. A última reavaliação substitui evaluated_ms enquanto a linha continua inconclusiva; esse campo não prova a primeira tentativa. Não são mensagens pendentes. A referência activation_ms sobrevive à migração; os intervalos, por si só, não distinguem PC parado de versão anterior sem ledger. São dívida de evidência, não prova de 135 sinais perdidos.

Desde a primeira observação persistida, o snapshot V07 contém 30 fechos BNB 4H, 119 SOL 1H e 1411 SOL 5m. As únicas linhas inconclusivas são as duas iniciais; 25 linhas SOL5 estão SIGNAL_QUEUED, 1386 NO_SIGNAL. Não há intervalos adicionais no ledger até aos últimos fechos do snapshot. Isto prova continuidade das observações registadas, não uptime contínuo nem paridade externa.

`lane.state` descreve a tentativa atual; após 180 s torna-se EXPIRED_CLOSE. `latest_close_state` preserva NO_SIGNAL/SIGNAL_QUEUED obtido na janela elegível. Portanto EXPIRED_CLOSE com latest_close_state=NO_SIGNAL não é nova falha nem revogação da decisão. O patch adiciona latest_close_decision_proven e oldest_unresolved_close_ms sem reclassificar ou apagar linhas. complete_coverage_proven permanece false.

## Identidade e entrega Windows
Receipts: `audits/evidence/crypto-lab-20261020/`.
V07 SHA256 99d06384268d649b2224a10fa9d231ad8ce78fb6ced8aaee4389f12d86e12e84 e V11 8143e21de4cefb59c896fbb706d59def525ff9d459cdb36e182bf0bdd33db3bc coincidem com previews V2. V12 instalado SHA256 0aa45a022de9c5e642316c757db72996c8bf126a3b6aed0247691852b6713bfe; paridade com source desta branch não demonstrada. As três tarefas estavam Running, fontes OK, reports <1 min, filas zero. Dois processos por EXE formam pares parent/child compatíveis com PyInstaller onefile; contagem=2 isoladamente não prova duas instâncias de trabalho.

V07: 270 notificações sent no total, incluindo operacionais; há 25 decisões de sinal SOL5 no coverage. Os 20 ACKs de sinal mais recentes foram extraídos, incluindo `SIGNAL:SOL_CONVEX_NATIVE_5M:1792474500000`, message_id 923. Evidência do caminho histórico sinal→outbox→ACK, não de leitura humana nem de entrega de todo sinal possível. V11: zero mensagens/sinais persistidos, 18 gaps iniciais e 3 expirados iniciais. V12: 26 notificações sent, pending=0, mas schema instalado sem message_id e sem coverage ledger; entrega histórica com identidade de ACK não demonstrável.

Bug demonstrado V12: send retorna message_id validado, drain descartava esse ID. Patch migra schema adicionando coluna nullable e persiste ACK junto de sent_ms; falha de envio continua pending; IDs históricos não são inventados. Crash após ACK antes de commit pode duplicar; exactly-once não prometido. O relógio é revalidado após downloads em PR237/239; permanece limitação do relógio capturado no início do drain para uma sequência lenta de envios. Não se altera TTL nem regra científica nesta correção.

## Catch-up e paridade
Catch-up dos feeds recompõe histórico contíguo de 5m e valida closeTime=open+300000-1. Não faz replay de todas as decisões perdidas. V07/V11/V12 calculam apenas último fecho completo que coincide com boundary da lane e idade 1–180 s; fetch aguarda 2 s após boundary. Primeira aquisição longa pode perder a janela: é inconclusiva, não NO_SIGNAL. Ledger e filas/activation persistem; lock OS impede instâncias cooperantes; ACK→crash continua ambíguo.

As dez estratégias permanecem exatamente V07 SOL5/SOL1H/BNB4H; V11 SOL4H/BNB30m/ETH1H; V12 BNB5m/SOL30m/BNB15m/DOGE4H. Todas usam função parent V5 fixada e agregação causal, mas histórico inicial dos indicadores e venue Binance diferem de fonte externa/MEXC. Paridade externa de sinal continua NÃO PROVADA. Fontes OK e signal_events=0 são informação do ciclo, não prova de censura nem garantia universal de envio.

## RC3.3: emissor comprovado e isolamento preparado
Processo observado PID 33488 executa tg_watch_v2; paths, parent PID e hashes dos scripts constam de windows_identity.json. A identidade é temporal, nunca reutilizar PID cegamente.
`RC33SafetyTelegramV2/app/observer_telegram.py:21–29` renderiza OBS_BATCH_SUMMARY com texto exato “ETH / SOL / BNB — RESUMO HORÁRIO OBSERVE-ONLY”. `tg_watch_v2.py:245–247` chama summary periodicamente; poll_broker:269–305 envia auditorias MEXC por mudança ou repetição 600s risco/3600s normal. O mesmo loop também preserva alertas críticos e reconciliação: não desligar o bridge inteiro.

Monitor/observer estavam frescos; heartbeat do executor ConvexRadarUnifiedRC33 tinha 7229 min. São componentes diferentes. CryptoLab-Convex-Radar-WATCH aponta para runtime/watcher.py numa pasta Downloads e grava observações; o código inspecionado não chama Telegram. OPTIONS-V21-Telegram-Watcher agora Disabled: o inventário antigo de PR239 está ultrapassado para este PC. main radar-v09-keepalive também contém sender de infraestrutura; partilha atual de destino e envios recentes desse workflow não foram comprovados.

Plano de isolamento, ainda sem aplicação: SIGNALS aceita apenas os dez IDs de lane; RC33 OBS_BATCH_SUMMARY, OBS_HOURLY_SIGNAL e summary vão para OPERACIONAL, nunca ampliam inventário. Auditorias MEXC, stale heartbeat, source failures e todos IMPORTANT/URGENT continuam em OPERACIONAL, incluindo alarms críticos imediatos. Usar configuração de destinos separada/roteamento explícito, preservar cursores e ACKs; só migrar depois de confirmar destino/permissões e identidade do bridge. Não silenciar segurança por um filtro textual nem desligar tarefas executoras. Os scripts RC33 instalados não pertencem à árvore das branches inspecionadas; preparou-se plano com hashes e pontos exatos, não um patch contra uma fonte suposta.

## Validação e próximos passos mínimos Windows
198 testes offline distintos passam no Windows: V05 50, V06 75, V07 22, V11 12, V12 14, auditoria 25. Transportes fake; nenhum send real ou MEXC solicitado por esta auditoria. WSL ausente; workflow Windows/Linux preparado na branch, resultado novo CI separado dos receipts locais.

1. Identidade V07/V11, ledger e saúde já recolhidos; não pedir reinstalação para resolver 135/2. Repetir comandos abaixo perto de novos fechos para verificar crescimento, sem resetar activation ou DB.
2. Confirmar visualmente no Telegram um ID de sinal/ACK existente (ex. 923); para V11 é necessário aguardar sinal elegível real. Nenhum sinal de teste no feed.
3. V12: validar novo build/hash offline após CI e planear atualização controlada com backup SQLite consistente/rollback; não executar preview sobre DB ativa. Atualização não feita nem autorizada por este receipt. Os 26 ACKs históricos não podem ser reconstruídos com este patch.
4. Confirmar destino OPERACIONAL e permissões; preparar/aprovar separadamente alteração do bridge identificado, preservando alertas e cursores. Até lá a mistura continuará. Não mudar KILL_SWITCH/LIVE_AUTHORITY.

Comandos, na raiz deste checkout, sem executar watchers:
```powershell
& .\engine\convex_ten_governance\AUDITAR_TELEGRAM_WINDOWS_READONLY.ps1
& .\engine\convex_observer_audit\WINDOWS_IDENTITY_READONLY.ps1
python -m engine.convex_observer_audit.read_ledger "$env:LOCALAPPDATA\CryptoLab\ThreeConvexV07\data\v07_events.sqlite3"
python -m engine.convex_observer_audit.read_ledger "$env:LOCALAPPDATA\CryptoLab\ThreeConvexV11\data\V11_OUTBOX.sqlite3"
python -m engine.convex_observer_audit.read_ledger "$env:LOCALAPPDATA\CryptoLab\ThreeConvexV12\data\V12_ONLY.sqlite3"
```
O leitor SQLite usa mode=ro, query_only e transação consistente; não seleciona mensagens, tokens ou chat IDs. Erro/lock é READ_BLOCKED, nunca fila vazia. Nenhum segredo foi exportado.
