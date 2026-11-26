# POLYMARKET-DIAMANTE-007

26 de novembro de 2026 · Continuação dos PRs #404 e #405 · Investigação offline

**Veredito económico: SOURCE_BLOCKED. NO-GO para empregar capital.** A fonte indispensável de livro e tape de novembro não ficou disponível. Nenhum PnL maker, híbrido, de divergência ou por capital foi calculado. A evidência existente não decide se alguma destas hipóteses contém vantagem.

## Aquisição

O conector Google Drive devolveu HTTP 413 para o menor CLOB: 2 304 091 816 bytes contra um limite de 268 435 456 bytes (256 MiB), mesmo pedindo referência de download sem Base64. Os outros dois ficheiros referenciados têm 2 491 201 085 e 4 610 212 840 bytes conforme inventário fornecido. O navegador remoto abriu diretamente o ficheiro privado e foi redirecionado à página de autenticação Google. A pasta de trabalho não continha CLOB de novembro e a pesquisa de anexos por BTC_clob não encontrou cópias. Os endpoints de novembro de PMData, Vike e PolyData5 devolveram HTTP 401 sem autenticação. Sem mudança de permissões, pagamento, subscrição ou envio do conteúdo privado para terceiros. O fornecedor PolyData5 descreve CLOB por ambos os tokens, com snapshots iniciais e reconnects. O conteúdo dos CLOB originais permanece por identificar, inclusive datas, SHA-256, CRC, lacunas, continuidade L2 e tape.

## Referência e liquidação

| Data UTC de receção | Linhas RTDS | Atualizações live TWAP 60s | P50 / P99 atraso RTDS | Maior intervalo entre timestamps live 60s |
|---|---:|---:|---:|---:|
| 7 novembro | 253 819 | 84 119 | 1,577 s / 2,401 s | 16 s |
| 8 novembro | 253 345 | 83 947 | 1,577 s / 2,383 s | 16 s |
| 9 novembro | 253 612 | 84 037 | 1,588 s / 2,383 s | 15 s |

Validei gzip até EOF nas três cópias distintas, calculei SHA-256 nos quatro objetos e confirmei que os dois de dia 9 são idênticos byte a byte pelo hash. As três capturas não duplicadas têm 760 776 linhas. Este é o total bruto após deduplicação por ficheiro, incluindo mensagens de serviço. Há zero erros de parsing e zero regressões no relógio de receção. A estrutura das 2 613 mensagens de histórico é um array e foi tratada separadamente dos ticks live. Os ficheiros contêm spot, TWAP 30 s e TWAP 60 s. O atraso mede observação Chainlink a receção local, incluindo o caminho de publicação.

Consultei 36 mercados consecutivos às 12:00–13:00 UTC de 7–9 de novembro. A Gamma devolveu para os 36 o identificador da condição, token IDs, liquidação resolvida 0/1 e a referência Chainlink BTC/USD TWAP 60 s. Comparar preços exatos no início e no fim com ticks live deu cobertura para 13/36, todos concordantes com o resultado oficial. Usar também as mensagens de histórico, carimbadas pela hora local em que chegaram, deu cobertura para 34/36 e 34/34 concordantes. Em dez mercados a observação exata da abertura só chegou depois de três segundos. Um replay tem de usar o timestamp de receção do histórico para decidir quando o preço se tornou conhecido. O diagnóstico de liquidação não serve para estimar execução ou PnL.

## Veredito por dimensão

| Dimensão | Estado | Evidência |
|---|---|---|
| Qualidade dos dados | INCONCLUSIVO | RTDS auditado, com falhas pontuais nos ticks exatos. CLOB sem acesso aos bytes. |
| Reconstrução L2 | SOURCE_BLOCKED | Sem snapshots, deltas ou reconnects verificáveis de novembro. |
| Maker | SOURCE_BLOCKED | Sem tape deduplicada nem profundidade para sustentar crédito de fila. |
| Híbrido | SOURCE_BLOCKED | Sem dados para simular primeira perna maker e hedge IOC. |
| Divergência face ao oráculo | SOURCE_BLOCKED | Referência de 60 s verificada. Falta preço implícito contemporâneo executável. |
| Gestão de inventário | SOURCE_BLOCKED | Sem trajetória de fills e de pernas residuais. |
| Robustez económica | INCONCLUSIVO | Sem replay. O ensaio de três dias, quando executado, será piloto. |
| Replicabilidade com $100/$250/$500/$1 000/$5 000 | SOURCE_BLOCKED | PnL, drawdown, capital e concentração por calcular. |

## Menor transferência que desbloqueia o piloto

Um recorte **CLOB BTC de 12:00–13:00 UTC por dia para 7, 8 e 9 de novembro**, total de 36 mercados, com snapshots iniciais dos dois tokens, deltas, negócios, reconnects e timestamps de origem/receção. Incluir as mensagens iniciais anteriores ao intervalo quando forem necessárias para reconstruir o primeiro livro. Enviar blocos gzip independentes com **até 250 MiB cada**, cortados em limites de linha e contendo o SHA-256 de cada bloco. Não é necessário reenviar os RTDS. Este recorte verifica a execução maker/híbrida e o emparelhamento temporal. Para o mínimo de 20 observações por horizonte da calibração do oráculo, é necessário acrescentar no dia de descoberta pelo menos oito mercados elegíveis (por exemplo, enviar 12:00–14:00 UTC de dia 7). Uma amostra nova continua obrigatória para replicabilidade independente.

O desenho e os cenários foram registados em protocol.md antes de qualquer resultado económico. Os recibos de fonte são rtds-audit.json e gamma.json. Para reproduzir, executar audit_rtds.py sobre os RTDS originais e source_probe.py para o recorte Gamma. O repositório contém código, hashes e síntese, sem publicar os objetos privados.

- [PolyData5](https://huggingface.co/datasets/polydata5/polymarket-updown-5m-ws)
- [PMData](https://pmdata.dev/docs/historical-data-details/polymarket)
- [Vike](https://vike.io/data/polymarket/historical-data)
