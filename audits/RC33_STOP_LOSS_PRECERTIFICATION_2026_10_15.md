# RC3.3 — Preparação de certificação do stop-loss — 15/10/2026

**VEREDITO: NOT_CERTIFIED / NO_LIVE_GO.** Este pacote é exclusivamente offline. Não faz login, não usa DPAPI, não lê segredos, não faz GET autenticado e não envia POST, ordens, closes ou stops reais.

## Evidência de entrada (PC real)
Recebido o relatório RC33_READONLY_RECEIPT.json de 15/10 10:10:40 UTC. Neste snapshot: engine.py SHA256 \`26b05a1f229f1884d0c15c802c98ecad71f30b108f68efe165d72f3e2ab2b714\`, mexc_futures.py SHA256 \`fac987781b281deacab576134148f1611559c2ddd2061dc86110319103263034\`. Naquele instante havia um executor e LIVE_AUTHORITY, e KILL_SWITCH estava ausente. O utilizador **depois confirmou** kill switch TRUE, LIVE_AUTHORITY inexistente, OBSERVE_ONLY, posições e pending entries locais zero às 10:25:33 UTC. Isto **não** substitui broker account GET para posições/ordens/stops.

O reporte original mede hash, não fornece o conteúdo de engine.py instalado. Um ficheiro engine.py antigo em documentação do laboratório usa outra pasta \`CryptoLab/ConvexRadarTrade\` e não deve ser tratado como a instalação \`ConvexRadarUnifiedRC33\`. O código do motor 3-CONVEX V08/V09 num PR separado também NÃO prova o comportamento deste RC3.3.

## O que foi preparado nesta branch
- \`audits/rc33_stop_preflight_v01/synthetic_stop_contract.py\`: contrato puro de referência dos invariantes de stop/readback. Valida nos MOCKS identidade da posição, lado long, volume integral, stop único não encerrado, preço, TP nulo, dados frescos, interrupção/restart e resposta ambígua sem reenvio. Em **nenhum** cenário concede live_go, nem para o mock positivo.
- \`audits/rc33_stop_preflight_v01/test_rc33_stop_offline_v01.py\`: regressões isoladas para 23 cenários, incluindo fill parcial, ausência de stop, cobertura a mais ou a menos, NaN, posição errada, timeout, restart pendente e fonte local desarmada. Não importam módulos de execução real.
- \`audits/rc33_stop_preflight_v01/rc33_local_source_preflight.py\`: verifica apenas o SHA256 dos dois ficheiros instalados, analisa a **sintaxe AST sem executar código**, procura nomes conhecidos de funções e lê flags locais desarmadas. Não mostra fonte, tokens, caminhos absolutos nem dados de conta. \`installation_certification\` é **sempre NOT_CERTIFIED**, \`broker_account\` é NOT_QUERIED, \`live_go=false\`.
- Workflow GitHub Actions apenas nesta branch: \`rc33-stop-loss-offline-v01-qa.yml\`, compila/verifica os testes isolados, sem secrets, sem mercado ou acesso ao Windows.

**Um teste mock aprovado prova apenas que o modelo de segurança rejeita cenários sintéticos. Não prova integração do motor RC3.3 com a corretora.** Um hash matching também só prova igualdade com o snapshot enviado, não qualidade nem autenticidade da execução.

## Próximo passo seguro no PC Windows (sem ordens)
Manter KILL_SWITCH presente e LIVE_AUTHORITY ausente. Num PowerShell normal, executar:

\`\`\`powershell
$url = "https://raw.githubusercontent.com/joseluisvieira28-oss/Laboratorio/ops/rc33-stop-offline-preflight-2026-10-15/audits/rc33_stop_preflight_v01/rc33_local_source_preflight.py"
$out = Join-Path $env:TEMP "rc33_local_source_preflight.py"
$report = Join-Path ([Environment]::GetFolderPath("Desktop")) "RC33_STOP_OFFLINE_PREFLIGHT.json"
Invoke-WebRequest -Uri $url -UseBasicParsing -OutFile $out -ErrorAction Stop
py -3 $out | Tee-Object -FilePath $report
\`\`\`

Se Python não estiver instalado, parar e informar; **não** instalar serviços nem executar o bot para contornar o problema. O output é metadata-only e pode ser entregue ao auditor.

Para efetivamente executar testes do **motor instalado**, é preciso receber/examinar os dois ficheiros \`%LOCALAPPDATA%\CryptoLab\ConvexRadarUnifiedRC33\app\engine.py\` e \`app\mexc_futures.py\` (sem config.json, LIVE_AUTHORITY.json, DPAPI, chaves, credenciais, .env). Rever manualmente ficheiros antes de partilhar; se contêm segredos, NÃO os partilhar. O hash permite ligar o código aos recibos, mas se o conteúdo for alterado para o limpar é preciso registar divergência.

## Gates em falta para certificação
1. **Versão instalada ainda não foi auditada em código:** mock/stub adapter da interface real; testes exatos de order create, GET authoritative, attached stop readback, stop underfill/overfill, preço e ordenação temporal, falha de API, crash/restart, stop amendment.
2. **Prova no broker inexistente:** snapshots autenticados só de leitura, via PC, com ordens, posições e stops reais. Nunca pedir ou enviar segredos.
3. **Proteção de entrada não atómica/não provada:** ACK de POST ou um parâmetro stopLossPrice NÃO provam proteção antes de exposição. Exige prova de semântica atual do broker, reconciliação e latência; se não houver atomicidade, o desenho pode não ser certificável para live automático sem risco de intervalo desprotegido.
4. **Roundtrip real ainda NÃO autorizado:** testar mínimo sob protocolo separado, com orçamento de perda, conta sem posição/ordens, confirmação independente do stop nativo e tratamento de unknown POST, fill parcial, amend, close e restart. Possibilidade de perda real, slippage, liquidação e falhas de stop.
5. **Firewall final:** até todos os gates passarem, \`BROKER_ATTACHED_SL_ROUNDTRIP_NOT_CERTIFIED\` permanece; KILL_SWITCH presente, live authority inexistente; nunca autorizar ordens automaticamente por resultado de testes offline.

## Outros sistemas
O Radar Render Public Shadow, PR #230 e Telegram PR #229 são sistemas distintos; este pacote não toca neles. O motor 3-CONVEX V08/V09 é uma implementação distinta e permanece NO_LIVE_GO. Nunca transferir PASS entre motores.


## CI verificado
- [GitHub Actions #38731349731](https://github.com/joseluisvieira28-oss/Laboratorio/actions/runs/38731349731) — commit \`5a0e1dd58f54d3e835bffb177253bcf674252f81\`.
- **23/23 testes sintéticos PASS**; compilação PASS; input negativo sem motor Windows PASS e \`live_go=false\`.
- Teste nenhum invoca engine instalado, MEXC, autenticado GET, POST nem chave API. Logo estes PASS são **apenas preparação**, não certificação de stop ou prova de fills.
