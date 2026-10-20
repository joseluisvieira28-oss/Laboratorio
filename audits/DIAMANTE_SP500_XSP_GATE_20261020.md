# Diamante Puro — gate económico e de dados: puts S&P 500
20 de outubro de 2026 · **INCONCLUSIVO / SOURCE_BLOCKED**

**Decisão:** não avançar para freeze ou teste completo. Não há vantagem demonstrada nem prova de inviabilidade universal. O obstáculo é a falta de um histórico XSP com cobertura, sincronização, execução e direitos de uso suficientemente verificados. Os custos tornam essa exigência especialmente importante num spread de um contrato.

## Evidência económica
A investigação favorável sobre PUT/WPUT sustenta a hipótese histórica de remuneração por vender seguro, mas usa puts colateralizadas, índices hipotéticos e custos incompletos. Não demonstra o resultado de vender uma put e comprar outra mais baixa. A proteção comprada reduz perdas, crédito e exposição; pode absorver precisamente o prémio procurado. O trabalho contrário obrigatório de Dew-Becker e Giglio (Chicago Fed, 2025) encontra alphas recentes indistinguíveis de zero. Não prova zero para este spread, mas impede assumir que a vantagem histórica persiste. Fontes e limitações estão no [anexo, secção 1](DIAMANTE_SP500_XSP_EVIDENCE_20261020.md#1-o-que-a-investigação-permite-concluir).

Exposição direcional, prémio por risco de cauda e alpha são coisas diferentes. A taxa de acerto e o prémio bruto recebido não resolvem essa distinção; seria necessário comparar resultados líquidos com risco, capital e benchmark adequados.

## Dados e acesso
Não encontrei uma fonte gratuita suficiente. O gratuito Theta é EOD baseado no último NBBO quando gera o relatório; não garante uma entrada sincronizada executável. IBKR exclui históricos de opções expiradas. Valores de liquidação XSP aparecem publicamente na Cboe, mas o arquivo completo e os direitos para o estudo continuam por validar.

O menor pacote útil que consegui orçamentar foi **US$1.100 de subtotal**, no calculador público Cboe: `^XSP`, 04-01-2016 a 31-12-2025, snapshots de 15 minutos, sem Greeks/open interest. Não se comprou. O formulário aceitar o símbolo não demonstra cobertura efetiva. Faltam ainda idade das quotes, execução complexa, índice subjacente e preço/licença total. Theta e Databento são alternativas identificadas, sem orçamento XSP confirmado. A amostra ou um dia de dados só qualificariam formato/qualidade.

Para um residente suíço, IBKR e XSP parecem acessíveis em princípio, sujeitos a elegibilidade, permissões de opções e reconhecimento do spread. Não houve consulta de conta. XSP é europeu e liquidado em dinheiro; o QSB atual cobre verticais de um ponto com vencimento no próprio dia ou seguinte. Isso não valida liquidez mensal nem fills simultâneos. Fontes oficiais, condições e lacunas: [anexo, secções 2–3](DIAMANTE_SP500_XSP_EVIDENCE_20261020.md#2-gate-de-dados-e-legalidade).

## Custos que mudam o gate
Num **exemplo hipotético**, um spread de largura US$100 recebe US$30 usando bid da curta e ask da longa, contra US$40 indicativos ao midpoint. Não é uma cotação observada nem execução garantida.

O mínimo IBKR por perna leva a US$2 de comissão de entrada e US$4 se houver entrada e saída. Com taxas e ORF explicitamente assumido, o cenário conservador calculado dá **US$3,13 à entrada**, antes de câmbio e dados. Para uma operação mensal, OPRA não profissional, duas pequenas conversões manuais e amortização hipotética dos US$1.100 por 120 operações, os custos fora do bid/ask chegam a **US$17,80/operação**; diferença ao midpoint acrescenta US$10. Rebates e conversão automática podem reduzir custos, mas não foram presumidos. Subscrever índice/book complexo, impostos e custo de capital podem aumentá-los. Logo, não existe ainda uma fatura all-in confirmada. [Fórmulas, tarifas, pressupostos e sensibilidades](DIAMANTE_SP500_XSP_EVIDENCE_20261020.md#4-economia-de-um-spread-pequeno--cálculo-não-cotação).

## Utilidade de um futuro teste
Dez anos mensais oferecem cerca de 120 intervalos não sobrepostos; não garantem independência nem muitos episódios de cauda. Aumentar posições sobrepostas não cria informação independente. Um teste poderia rejeitar uma economia fraca, mas certificar alpha pequeno exigiria incerteza por blocos/regimes e um mínimo económico fixado antecipadamente.

**Compensa esclarecer as lacunas documentais; não se justifica agora despesa ou infraestrutura.** Reabrir o gate quando cobertura XSP/settlements, licença/preço total, qualidade temporal/execução e taxas de combo/ORF estiverem resolvidos. Não contactar fornecedores nesta fase.

O gate não passou: não se escolhem parâmetros nem se propõe freeze. Qualquer futuro teste exigirá uma única implementação e critérios económicos/estatísticos fixados antes de abrir outcomes. [Anexo integral](DIAMANTE_SP500_XSP_EVIDENCE_20261020.md) · [cálculos reproduzíveis](DIAMANTE_SP500_XSP_CALCULATIONS_20261020.json).

Execução: árvore remota main `75fb36c8337c3221b7551c513e049cd472dad231` inspecionada; nenhum AGENTS.md encontrado, raiz devolveu 404. Aplicadas instruções locais de sources/ só leitura. Não se abriram holdouts, resultados de experiências ou contas privadas. Só documentação de investigação num branch novo; sem despesas, ordens, contactos, Render, alteração de main ou merge.
