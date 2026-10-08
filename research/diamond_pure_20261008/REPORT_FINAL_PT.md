# OPERAÇÃO DIAMANTE PURO — VEREDITO ECONÓMICO

Data: 8 outubro 2026. Investigação apenas. **NÃO encontrei uma vantagem extraordinária nem uma estratégia com lucro líquido executável demonstrado nesta missão.**

O trabalho atingiu um veredito legítimo de viabilidade para uma nova hipótese, não o encerramento de toda a procura possível. Uma auditoria de documentos anteriores e um teste de cotações atual não permitem afirmar que não existe edge em crypto.

## 1. Trabalho realmente executado

- Leitura da auditoria obrigatória no commit `ebaddeb5e0ac2922ba523c011c87866f35060409` e rastreio dos freezes/closeouts de LICP, XALT, OPTIONS V2.1, ETF-CME, CED1D, BNB, DH03, BTC Options VRP V2, funding carry, quarterly basis e execução L2.
- Verificação de receitas contabilísticas já existentes no GitHub. Não consultei contas, ordens privadas, saldos ou credenciais.
- Comparação económica de mecanismos: forced-flow direcional, transferência de risco de volatilidade, financiamento com funding variável, convergência de futuros e financiamento por box de opções.
- Criação de **uma** experiência nova: `BOX-FINANCING-USDC-001`, sem reutilizar um resultado histórico como validação.
- Freeze remota às **15:24:00 UTC**; primeiro acesso às opções às **15:26:17 UTC**. Código local, cinco testes de invariantes, coleta pública e replay offline.
- 36 respostas públicas arquivadas com bytes comprimidos, SHA-256, URL, timestamps e RTT. 3.998 opções USDC no catálogo, 1.222 BTC/ETH, 40 combos ativos. Quatro geometrias pré-definidas e duas fotografias de cada uma: **8/8 válidas**. Não são oito trades independentes.
- Nenhum backtest novo, nenhum outcome futuro aberto, nenhuma ordem real. Nenhum novo workflow de mercado foi iniciado. A execução local evitou depender das filas de Actions.

O branch tem uma árvore isolada para esta investigação, com a auditoria anterior na história. Não copia os workflows operacionais de produção. Não é uma proposta de merge para main.

## 2. O que aprendemos com os resultados anteriores

Os números abaixo são evidência documental anterior, não experiências reexecutadas nesta missão. Os progressos forward são os da auditoria de 8 outubro, não uma alegação de monitorização contínua.

| Família | Evidência relevante | Decisão económica nesta auditoria |
|---|---|---|
| LICP BTC 60s | 8/20 episódios, 2 datas. A média anterior de seis episódios era −12,8513 bps líquidos | Forward insuficiente. Nenhum veredito terminal inventado |
| XALT BTC ignition → SOL short 60m | Holdout: 35 observações válidas, 60% de resultados brutos positivos, +25,0714 bps brutos e +9,0714 bps após hurdle de 16 bps. Novembro bruto +2,7075; dezembro +41,8443 | Melhor pista histórica independente deste conjunto, mas é um **teto de transferência**, não PnL executável. Novembro já não cobre 16 bps. Forward inicial: quatro completos, −11,2958 bps; insuficiente |
| OPTIONS-SPOTPERP V2.1 | OOS +5,0428 bps a NET10, −4,6759 a NET20. Break-even implícito 15,1887 bps. API MEXC: 16 bps apenas em fees | Rota taker/taker não sustentada pelo custo histórico. 16/50 forward: BASE −49,74785 bps, PF 0,3282; ainda não é o veredito final congelado |
| ETF-CME | 50 semanas OOS: NET10 +11,40 bps, PF 1,0572; NET20 +1,60 bps, PF 1,0078. HAC unilateral p=0,10365, diagnóstico. Retirar um trade pode deixar média −12,07 bps | Resultado frágil, não uma vantagem extraordinária. Drawdown aditivo histórico −35,43%; não confundir com drawdown de capital comprometido. Q4 2026 continua selado até 2027-01-01 |
| CED1D | Auditoria: 13/60 forward, 1/8 semanas; receipt anterior tinha cinco pares executáveis e média BASE −64,859 bps | Amostra insuficiente; preservar coleta canónica |
| BNB Launchpool | Zero eventos causais elegíveis / 25. Closeout preserva etiqueta histórica Tier 2, mas teste prospetivo espera fonte elegível | Frequência por provar. Etiqueta histórica não equivale a Diamond independente |
| DH03 12H | Zero sinais/resoluções na auditoria; freeze long-only, seis ativos, custo base 0,2%, stress 0,3% | Sem amostra forward; não falsificado nem promovido |
| BTC Options VRP V2 | 192 semanas; IV−RV médio ~10,43 pontos de vol, ~74,5% positivo; limites inferiores HAC/bootstrap acima de zero | Melhor mecanismo de transferência de risco documentado. **Não é PnL de opções**. BBO histórico insuficiente; desenho semanal sem poder útil no capital correto |
| Funding cash carry 24h | N=131; média NET30 −25,20 bps; PF 0; IC bootstrap 95% [−26,52;−23,69] bps. Funding médio +5,05 bps | Exact MVE fechado por insuficiência económica face aos 30 bps congelados. Não alterei custos ou horizonte |
| L2 passive standard | Upper bound com fills perfeitos: −1,6696 bps/oportunidade; 0/6 células positivas, maker 1,5 bps por lado | Monetização direta fechada, apesar do mecanismo validado. Nem um simulador de filas melhor salva este upper bound |
| Quarterly basis T−7d | 24 contratos Discovery; zero entradas acima do limiar congelado de 0,7% | INSUFFICIENT_EVALUABLE_SAMPLE, não NO_EDGE. Exato MVE fechado; 2024–2026 continuam intocados |

