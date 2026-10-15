# CRYPTO LAB — Auditoria de 10 canas, exclusividade Telegram e inventário seguro
**Data: 2026-10-15 | Estado: código GitHub auditado; Windows atual ainda não observado remotamente.**
**Autoridade: GitHub branched changes only. Nenhuma tarefa, bot, posição, ordem, segredo ou workflow em main alterado.**

## Inventário exato autorizado — 10 combinações, sinais LONG potenciais, NUNCA ORDENS
| Origem | Canas |
| --- | --- |
| V07, 3 | SOL 5m, SOL 1H, BNB 4H |
| V11, 3 | SOL 4H, BNB 30m, ETH 1H |
| V12, 4 | BNB 5m, SOL 30m, BNB 15m, DOGE 4H |

Nenhum outro sinal de estratégia deve entrar no feed SIGNALS. Sobreposição entre estratégias SOL/BNB é possível e não equivale a trades independentes. Histórico 2023–25, custos modelados, sem vantagem líquida MEXC prospectiva provada.

## Descobertas concretas
1. **V07/V11 — código corrigido não instalado:** PR #237 V2, commit de ciência/engenharia d31a4be, pacote 11983865584 e run 38754922098 com **180 testes em Windows e Linux**. Corrigidos na branch falhas de colisão SOL, cache .tmp órfão, supressão de fila no erro da fonte, duplicação concorrente, falta de message_id persistido, guarda GET-only e ledger de coverage/gaps. Nenhuma evidência fornecida de hashes do executável instalado coincidirem com o preview. V07/V11 atualmente no PC podem ser versões originais. Não executar previews sobre SQLite ativas; fazer backups e plano rollback antes de atualizar.
2. **V12 — falha de isolamento reproduzível pela inspeção do código original:** no commit original 413a10c, cycle faz fetch sequencial BNB, SOL e DOGE; se DOGE lança FeedHalt, termina antes de enfileirar sinais já encontrados e antes de drenar pending. O JSON pode reportar FAIL_CLOSED apesar de as fontes anteriores serem válidas. O código original também usa relógio capturado ANTES de download para classificação de sinais/TTL; se fetch exceder vários minutos, notificações podem ser entregues com idade falsa. Correções propostas apenas nesta branch: isolamento por ativo, separação de estado DEGRADED com source_status por ativo, preservação da fila antiga e releitura de relógio Binance antes de detectar/enviar. Regressões adicionadas. **Isto NÃO altera a instalação V12 do operador.** Requere CI e novo pacote auditado, depois substituição controlada da tarefa V12 se aprovado.
3. **Emissor LEGACY conhecido no último inventário:** task CryptoLab-OPTIONS-V21-Telegram-Watcher estava Ready no receipt de operador 2026-10-14. Ready não comprova Running nem envio. Não é uma das dez. Revalidar estado real e se é apenas um notifier antes de desativar. Outras tarefas OPTIONS-V21-Futures-AutoLive, BNB-Operator-AutoLive-V01 e Triple-Fishing-Operator-V03 estavam Disabled nesse dia. Não desligar executores potencialmente responsáveis por posições/stops sem conciliar contas e posições.
4. **Emissor adicional GitHub, não trading:** a branch main contém .github/workflows/radar-v09-keepalive.yml com schedule cron */8 e step que envia Telegram quando Radar PUBLIC_SHADOW é degradado, se secrets presentes. É um alerta de INFRAESTRUTURA, não uma 11a estratégia. Estado atual das execuções e partilha efetiva de chat com as três canas não foi auditado aqui. O workflow de teste offline radar-telegram-test-v01.yml NÃO envia automaticamente teste real, salvo fluxo próprio de main keepalive via dispatch.
5. **Limite estrutural:** 3 tarefas Windows independentemente agendadas e sendMessage para o mesmo TELEGRAM_CHAT_ID configurado (V11/V12 herdam chat ID/token da V07). Sem router central imposto a todos emissores, um terceiro emitter antigo continua capaz de enviar mensagens. Alterar apenas nomes/títulos do chat não interrompe bots nem GitHub Actions.
6. **Garantia universal de entrega continua NÃO:** processos Running e sources_ok são observação de um ciclo. Sinais elegíveis podem não ser detetados se PC/rede indisponível >180s; ACK API≠leitura humana; ACK→crash pode produzir duplicado. V12 original não traz o ledger de cobertura V2 do PR237. Futuro upgrade requer validação externa da paridade REST↔V5, receipts locais e sinal real→Telegram.

