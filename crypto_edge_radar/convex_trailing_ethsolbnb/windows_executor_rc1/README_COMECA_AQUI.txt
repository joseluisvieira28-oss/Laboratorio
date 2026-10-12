CRYPTO LAB / BTC-CONVEX RADAR ETH SOL BNB
Windows integrated local executor RELEASE CANDIDATE 1.0 -- 12 OUT 2026

ESTADO HONESTO
Este ZIP contem instalador, servico, motor de sinais, transporte REAL de ordens MEXC, stop inicial,
modificacao de stop por posicao, diario de execucao, reconciliacao por externalOid, fecho de emergencia
unico quando uma posicao gerida perde o stop, log e tarefa automatica Windows.
Pode ser ARMADO para pedidos REAIS a API. ATENCAO: nao foi efetuada uma transacao real com este build,
nao foi verificado um stop instalado e modificado nesta conta. Os testes sao sinteticos/mocks.
NAO esta certificado para LIVE e NAO garante perdas limitadas a 4% nem lucros.
O codigo opera como um motor local do projeto Crypto Edge Radar. NAO substitui nem partilha ainda
o dispatcher central V0.4; por isso DEVE bloquear se existir outro executor a correr.
O utilizador decide assumir o risco da primeira ordem real depois de ler e verificar este aviso.

ANTES DE INSTALAR
- Windows 10/11; Python 3 com comando 'py -3' existente.
- Credenciais MEXC antigas ja guardadas via DPAPI em LOCALAPPDATA\CryptoLab\ConvexRadar\private.
- Permissao MEXC Futures Order Placing na chave: ter PASS read-only NAO prova esta permissao.
- Verifica no site/app que NAO tens outras posicoes nem ordens em aberto.
- Nao interrompas um operador antigo a gerir uma posicao.
- A autorizacao de 20x nao garante que um SL 4% abaixo resista a liquidacao. 20x e MUITO agressivo.

PASSOS
01_INSTALAR.cmd : instala o motor em LOCALAPPDATA\CryptoLab\ConvexRadarTrade. Sem ordens.
02_ESTADO.cmd : mostra as posicoes do motor, pausas e autoridade. Sem ordens.
03_INICIAR_RADAR.cmd : instala e inicia uma tarefa Windows. Inicia DESARMADO.
04_ARMAR_ORDENS_REAIS.cmd : consulta a conta, verifica conflitos de tarefas antigas e solicita
    escrever ATIVAR TRADING REAL. Caso aceite, ordens REAIS serao enviadas APENAS quando houver
    sinal valido 1H, risco e lote viaveis, com protecao SL inicial incluida na criacao.
05_PARAR_NOVAS_ORDENS.cmd : cancela a autoridade local de novas entradas; nao interrompe
    a gestao das protecoes de posicoes que ja pertencam ao motor.

REGRAS INALTERADAS
- ETH_USDT SOL_USDT BNB_USDT, apenas LONG, candle 1H fechado, Parent V5 score>=3 RSI/Wilder14,
  z-score20<-2, BB20 inferior 2 desvios, volume>SMA20, regime close>SMA200.
- Inicial SL -4% calculado com referencia ao preco de entrada, ajustado apos o preenchimento.
- Quando o fecho da vela >= entrada +5%, atualiza para max(SL inicial, peak_high*0.88).
- E NONLATCHED: se fechar abaixo de +5%, o stop calculado reverte ao SL inicial; exchange
  pode recusar afrouxar: em caso de recusa a execucao para, nao altera ciencia em silencio.
- ZERO TP fixo, sem timeout; nao e a estrategia de 4R.
- Maximo um LONG por ativo, ate 3 em carteira, sujeito a risco agregado.
- Entrada apos a vela 1H, dentro de 10 minutos; NAO e o preco exato de abertura de backtest.

LIMITES NUMERICOS EM config.json (sao limites conservadores, nao promessas)
- leverage 20 (configuravel 1..20; 20x pode liquidar antes de o SL ser atingido)
- risco modelo .25% do equity por entrada, .50% agregado, margem maxima estimada 25% equity
- stop -4%, trail +5% / 12%, sem TP; esses parametros NAO podem mudar por config.
- Minimo de contrato/fees podem impedir entrada com saldo pequeno. Nao forcar tamanho minimo.
- Custos reais, funding e slippage podem exceder o orcamento; a perda efetiva pode ser maior.

SEGURANCA / FAIL CLOSED
- Regista o OID ANTES da criacao da ordem. Se houver timeout, NAO volta a enviar cegamente.
- Toda a posicao do motor fica vinculada ao ID broker + stop ID e e verificada por GET.
- Stop inexistente em posicao registada: tenta exatamente 1 market exit por ID, depois bloqueia.
- Falha de rede, stop diferente do desejado, dados incompletos ou candle perdido bloqueiam.
- O KILL impede novas entradas mas deixa o motor gerir stops que lhe pertencem.
- NUNCA apagar ledger.json nem KILL_SWITCH com posicoes ou ordens incertas.
- Se o Windows dormir, a tarefa pode nao correr: a corretora pode executar SL mas o trailing para.
- Se a MEXC nao permitir a permissao de POST, o operador nao abre ordens e bloqueia.
- Para ajuda guarda apenas state\status.json e linhas relevantes de state\events.jsonl. NUNCA chaves.

FICHEIROS PRINCIPAIS
app\engine.py (ciclo real), app\market.py (publico), app\mexc_futures.py (API assinada),
app\convex_core.py (science), config.json, tests\test_engine.py, scripts\*.ps1.

TESTES NESTA MAQUINA DE CONSTRUCAO
python -m unittest discover -s tests -v: 23 testes PASS simulados.
python app/engine.py selftest: PASS. NAO foi possivel testar API autenticada nem Windows
neste ambiente, nem introduzir chaves privadas por chat.

FONTES OFICIAIS MEXC
https://www.mexc.com/api-docs/futures/integration-guide
https://www.mexc.com/api-docs/futures/account-and-trading-endpoints/place-order
https://www.mexc.com/api-docs/futures/account-and-trading-endpoints/place-tpsl-order-by-position
https://www.mexc.com/api-docs/futures/account-and-trading-endpoints/modify-tpsl-prices-on-a-tpsl-planned-order
https://www.mexc.com/api-docs/futures/account-and-trading-endpoints/get-current-take-profitstop-loss-order-list

ESTE PACOTE NAO E CONSELHO FINANCEIRO NEM GARANTIA DE RENTABILIDADE.