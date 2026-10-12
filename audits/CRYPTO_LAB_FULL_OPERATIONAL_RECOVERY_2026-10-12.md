# CRYPTO LAB — FULL OPERATIONAL RECOVERY — 12/10/2026
Corte de verificação: 10:11 UTC / 12:11 Europe/Zurich.
Autoridade: missão do utilizador de 12/10. Branches operacionais isoladas. Nenhum deploy, ordem, conta/wallet de exchange, gasto, merge main, backfill, alteração de ciência ou threshold.
**NET_EDGE_CONFIRMED: nenhum. A recuperação técnica não é um veredicto económico.**

## 1. Execução real e provas

### Radar após billing — serviço retomado, HEALTH ainda não passou
- Eventos Render oficiais de 09:36:26.966384 UTC: suspender_removed Billing e service_resumed. Serviço not_suspended, sem suspenders.
- Logs reais avançam de 30 em 30 segundos, com identidade canónica srv-dalqkpu1egvs73fhiehg e commit d645891a588c594b69f41938263cc4066652aa9b.
- Runtime reporta PASS_CANONICAL_SUPABASE_SINGLE_WRITER e cadeia verificada de 2737 eventos / 2659 keys; sequência 2737. É prova do runtime, não nova recomputação independente da base.
- Não criei writers, não promovi o SQLite local, não alterei infraestrutura. O watchdog valida este serviço; ausência global de outros escritores continua sem enumeração independente.
- Endpoint público verificado novamente: HTTP **503 com JSON válido**, checked_at 09:57:45 UTC, mode PUBLIC_SHADOW_ONLY, health DEGRADED_FAIL_CLOSED. Antes da retoma havia HTML 503.
- Causa remanescente: archive exato AVAXUSDT-bookDepth-2026-10-08.zip HTTP404, CED FAIL_CLOSED; 31 receipts de gaps históricos requerem revisão. Retomar o serviço não apaga as lacunas.
- OPTIONS/BINANCE/ETF fontes OK, ETF supervisor WAITING_EXACT_TARGET. Q4 outcomes selados.
- Diagnóstico público [38224423382](https://github.com/joseluisvieira28-oss/Laboratorio/actions/runs/38224423382), attempt 2, job114757650904. Sem Telegram send.
- Relatório exigido: [RADAR_POST_BILLING_RECOVERY_2026-10-12.md](https://github.com/joseluisvieira28-oss/Laboratorio/blob/ops/radar-public-health-diagnosis-2026-10-12/audits/RADAR_POST_BILLING_RECOVERY_2026-10-12.md).

### Overshoot V024 — matriz original recuperada e diagnóstico corrigido
- Branch ops/overshoot-coverage-source-recovery-2026-10-12, revisão técnica f9fdca7a72abf0f05ec475ea7b65eee5558b5d84.
- Artifacts originais A11564951470 / B11575591555: ZIP SHA256 b766d27f2785748278352d26c1221a7b044665927517122b6b73408b06052b67 / 50712ef27bac0d6c632ceda3384783a286722b4d193b3cd9c1073ab63063e999, ambos verificados.
- Receipts SHA256 c85517ba66c22b722d10eec32646b3af5da3fddc248ff5101716348fc774a79e / 83b9c9eb43d2a6af7b20d0f17e3a765d8348094eb57022de8ca2d0f03c66c2e0.
- **13335 células asset-minute esperadas**: 1713 MISSING_EXACT_SOURCE_POINTS MEXC; 7 asset-signals aceites pelo cooldown; 6 suprimidos; 11609 sem trigger/erro reportado mas SEM prova raw retida. Sete baskets, uma data; nenhum conflito asset-event.
- Não há desconexões registadas. Os receipts antigos não retêm source points de minutos sem trigger. Não é possível provar retroativamente se cada ausência era feed esparso, finalização tardia ou outro defeito sem raw messages; não inventei uma causa.
- Matrix [38232821470](https://github.com/joseluisvieira28-oss/Laboratorio/actions/runs/38232821470) SUCCESS, artifact11738599320, ZIP5f26c13c4a95339c0442d0c0658d93459e33b92083998475180db10b314da2a7. Guarda originais, matriz completa e resumo.
- Invariantes científicos e teste público original [38232989154](https://github.com/joseluisvieira28-oss/Laboratorio/actions/runs/38232989154) SUCCESS. Nenhuma edição dos coletores, regras, freezes, fees ou agregador científico.
- Corrigi um bug **do novo diagnóstico operacional**, não do coletor científico: lookup do cache Binance deve usar uppercase. Primeiro diagnóstico 38233168706 é não autoritativo para Binance; preservado, não apagado.
- Diagnóstico corrigido [38233923648](https://github.com/joseluisvieira28-oss/Laboratorio/actions/runs/38233923648) SUCCESS: 35/35 símbolos com pontos fechados nas três venues, conexões ativas, zero erros de conexão, janela real de 125s.
- **125s fora da sessão não demonstram exact pairs de 5m dentro da sessão.** Não lancei sessão económica Overshoot sem esse preflight. Histórico +4.0820bps após 16bps modelados permanece histórico; forward original negativo e SOURCE_BLOCKED permanece intacto.
- [Resumo verificável da matriz](https://github.com/joseluisvieira28-oss/Laboratorio/blob/ops/overshoot-coverage-source-recovery-2026-10-12/audits/OVERSHOOT_V024_ORIGINAL_COVERAGE_SUMMARY_2026-10-12.json).
- Tentativa de abrir PR e publicar receipt corrigido não foi executada: revisão automática da integração falhou com429. Não usei rota alternativa para contornar.

### Multi-Stable — original recuperado e um segmento futuro protegido
- Readiness original: [37780604059](https://github.com/joseluisvieira28-oss/Laboratorio/actions/runs/37780604059), attempt2, job114710002904; 9/40 baskets, 2/7 datas, BTC3/10, ETH6/10, concentração66.7%, 19/19 execuções completas; economia selada.
- JSON malformado Oct08 01–03:59 permanece byte-identical, blob c6c15fc509f49c73a3868385fe19bbee9c49b03f. Os360/360 scans referem-se apenas ao denominador do parser de triggers válidos; não são cobertura integral da intenção de scheduling.
- Branch ops/multistable-original-evidence-recovery-2026-10-12, workflow commit79dc2fd3d4f1deaa9c76c04529d5dc0368deda22.
- Novo [38233695509](https://github.com/joseluisvieira28-oss/Laboratorio/actions/runs/38233695509) em execução, um único segmento futuro **10:15–13:14 UTC**. Wrapper faz preflight das8 rotas de closes exatos mais metadata6 contratos, valida preços finitos e hash do coletor original e01a12c6794721981f6329b3c4c6473f7f968d24; falha bloqueia captura.
- Recusa começar se a hora inicial já passou. Não repete janelas antigas, não usa FORCE_PHASE, não executa adjudicador económico. Original q99/fees/horizonte/cohort intactos.
- **Preflight/captura ainda não certificados**: logs do job em execução não estavam disponíveis; não inferi PASS de in_progress. Verificar artifact final depois de13:29UTC e deduplicar apenas originais. Não juntar branches herdadas em duplicado.
- Antes de adjudicação futura, preservar toda a limitação do denominador e passar TODOS os gates congelados. O parser científico não foi alterado.

### LICP / Aave / Exitflow / USOPEN
- LICP último [38231030051](https://github.com/joseluisvieira28-oss/Laboratorio/actions/runs/38231030051):13/20 episódios independentes BTC,4 datas,21 receipts; FORWARD_INSUFFICIENT. Confirmado watch local licp-001-at-veredito-congelado ACTIVE; não criei shard/watch/writer adicional. Faltam7 episódios, não apenas7 ficheiros; depois aplicar todos os gates de outcomes e integridade.
- Aave HF:[38221678561](https://github.com/joseluisvieira28-oss/Laboratorio/actions/runs/38221678561),488/488 HFs, zero erros;3/30 dias, mediana100%, outcomes fechados. AmendmentV0.1A intacto, não repeti snapshot12/10.
- Exitflow:08 e09UTC originais preservados; nova hora10UTC [38234248930](https://github.com/joseluisvieira28-oss/Laboratorio/actions/runs/38234248930) SUCCESS, receipt blob11c3dc68bdde5cdb52de8e888e0f3f93b3f2dbb5. Apenas hora real; janelaOct10–23 e320/336 intactos, sem backfill. Gate terminal depois24/10UTC.
- USOPEN:[38222918013](https://github.com/joseluisvieira28-oss/Laboratorio/actions/runs/38222918013) SUCCESS=NOOP,8/8 testesDST/window. Ainda nenhuma observação económica elegível; próximas janelas12/10 **13:00–13:10 e15:00–15:10UTC**, equivalentes09/11NY. Continuação horária só dispara dentro das janelas. Queue delay pode perder janela; não a alargo.
- PRs[190](https://github.com/joseluisvieira28-oss/Laboratorio/pull/190),[191](https://github.com/joseluisvieira28-oss/Laboratorio/pull/191),[192](https://github.com/joseluisvieira28-oss/Laboratorio/pull/192) continuam drafts/open/unmerged.

## 2. Quadro científico e económico obrigatório
SHAs são o corte de verificação; branches de receipts podem avançar depois.

| Candidate ID | Branch / SHA | Freeze | Último receipt | Source / forward gate | Custos e resultado autorizado | Bloqueio / próxima ação legítima |
|---|---|---|---|---|---|---|
| MEXC-GLOBALASSET-INTRADAY-OVERSHOOT-SNAPBACK-V1.0 | ops/overshoot-coverage-source-recovery-2026-10-12 / f9fdca7a72abf0f05ec475ea7b65eee5558b5d84 | SHADOW_FREEZE_V0.2 + AMENDMENT_V0.2.4; 35assets,5m,10/40/35bps invariantes | matrix38232821470; counts38233923648 | Fonte histórica SOURCE_BLOCKED;7/30baskets,1/5datas. Live125s não é5m in-session |16bps modelados+book;histórico+4.0820bps;shadow original−68.30..−68.81bps/dia em1dia, descritivo bloqueado | NET_EDGE_UNPROVEN / SOURCE_BLOCKED; provar exact5m atuais e loggingraw antes de sessão futura, sem apagar erros |
| LICP-001 BTC60s | liquidation-cascade-propagation-v0.1 / d614583ec7751a22b9f6cecf0489798043e8add4 | LICP_001_FORWARD_ECONOMIC_VERDICT_FREEZE_V0_1.md + authorityV03 |38231030051 |13/20,4datas;21receipts≠21episódios;gatefinal não atingido |16bps congelados;finalnet não aberto. SOL60m é família separada, não se agrega | FORWARD_INSUFFICIENT;aguardar7BTCindependentes e todos os outcomes válidos no watch existente |
| MEXC-MULTI-STABLE-BASIS-001 | ops/multistable-original-evidence-recovery-2026-10-12 /79dc2fd3d4f1deaa9c76c04529d5dc0368deda22 | PROSPECTIVE_PREOUTCOME_FREEZE_V0.3 + amendmentsV034 |37780604059attempt2;38233695509pendente |9/40,2/7datas,BTC3/10,ETH6/10;concentração66.7%>35%.360validscansnãoresolvegap |8bps/fill/leg primário,12stress;25USDT/leg;outcomes SELADOS | FORWARD_INSUFFICIENT;certificar apenas segmento futuro atual, sem duplicação;resolver accounting da lacuna antes dejudic |
| AAVE-HF-CROWDING-001 | ops/aave-daily-source-recovery-2026-10-12 /2b0248ece387350d7c45f03202751ca5dd06d957 | CALIBRATION_FREEZE_V0.1 + TECHNICAL_AMENDMENT_V0.1A |snapshotOct12,38221678561 |3/30dias,488HFs,coverage100%;q90não calculado |N/A,medição/calibração;nenhuma rentabilidade ou liquidation outcome | FORWARD_INSUFFICIENT;uma nova dataUTC por dia;30dias não é edge |
| RW-HL-EXITFLOW-001 | ops/exitflow-actual-hour-recovery-2026-10-12 /c7f00746e6fe3912b7ad984379bebb503b321d29 anterior ao tick10UTC | G3_SCHEDULER_ACTIVATION_2026-10-09.json + original14-dayfreeze |38234248930,hora10UTC |G2sourcePASS;G3incompleto,lacunas preservadas;320/336e14datas |economiaNOT_TESTED;9bps takerRT do contrato+funding/slippage, não fees atuais deconta | FORWARD_INSUFFICIENT / NET_EDGE_UNPROVEN;recolha realhorária;terminal só24/10,semrescuejanela |
| USOPEN-SHORTVOL-FWD-001 | ops/usopen-window-recovery-2026-10-12 /5c156583f87f37b332662f927a3166eac055bf7d | USOPEN_SHORTVOL_FWD_001_PREFREEZE.md |38222918013NOOP |8testesPASS;0datas económicas completas;primeiro30+gatesPF/bootstrap2mesesconcentração |bid→ask+0.0003BTC por1optionamount capped12.5%,amount0.1;semresultado | FORWARD_INSUFFICIENT;captura realENTRY/EXITNY,semFORCE_PHASE |
| RADAR / múltiplos watchers | crypto-edge-radar-postgres-v0.5 head e5ce9f7290cae2dd1d42b4db6d7fbc146e9570f9; runtime d645891a588c594b69f41938263cc4066652aa9b | authority por watcher;ETFQ4até2027-01-01 |Render09:48,public09:57;2737eventos |PersistênciaruntimePASS;overallDEGRADED;CED404/gaps/writer-globalunknown |Radar nãoestratégia;OPTIONSúltimohistórico20/50 negativo, nãoPnLatual | OPERATIONAL_BLOCKED / SOURCE_BLOCKED;archiveexatoecontinuidade,semdeployinseguroou2ºwriter |

NET_EDGE_CONFIRMED: zero. NO_EDGE económico novo: nenhum. DLS2025 continuaNO_EDGEterminal;INDEXencerradoporatribuiçãoerrada. Não foram reabertos. TVFP permanecePASS_STRONG de medição;Triple nãofoiarmado.

## 3. Bloqueios, testes e continuação
- Matriz+hashes e testesoriginais Overshoot executados. Regressãoinstrumentaluppercase corrigida com rerunreal; não é retune de estratégia.
- Rawpointshistóricosfaltam: não posso reconstruir candlesnemcausasindividuais semprova.
- Radartransportresumed≠HEALTHPASS;CED404e31gapscontinuam. Ausência globaldeoutroswritersnãofoiprovada;nenhumdeploy/cutover.
- Multi futuro ativo, receiptfinalpendente;nenhuma afirmaçãoeconómicaatéallgates. Falha dequalitylevaSOURCE_BLOCKED/BLOCKED_DATA_QUALITY,nãoNO_EDGE.
- Watch horário crypto-recupera-o-at-veredito ACTIVE, atualizado com esta missão ecomrunatualparaevitarduplicação. LICPwatchpréexistenteintacto. Notificaçõesapenasmudançamaterial/terminal/bloqueiohumano.
- Main revalidado75fb36c8337c3221b7551c513e049cd472dad231.
- Os coletores dependem de tempo científico real. Próxima prioridade económica: fonteexactaOvershoot+receiptsintegridade;LICPcontagemblind;Multifutureoriginal;USOPENclock. Sempromoverfonte/CIcomoedge.

## 4. Limites de entrega
A revisão automática da integração falhoucom429 ao tentar abrir o PR doOvershoot e publicar oreceiptinstrumentalcorrigido. Ações nãoexecutadas, sembypass. Logs/artifacts verificados ebranchoperacional existentes preservam a prova. Esta limitação administrativa nãoaltera o veredicto científico. O relatório consolidado local permanece disponível se a publicação final for igualmente bloqueada.
