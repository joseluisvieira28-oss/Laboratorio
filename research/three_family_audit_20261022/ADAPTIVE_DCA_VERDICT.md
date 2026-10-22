# DCA Adaptativo — veredito ADCA-BTC-SMA200-001
Data: 2026-10-22. **HISTORICAL_SUPERIORITY_NOT_REPLICATED / sem edge independente executável demonstrado.**
A regra ficou congelada antes do novo replay e não foi ajustada após outcomes.

## Regra e desenho
BTCUSDT Spot Binance; depósito100USDT todas as segundas00:00UTC. Compra150 abaixo da SMA200 do fecho anterior,50 caso contrário, limitada ao cash existente. Sem crédito; caixa não utilizada permanece sem juros. Cada ano começa sem posições. Comparadores: DCA fixo100, compra constante75 com caixa e caixa integral.
2021–23 descritivo;2024 validação temporal;2025 teste temporal. São duas trajetórias OOS para esta regra, mas não holdout virgem do laboratório. Nenhum outcome2026 adquirido. Não se tratam compras semanais como observações independentes.
Freeze:1d746cd94451829d5b70402f0f70fbee8f761421. Runner verificado:4bcbad3e6644cea2b297837e86959915bcd86094. Gate pré-outcome:212048b8531929c74f205d8cd514ceb9c46957f6.
Uma correção pré-outcome tratou denominador zero antes do primeiro depósito. Seis grupos de testes sintéticos passaram. Após o único replay,2353 verificações de contabilidade passaram; não houve alteração da regra.

## Fonte com timestamps e custo de aquisição
72 ZIPs e72 sidecars oficiais;163309bytes no total; SHA256 verificado por objeto.2192 dias UTC2020-01-01..2025-12-31; zero lacunas/duplicados. Parser trata ms antes2025 e micros desde2025.
SOURCE_PASS pré-outcome:2026-10-22T11:47:54.101854Z. Outcomes calculados:11:48:58.060799Z. O manifesto inicial está conservado separado do manifesto de revalidação posterior. Arquivos podem ser revistos pelo provedor; hashes identificam a versão adquirida, não provam a sua vintage histórica.
Falha inicial real: DNS getaddrinfo11001 no processo local. Foi resolvida ao usar execução com permissão de rede concedida. Não é obstáculo atual.
Custo monetário adicional:0; runtime existente, fonte pública, sem subscrições. Consumo da sessão não foi quantificado em moeda.

## Resultado líquido após15bps por lado
Todos os valores são simulação em USDT. Ganho/contribuições não é retorno de um capital todo investido no início.
| ano | contribuições | riqueza DCA fixo | riqueza adaptativo | diferença/contribuições |
|---|---:|---:|---:|---:|
|2021|5200|5284.97|5580.28|+5.68pp|
|2022|5200|3426.91|3426.91|0.00pp|
|2023|5200|7977.92|7263.19|-13.74pp|
|2024|5300|7907.05|7183.81|-13.65pp|
|2025|5200|4535.42|4873.37|+6.50pp|

2024 possui53 segundas; não é erro de contribuição. Em2025 ambas as regras perderam dinheiro face às contribuições: adaptativo-6.28%,fixo-12.78%.
Com30bps por lado, diferença2024=-13.51pp;2025=+6.55pp. O gate exigia vantagem nos DOIS anos e nos DOIS custos: falhou.
No controlo constante75, riqueza2024=7255.29 e2025=4701.56. O adaptativo ficou71.48 abaixo desse controlo em2024 e171.81 acima em2025. Caixa integral:5300/5200. Estes controlos não permitem atribuir uma vantagem robusta à SMA.

## Custo total e risco
Base15bps/lado=10fee+2.5half-spread+2.5slippage; stress30=20+5+5. São cenários, não custo de conta verificado.
Fricção total base incluindo venda final:
|ano|adaptativo|fixo|
|---|---:|---:|
|2024|13.77998|19.81648|
|2025|11.50935|14.60167|
Stress:adaptativo27.51874/22.98427;fixo39.57369/29.15966.
Sem perp:funding e borrow não se aplicam. Sem depósitos/levantamentos de exchange modelados, impostos ou perdas de contraparte/USDT; nenhum custo relevante foi declarado verificado só por ser omitido.
Máximo drawdown diário TWR2024:adaptativo-15.72%,fixo-26.26%;2025:-22.75%/-32.04%. Mais caixa reduz exposição; isso não prova previsão superior. Em2022 o cash cap levou ao mesmo ledger económico do DCA fixo.

## Limitações e decisão
A compra no open diário usa o fecho anterior completo exatamente na fronteira UTC: é referência idealizada, sem comprovação de latência/fill posterior ou livro executável. Não é uma ordem simulada com execução demonstrada.
BTC/venue única, duas trajetórias temporais, regimes partilhados, exposição prévia do laboratório, caixa a juro zero e resets anuais limitam generalização. Não há intervalo de confiança independente robusto com dois anos. Não extrapolar para DCA contínuo plurianual ou outras regras.
Encerrar esta comparação com superioridade não replicada. Não testar SMA diferente, alvos, filtros ou caixa remunerada escolhidos pelos resultados. Próximo estudo exigiria mecanismo justificado separadamente e freeze prospectivo com dados/fills posteriores. Nenhum live GO.

Fonte técnica: [Binance Public Data](https://github.com/binance/binance-public-data/blob/master/README.md), lida2026-10-22. Manifestos/ledgers/código acompanham o relatório.
