# Fusion Shadow V0.7 — Experiência operacional de 14 dias (Portugal)

**Estado:** software e 21 testes offline PASS; sem instalação confirmada no Windows; sem envio Telegram comprovado; sem trading, ordens, contas ou merge para main. O resultado histórico não prova edge líquido.

## Âmbito prospectivo congelado
- Datas UTC inclusive: 2026-10-27 até 2026-11-09 (14 dias). Nenhum backfill, datas adicionais ou consulta ao histórico protegido do Crypto Lab.
- Às 01:00 UTC: ler 21 velas UTC fechadas BTCUSDT Binance Spot e AVAXUSDT Binance USD-M; estados de 20 dias = último close D-1 comparado ao close D-21. BTC20 e AVAX20 iguais UP => LONG_CONTEXT; iguais DOWN => SHORT_CONTEXT; caso contrário NO_CONFLUENCE. Estes rótulos **não são recomendações de ordens**.
- Às 01:00 e 02:00 UTC: snapshot público MEXC AVAX_USDT, com verificação de timestamp recente, níveis ordenados, spread, contrato 0,1 AVAX/contrato. Um snapshot não equivale ao preço de execução.
- Não abrir holdouts científicos selados 2024–2026. As velas públicas correntes de 2026 são usadas **exclusivamente** para esta observação prospectiva operacional, nunca um novo backtest supostamente independente.
- Horário de tolerância estrito: apenas primeiros quatro minutos de 01:00/02:00 UTC. Sem tarefas retroativas; falhas => SOURCE_BLOCKED ou registo ausente.

## Ficheiros e instalação
Guardar todos os ficheiros desta pasta numa pasta Windows separada dos executáveis CONVEX: fusion_shadow_observer_v07.py, test_fusion_shadow_v07.py, register_windows_observer_v07.ps1, unregister_windows_observer_v07.ps1 e este README. Requer Python 3.10+ com comando py e relógio Windows correto.

Na PowerShell, dentro dessa pasta, primeiro executar:

    py -m unittest -v test_fusion_shadow_v07.py
    py fusion_shadow_observer_v07.py

Esperado: 21 testes PASS e NOT_RUNNING. Não há chamada real à MEXC/Binance nesse comando de apresentação.

## Configuração privada Telegram (opcional)
Criar bot dedicado com BotFather, iniciar conversa, obter Chat ID. Definir na interface gráfica das variáveis de ambiente de **utilizador Windows** os valores:
- FUSION_TELEGRAM_BOT_TOKEN
- FUSION_TELEGRAM_CHAT_ID

Nunca partilhar token aqui, nem em commits, screenshots ou histórico PowerShell. Terminar a sessão Windows e entrar novamente antes de instalar tarefa. O programa usa APENAS sendMessage do Telegram, às 01:00 UTC, após consulta pública; não envia ordens.

Instalar tarefa opcional em Windows (ação humana explícita, não foi executada pelo assistente):

    powershell -NoProfile -ExecutionPolicy Bypass -File .\register_windows_observer_v07.ps1

A tarefa individual chama-se CryptoLab-Fusion-Shadow-V07-ReadOnly e usa três triggers de hora local suíça 02:00, 03:00 e 04:00; apenas 02:00 e 03:00 correspondem aos horários UTC válidos nas duas semanas de observação (CET). O trigger 04:00 é rejeitado pelo verificador UTC. A data de expiração da tarefa é 2026-11-10, não pode acordar o PC, não recupera dias perdidos. Windows Task Scheduler não foi testado nesta sessão; confirmar a tarefa na consola do Windows depois da instalação e conferir primeiros recibos.

Parar/remover:

    powershell -NoProfile -ExecutionPolicy Bypass -File .\unregister_windows_observer_v07.ps1

Os recibos ficam em shadow_ledger_v07/YYYY-MM-DD_entry.json e ..._exit.json: status OBSERVED, SOURCE_BLOCKED ou PENDING_NO_RETRY no caso de interrupção. Um recibo por janela (sem reenvio automático); o alerta contém o aviso INVESTIGAÇÃO / OBSERVAÇÃO APENAS.

## Limites importantes
- Pesquisa histórica 2022/23 era proxy de preço Binance; não representa fills na MEXC, nem replicou o parent CED1D.
- O 0,000% maker/taker visto na interface MEXC em 26/10/2026 é evidência da interface nesse momento, não garantia de fee para dia seguinte/ordens API.
- Estes 14 dias são apenas validação operacional de feed, Telegram, horários e spread, não poder estatístico nem certificado de rentabilidade.
- Nunca clicar em BUY/SELL por causa destes alertas sem uma validação de risco separada. Nenhuma instrução de SL, alavancagem ou posição é gerada.
- Não interferir com estratégias CONVEX V07/V11/V12 e bots existentes.

Documentação técnica oficial: https://binance-docs.github.io/apidocs/spot/en/ ; https://developers.binance.com/docs/derivatives/usds-margined-futures/market-data/rest-api/Kline-Candlestick-Data ; https://mexcdevelop.github.io/apidocs/contract_v1_en/ ; https://core.telegram.org/bots/api
