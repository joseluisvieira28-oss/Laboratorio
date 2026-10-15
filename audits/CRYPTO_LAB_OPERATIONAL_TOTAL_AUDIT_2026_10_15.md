# Crypto Lab — auditoria operacional total — 15/10/2026

## Veredito: PARCIALMENTE RECUPERADO

O deploy anterior está efetivamente em execução e o endpoint voltou a responder. Isso **não** recuperou a disponibilidade contínua, o CED1D nem certificou o Windows RC3.3. As correções desta auditoria estão apenas em branches isoladas; não foram aplicadas em produção. Não houve merge, deploy, restart, alterações de credenciais, mensagens Telegram, chamadas MEXC autenticadas ou ordens.

Escopo: serviço canónico `srv-dalqkpu1egvs73fhiehg`, branch `crypto-edge-radar-postgres-v0.5`, diagnóstico obrigatório `ops/radar-first-cycle-stall-diagnostics-2026-10-14`, estado público, logs/eventos/métricas Render, SQL Supabase read-only, fontes Binance e pacotes RC33 existentes. Horas abaixo em UTC. Evidências selecionadas: [receipt JSON](evidence/OPERATIONAL_AUDIT_2026_10_15.json).

## 1. Causas comprovadas e limites

### Render, primeiro ciclo e identidade

