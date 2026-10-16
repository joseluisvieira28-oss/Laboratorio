# CONVEX — auditoria forense dos dois alertas das 20:55 UTC de 15/10/2026

Branch isolada; pesquisa offline somente. Sem ordens, credenciais, mutação em exchanges, mudanças na SQLite de produção, execução Windows nem merge em main. As imagens Telegram foram fornecidas pelo operador, não extraídas desta branch.

## Identidade dos eventos

- **V07**: SOL_CONVEX_NATIVE_5M, SOL_USDT, LONG potencial, SIGNAL:SOL_CONVEX_NATIVE_5M:1792097700000, fecho UTC 2026-10-15 20:55:00.
- **V12**: BNB_CONVEX_NATIVE_5M_EXPERIMENTAL, BNB_USDT, LONG potencial, BNB_CONVEX_NATIVE_5M_EXPERIMENTAL:1792097700000, fecho UTC 2026-10-15 20:55:00.
- 1792097700000ms é exatamente o boundary UTC 5m. O último candle válido abre às 20:50 e fecha às 20:55. Ativos distintos podem assinalar no mesmo fecho sem duplicação.
- O screenshot corrobora visualmente a receção das duas mensagens, não a sua rentabilidade ou a origem independente dos OHLC.

## Proveniência efetiva dos executáveis instalados

**Crítico:** V07 V2 e V11 V2 foram compiladas a partir do PR #237, fonte d31a4be82c8eed8d08cd9fba54567573b9153391 na branch audit/convex-v07-v11-independent-2026-10-15. V12 é o PR #239, EXE SHA256 0aa45a022de9c5e642316c757db72996c8bf126a3b6aed0247691852b6713bfe. A branch operacional de cutover conserva ficheiros de fonte V07/V11 antigos; **não atribuir falsamente às versões V2 comportamento dessa cópia obsoleta**.

- V07 V2 implementa fila SQLite outbox, drenagem com API ACK e coluna telegram_message_id, status fonte e coverage por lane.
- V12 PR239 implementa fila notices, grava sent_ms e expired_ms mas **não persiste o message_id retornado por TelegramBot.send**. A imagem comprova a receção visual, porém não existe recibo numérico persistido correlacionável em V12.
- Ambas dependem de source Binance USD-M 5m e do parent V5 pinned por Git blob. O source local não foi confrontado com histórico externo auditado.
- Contadores telegram_sent_this_cycle=0 lidos num ciclo posterior não negam sinais anteriores. O status V07 usa telegram_outbox_pending, não telegram_pending, e não contém signal_events como V11/V12.

## Problemas e gates

| Prioridade | Achado | Evidência | Decisão |
| --- | --- | --- | --- |
| P1 rastreabilidade | V12 não guarda Telegram message_id apesar do send positivo | engine/three_convex_v12/watcher.py, Outbox.drain | Receção visual sim; ACK vinculado à row não provado |
| P1 cobertura | V12 não regista ledger persistente por candle, ao contrário de V07/V11 V2 | Outbox V12 tem kv + notices, mas não observer_coverage/gaps | Não afirmar cobertura de todos os fechos |
| P1 forense | Fonte de candles e replay com mesma janela não foram ainda examinados no Windows | Falta receipt local dos caches/SQLite | Executar verificador read-only |
| P2 observabilidade | Os contadores de último ciclo têm nomes e significados diferentes | JSON de status por versão | Não equiparar zero por ciclo a zero cumulativo |
| Gate económico | Dois alertas não validam execução, proteção, stop, OOS nem rentabilidade líquida | Mensagens explicitam NÃO É ORDEM | NO-GO de vantagem económica comprovada |

Estes pontos não provam que tenham existido falsos alertas ou mensagens perdidas.

## Ferramenta criada

tools/convex_signal_forensics/forensic_2055.py: lê exclusivamente JSON do public-market cache das V07/V12, snapshots nos backups de cutover e as duas linhas específicas de SQLite através de URI de leitura. Nunca chama redes, Telegram, brokers, ordens ou DPAPI. Reconstrói 12.576 candles 5m contínuos para cada ativo exatamente até ao candle 20:50, compara duas cópias locais independentes, verifica hash SHA256 das janelas, reexecuta o algoritmo V5 pinned e consulta timestamps/receipt das duas filas. Retorna JSON com booleans, hashes, datas e IDs sem OHLC, mensagem completa ou dados de conta.

Qualquer conflito, missing cache ou divergência retorna NOT_YET_PROVEN; nunca inventar dados. É possível que backups antigos mais os caches rotativos recentes não cubram a janela integral; isso limita o veredito mas não condena a estratégia.

## Veredito atual

- **RECEÇÃO TELEGRAM — duas mensagens visíveis: PASS visual limitado**.
- **VENDA DE TRADING OU ORDENS — NÃO AUTORIZADAS**.
- **EXATIDÃO DOS SINAIS NAS 12.576 VELAS — PENDENTE de replay local**.
- **RECEIPT SQLite/Telegram — PENDENTE de inspeção local (V12 não guarda message_id)**.
- **VANTAGEM ECONÓMICA — NO-GO de alegação de rentabilidade**.

A próxima evidência necessária é a saída sanitizada do verificador Windows, após validação Windows/Linux CI. Não solicitar nem publicar SQLite, pastas data completas, tokens ou ficheiros DPAPI.
