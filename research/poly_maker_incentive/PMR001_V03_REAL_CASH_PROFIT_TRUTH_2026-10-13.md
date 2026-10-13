# CRYPTO LAB — PMR-001 V0.3: EVIDÊNCIA DE LUCRO LÍQUIDO (DINHEIRO REAL)
**Data:** 13 outubro 2026  
**Veredito operacional:** **NÃO EXISTE PROVA DE LUCRO LÍQUIDO REPLICÁVEL PARA O NOSSO PMR-001. NÃO CRIAR BOT, NÃO ARRISCAR CAPITAL.**  
**Categoria científica:** rotas de liquidez patrocinada/rebates existem, mas a vantagem líquida permanece não demonstrada para o operador; duas evidências externas reais são NEGATIVAS nos respetivos períodos. Isto NÃO é um teorema de que todos os makers perdem.

## Resposta direta: quem recebeu dinheiro e quanto sobrou?

**A) ClydeScan (relatório do próprio operador, não auditado de forma independente).**
- Fonte https://clydescan.com/results e relato de 28 dias https://clydescan.com/blog/how-much-can-you-earn-polymarket-liquidity-rewards
- Período: 15 dias de payout, até 17 agosto 2026; capital aproximado em risco **US$3.184**.
- Recompensas + maker rebates creditados: **+US$349,45**.
- P&L em operações de inventário encerradas: **−US$479,35**.
- **Resultado combinado divulgado: −US$129,90** (−4,08% do capital aproximado). Exposição residual em posições abertas não é certificada por este número. O blog divulgou correções explícitas a totais incorretos prévios.
- Estimativa do problema: precisar de **1,3717x** receitas de recompensa, mantendo exatamente iguais as perdas, apenas para chegar a zero; aumentar rendimentos ~37,17% ou reduzir perdas ~27,10%, sem despesas adicionais.
- A recompensa era REAL; não era lucro REAL.

**B) tlafargue / Polymarket research (relatório do próprio operador, não auditado de forma independente).**
- Fonte https://github.com/tlafargue/polymarket-research/blob/main/studies/2026-07-09-rewards-pilot-live.md
- 5 mercados, capital alocado ~US$190, ~40h de cotação em 07–09 jul 2026.
- Recompensas efetivamente recebidas **+US$7,52**, P&L de inventário **marcado a mercado −US$18,33** após sete preenchimentos (cinco incidentes).
- **Resultado combinado marcado: −US$10,81**, mas posições residuais não liquidadas tornam isto diferente de resultado final realizado.
- Montantes recebidos no dia 1 foram 0,696x do modelo; dia 2 0,698x. A seleção de mercados teoricamente tranquila foi falsificada por informação/eventos abruptos e a seleção `uncontested AND safely quotable` ficou sem elegíveis numa nova varredura do respetivo operador.
- A experiência de papel tinha indicado +US$994 de accrual teórico vs só −US$40 de fills em ~10h; a passagem a operação real INVERTEU o aparente resultado. Não importar números de papel como lucro.

**A e B são estudos externos distintos, com contabilidades diferentes; NÃO se agregam num P&L nem são uma amostra aleatória de mercado.** São depoimentos de risco e falsificação, não estatística de que toda a plataforma perde. Publicações de terceiros podem conter erros, divulgação incompleta, conflitos comerciais ou contabilidade não auditada; a validação de carteira e fees requer auditabilidade independente.

## C) O que NÓS provámos na PMR-001 (não extrapolar)
- Nossa V0.1: 200 mercados Gamma amostrados por volume; 64 programas ativos, 33 com `rewardsMinSize <=100`, 18 <=50. Run https://github.com/joseluisvieira28-oss/Laboratorio/actions/runs/38404645524
- Nossa V0.2: três mercados selecionados sem olhar primeiro aos novos resultados; 3 lotes CLOB, **9/9 pares YES/NO válidos**, sem ordens, sem prémios recebidos. Run https://github.com/joseluisvieira28-oss/Laboratorio/actions/runs/38412840289
- Pools diários **partilhados entre TODOS os market makers**, NÃO nossos: 562802 US$222, 562803 US$278, 608545 US$9; quantidade mínima 50 shares. Estimativa grosseira de capital ao melhor BID de 50 YES+50 NO ~49,50 /49,50 /49,80, NÃO capital necessário certificado.
- Livro com milhões de shares não identifica contas, não mede cotação efetivamente elegível nem scores individuais, pelo que as anteriores 'pontuações de concorrência' 8.731/10.943/365 **não eram valores medidos**; são relações hipotéticas condicionais, não evidência de recompensa. **RETIRAMOS qualquer classificação de impossibilidade económica derivada desses três números.**
- Não há registo de OUR account rewards, fills, fee receipts, inventory markouts, owner-level scoring ou distribuição real. Nosso net realized **DESCONHECIDO**, e não zero nem negativo observado.