- `dep-db7u08mi0phs73cph9gg`: **live**, commit `e21b03b9813f7ee1c76d935d1bf9310a0c3c421b`. Evento `deploy_ended` succeeded às **21:38:29 de 14/10**; build terminou às 20:04:27, deploy_started às 21:24:14. A demora entre build e deploy é observada; a razão interna da fila não foi demonstrada.
- Build real: log **Ran 354 tests in 16.273s**, seguido de Build successful. O build anterior falhou; não confundir os dois.
- Prova de execução, além do dashboard: logs às 05:41:49 e GET público `/api/state` às **06:03:46 de 15/10** devolvem `runtime_identity.git_commit=e21b03b...`, serviço canónico e instâncias Render. A primeira tentativa deste audit expirou em 25 s; a segunda devolveu JSON. Não foi usado um build como substituto desta prova.
- `RADAR_BOOTSTRAP_TRACE` real, com identificador de instância: ciclo iniciado 21:28:45 terminou após **372,1 s**, DEGRADED_FAIL_CLOSED; seguinte 22:37:38 terminou após **308,7 s**, DEGRADED_FAIL_CLOSED; 00:53:48 terminou após **66,7 s**, OK; 05:38:31 terminou após **137,6 s**, OK.
- Pilhas amostradas identificam `ced1d_render_shadow_runtime.run_once`, linha 233 (`subprocess.run`), como espera dominante nos ciclos longos. No arranque das 05:38 também aparecem HTTP de EMA6H e `market.all_market_snapshots`. Não é correto atribuir toda a demora exclusivamente à Binance ou à base de dados.
- `ForwardShadowRuntime.__init__` inicializa um estado mínimo STARTING; identidade/heartbeat completos só entram quando `run_cycle` termina. HTTP é publicado antes do ciclo. Logo, JSON STARTING com campos ausentes é um estado inicial incompleto por construção, não prova de corrupção.
- Há vários arranques/instâncias, não um único ciclo eternamente parado. Memória amostrada 85–94 MB de 537 MB; CPU amostrada 0,0153 CPU. Não existe nesta janela evidência de OOM ou saturação; isto não exclui incidentes fora dela.
- Eventos confirmam **suspensão por Billing em 11/10 02:35:41**, retomada em **12/10 09:36:26**. A API não demonstra qual limite/fatura causou o evento.
- Plano real `free`, uma instância, autoDeploy off, previews off. A documentação [Render Free](https://render.com/docs/free) descreve suspensão após 15 minutos sem tráfego e perda de ficheiros locais em restart/spindown. O keepalive GitHub configurado a cada 8 minutos não garante essa disponibilidade: os últimos runs observados foram 22:37, 00:53 e 05:37. Não se provou a causa do atraso do scheduler. Não criar uma tempestade de pings como correção.

### CED1D: o verde atual é enganador

- Reconsulta direta do ZIP exato **AVAXUSDT-bookDepth-2026-10-08.zip** e `.CHECKSUM`: ambos **HTTP 404 em 15/10**.
- SQL confirma quatro falhas históricas pelo mesmo bookDepth: eventos 2675, 2736, 2805, 2876, última em 14/10 10:30:07. Não desapareceram.
- Estado atual para through_signal_day 12/10 para **antes**, num arquivo diferente: `klines/AVAXUSDT/1m/AVAXUSDT-1m-2026-10-14.zip` ausente. Classifica WAITING_SOURCE_ARCHIVE e preserva métricas **apenas até 05/10**. `progress_metrics_are_current_through_day=false`.
- O classificador global só degrada FAIL_CLOSED/SOURCE_BLOCKED/ERROR, não WAITING_SOURCE_ARCHIVE. Isto permite `health=OK` apesar de fonte por completar. Novo erro inicial não resolve uma falha anterior, e métricas preservadas não são dados atuais.
- Nenhuma alternativa oficialmente equivalente foi demonstrada no contrato congelado. REST depth atual, vizinhos ou agregados não substituem a profundidade histórica exigida. O próximo gate legítimo exige ZIP original, checksum, SHA256, schema e cobertura diária, antes de qualquer persistência de outcomes.
- **Decisão: SOURCE_BLOCKED para avaliação completa; não NO_EDGE; não GO.** Arquivar evidências é permitido; declarar cientificamente morto por 404 seria incorreto.
- CED1D não tenta a cada ciclo de 30 s: WAITING_SOURCE_ARCHIVE repete a cada **15 minutos**; FAIL_CLOSED volta no dia seguinte. Os contadores são em memória, pelo que reinícios repetem trabalho. Cada tentativa usa diretório temporário novo e o coletor pode fazer três tentativas por download, timeout 180 s; timeout do subprocesso 1800 s. Há desperdício por reconstrução e perda do cooldown após arranque.
- Execução GitHub V0.2 [38671387577](https://github.com/joseluisvieira28-oss/Laboratorio/actions/runs/38671387577) também falhou no arquivo 14/10 e guardou artefacto fail-closed. É coleta paralela da mesma família; não foi demonstrado que escreva na base canónica. Rever necessidade antes de suspender.

### Persistência: integridade confirmada, exclusividade com limite

SQL read-only no projeto Supabase `jqzdvgjeuveiktftyrlz`:

- 2 913 eventos/max ID 2 913 no snapshot verificado; zero diferenças de hash dos payloads, zero quebras entre elos, zero diferenças no recálculo do hash da cadeia; zero chaves órfãs.
- Runtime reporta `PASS_CANONICAL_SUPABASE_SINGLE_WRITER`, sequência consistente, target SUPABASE_POOLER, service ID correto. Postgres usa advisory lock transacional para serializar append.
- Isto confirma integridade e autorização do serviço observado. **Não prova exclusividade global de processo**: os recibos liveness não guardam identidade do escritor, e o advisory lock serializa transações, não concede lease exclusivo por processo. As conexões amostradas não identificam todos os possíveis escritores. Não certificar “único escritor no mundo” a partir do nome PASS.
- **45 recibos de lacuna histórica**, revisão pendente. Último gap reportado 16 686,05 s, entre 01:00:25 e 05:38:31. Heartbeat novo não adjudica observações perdidas. Não houve backfill.
- A expiração de 17/10 refere-se ao antigo Render Postgres de rollback, não ao Supabase canónico. Preservar backup e recibos antes de qualquer retirada; não trocar URLs às cegas.
- Tentativa de inventariar `cron.job` devolveu relation does not exist; não se pode afirmar que existam cron jobs Supabase duplicados.

### Telegram: cascata e disponibilidade, não seis causas independentes

Código atual em `main` 75fb36c e run [38687823513](https://github.com/joseluisvieira28-oss/Laboratorio/actions/runs/38687823513), job 116266633349:

- Uma resposta inválida produz PUBLIC_RADAR_UNREACHABLE_INVALID_JSON, depois NO_VALID_JSON_STATE e verificações de campos em objeto vazio: identidade, timestamp, saúde e continuidade viram erros derivados.
- STARTING é JSON válido mas igualmente incompleto: o último job gerou seis razões de campos não verificados. O passo de inspeção passou; deduplicação encontrou cache; envio Telegram foi **skipped**; a falha final foi o `exit 1` deliberado RADAR_NOT_OK. Não comprova falha de entrega Telegram.
- Quando há JSON completo, SOURCE_BLOCKED, timestamp stale, identidade divergente e revisão de gaps são problemas independentes e devem continuar visíveis.
- A deduplicação existente é por dia + conjunto de razões, best effort com cache; mudança STARTING → DEGRADED → indisponível pode gerar incidentes diferentes. Não há prova de entrega duplicada neste último run. Não foi enviado teste nesta auditoria.

### RC3.3 Windows: separado e NÃO VERIFICADO localmente

Foram lidos os pacotes `RC33_MEXC_PRIVATE_GET_RETRY_PATCH_FIX_WINDOWS_POWERSHELL51_2026-10-14.zip` e `RC33_RESILIENT_READONLY_OBSERVER_ETH_SOL_BNB_TELEGRAM_V2_2026-10-13.zip`. O código RC1 encontrado no GitHub não foi tratado como prova do binário RC3.3 instalado.

- Patch GET: até 3 tentativas, timeout 3 s, esperas 0,25/0,50 s, assinatura renovada por tentativa. POST não tem retry cego. **15 testes mock passaram**; não prova instalação nem conectividade do PC. Hash esperado de `app/mexc_futures.py`: `fac987781b281deacab576134148f1611559c2ddd2061dc86110319103263034`.
- Observador público usa estado próprio em `%LOCALAPPDATA%\CryptoLab\RC33SafetyTelegramV2`; executor usa `ConvexRadarUnifiedRC33`. Observador não importa o motor nem concede LIVE_AUTHORITY. **13 testes offline passaram**. O pacote base do monitor pode ter auditoria privada GET; não confundir o observador público com todas as funções Telegram.
- `EngineBlocked:KILL_MARKER_MISSING_PREARM` sugere pré-condição de segurança ausente, mas **não foi possível verificar o engine.py RC3.3 instalado nem a linha responsável**. Não criar/remover marker para silenciar o erro. `COMMAND_FAILED` é uma categoria genérica, não uma causa raiz: exige evento, hora, comando e versão locais.
- Não foi comprovada concorrência Windows. É necessário inventário de tarefas, instâncias, hashes de ações, processos e relação parent PID. Tarefas antigas podem chamar PREARM/ARM, mas isso permanece hipótese até ao recibo.
- **BROKER_ATTACHED_SL_ROUNDTRIP_NOT_CERTIFIED permanece bloqueado**: protocolo existente declara que roundtrip real não foi realizado; conta vazia ou stop observado por GET não certifica fills parciais, proteção anexada e recuperação. Esta missão não autoriza executar o roundtrip.
- Recolha exata e sem API: executar [RC33_LOCAL_READONLY_RECEIPT.ps1](RC33_LOCAL_READONLY_RECEIPT.ps1) no PC. Mostra hashes, markers, contagens de ledger, tarefas/processos e freshness do observador; não carrega DPAPI nem inicia motor. Script revisto estaticamente, **não executado em Windows**. Se faltam direitos para inventário, termina com erro, não produz PASS. Para localizar COMMAND_FAILED ainda é necessário fornecer o trecho sanitizado do evento e o engine.py correspondente ao hash. Ledger local zero não prova conta broker vazia.

## 2. Componentes e desperdício

| Componente | Estado comprovado | Decisão |
|---|---|---|
| Render v05 / endpoint | Degradado: responde, commit confirmado, arranques lentos/gaps | Corrigir diagnóstico; disponibilidade contínua pendente |
| Supabase / cadeia | Saudável no snapshot verificado | Preservar; exclusividade global não certificada |
| CED1D | Bloqueado por fonte, métricas antigas | SOURCE_BLOCKED, reconsulta barata, nenhuma promoção |
| Telegram GitHub | Degradado por cascata; dedup observada | Patch isolado, não confundir job vermelho com envio falhado |
| RC33 executor | Bloqueado / local não verificado | Manter desarmado, recolher receipt |
| Stop broker | Não certificado | Sem ARM ou ordens nesta missão |
| Observador RC33 | Código offline verificado; local desconhecido | Verificar processo e freshness próprios |
| v04, v06 ETF, v07 control-room, v09 preflight | Candidatos redundantes, não escritores canónicos | Preparar retirada após dependências/backup |
| EMA6H equivalence canary | Utilidade atual não demonstrada | Rever gate/closeout antes de retirar |
| TV footprint ingest | Papel distinto de receção | Não desligar só por não ser Radar |
| Laboratorio / Dream Account | Serviço pago, main autoDeploy ON | Mapear consumidores e custo antes de retirar |

Render inventariou 8 web services: 7 free e 1 pago; todos `not_suspended` no inventário. **Não equivale a todos estarem a consumir CPU**: v04/v06/v07/v09 não devolveram amostras CPU na janela de 24 horas consultada. Não estimar poupança sem uso/fatura. Não há workers ou cron services no inventário devolvido.

Em main há quatro schedules: Radar */8 minutos, ARQ018 seis vezes/dia, EBST diário e LCOD diário. LCOD recovery é workflow_run condicionado, não um segundo cron independente. Branches de investigação contêm muitos workflows mas presença do ficheiro não prova schedule ativo. Nenhuma família foi declarada morta nesta auditoria sem closeout científico. CED1D é bloqueio de fonte; OPTIONS e outros forwards não ganham nem perdem elegibilidade por testes operacionais. A auditoria não produziu um catálogo exaustivo de todas as estratégias rejeitadas do repositório; cortar todas por analogia seria indevido.

## 3. Correções preparadas e validação

1. Radar, branch `ops/total-operational-audit-2026-10-15`, base exata e21b03b: STARTING expõe identidade e flags de segurança sem inventar heartbeat fresco; WAITING_SOURCE_ARCHIVE passa a saúde global degradada. Nenhum coletor, retry, freeze, ordem, schema ou outcome alterado. **355/355 testes locais passaram**, incluindo regressão para source pending com zero/45 gaps. Código local 8ef9c08; a publicação via conector terá SHA próprio, registado no PR.
2. Telegram, [draft PR #229](https://github.com/joseluisvieira28-oss/Laboratorio/pull/229), branch `ops/telegram-root-cause-alerts-2026-10-15`, commit publicado `ba8b5e911f1ab52956ac26b1dac76592aa66331b`: uma causa de transporte/bootstrap em vez de cascata, falhas explícitas de segurança mantidas, pending CED1D visível e objeto de continuidade vazio bloqueado. **17/17 testes passaram**. Sem envio real nem alteração de cron/cache.
3. Receipt PowerShell local read-only e este relatório. Não aplicados no PC.

Publicação por conector GitHub: o push HTTPS local não tinha credencial configurada. Isto não impediu publicar pelo conector autorizado. PRs ficam draft, sem merge. O serviço pago ligado a main tem autoDeploy: qualquer futuro merge exige autorização separada.

## 4. Plano de recuperação por prioridade

**P0 — decisões de segurança:** manter RC33 desarmado; recolher recibo local; preservar 45 gaps e cadeia. Não apagar evidência para obter verde. Stop real continua não certificado.

**P1 — correções prontas:** rever os dois drafts; depois de autorização específica, integrar e fazer rollout controlado do Radar. Aceitação em produção: identidade do novo commit; trace start/finish; JSON STARTING inequívoco; CED1D pending continua degradado; Supabase íntegro; restantes coletores sem regressões; Telegram não emite cascata e mantém incidentes críticos. Build verde sozinho não fecha a recuperação.

**P1 — disponibilidade:** escolher host existente com disponibilidade adequada ou aceitar formalmente que Free não suporta o forward contínuo pretendido. Migração/upgrade/restart não autorizados agora. Um keepalive atrasado não é garantia operacional. Rever cada janela perdida com as regras já congeladas, sem replay oportunista.

**P2 — CED1D:** preparar gate barato persistente para consultar apenas URLs/checksums em falta, com cooldown que sobreviva a restart e erro original visível; só relançar coleta completa quando os arquivos exigidos estiverem disponíveis. O coletor congelado fica intacto. Qualquer mudança de cadence precisa de revisão do contrato operacional. Separar coleta lenta da publicação do estado mantendo um escritor e sem introduzir concorrência na evidência. Esta mudança de arquitetura NÃO foi implementada como correção improvisada.

**P2 — desperdício:** candidatos prioritários a retirar são v04/v06/v07/v09 e coleta CED paralela; confirmar consumidores, receipts finais e rollback antes da suspensão. Distinguir serviços não suspensos de consumo efetivo. Não foi executada desativação remota.

**P3 — prova de escritor:** acrescentar identidade auditável por processo e uma lease/controle de exclusividade apropriado, com testes de restart/overlap. Isso necessita desenho próprio; hash-chain íntegra não basta.

## 5. Verificação científica e fecho

Nenhum PASS operacional foi usado como prova de rentabilidade. Nenhum sinal, parâmetro, fee, outcome, holdout ou autorização de trading foi alterado. WAITING_SOURCE_ARCHIVE continua incompleto; SOURCE_BLOCKED não é NO_EDGE. Nenhuma promessa de lucro.

**PARCIALMENTE RECUPERADO:** deploy anterior e acesso público confirmados, integridade Supabase verificada, causas e correções documentadas. **Ainda não recuperados:** continuidade Render, arquivo Binance, gaps, instalação/concorrência RC33 e certificação do stop. Dependências restantes são reais: rollout autorizado, fonte reparada e recibos do PC. Esta auditoria não declara a operação recuperada por 355 testes offline.
