# LIQMAP-DIAMANTE-003 — Auditoria forense de arquivos históricos
Protocolo pré-resultados, 26 de novembro de 2026.

## Pergunta congelada
Podemos recuperar 60–180 mapas BTC com níveis de liquidação, timestamps verificáveis anteriores aos movimentos, a partir de arquivos públicos HyperQuant ou fontes secundárias gratuitas, e testar rigorosamente o sinal congelado LIQMAP-002 sem leakage?

## Fontes e critérios
1. HyperQuant Data, repo rdemb/hyperquant-data. A README MAIN afirma UM commit com estado atual. Verificar commits na rota liq-map/BTC.json e contagem de pais; branch history contém 7 dias de tapes/orderbooks, não mapas de liquidação; ledger guarda previsões de outros modelos; archive guarda velas/funding. Inspecionar se liq-map/BTC.json existe nas branches antigas. NÃO aplicar mapa atual a velas antigas.
2. Hugging Face Hydromancer/hyperliquid-reservoir: inventariar arquivos de posições em datas anteriores e campos de preço de liquidação reportados; ~13 snapshots mensais conforme publisher, confirmar nomes/tamanhos antes de download. Fonte pública HF não implica custo AWS requester-pays.
3. Hugging Face ProbioticFarmer/hyperliquid-augmented-copytrading: inventariar snapshots_perp diários (nomes, datas, bytes, formato). Não presumir que são posições verdadeiras, completas ou têm liqPx até verificar schema original e fonte. Não descarregar vários GB antes de avaliar tamanho e integridade.
4. Blocklens API tem histórico 30 dias no escalão gratuito, mas exige API key mesmo gratuita; consultar docs sem autenticar nem fazer pagamentos. Qualquer tentativa pública sem chave = bloqueio de acesso, NÃO edge negativo.
5. Arquivar URL, hora de GET, HTTP status, hash SHA256 quando possível, árvores / commits, nomes e datas. Publicar metadados agregados, NUNCA identificadores de carteira ou posições individuais.

## Gates económicos congelados
- Replay exato HyperQuant requer >=60 mapas de datas anteriores, com niveles e preço marca conhecidos no momento e hashes/recibos de imutabilidade, não candles apenas.
- Outro fornecedor com posições completas permite TESTE DE HIPÓTESE INDEPENDENTE, mas não replicação exata da cobertura HyperQuant. Para avaliar requer >=60 dias de snapshot e >=50 eventos com primeira barreira resolvida, preço inicial e 24h de OHLC conhecido apenas depois, regra congelada LIQMAP002 de bins log .005, distância .005-.05 e score massa*exp(-dist/.03), MOM24 com as mesmas barreiras, ambos atingidos na mesma vela = ambíguo, custo 80bps por perna+5bps, bootstrap em blocos.
- 13 snapshots mensais ou um dia com 28 snapshots são insuficientes para prova económica. Sem 50 eventos resolvidos => INCONCLUSIVO. Sem histórico => SOURCE_BLOCKED/INSUFFICIENT. Bom histórico retrospectivo nunca é true prospective; mesmo acerto => candidato apenas para SHADOW, não para trading real.
- Não reotimizar distâncias, pesos, janelas ou subset de ativos para obter melhor resultado. Fonte de preços sem mapas (ou eventos de liquidação já ocorridos) não preenche mapas do passado.

## Limites
Sem dinheiro real, ordens, assinaturas, compra de dados, API privadas, contas, endereços pessoais, chaves de exchanges, ferramentas pagas, AWS requester-pays, merge nem produção. Não tocar na tarefa LIQMAP002 ativa.