## Organização Telegram recomendada — SEM alterar bot ou grupos nesta auditoria
**Separar ALERTAS DE MERCADO de OPERACIONAL, mas NÃO criar uma 11a cana.**
- Canal/grupo privado existente, categoria **#SINAL**: somente V07 (3), V11 (3), V12 (4), todos com versão, símbolo, timeframe, LONG potencial, fecho UTC, signal_id, classe EXPERIMENTAL quando aplicável e aviso NÃO É ORDEM.
- Tópico/canal de operações **#SISTEMA**: Binance source degraded, Windows heartbeat/gaps, Telegram ACK; Radar keepalive apenas se ainda for desejado, sem simular trades.
- Grupo/tópico **#ARQUIVO_LEGACY** opcional: capturas históricas exportadas manualmente; antigos emitters deixam de enviar, preservam recibos e o histórico, sem apagar dados.
- No imediato, antes de criar tópicos ou mudar chat IDs, usar os prefixes V07/V11/V12 existentes, documentar separadamente os alarmes e retirar emissores legados comprovadamente de alertas; para separação real por tópico requer suporte Telegram message_thread_id nos emissores e permissões no grupo. Emissão compartilhada de token/chat precisa isolamento do segredo e migração verificada, não um clique de mudança do nome.

## Protocolo de limpeza local (sem riscos ocultos)
**Passo 1: Inventariar (zero alterações).**
Executar engine/convex_ten_governance/AUDITAR_TELEGRAM_WINDOWS_READONLY.ps1 num PowerShell no mesmo utilizador Windows. Lista nomes/estados de tarefas, estado/frescura V07/V11/V12 e hashes locais. Não imprime argumentos, comandos, chat_id, DPAPI, tokens ou credenciais. A origem GitHub Actions precisa inspeção separada no repositório.
**Passo 2: Comparar hashes V2 antes de qualquer alteração.**
Expected V07 V2 = 99d06384268d649b2224a10fa9d231ad8ce78fb6ced8aaee4389f12d86e12e84.
Expected V11 V2 = 8143e21de4cefb59c896fbb706d59def525ff9d459cdb36e182bf0bdd33db3bc.
Match significa mesmo hash desses previews, NÃO instalação confirmada por esta auditoria. Primeiro correr os dois scripts offline do PR #237 V2 em pasta isolada: VERIFICAR_PACOTE.ps1, WINDOWS_READONLY_RECEIPT.ps1. Não iniciar EXEs contra os dados ativos.
**Passo 3: Fazer cutover de V07/V11 com recibos, backups SQLite e rollback próprio.**
Preservar queues, activation_ms, caches, MEXC DPAPI e Telegram DPAPI. Não interromper sem identificar tarefa/exe/PID e conferir conta MEXC para qualquer executor legado que se planeie desativar.
**Passo 4: Decidir a DESATIVAÇÃO do watcher OPTIONS antigo (apenas notificador).**
Só quando o output atual confirmar a identidade exata e o code path não contém gestão de posições, stops ou ordens; desativar apenas esse notifier e verificar que V07, V11, V12 mantêm saúde. Jamais confundir OPTIONS Watcher com OPTIONS Futures AutoLive executor. Nada apagado.
**Passo 5: Decidir o destino do Radar keepalive.** Pode continuar como #SISTEMA separado. Se o operador exigir que o mesmo chat receba SOMENTE as dez canas, é necessário mudar o destino de health alarms ou desativar explicitamente o workflow do GitHub; não confundir alarmes de segurança com estratégias de trading. Nenhuma alteração de main feita aqui.
**Passo 6: Verificar o Telegram REAL.** Confirmar ACK id de sinal real e mensagem visível, com timestamp, não usar falso 'sinal de teste' no canal de mercado.

## Estados finais nesta auditoria
- Dez canas **configuradas conforme relatórios anteriormente enviados pelo operador**; não verificadas simultaneamente agora.
- V07/V11 correções PR237 **QA PASS / INSTALLED NOT PROVEN**.
- V12 correção **BRANCH ONLY / CI PENDING** até chegada de receipts, instalada original sem correção.
- Outros emissores **identidades parcialmente conhecidas, estado atual NÃO VERIFICADO**; nenhuma tarefa desativada.
- Trading e capital: nenhum alterado; edge executável NÃO demonstrado.

### Evidências
- [PR237](https://github.com/joseluisvieira28-oss/Laboratorio/pull/237), [run 38754922098](https://github.com/joseluisvieira28-oss/Laboratorio/actions/runs/38754922098), audits/CONVEX_V07_V11_CONTINUATION_V2_2026-10-15.md.
- [PR238](https://github.com/joseluisvieira28-oss/Laboratorio/pull/238); engine/three_convex_v12/watcher.py V12 original.
- audits/THREE_CANAS_WINDOWS_OPERATOR_TASK_INVENTORY_2026-10-14.md.
- main/.github/workflows/radar-v09-keepalive.yml.