## D) Break-even realmente exigido — sem simular prémios que não recebemos
Os seguintes cálculos são CONDICIONAIS, não retornos:
- Mínimo de prémio diário para haver pagamento na conta = 1 USD ao nível da conta inteira; noutros mercados a quota pode ajudar a atingir esse mínimo; de um mercado isolado, precisa receber >= 1 USD.
- Se uma das duas ofertas hipotéticas de 50 shares sofrer **uma execução adversa** e o preço se mover **5 cêntimos** contra nós antes de conseguirmos desfazer, perda de marcação = 50 × .05 = **US$2,50**. Para compensar APENAS este incidente com prémios diários do mesmo mercado (e receber pagamento):
  - pool 222 => quota da pool > **1,1261%**;
  - pool 278 => > **0,8993%**;
  - pool 9 => > **27,7778%**.
- Para um movimento adverso **10 cêntimos** numa única execução de 50 shares, são US$5; última pool de US$9 requer > **55,5556%** da pool. Uma perda de gap maior ainda é possível; uma ordem pode preencher só um dos lados, e o spread observado não representa garantia de ambas as execuções.
- Mesmo se fosse possível recolher essas quotas, os custos de manter cotação, mudança de pools, risco de liquidação, posição residual e restrições de uso continuam por descontar.
- Calculadora determinística `pmr001_real_cash_truth.py` e testes `test_pmr001_real_cash_truth.py`. É aritmética de cenários, NÃO backtest, ordens de papel ou profit forecast.

## E) Regras oficiais, pagamento, elegibilidade
- Recompensas de liquidez: https://help.polymarket.com/en/articles/13364466-liquidity-rewards — pagam diariamente quando total diário da conta atinge $1, exigem spread, quantidade e cotação elegível.
- Maker rebates: https://help.polymarket.com/en/articles/13364471-maker-rebates-program — só têm lugar quando ordens maker são preenchidas, partilhados dentro do mercado.
- Localização: https://help.polymarket.com/en/articles/13364163-geographic-restrictions — Suíça não listada entre 39 países integralmente bloqueados no snapshot 2026-08-14; isso NÃO verifica permissões da conta do utilizador nem enquadramento legal local. Não contornar bloqueios regionais.
- Fontes externas partilham resultados auto-declarados; não existe verificação independente completa dos comprovativos privados de P&L.

## F) Declaração de prova necessária — não mais 'PASS técnico = lucro'
Considerar **PROVEN_NET_PNL** SOMENTE com:
1. Recibos independentes de prémios efetivamente pagos numa conta e período definidos;
2. Livro de fills/fees, posições e inventário reconciliado (incluindo posições não encerradas, e P&L não marcado não vendido como lucro realizado);
3. Custos adicionais e saídas verificadas, risco e drawdown;
4. Janela prospetiva independente da descoberta, vários dias de payoff com spread e perdas de informação; comparação com não cotar/hold baseline;
5. Direitos de negociação/acesso à venue confirmados para o operador.
Não possuímos os dados 1–4 para uma configuração nossa, e não pedimos credenciais/capital para os fabricar.

## Decisão
**PMR-001 ZERO LIVE GO. NO BOT. NO RADAR PROMOTION.** Também não declarar NO_EDGE universal. Existem casos em que makers ganham; estes dois casos reais publicados perdem, e a nossa microamostra não demonstra o inverso. Nenhuma necessidade de criar mais workflow persistente, restarts, EXEs, carteira ou efetuar trading. Preservar provas, regressões e dados. Manter as 8 estratégias retiradas, 0 ativas. Se houver no futuro outro mecanismo REALMENTE distinto que traga um comprovativo rentável com custos auditados, iniciar novo LAB_ID; não retunar esta amostra de 3 mercados após observar.