**Erro objetivo confirmado:** `totalFee=0` fazia ignorar `takerFee`. O receipt corrigido dos quatro trades OPTIONS regista +0,04204 USDT antes da correção, 0,05378003 de fees omitidas e **−0,01174003 USDT** depois. A correção já existe; não é fundamento para anunciar uma estratégia resgatada.

**Lição estrutural:** um fenómeno previsível pode pagar menos do que o spread/comissões. Um prémio bruto de risco pode exigir muito capital e expor a caudas. Uma média positiva pode depender de um mês ou de um trade. Um resultado proxy de outra venue não prova transferência executável.

## 3. Hipótese nova: financiamento por box USDC

Uma box europeia longa combina +C(K1), −P(K1), −C(K2), +P(K2), com K1<K2 e a mesma maturidade. O pagamento bruto contratual é q×(K2−K1), independentemente do preço final, **se os contratos forem honrados e a posição sobreviver até ao vencimento**.

| Pergunta de realidade | Resposta anterior/associada ao teste |
|---|---|
| Quem paga? | Um eventual desconto ao valor final remunera disponibilizar capital; não foi identificado lucro efetivamente pago nas cotações observadas |
| Porquê poderia persistir? | Capital imobilizado, acesso à margem, custos de quatro pernas e risco de exchange/stablecoin. São hipóteses económicas, não evidência de um prémio observado |
| Dados públicos/grátis? | Catálogo, índice, BBO, tamanho e combos acessíveis. Não se pressupôs histórico BBO gratuito |
| Informação antes da decisão? | Sim para contrato/cotações; freeze antes da coleta. Nenhum settlement futuro consultado |
| Custos? | Bid/ask observado; fee pública e metadata 3 bps por perna, cap 12,5% do prémio. Delivery e risco operacional adicionais. Não apliquei desconto combo a ordens separadas |
| Capital mínimo? | Quantidade 0,01 BTC / 0,1 ETH. Débito ~51–173 USDC; estimativa inicial com SM ~115–371 USDC. Não é reserva suficiente garantida |
| Frequência? | Não estimável por duas fotografias. Quatro geometrias atuais, nenhuma economicamente elegível |
| Automação legítima? | Leitura pública passou. Zero BOX BTC/ETH-USDC ativos para execução conjunta na lista consultada; não criei instrumentos nem RFQs |
| Caudas? | Perda de custódia, depeg, mudança de margem, liquidação antes da compensação final, falha de settlement e legging. Payoff final constante não elimina risco de margem |
| Justifica capital e trabalho? | Não nesta rota observada: o custo inicial já excede o recebimento bruto, antes de qualquer fee |

Geometria congelada: BTC/ETH-USDC, todas as maturidades entre 30 e 120 dias, strikes comuns call/put mais próximos de 90% e 110% do índice; empate para strike inferior. Nenhuma seleção posterior por rentabilidade.

## 4. Números novos e veredito

Primeira fotografia; valores USDC à quantidade mínima. As duas fotografias reproduzíveis constam de `quote_diagnostics.json` no pacote.

| Box | Quantidade | Débito às pontas | Recebimento bruto final | Fees entrada | Resultado máximo após fees de entrada | Capital inicial indicativo SM |
|---|---:|---:|---:|---:|---:|---:|
| BTC 27-Nov, K 73.000/90.000 | 0,01 | 173,00 | 170,00 | 0,97684 | **−3,97684** | 360,00 |
| BTC 25-Dez, K 74.000/90.000 | 0,01 | 162,60 | 160,00 | 0,97659 | **−3,57659** | 371,22 |
| ETH 27-Nov, K 2.200/2.700 | 0,1 | 50,90 | 50,00 | 0,29610 | **−1,19610** | 114,77 |
| ETH 25-Dez, K 2.200/2.700 | 0,1 | 51,00 | 50,00 | 0,29606 | **−1,29606** | 123,47 |

Na segunda fotografia: −3,57750 / −3,37809 / −1,29606 / −1,49641 USDC, respetivamente. As diferenças de timestamp dentro de cada quarteto respeitaram o limite pré-definido de 2 segundos; cotações respeitaram a idade máxima de 5 segundos.

Estes resultados são **limites superiores condicionais às cotações por pernas**, não trades realizados nem lucro líquido all-in. Ignoram despesas não negativas adicionais. O facto decisivo é mais simples: mesmo com zero fees, o débito excedia o pagamento final em **0,90–3,00 USDC** na primeira fotografia. Acrescentar custos reais não torna isso lucrativo.

