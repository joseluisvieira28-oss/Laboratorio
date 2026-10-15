# CRYPTO LAB V07 — Telegram + 3 CONVEX + MEXC Futures (leituras autenticadas)

## O QUE É

Programa Windows AUTÓNOMO (.exe, **não instala Python**) para enviar alertas automáticos ao Telegram:

- 🎣 **SINAL OBSERVADO, NÃO É ORDEM**: SOL CONVEX nativo 5m, SOL CONVEX 1H e BNB CONVEX 4H via sinal original V5 recuperado. Só velas fechadas; usa Binance USD-M 5m pública com carimbo de tempo e cache local, não a MEXC como fonte de sinais. O sinal derivado via API pública **não tem paridade histórica independente provada** com arquivos de 2023–2025.
- ✅ **LEITURA MEXC AUTENTICADA**: quando a conta é observada sem posições/ordens/stops, envia confirmação no arranque e no máximo a cada 6h. Verifica a conta MEXC Futures usando **GET privado apenas** (reuse dos ficheiros DPAPI já guardados no mesmo utilizador Windows). A verificação pode falhar/ficar stale; avisa em vez de assumir estado vazio.
- 🚨 **PROTEÇÃO NÃO CONFIRMADA**: quando a conta tem qualquer posição, ordem ou stop, alerta e pede inspeção direta da corretora. Não afirma que uma posição foi gerada pelo V07, nem que está protegida sem confirmação efetiva.
- ⚠️ Falha Binance/MEXC e colisão de dois sinais SOL na mesma vela.
- Telegram é **só saída**: não aceita comandos Telegram para ordens, não há handlers de compra/venda, não publica chaves, não instala serviços no Render.

## VEREDITO / AUTORIDADE

**V07 = TELEGRAM+SINAIS+ACCOUNT-WATCH, não live executor.** O V06 contém código de transporte para POST de ordens, mas o V07 NÃO as chama. `LIVE_GO=FALSE`. Nenhuma comissão, spread, stop garantido, vantagem económica forward ou trade real é demonstrado pelos testes sintéticos. Os três sinais são virtuais; os dois SOL LONG partilham um símbolo físico, portanto colisões SOL simultâneas são bloqueadas.

O circuito completo por executar continua a exigir: fonte causal de sinais e paridade, autorização de risco não falsificável, 10× isolated por posição, ordens idempotentes, proteção broker nativa imediatamente ao fill, readback após ACK, trailing original NONLATCHED, recovery e testes sem ordens escondidas, forward líquido independente. Não alterar main; não reativar as tarefas antigas.

## LIGAR TELEGRAM EM 3 PASSOS

1. **Reutiliza o bot que já tens a funcionar** (por exemplo o dos alertas OPTIONS V2.1). Não cries outro e **não desligues nem alteres o operador antigo**. Guarda o Chat ID numérico do mesmo destino a partir da configuração local do operador antigo; se existir em `%LOCALAPPDATA%\\CryptoEdgeRadar\\secrets\\telegram_chat_id.txt`, o script consegue lê-lo. Se já existe um token DPAPI local do V07 ou em `%LOCALAPPDATA%\\CryptoEdgeRadar\\secrets\\telegram_bot_token.dpapi`, pode reutilizá-lo; senão pede o token de forma oculta. **NÃO coles tokens ou chaves neste chat.**
2. Descompacta **o único ZIP** e abre PowerShell nessa pasta. Executa:

   `powershell -NoProfile -ExecutionPolicy Bypass -File .\CONFIGURAR_TELEGRAM.ps1`

   **Correção de compatibilidade com bots já ativos:** o script **NUNCA chama `getUpdates`, `setWebhook` ou `deleteWebhook`**. Procura Chat ID em configurações locais conhecidas ou pede-o no PowerShell (um número, privado ou grupo). Reutiliza o token DPAPI quando possível ou pede-o oculto. Envia um único `sendMessage` de teste ao destino indicado e só grava a configuração após resposta de entrega. **Não interfere com consumidores de updates nem webhooks do bot antigo.** Se não souberes o Chat ID, consulta a configuração do teu watcher OPTIONS existente; o token sozinho não identifica um chat privado de forma fiável.

3. Instala apenas monitor V07, que reutiliza MEXC DPAPI existente:

   `powershell -NoProfile -ExecutionPolicy Bypass -File .\INSTALAR_V07_TELEGRAM.ps1`

   A tarefa `CryptoLab-Three-CONVEX-V07-Telegram-ReadOnly` inicia no login e mantém um loop de verificações de 60s. Primeiro arranque da cache pública poderá levar minutos. O teste de conectividade à MEXC é GET **autenticado e só de leitura**.

Estado: `powershell -NoProfile -ExecutionPolicy Bypass -File .\ESTADO_V07.ps1`

Parar: `powershell -NoProfile -ExecutionPolicy Bypass -File .\PARAR_V07.ps1`

Desinstalar: `powershell -NoProfile -ExecutionPolicy Bypass -File .\REMOVER_V07.ps1`

**Erro antigo**: `TELEGRAM_SETUP_BLOQUEADO: envia /start` era causado pela tentativa de descobrir o Chat ID via `getUpdates` no bot já em uso. Esta versão elimina esse caminho. Se surgirem `CHAT_ID_INVALIDO` ou `TELEGRAM_SENDMESSAGE_FALHOU`, o bloqueio é destino/token/permissão ou rede; o operador antigo fica intacto.\n\n## Segurança

- Se Telegram não estiver disponível, a mensagem continua numa fila SQLite para envio posterior. Depois de uma falha entre confirmação Telegram e atualização da fila, poderá haver uma **mensagem duplicada**, nunca uma ordem duplicada.
- Se a fonte Binance estiver indisponível, avisa quando possível e **não fabrica velas ou sinais**.
- Só aceita token Telegram + chat ID introduzidos/discover localmente; encriptação DPAPI vinculada ao mesmo utilizador Windows. As credenciais antigas MEXC ficam no caminho `%LOCALAPPDATA%\CryptoEdgeRadar\secrets\`, não são copiadas, apenas desencriptadas na memória para o processo local.
- Telegram é serviço de terceiros: envia o conteúdo dos alertas para o bot/chat escolhido; mensagens sobre posições podem revelar metadados da conta, mas não incluem saldo exato, segredos, IDs de posição, nem histórico privado.
- O instalador não usa `winget`, não exige `python.exe`, não toca em operadores V03, OPTIONS nem BNB antigos e não cria nenhum POST MEXC.
- A autenticação e a aceitação Telegram só ficam comprovadas após receberes a mensagem de teste no teu bot e um relatório `ESTADO_V07` recente. Testes offline não são prova do envio do teu bot.
- Uma operação aberta na MEXC não significa que este monitor consiga fechá-la; em caso de alerta inspecciona diretamente a MEXC.

## Validar em desenvolvimento sem credenciais

```
python -m unittest discover -s engine/three_convex_v07 -p "test_*.py" -v
```

Todos os testes usam fakes, sem HTTP real nem chaves.
