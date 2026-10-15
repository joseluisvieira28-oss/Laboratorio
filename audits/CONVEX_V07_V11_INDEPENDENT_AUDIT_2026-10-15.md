# Auditoria independente CONVEX V07 + V11 — 15 outubro 2026

**Veredito: NÃO. O código distribuído auditado não garante que qualquer sinal elegível das seis estratégias chegue ao Telegram.** Há falhas reproduzidas que suprimem ou duplicam alertas. Quanto ao estado atual do Windows: **AINDA NÃO COMPROVADO** por esta auditoria. As correções são propostas isoladas, não instaladas.

## Âmbito, identidade e cadeia de prova

- Snapshot auditado: PR [236](https://github.com/joseluisvieira28-oss/Laboratorio/pull/236), SHA `ff9ef714763cfd0656c67f4d38c3f2d7615fe199`. V07 é o código herdado nesse snapshot; não presumimos que o EXE instalado no PC seja este código.
- Reparações isoladas: [PR 237](https://github.com/joseluisvieira28-oss/Laboratorio/pull/237), [commit c2d5192](https://github.com/joseluisvieira28-oss/Laboratorio/commit/c2d5192ef969b3459218c5984ba535743a624323).
- Parent V5: blob Git `19c8b8e2363f253458db42111b6701f3a3ef1f4b`; compiladas apenas as cinco funções originais de indicadores/sinais. Nenhuma regra/threshold foi afinada e nenhum holdout protegido foi aberto.
- Logs originais de [38745377979](https://github.com/joseluisvieira28-oss/Laboratorio/actions/runs/38745377979) lidos: jobs Windows `116457519457`, Linux `116457519866`, packaging `116457688398`. Ambos OS executaram **12 testes V11**. Packaging executou `--help`, não um ciclo completo empacotado com dados/DPAPI/Telegram. Artifact `11977408285`; digest do ZIP exterior no log `8d7fdd05b15536f7e2f0e9d50c57724d85e680216603058ca4cfe4500b74c5a7` NÃO é o SHA256 do EXE.
- [BASELINE_FAULTS.txt](evidence/convex-v07-v11-2026-10-15/BASELINE_FAULTS.txt): oito testes novos sobre o código original, quatro FAIL e um ERROR, três passaram. São falhas de requisitos operacionais, não de rentabilidade.
- [LOCAL_REGRESSION.txt](evidence/convex-v07-v11-2026-10-15/LOCAL_REGRESSION.txt): 50 V05 + 75 V06 + 22 V07 + 12 V11 + 13 testes de falhas passaram após reparação inicial. Dois testes adicionais posteriores verificam sinal positivo nas seis lanes e reproduzem a ambiguidade ACK/commit; total local atualizado **174**, com 15 testes de auditoria. Todos offline; nenhum envio Telegram real ou pedido privado efetuado.
- CI das reparações: [auditoria independente 38752907861](https://github.com/joseluisvieira28-oss/Laboratorio/actions/runs/38752907861), [regressão V07 38752914737](https://github.com/joseluisvieira28-oss/Laboratorio/actions/runs/38752914737), [V11 38752914680](https://github.com/joseluisvieira28-oss/Laboratorio/actions/runs/38752914680). Windows e Linux SUCCESS no SHA c2d5192, 172 testes por OS; logs de ambos os jobs lidos. Preview duplo artifact [11982680294](https://github.com/joseluisvieira28-oss/Laboratorio/actions/runs/38752907861/artifacts/11982680294), digest do ZIP exterior `6e2944b284439736696b2d40a60c74a0bde23d7fbb64e2976983a6a903a5041c`. Os dois testes posteriores constam de [ADDITIONAL_SCIENCE_AND_LIMIT_TESTS.txt](evidence/convex-v07-v11-2026-10-15/ADDITIONAL_SCIENCE_AND_LIMIT_TESTS.txt); CI de revisão é consultável no PR. Não inferir que CI comprova instalação.

## Classificação individual

Estado operacional refere-se ao código original configurado pelo operador, não ao preview corrigido. A comunicação do operador é evidência declarada; não é observação independente do PC.

| Estratégia | Estado | Sinal tecnicamente verificável | Histórico | OOS independente | Forward disponível | Economia líquida real |
|---|---|---|---|---|---|---|
| SOL CONVEX 5m V07 | DEGRADADO | Sim em fixture positiva; paridade externa do monitor pendente | Favorável reportado ~+59,9%; ledger nativo não revalidado nesta missão | Não comprovado | Monitor reportado ativo; ledger de sinais/ACK não fornecido | Não demonstrada |
| SOL CONVEX 1H V07 | DEGRADADO | Sim; colisão com 5m suprime ambos no original | 2023–25 BASE +59,39%, STRESS +58,30% | Não comprovado | Idem; amostra independente insuficiente/não apresentada | Não demonstrada |
| BNB CONVEX 4H V07 | DEGRADADO | Sim; problemas comuns de cache/fila/latência | +27,38% / +27,06%; 28 trades | Não comprovado | Idem | Não demonstrada |
| SOL CONVEX 4H V11 | DEGRADADO | Sim; implementação experimental | +35,90% / +35,42%; dependência top-3 | Não comprovado | Status operador com 0 eventos; não prova percurso de entrega | Não demonstrada |
| BNB CONVEX 30m V11 | DEGRADADO | Sim; implementação experimental | +19,67% / +18,17%; residual top-3 frágil | Não comprovado | Idem | Não demonstrada |
| ETH CONVEX 1H V11 | DEGRADADO | Sim; implementação experimental | +18,77% / +18,34%; dependência top-3 | Não comprovado | Idem | Não demonstrada |

Fontes científicas: [closeout original 8×4](https://github.com/joseluisvieira28-oss/Laboratorio/blob/research/convex-sol1h-bnb4h-economic-source-gates-2026-10-13/audits/CONVEX_8ALT_4TF_COMMON_2023_25_FINAL_CLOSEOUT_2026_10_13.md), lido nesta missão; [closeout SOL1H/BNB4H](SOL1H_BNB4H_EARLY_PROFIT_V01_CANONICAL_HISTORICAL_CLOSEOUT_2026-10-14.md); [evidência de expansão](TELEGRAM_SIGNAL_EXPANSION_EVIDENCE_AUDIT_2026-10-15.md); [engenharia V05](THREE_CONVEX_V05_ENGINEERING_VERDICT_2026-10-14.md). O native5m é citado por relatório secundário, não elevado a resultado reexecutado.

Os resultados modelam 20% notional, 1×, fees/slip/funding proxy sobre Binance. Não demonstram fills, mark funding, custos/sizing MEXC ou resultado alavancado. SOL4H e ETH1H ficam negativos após subtração estática dos três maiores vencedores; BNB30m conserva apenas +61,77 USDT. Esse diagnóstico não é um novo backtest nem rejeição automática de convexidade. Não há prova de vantagem futura independente.

## Falhas comprovadas, correções e regressões

| ID | Causa e efeito original | Correção proposta | Prova / restante |
|---|---|---|---|
| F1 | V07 `cycle` agrupa duas lanes SOL e faz `continue`: envia zero sinais quando ambos surgem | Notificar cada lane com ID próprio; nenhuma execução física | `test_v07_both_sol_observations_survive_collision`: original 0 != 2; corrigido 2. Antigo teste exigia a supressão e foi substituído explicitamente |
| F2 | `_save_json_atomic` abre sempre `cache.tmp` em modo exclusivo; crash deixa órfão e todas as tentativas seguintes falham | Temporário exclusivo com nome único, fsync e replace atómico; limpeza do próprio temporário | `test_cache_orphan_tmp_does_not_permanently_block_writer`: original FileExistsError; corrigido passa. Afeta feed partilhado por V07/V11 |
| F3 | V11 apenas drena SQLite depois de todas as fontes passarem | Drenar mensagens previamente persistidas antes da recolha; falha de fonte continua bloqueando novas observações | `test_v11_pending_drains_even_if_public_source_fails`: original zero envios; corrigido um. Nenhum envio real |
| F4 | Filas guardam mensagens sem marcar atraso e enviam horas depois com aspeto normal | Acrescentar aviso ATRASADO quando entrega >180s após fecho; preservar registo, não fingir elegibilidade | `test_v11_old_pending_is_marked_late`; janela científica não alterada |
| F5 | Duas conexões selecionam os mesmos pendentes antes de qualquer update | BEGIN IMMEDIATE envolvendo seleção/envio/commit; lock de instância OS no entrypoint de ambos | `test_v11_two_connections_cannot_send_same_notice_concurrently`: original dois envios; corrigido um. Locks liberados após saída testados |
| F6 | ACK message_id validado pelo TelegramBot mas descartado na persistência | Migração aditiva SQLite guarda `telegram_message_id` quando o sender o devolve | `test_telegram_ack_id_is_durable`; registos antigos ficam NULL e não são provas de ACK |
| F7 | V07 instanciava transporte V06 que contém métodos POST (não chamados no fluxo atual) | ObserverTransport rejeita método diferente de GET/ticket antes do transporte | `test_exchange_write_rejected_before_network`; não foi observada ordem/POST real nem exploração do transporte |

F1–F5 reproduzidos antes/depois. F6–F7 são endurecimentos adicionais, não alegações de envios/ordens indevidos observados. Todas as correções estão apenas no branch de auditoria.

## Dados, fidelidade e limites ainda abertos

- Hosts/paths públicos Binance USD-M time e klines, candles 5m com open alinhado UTC, close exatamente open+299999ms, OHLC finitos e consistentes, páginas com contagem/timestamps exatos. Duplicados, reordenações e gaps são rejeitados. Cache começa no início exigido ou é novamente adquirida; corrupção dá fail-closed, sem preenchimento inventado. Volume é agregado por soma.
- 1h/4h/30m derivados por grupos UTC completos de 12/48/6 barras. Fixture independente de agregação e fixture com sinal parent positivo passam nas seis lanes. Testes existentes rejeitam candles abertos, gaps e ativação retroativa. Isto demonstra adaptadores determinísticos, não coincidência com toda a série histórica original.
- Histórico móvel de 12.576 barras 5m (~43,7 dias), floor de 250 candles TF. O V5 usa RSI/RMA recursiva; começar a cada janela móvel não é matematicamente idêntico ao warmup Nov/Dec 2022 original. O código já declara paridade externa NÃO comprovada. Não se afinou warmup depois de observar resultados.
- Fonte interrompida durante download não grava cache parcial; teste recupera após restabelecimento. Cache incompleta de início é novamente adquirida. Sem internet não há deteção; suspensão/desligamento Windows também não recolhe dados.
- Apenas último fecho compatível com TF é avaliado. A regra recency 1–180s impede replay antigo. Uma interrupção >180s pode perder definitivamente um sinal; ciclos mais lentos e chamadas de rede em série também podem fazê-lo. Não existe ledger durável de todos os fechos esperados/processados/perdidos nem recuperação marcada como informativa para fechos nunca detetados.
- Todas as fontes têm de passar antes de gravar novos findings. Falha BNB pode suprimir sinal SOL já calculado nesse ciclo. F3 corrige pendentes, NÃO esta dependência entre fontes na deteção. Corrigir requer receipt por lane e fila de observações, preservando elegibilidade original.
- `server_ms` é capturado antes de downloads; não há nova leitura de relógio no instante de envio. Cold-start V11 faz aproximadamente 27 pedidos de páginas; latência real no PC não foi medida. Não existe SLA de entrega. Desvio >5s é bloqueado/testado; corrigir relógio automaticamente não faz parte desta missão.
- Falhas V07 de Telegram podem deixar o último JSON de sucesso intacto. V11 publica erro genérico sem diagnóstico de causa. `Running`, zero pendentes e `sources_ok` isolados não provam frescura nem processamento contínuo de todos os fechos.

## Telegram: o que foi e não foi provado

SQLite WAL persiste reinícios e deduplica por lane+fecho. Erro antes do ACK deixa pendente e retry acontece; duas instâncias deixam de duplicar envio simultâneo no preview. **Exactly-once não é garantido**: ACK remoto seguido de crash antes do commit ou timeout após aceitação pode gerar duplicação. Teste `test_lost_ack_commit_still_has_duplicate_risk_documented` reproduz esse limite, não o mascara com PASS.

TelegramBot valida `ok=true` + message_id. Isso prova aceitação da API quando resposta real existe, não leitura humana. CI usa HTTP falso/senders locais. **Zero entregas reais foram efetuadas ou comprovadas nesta missão.** O operador reporta instalação e fontes OK, não forneceu receipt sanitizado com signal_id↔message_id↔UTC de entrega. V11 diz EXPERIMENTAL e NÃO É ORDEM; V07 diz SINAL e execução/STOP não confirmados. Não há processamento de comandos Telegram no watcher. Script de onboarding `/getUpdates` serve configuração, não controlo remoto.

## Windows, distribuição e segurança

- Paths originais: `%LOCALAPPDATA%/CryptoLab/ThreeConvexV07/data/v07_events.sqlite3` e `ThreeConvexV11/data/V11_OUTBOX.sqlite3`; caches e status separados. V11 reutiliza apenas Telegram DPAPI do V07, não SQLite nem credenciais MEXC. A dependência do segredo V07 deve ficar documentada; não foi alterada.
- DPAPI é desencriptada no mesmo utilizador; launchers retiram CR/LF finais e limpam variáveis no finally. Secrets não estão hardcoded no watcher. Variáveis existem em memória do processo: não se promete proteção contra administrador local.
- Scheduled Tasks usam AtLogOn + IgnoreNew + três reinícios de um minuto. **Não são serviço de arranque antes de login, não garantem recuperação ilimitada, PC desligado/suspenso não monitoriza.** IgnoreNew não protege execuções manuais fora do scheduler; lock OS novo protege o mesmo data-dir. Nenhuma tarefa foi desativada, alterada ou instalada nesta missão.
- Instaladores conferem EXE contra manifesto local; isso deteta corrupção, não autentica um pacote inteiro adulterado. Falta receipt do hash instalado contra artifact/commit original. Build original tem smoke `--help`; não valida loop empacotado, DPAPI real e Scheduled Task do operador.
- Preview novo inclui BUILD_MANIFEST com commit e hashes dos EXEs V07/V11, sem instalador automático. Não substitui o executável ativo. A correspondência do EXE atualmente distribuído/instalado é **NÃO VERIFICADA** nesta missão.
- V07 faz leituras autenticadas MEXC e contém dependência de transporte com POST no módulo V06; o fluxo auditado não chama POST. O novo wrapper rejeita writes incondicionalmente no watcher. V11 não importa transporte MEXC. Nenhum trading authority, alteração de posição, ordem, POST privado, segredo modificado ou comando remoto foi utilizado.

## Provas locais necessárias e ordem prática

1. Executar manualmente [WINDOWS_READONLY_RECEIPT.ps1](../engine/convex_observer_audit/WINDOWS_READONLY_RECEIPT.ps1). Apenas lê tarefa/processo/status/hash; não revela secrets, não envia Telegram e não modifica tarefas. Comparar hash instalado com manifesto do artifact do commit correspondente. Não executar preview sobre dados ativos para fazer essa comparação.
2. Obter evidência sanitizada de sinal real: lane, signal_id, fecho UTC, detection UTC, enqueue UTC, ACK UTC e message_id. Um teste SYSTEM_ONLINE não prova percurso de sinal.
3. Após rollout separado, exercitar reinício antes de entrega e duas instâncias em diretório de teste, nunca assumir que CI seja o PC. Validar saída do launcher e recuperação após logoff/reboot/Internet indisponível sem interromper tarefas existentes nesta missão.
4. Resolver ledger de fechos/falhas por lane, dependência cruzada de fontes e medição real de latência. Provar paridade externa e impacto de warmup antes de declarar fidelidade integral. Não alargar regras temporais para salvar sinais perdidos.

**Conclusão obrigatória: NÃO podemos confiar hoje na garantia de que qualquer sinal elegível das seis chegará ao Telegram. Cinco defeitos foram demonstrados e reparados no branch; reparações ainda não instaladas, limites de cobertura permanecem e estado Windows/entregas reais ainda não estão comprovados.**