- **OBSERVED_LEG_ROUTE_ECONOMIC_REJECT:** 8/8 fotografias válidas negativas; zero candidatas.
- **SOURCE_BLOCKED_ATOMIC_EXECUTION:** zero boxes BTC/ETH-USDC ativas na lista pública de combos. Não substituí um livro conjunto ausente pela soma das pernas.
- **Não é NO_EDGE universal:** não foram testados outros strikes, livros maker, outras venues, instrumentos inverse ou outros momentos. Não houve retuning para os procurar neste MVE.
- Expectativa realizada, PF, drawdown, frequência, IC de lucro e independência temporal: **não estimáveis, N realizado=0**. Não transformei oito quotes correlacionadas num estudo estatístico.

## 5. Capital e cenários

| Cenário | Conclusão |
|---|---|
| Otimista, sem fees, sem latência e sem falhas | Todas as combinações observadas já negativas |
| Base indicativa, BBO + fees standard de entrada | Perdas da tabela; delivery ainda por pagar. Não é uma previsão de resultado realizado |
| Conservador, delivery/latência/operação adicionais | Menor resultado; os custos não foram inventados nem tratados como valores medidos |
| Adverso de margem/custódia | Pode haver liquidação antes do vencimento ou perda do capital na venue; a compensação de opções longas não deve ser assumida sob Standard Margin |

Apenas para dimensionamento: no primeiro BTC, a estimativa inicial para as duas pernas short é ~186 USDC; um choque de duplicação do índice dá um **limite inferior ilustrativo de IM short** de ~1.045 USDC usando valores intrínsecos, sem valor temporal. Para ETH, ~64 passa a ~320 USDC. Estes não são quantis históricos nem uma reserva suficiente calculada. Mostram por que o débito de 51/173 USDC não é o capital de risco total.

**Capital recomendado para esta hipótese rejeitada: zero.** Não há estimativa honesta de capital para uma máquina rentável enquanto não houver edge líquido e execução demonstrados. Para VRP, o documento existente aponta ~301 USDC para o par mínimo linear, antes de hedge/reservas; isso também não é um orçamento de segurança nem recomendação de alocação.

## 6. A oportunidade mais forte e o caminho mais curto

**Não existe um vencedor investível nesta evidência.** Se tiver de priorizar UMA pista já existente para validação, é **LICP-FWD-XALT-004**, porque há um holdout histórico independente positivo e um teste de transferência já definido. Esta escolha não é promoção: o holdout é coarse, a fonte forward é diferente, o lucro histórico concentra-se mais em dezembro, e o forward inicial é negativo.

O caminho mais curto é cumprir o teste já congelado: recolher episódios genuínos, persistir IDs/receipts sem duplicações, esperar maturação de 60 minutos, medir BBO e custos da rota e aplicar exatamente os gates existentes. Não são permitidos trocar sensor, reduzir fees, mudar direção ou horizonte depois dos resultados. **Não lancei outra coleta concorrente nem declarei corrigida a persistência nessa frente.** A auditoria anterior identifica essa dependência operacional; não a reavaliei aqui.

A versão BTC LICP 60s é outra hipótese e não pode ser misturada com SOL 60m. O freeze XALT exige pelo menos 20 episódios independentes e três datas; esse é um gate legado desta experiência, não uma regra universal proposta agora. Passar esse gate seria apenas transferência candidata, não prova suficiente de rendimento recorrente.

O mecanismo VRP merece preservação científica, mas exige BBO e redesenho pré-outcome do estimando/poder e do denominador de capital. Não o escolho como caminho mais curto para dinheiro demonstrado. O box rejeitado não justifica construir executor. Nenhuma nova especificação de trading real foi criada.

## 7. Limites e prova verificável

A missão não foi uma revisão integral de centenas de branches. Os documentos essenciais e referências estão em `SOURCE_INDEX.md`. Não reexecutei os backtests históricos, não verifiquei novamente cada job citado e não abri holdouts selados. A investigação nova foi uma viabilidade contratual/cotacional, limitada e suficiente para rejeitar a rota observada. Não foi uma busca exaustiva de arbitragem.

Artefactos:
- `PRE_QUOTE_FREEZE.md`: critérios anteriores às cotações.
- `probe.py` e `tests/test_probe.py`: collector público e testes.
- `PUBLIC_SOURCE_EVIDENCE.zip`: todas as respostas brutas e manifests, geometria, diagnósticos e resumo.
- `OFFLINE_REPLAY_RECEIPT.json`: 36 hashes verificados, oito cálculos reproduzidos, cronologia posterior à freeze.
- `replay.py`: reproduz tudo offline; extrai o pacote se necessário.

Reprodução: `python research/diamond_pure_20261008/replay.py` e `python -m unittest discover -s research/diamond_pure_20261008/tests -v`.

**Veredito desta missão: vantagem líquida extraordinária NÃO ENCONTRADA; novo box por pernas rejeitado nas quotes observadas; execução conjunta SOURCE_BLOCKED; candidatos anteriores preservados nas respetivas categorias.**
