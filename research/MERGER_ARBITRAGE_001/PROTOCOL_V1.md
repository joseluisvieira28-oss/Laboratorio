# MERGER ARBITRAGE 001 — protocolo v1.0 congelado
Data de desenho: 2026-10-20, Europe/Zurich. O carimbo verificável de pré-registo é o commit GitHub deste ficheiro, não esta data declarada.
Base: main 75fb36c8337c3221b7551c513e049cd472dad231.
Branch exclusiva: research/merger-arbitrage-001-20261020.
Estado inicial: nenhuma recolha de novos resultados ou preços efetuada para este estudo antes da publicação deste protocolo. Conhecimento geral prévio de operações famosas existe; uma análise histórica não é um holdout genuinamente desconhecido.

## 1. Proteção e hipótese
Apenas novos ficheiros sob research/MERGER_ARBITRAGE_001/. Não abrir dados/resultados de holdouts existentes; não modificar estudos, main, workflows ou infraestrutura. Nenhuma ordem, conta privada, capital, automação de trading ou estratégia implementada.
H0: após custos, oportunidade temporal do dinheiro e risco de falha, não há excesso líquido reproduzível para particular residente suíço.
H1 primária: carteira de ofertas em dinheiro com filtro de qualidade fixo supera caixa comparável e exposição indiscriminada, após custos, com execução plausível.
Estimando primário: diferença de retorno líquido anualizado de carteiras calendárias em CHF, incluindo caixa ocioso e operações falhadas. Retornos por evento não substituem uma carteira.

## 2. Desenho e universo
Viabilidade primeiro, com limite de 12 operações de auditoria e 3 rotas de dados públicos (fontes oficiais da transação, reguladores/SEC, fornecedor público de preços), nesta execução. Casos de auditoria são selecionados deliberadamente para cobrir sucesso, cancelamento, atraso, revisão e crise; não são uma amostra de inferência nem base para taxa de sucesso.
Universo confirmatório proposto, imutável nesta versão: TODOS os acordos definitivos anunciados entre 2018-01-01 e 2024-12-31 para adquirir controlo de ações ordinárias listadas nos EUA, Reino Unido ou Suíça, preço fixo integralmente em USD/GBP/CHF/EUR, valor de equity anunciado >= 500 milhões CHF convertido à data do anúncio, alvo negociável em bolsa no momento de entrada. Incluir acordos posteriormente cancelados, contestados, revistos, atrasados e ainda pendentes.
Excluir propostas não vinculativas antes de acordo definitivo, pagamentos mistos/ações, earn-outs/CVR obrigatórios, escolhas de contraprestação que impeçam determinar cash fixo, privatizações sem ações cotadas e instrumentos inacessíveis ao particular. Não excluir falhas ou spreads negativos por resultado.
Exigência de acesso: comprovação pública do instrumento, mercado, lotes e restrições a residente CH; se não verificável, marcar acessibilidade desconhecida, sem presumir execução. Sem aceder a contas.
Construir universo a partir de registo cronológico independente da performance, reconciliar com filings oficiais e lista de exclusões. Não usar apenas lista de negócios concluídos, constituintes atuais de ETFs, ou os casos de auditoria.
Períodos fixos: 2018-2019 diagnóstico; 2020-2022 stress (inclui COVID; rótulo amplo, não afirma que todo o período seja crise); 2023-2024 validação cronológica histórica, apenas se não anteriormente examinada e sem recalibrar filtros. Novos anúncios posteriores ao commit apenas constituem validação prospetiva após novo protocolo; não iniciar monitor automático.
Corte de resultados: 2026-10-19 23:59:59 UTC. Pendentes ficam censurados e marcados ao mercado no corte, nunca rotulados sucesso ou eliminados.

