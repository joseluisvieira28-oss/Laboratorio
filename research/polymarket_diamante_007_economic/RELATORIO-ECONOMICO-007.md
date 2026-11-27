# POLYMARKET-DIAMANTE-007 · Resultado económico

27 de novembro de 2026 · Continuação dos PRs #404–406 · Simulação offline

**NO-GO para promover as regras simuladas. Decisão C sobre o edge independente.** Nenhuma combinação das cinco hipóteses, três horizontes e cinco capitais teve lucro líquido estritamente positivo nos dois dias de validação no cenário-base. Mesmo com um cenário alternativo usando termos publicados pela Gamma, nenhuma passou. A prioridade real e a exposição durante descontinuidades permanecem indeterminadas, por isso o resultado não rejeita universalmente maker, híbrido ou oráculo.

## Resultado principal

Validação de 8 e 9 de novembro, 12:00–13:00 UTC, $500 e entrada a 120 s. Horizonte central apresentado por convenção, com todos os horizontes no arquivo. Fills contam execuções parciais como eventos. Pares completos contam mercados sem residual e com exposição emparelhada. Custos nesta tabela são comissão e slippage adicionais ao preço do fill. Drawdown é o máximo diário sobre o PnL realizado, sem marcação intramercado. A coluna adversarial mostra os dois dias separadamente.

| Hipótese | Mercados elegíveis por livro | Ordens | Fills | Pares completos | Residual em contratos | PnL bruto | Custos | PnL líquido | Drawdown | Adversarial 8 / 9 | Veredito de promoção |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---|
| H01 Maker + Maker | 24 | 114 | 1 | 0 | 0,69 | +$0,1242 | $0 | +$0,1242 | $0 | +$10,85 / +$3,58 | NO-GO |
| H02 Maker + Taker | 24 | 114 | 1 | 0 | 0,69 | +$0,1242 | $0 | +$0,1242 | $0 | +$0,95 / +$1,69 | NO-GO |
| H03 Oráculo | 24 | 84 | 0 | 0 | 0 | $0 | $0 | $0 | $0 | $0 / +$3,58 | NO-GO |
| H04 Inventário | 24 | 114 | 1 | 0 | 0,69 | +$0,1242 | $0 | +$0,1242 | $0 | +$7,75 / +$3,58 | NO-GO |
| H05 Microestrutura | 24 | 50 | 0 | 0 | 0 | $0 | $0 | $0 | $0 | +$10,85 / +$3,58 | NO-GO |

Os $0,1242 de H01 e H02 são a liquidação favorável da mesma exposição unilateral, parcialmente executada no dia 8. O dia 9 teve zero fills no cenário-base de ambas as regras, nos três horizontes e com $500. Aos 180 s H01/H02 perderam $0,75 no dia 8. Nenhuma regra teve PnL positivo em ambos os dias no cenário-base com nenhum dos cinco capitais. H04 não demonstrou ganho incremental sobre H01. H05 não demonstrou ganho incremental no cenário-base sobre H01. H03, calibrada com 24 observações de descoberta em cada horizonte, teve zero fills aos 120 s e perdeu $2,25 aos 180 s no dia 8 com $500 e cenário-base. A escolha de lado por hash invertido é o controlo de direção e a regra maker sem a intervenção é a ablação de inventário e microestrutura.

Ranges de PnL líquido por dia, entre regras e horizontes, nos dois dias de validação, excluindo o controlo. Os extremos não são retornos esperados.

| Capital | Pior–melhor PnL diário, base | Pior–melhor PnL diário, adversarial |
|---:|---:|---:|
| $100 | −$0,15 a +$0,12 | −$0,60 a +$1,75 |
| $250 | −$1,12 a +$0,12 | −$1,20 a +$4,38 |
| $500 | −$2,25 a +$0,12 | −$1,20 a +$10,85 |
| $1 000 | −$4,50 a +$0,12 | −$1,20 a +$17,50 |
| $5 000 | −$6,88 a +$0,12 | −$1,20 a +$24,98 |

## Provas e validade causal

