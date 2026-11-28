# LIQMAP-DIAMANTE-002 — Veredito de arranque, 26 novembro 2026

## DECISÃO CIENTÍFICA ACTUAL
**TECH/SOURCE PASS no preflight; 0 previsões verdadeiramente futuras; ECONOMIC NO-GO LIVE; estudo prospetivo EM CURSO (não concluído).** Não afirmar GO nem taxa de acerto até maturação verificável. Não é teste do Neuron, CoinGlass, nem previsão das liquidações efetivas.

## Provas
- [PR Draft #400](https://github.com/joseluisvieira28-oss/Laboratorio/pull/400), branch research/liqmap-diamante-002-forward-map-20261126.
- Protocolo congelado ANTES dos outcomes em commit d1e2bebcb88666fcb1875e1ac160d7a5fc150673: research/liqmap-diamante-002/PROTOCOL.md
- [GitHub Actions preflight #45765841419](https://github.com/joseluisvieira28-oss/Laboratorio/actions/runs/45765841419): 7/7 testes de integridade, anti-backfill, barreiras simétricas, candles 1h totalmente fechados, ambiguidades e fricção PASS.
- [Artefacto preflight #15092086179](https://github.com/joseluisvieira28-oss/Laboratorio/actions/runs/45765841419/artifacts/15092086179) com SHA256 divulgado pelo GitHub effbca3e6537ca53a84d88aa2ecb03769eacc718a14c7d356955d85d79e3f647.
- Fonte: HyperQuant public aggregation, rdemb/hyperquant-data/liq-map/BTC.json; mapa atual tinha cobertura cerca de 48.8% do OI BTC, 28 142 posições e 50 066 contas registadas no status. NÃO são posições de TODO o mercado, nem garantidas em tempo real.
- Preflight 26/11 às ~06:06 UTC: mapa com idade de ~2.57 minutos, indicação UP, controlo MOM24 igualmente UP. Mode LATE_PREFLIGHT_NOT_ECONOMIC: NÃO CONTA como previsão prospetiva, NÃO existe retorno posterior/resultado economico. Mercado externo liquidações confirmadas pelo scanner ZERO nesse momento (liq-tape 0 confirmed/7570 failed), portanto o sensor não foi calibrado contra liquidações reais de terceiros.

## Observação futura agendada
Foi criada uma automação ChatGPT activa com tentativa diária a partir de 27/11/2026, 07:00 hora Suíça flexível (não representa hora exata garantida). 61 dias de pedidos datados: 27/11/2026–26/01/2027; dois dias de settle only: 27–28/01/2027. Automação faz um único commit de pedido por data na branch, sem trading e sem backfill; o workflow deve preservar previsões, métricas e fontes, e o artefacto original. PR Draft não pode depender de cron interno do GitHub, pois schedule só corre em main.

### Limitação operacional a confirmar em cada execução
O preflight com pull_request está confirmado. O workflow push/branch da primeira captura futura ainda NÃO foi economicamente testado (é impossível em 26/11). O diagnóstico SETTLE_ONLY de 26/11 foi criado no caminho requests/2026-11-26.txt para testar a escrita de arquivamento, sem criar uma previsão falsa. Ausência de ficheiros de observação/rollup é TECH_PENDING e não sucesso. A automação deve comunicar bloqueios, e nunca atribuir acertos a capturas que não foram verdadeiramente recolhidas antes dos preços futuros.

## Gate irreversível
Cada snapshot com hora, SHA256 fonte, cobertura OI >=30%, weighted age P50 <=15m, banda mais forte 0.5–5% e espelho log simétrico. Outcome após 24 candles horários FUTUROS completos, classificado TARGET_FIRST/MIRROR_FIRST/NEITHER/AMBIGUOUS, comparador MOM24 na mesma barreira e custo hipotético 10/35/80bps por lado +5bps slippage. No mínimo 50 eventos resolvidos, Wilson lower >50%, vantagem >5pp MOM24, bootstrap semanal lower95 >0, 80bps net positivo e consistência de 2 meses para só poder dizer CANDIDATE_SHADOW. Insuficiente -> INCONCLUSIVE; suficiente e falha -> ECONOMIC NO-GO. Nenhum caso aprova trades com capital real (sem fills, custos e risco reais, estudos noutra exchange).

Sem subscrições, dados pagos, ordens, contratos, conta, wallets privados, merges ou produção.

## Atualização operacional confirmada (ainda 26/11/2026)
- O acionamento de cada marcador datado foi corrigido para sincronização do PR #400, observável pelo conector GitHub (sem cron em main). Não muda nenhum limiar de sinal, benchmark ou custo.
- Dry-run com marcador SETTLE_ONLY_2026-11-25, sem previsão nem PnL, foi executado por GitHub Actions [run #45766432576](https://github.com/joseluisvieira28-oss/Laboratorio/actions/runs/45766432576), com ambos os jobs daily-capture e preflight SUCCESS.
- Artefacto de escrita na branch: [ID 15092255952](https://github.com/joseluisvieira28-oss/Laboratorio/actions/runs/45766432576/artifacts/15092255952), SHA256 reportado pelo GitHub e803a63e237cf26c5ed4a116fe3f92a0057fb1547ab1529d57254cd3d0ab96f2.
- Ficheiro efectivamente persistido research/liqmap-diamante-002/rollup_summary.json na branch do PR, SHA GitHub bc4d427c1b7c36176a0c27a17b63929f5eaac172: 61 dias esperados, 0 observados, 0 maturados, scientific_status FORWARD_PENDING_OR_CENSORED, live_trading_verdict NO_GO.
- Automação criada e confirmada ACTIVA para 63 execuções diárias, primeira 2026-11-27 07:00 Europe/Zurich (horário flexível), última 2027-01-28. No dia da captura, o relógio real e a integridade da fonte decidem se a observação é válida. Não prometer execução futura garantida.
- Evidência agora: **TECH/SOURCE/ARCHIVE GATES PASS**, mas **ZERO ECONOMIC FORWARD EVIDENCE**, nenhum GO real.