## 3. Relógio da decisão e execução
t0 = primeira sessão regular COMPLETA após publicação do acordo definitivo, usando timestamp e timezone oficiais. Decisão após fecho de t0; execução no fecho da sessão seguinte t1. Sem timestamp preciso, usar conservadoramente mais uma sessão. Não usar preços anteriores ao anúncio como entrada.
Informação de seleção congelada no fecho t0. Datas esperadas são as comunicadas ATÉ t0, com intervalo textual e URL; não substituir por data final. Sem data esperada explícita, duração esperada e anualização ex-ante = NA.
Preço de entrada: ask histórico em leilão/fecho t1 com volume suficiente e timestamp, se disponível. Fecho diário não ajustado + slippage pré-fixado é apenas proxy, rotulado; não pode sozinho fundamentar DIAMANTE. Preços ajustados exigem reconstrução de splits e dividendos para evitar dupla contagem.
Saída: contraprestação efetivamente recebida e data de disponibilidade do dinheiro; se cancelada, venda no bid do fecho da primeira sessão completa após notícia pública do cancelamento. Se sem cotação, manter perda/recuperação explícita, nunca remover observação. Não vender só porque ultrapassou data esperada.
Registar revisões como caminho da MESMA operação; sem duplicar trades. Dividendos e reduções contratuais de preço separados. Pendentes: valor de liquidação ao bid no corte e censura.

## 4. Filtro e probabilidade ex-ante
Indiscriminada: todo universo elegível. Qualidade: simultaneamente (a) cash/financiamento comprometido documentado e ausência de financing-out; (b) todas aprovações concorrenciais/FDI/setoriais obrigatórias já obtidas ou inexistência de condições explicitamente documentada até t0; (c) sem litígio/injunção/oposição oficial que impeça fecho até t0; (d) sem condição de due diligence, sem voto ainda necessário ou tender minimum pendente. Desconhecido em qualquer campo = fora da selecionada, mas permanece no universo.
Não alterar filtro se resultar em zero operações. Não usar termos como “baixo risco” sem documento.
p(conclusão) nunca inferida apenas do spread; isso seria circular. Modelo probabilístico nesta execução = não estimável até existir coorte completa com >=100 resoluções e >=10 falhas em treino anterior a cada previsão. Se houver esses dados: regressão logística com L2=1, variáveis binárias financiamento/autorizações/voto-litígio e log dias esperados, padronização só em treino, treino expanding por ano, missing indicator, sem tuning. Reportar Brier/calibração fora da amostra. Se não, apenas limiar de break-even e cenários, sem p inventada.

## 5. Capital e custos
Carteira sem alavancagem, long-only, CHF 10k/50k/100k; primária CHF 50k. Máximo 10% do NAV por evento e 20% por comprador; ações inteiras; excesso de procura ordenado por timestamp depois ticker; caixa residual remunerado ao benchmark. Sem diversificação fictícia quando existem poucos nomes.
Broker referência de viabilidade: tarifas públicas IBKR Pro fixed (não assumir residência/conta efetiva). Guardar versão/data e confirmar instrumento. Não extrapolar tarifa atual como tarifa histórica: se histórico não recuperável, estudo de viabilidade a custos atuais, não P&L histórico líquido validado.
Separar corretagem e mínimos entrada/saída, taxas bolsa/regulador, bid-ask, slippage, FX com mínimos, custo de carry, eventuais taxas tender/corporate action, dividendos/retenção, imposto de selo e impostos pessoais. Não somar duas vezes spread se usar bid/ask.
Hipóteses de fricção para stress, NÃO tarifas observadas: custo total não fiscal de 0.25%, 0.5%, 1%, 2% do capital; slippage proxy 25 bps por lado, stress 100; financiamento zero (sem margem), custo de oportunidade pelo caixa. Custos fiscais/corporate actions desconhecidos impedem selo de execução.
FX primário: converter CHF na entrada e repatriar na saída usando taxas executáveis+comissão; reporte também moeda local e CHF sem hedge. Sensibilidade CHF +/-10% vs moeda do negócio; hedge apenas cenário com carry e custo, sem presumir gratuito.
Fiscalidade CH: distinguir investidor privado/profissional; mais-valias privadas não assumidas isentas universalmente; riqueza e rendimento/dividendos, selo por intermediário suíço e retenção estrangeira dependem do caso. Usar fontes oficiais, não inventar taxa cantonal pessoal. Apresentar cenários e lacunas.

