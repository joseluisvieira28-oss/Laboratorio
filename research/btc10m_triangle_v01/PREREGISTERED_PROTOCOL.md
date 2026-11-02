# BTC10M TRIANGULAR NUMERAIRE TRANSMISSION 001 — PRÉ-REGISTO
2026-11-02. Congelar antes de descarregar preços/resultados desta experiência. Uma hipótese, sem optimização nem variantes.

## Mecanismo e novidade delimitada
A arbitragem triangular liga BTCUSDC * USDCUSDT a BTCUSDT. Hipótese: discrepância persistente nos três últimos fechos com transacções contém informação sobre a próxima direcção BTCUSDT, por ajustamento do preço relativo. Isto é uma hipótese de transmissão entre numerários, NÃO prova de arbitragem executável: fechos de velas não são cotações simultâneas. Distingue-se do LOGIT de 11 indicadores BTCUSDT, do fluxo spot/perp e da antiga reversão USDCUSDT a 60min (SPD-USDCUSDT-CROSS25-H60). Inspecção dos nomes dos 1086 ramos e do protocolo SPD não identificou o mesmo teste triangular; não prova novidade universal nem revisão de todos os ficheiros.

## Fontes e períodos fixos
Só arquivos oficiais Binance Spot mensais 1m dos três símbolos BTCUSDT, BTCUSDC, USDCUSDT e .CHECKSUM: https://data.binance.vision/data/spot/monthly/klines/SYMBOL/1m/SYMBOL-1m-YYYY-MM.zip . Documentação https://github.com/binance/binance-public-data .
Diagnóstico/desenvolvimento: TODOS os meses Abril-Dezembro 2023. Validação OOS cronológica: TODOS os meses Janeiro-Dezembro 2024. Nenhum treino nem escolha de candidato em 2023: regra integralmente fixa agora, OOS executado mesmo se diagnóstico negativo para falsificação. 2024 não é holdout global virgem, pois já foi visto noutros estudos. Nenhum dado 2025/2026.
63 ZIPs + respectivos checksums. Validar SHA256, nome CSV, milissegundos, ordem estrita, ausência de duplicados e limites mensais. >=99.95% minutos por símbolo/mês; se não, SOURCE_FAIL sem interpretar como derrota económica. Minutos ausentes não preenchidos. Sem substituir fontes ou períodos. Guardar recibos de download e hashes.

## Sinal e alvo exactos
Em cada fronteira UTC B múltipla de 10min:
para i=B-3m,B-2m,B-1m, r_i=10000*ln(close_BTCUSDC(i)*close_USDCUSDT(i)/close_BTCUSDT(i)).
Exigir em cada uma das três velas de cada símbolo: número de negócios >0, volume base >0, preços OHLC finitos positivos, intervalo exactamente fechado em i+59999 ms.
UP somente se TODOS os três r_i >=5 pontos base. DOWN somente se TODOS <=-5 pontos base. Caso contrário ABSTAIN. Não arredondar r antes da decisão.
Uma previsão por B, sem sobreposição. Alvo OPEN BTCUSDT(B+600s) versus OPEN BTCUSDT(B), ambos com negócios >0 e volume>0. Igualdade exacta TIE com retorno 0. Excluir alvo que atravesse o fim do ano/período. O sinal não lê vela B ou futura. Sem filtros de volume ou volatilidade adicionais.
A referência OPEN(B) é idealizada: a publicação das três velas pode ocorrer depois desse preço. Nenhuma alegação de execução humana ou de paridade com MEXC Event Futures.

## Economia e critérios irrevogáveis
Simular q=.70 primário, q=.80 secundário descritivo: ganho q por acerto, -1 por erro, 0 empate. Não são payouts históricos reais. Exigir TODOS na validação 2024:
>=300 previsões não empatadas, >=20 dias UTC com sinais, acerto >1/1.7;
limite inferior percentil 2.5% do bootstrap por dia UTC do EV q70 >0;
limite inferior percentil 2.5% da diferença emparelhada q70 contra sempre-UP e contra momentum BTC dos mesmos últimos 3min >0;
>=3 de 4 trimestres com EV q70 estritamente positivo.
Bootstrap 10000 reamostragens dos 366 dias completos de 2024, incluindo dias sem sinais; estimador soma payoff / soma sinais (inclui empates), semente 20261102. Reportar n, wins/loss/ties, dias, meses, trimestres, q70/q80 e limites. Reamostragens sem sinais descartadas e contadas.
FAIL_SAMPLE se insuficiente frequência, FAIL_ECONOMIC se falha outro critério, PASS_PROXY somente se todos. Nenhum PASS autoriza trading.

## Auditoria e limites
Segunda implementação separada relê ZIPs originais e checksums, reconstrói cada sinal/alvo por timestamps exactos sem importar funções do teste, compara todos os eventos, contagens e payoffs; verifica causalidade com alteração sintética dos preços B e futuros e recálculo do sinal B. Reportar âmbito e divergências. Auditoria computacional separada pelo mesmo agente não é revisão externa independente; não inventar essa independência.
Congelar código antes de o executar com dados. Publicar resultados e auditoria num ramo de investigação, nunca main. Sem Actions/serviços pagos, contas, ordens, alertas, deploy, compras ou merge. Nunca mudar limiar, sentido, persistência ou períodos depois dos resultados. Fechar definitivamente esta versão perante FAIL; não abrir 2025 para a salvar.
