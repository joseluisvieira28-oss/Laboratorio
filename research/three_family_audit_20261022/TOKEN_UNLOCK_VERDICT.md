# Token Unlock Supply Shock — auditoria e veredito
Data: 2026-10-22. Veredito: **DUPLICADO IDENTIFICADO; manter NO_EDGE do MVE exato TUE-CLIFF-ADV30-001. Sem promoção.**
Isto não rejeita universalmente todo o efeito de unlocks. É uma adjudicação separada desta família; não é revisão por um segundo investigador.

## Hipótese e estudo herdado
Mais tokens desbloqueados por unidade de volume spot causal deveriam prever retorno relativo mais fraco. O estudo original congelou um limiar no percentil 67, antes dos outcomes: 1.735808924238034 dias de absorção. Signal: volume médio nos 30 dias completos anteriores à entrada. Afastamento spot de D-7 a D+8; janelas sobrepostas do mesmo token unidas.
Freeze original: blob 143483883d33055a98ecc2ee666d73d4754a6b2c. Resultado oficial em a550e46d69514174fa72eb994532e80a7d53e146; resultado blob eaf11961762885874d365a7a06eab2a23964ca94.
Fonte original: snapshots imutáveis históricos do provedor + arquivos oficiais Binance e checksums. O recibo PIT de uma etapa antecedente reporta disponibilidade >=30 dias antes do evento; não confundir os seus 227 candidatos com os 237 eventos finais de outro percurso de qualificação.
Sem reaquisição integral dos bytes upstream nesta auditoria: proveniência bruta e bootstrap herdados não foram reexecutados.

## Resultado e verificação independente da aritmética
237 eventos, 22 tokens, 2023–24; 80 eventos de pressão alta, 14 tokens; 77 episódios económicos.
Recalculei dos ledgers persistidos:
- beta pressão/retorno relativo: +0.00171024731832254, sinal contrário ao esperado; CI herdado [-0.02194115,+0.02536165].
- média por episódio após 30bps round trip: +0.0569637%;
- após 60bps: -0.2430363%;
- 2024 média base herdada: -0.7537843%.
Erros máximos de reconstrução de retorno e custos: zero. Todos os fins de janela de sinal precedem a entrada; nenhum exit entra em 2025.
O controlo BTC é favorável em parte da análise, mas não substitui a falha da regressão nem o custo stress negativo. Dependência foi tratada originalmente por clusters de token; o CI bootstrap stress cruza zero.

## Custo total, controlos e OOS
Custos congelados: 10bps fee+5bps execução por lado; stress 10+20bps por lado. Os 30/60bps são cenários, não fills auditados. Média por episódio não equivale a P&L de carteira com capital comum: falta ledger de notional/capital/concorrência entre tokens para custo total em moeda e capacidade.
Controlo BTC nos mesmos timestamps; união de overlaps; estabilidade anual; proibição de escolher vencedor-token ou inverter sinal. Não foram encontrados placebos/matched controls suficientes para atribuição causal universal. Resultado é associação/teste de regra.
Não abrir 2025/2026 para salvar o estudo: discovery falhou, logo OOS não autorizado pelo protocolo herdado. Nenhuma nova janela desta família foi aberta.
UNLOCK-CLAIM-FLOW-001 é um mecanismo adjacente distinto e continua com recibo de contaminação de reconhecimento externo/quarentena; não é prova de edge e não foi reativado. Nenhuma wallet foi consultada.

## Próximo gate defensável
Não repetir threshold/horizonte/recipiente. Só um mecanismo materialmente distinto, com fonte histórica known_at verificável, controlo de mercado/seleção e freeze prospectivo poderá constituir novo estudo. Veredito atual encerrado para o MVE exato.

Fontes (todas lidas em 2026-10-22):
- [protocolo original](https://github.com/joseluisvieira28-oss/Laboratorio/blob/a550e46d69514174fa72eb994532e80a7d53e146/Dream-Account-OS-v2.3-PARTIAL/research/token_unlock_event_001/FINAL_PRE_DISCOVERY_PROTOCOL_V01.json)
- [resultado completo](https://github.com/joseluisvieira28-oss/Laboratorio/blob/a550e46d69514174fa72eb994532e80a7d53e146/Dream-Account-OS-v2.3-PARTIAL/research/token_unlock_event_001/discovery_evidence/TUE_DISCOVERY_RESULT_V01.json)