## 6. Métricas e benchmarks
S = A/P - 1. Anualização indicativa = (A/P)^(365/d)-1; apenas d>0 e data esperada documentada; não promessa de retorno.
R_real = (cash saída + dividendos líquidos - todos custos)/desembolso total -1. Se custos percentuais de P: EV/P = p*(A/P-1)+(1-p)*(B/P-1)-c, onde B é recuperação após falha; p_BE=(P*(1+c)-B)/(A-B), A>B. Acrescentar benchmark de prazo ao numerador para break-even económico. B não é conhecido ex-ante; cenários de queda 10/20/40/60% e 100% stress, não preço pré-anúncio tratado como garantia.
Benchmark primário: caixa CHF por datas reais (SARON composto com custo do instrumento de acesso); diagnóstico de opportunity cost na moeda da transação via taxa overnight local; benchmark secundário ações globais total return em CHF, proxy ETF disponível e custos; comparável de risco merger-arb líquido se série pública total return verificável. Comparação com índice acionista não elimina exposição a caudas.
Carteira diária MTM, CAGR, excesso líquido, volatilidade, Sharpe (não central isoladamente), drawdown máximo, ES95/99 descritivo, pior evento/mês, duração mediana/p95, capital-dias, frequência e severidade de falhas, turnover e caixa.
Incerteza: bootstrap blocos mensais de 6 meses, 10000 réplicas, seed 20261020; agrupar múltiplos negócios do mesmo comprador; resultados com <60 meses são fracos. Não interpretar ES99 com poucos dados como estimativa fiável.
Atrasos +90/+180/+365 dias, custos x2, queda conjunta de 3 maiores posições em 40%, perda total de uma posição, FX e dividendos. Selecionada vs indiscriminada com o mesmo capital/caixa/custos; sem otimização posterior.

## 7. Portão de dados e condições de rejeição
Para inferência: universo reconciliado, >=100 eventos resolvidos com >=10 falhas, >=60 meses, >=95% preços/fluxos verificáveis por contagem E capital, >=20 eventos selecionados, cobertura de todos os resultados adversos; censura explícita. Limiares mínimos de desenho, não garantia de potência. Nenhuma falha relevante pode desaparecer por dados ausentes; calcular bounds conservadores ou parar.
Se auditoria não demonstrar rota pública reproduzível para universo, preços delisted/execução e informação point-in-time, PARAR rapidamente: INCONCLUSIVO, sem ampliar seleção de casos até “funcionar”. Isso não prova inexistência da vantagem.
DIAMANTE CANDIDATO exige portão passado, excesso anual líquido selecionado >2 pontos percentuais sobre caixa CHF, limite inferior IC95 >0, superioridade selecionada vs indiscriminada IC95 >0, drawdown <=15%, acesso/custos verificáveis, robustez a custos x2 e atrasos +180 dias, validação independente por investigador sem acesso a resultados de desenho. Sem revisão independente: nunca DIAMANTE.
REJEITADO se dados adequados mostrarem limite superior IC95 do excesso <=0 ou execução verificada tornar EV <=0 sob hipóteses justificadas. Restantes casos INCONCLUSIVOS; não confundir ausência de evidência com rejeição estatística.
Sem ajustar limiares, universo, janela, filtro ou datas depois de observar resultados. Emendas apenas novo ficheiro com motivação e timestamp, só para dados futuros; v1 permanece integral.

## 8. Auditoria e entregas
Separar ex_ante.csv (campos, timestamp publicação, conhecida_até_t0, URL), outcomes.csv (conhecimento posterior), prices.csv (origem, raw/adjusted, moeda, bid/ask/proxy), exclusions.csv e sources.md. Ausências = NA com motivo.
Nesta execução de viabilidade pode entregar inventário de casos e matriz de disponibilidade sem preencher preços/probabilidades não verificadas. Documentar fontes tentadas e distinção indisponível nesta investigação vs inexistente.
Publicar relatório adversarial, fórmulas/cálculos sintéticos reproduzíveis identificados como tais, custos e veredito. Scripts apenas se indispensáveis para verificar aritmética/dados, sem infraestrutura.
Qualquer futura recolha que passe portão exige executar exatamente este plano ou pré-registar nova experiência. Não declarar revisão da própria análise como validação independente.