- **Insumos.** Cinco gzip lidos até EOF, cinco SHA-256 validados, 6 792 829 frames, 6 591 425 price_change, 134 201 snapshots individuais, 67 041 negócios e 5 reconnects reproduzidos. A separação cronológica foi 24 mercados a 7 de novembro, seguida de 12 e 12. As 12 resoluções adicionais foram consultadas na Gamma, totalizando 48 condições oficiais e TWAP 60 s. Os RTDS previamente auditados têm 760 776 linhas após remoção da cópia duplicada. A calibração oracle só utiliza as diferenças futuras da descoberta, com variáveis do instante da decisão limitadas pelo timestamp de receção e pela idade de 3 s. H03 do dia 7 é in-sample.
- **Livro.** Emissão de 1 286 013 estados de duas pernas, 11 330 impressões SELL admitidas e 11 183 invalidações. Houve 11 055 desacordos entre melhor preço publicado e o reconstruído, mais invalidações por tick, reconexão ou mercado cruzado. Um desacordo retira o token do livro e requer recuperação via snapshot. Uma lacuna com ordem ativa invalida o crédito económico para promoção. A síntese identifica essas lacunas por cenário e mercado. O simulador preserva todos os fills já reconhecidos e liquida o residual. A perda adicional por fills possíveis dentro da lacuna não foi quantificada. Assim, não é possível defender o PnL líquido como limite inferior realizável.
- **Tape e execução.** Fonte identifica a direção agressora e a transação. O replay usa no máximo uma impressão por hash por mercado e não converte cancelamentos em fills. O cenário de fila exige volume SELL no preço no mesmo token depois da chegada registada. O cenário trade-through exige SELL estritamente abaixo do preço passivo e usa atraso de 1 s. Trade-through verifica uma evidência diferente e pode dar mais fills que o cenário de fila quando o preço anterior deixa de aparecer. Os resultados adversariais não são um limite inferior monotónico do caso base. O tamanho exibido à chegada inicializa a fila por hipótese, sem identificação individual de ordens.
- **Custos, caixa e mínimos.** Modelo principal conserva a caixa até ao final do dia, usa 0,07·q·p·(1−p) para IOC e 0,005/0,01 de slippage, sem incentivos. A Gamma retornou mínimo 5, tick mínimo 0,001 e taxa publicada 0,01 para os 48 mercados. O motor usa mínimo 5 no envio maker, IOC com mínimo de $1 como hipótese, granularidade 0,01 na quantidade e preço cotado em milésimos. A diferença em relação à convenção inicial de tick 0,01 está documentada aqui. Não há verificação histórica independente dos filtros exatos de IOC e da taxa aplicada em cada execução simulada. Uma sensibilidade separada com $500 usa 0,01 e recicla a partir de closedTime +15/30 min. É uma aproximação de disponibilidade, sem prova de resgate no mesmo instante. Nenhuma variante dessa sensibilidade foi positiva nos dois dias e cenários.
- **Limitações.** O livro normalizado guarda melhores preços, profundidade no topo e desequilíbrio de três níveis quando o topo muda ou um snapshot chega. H05 pode ignorar alterações isoladas fora do topo. O replay usa o primeiro evento após o atraso, com aritmética em milissegundos. O controlo aleatório é determinístico e não amostra a distribuição de seeds. A decomposição do ledger usa custo médio para lucro bruto de pares e residual, mais comissão/slippage em separado. O capital gasto fica segregado no cenário principal. Não foi instrumentado um pico completo de reservas pendentes por instante, nem drawdown por marcação intramercado. O veredito de replicabilidade e a robustez após custos continuam INCONCLUSIVOS. A decisão de avançar com capital pequeno é NO-GO. A amostra não suporta promoção nem GO piloto.  

## Reprodução

Colocar os cinco CLOB e manifest.json junto dos scripts. Colocar os RTDS originais e gamma.json da fase anterior em ../seven. Verificar protocol.md e a interpretação do motor com freeze.sha256. Para regenerar os 12 recibos adicionais, executar python source_probe.py > gamma-extra.json. Executar python extract.py, python replay.py, python summarize.py e opcionalmente REPLAY_PROFILE=published_terms python replay.py. A compressão gzip contém carimbo de escrita e pode alterar o SHA-256 do ficheiro comprimido ao repetir a execução. Verificar a equivalência dos registos descomprimidos. A síntese decisão verifica 8 640 linhas de ledger e 75 comparações de promoção. O arquivo inclui as duas trajetórias por mercado e todos os fills virtuais. Objetos de fonte privados não foram publicados.

Nenhuma ordem real, depósito, pagamento, subscrição, alteração em produção ou reotimização das regras taker anteriormente rejeitadas.
