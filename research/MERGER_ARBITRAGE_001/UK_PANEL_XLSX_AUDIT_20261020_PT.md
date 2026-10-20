# Auditoria dos seis XLSX do UK Takeover Panel — MA001
Data: 2026-10-20, Europe/Zurich. Nova verificação limitada de viabilidade; sem preços, retornos, trading ou capital.

## Veredito
**INCONCLUSIVO; fonte de eventos promissora, portão confirmatório não cumprido.**
Os seis XLSX contêm registos individuais, não apenas tabelas agregadas. Enumeram anúncios firmes independentemente do desfecho e incluem resoluções adversas. Permitem iniciar um inventário cronológico de ofertas reguladas pelo Panel. Não bastam, isoladamente, para certificar um universo completo sem enviesamento de sobrevivência, classificar todos os pendentes/cancelamentos, ou executar o universo congelado EUA/Reino Unido/Suíça 2018–2024.

Não aprovar recolha integral de preços/backtest com base nestes ficheiros. Antes disso falta reconciliar anúncios e resoluções, documentar elegibilidade e preencher as lacunas geográficas e temporais. Uma eventual prova limitada de preços, autorizada em nova execução, teria de cumprir os exemplos de sucesso/cancelamento/revisão e delisting previstos no relatório; não seria aprovação do portão. Esta auditoria não procurou novos casos narrativos nem ampliou os seis casos anteriores.

## Referências congeladas
Lidos exclusivamente na branch research/merger-arbitrage-001-20261020:
- research/MERGER_ARBITRAGE_001/PROTOCOL_V1.md — blob 15fa1124ea223545fcfbb2e9bdf5dcd363180368.
- research/MERGER_ARBITRAGE_001/REPORT_PT.md — blob 29516a673622a33cfd0a86268c1a7e11891b5718.

O protocolo exige TODOS os acordos definitivos 2018-01-01 a 2024-12-31 de controlo de ações ordinárias listadas nos EUA/UK/CH, integralmente em dinheiro fixo nas moedas previstas, equity >=CHF500m à data, acessíveis ao particular. Corte de resultados: 2026-10-19 23:59:59 UTC. Pendentes censurados, não eliminados.
Mínimos: universo reconciliado; >=100 resoluções e >=10 falhas elegíveis; >=60 meses; >=95% preços/fluxos verificáveis por contagem E capital; >=20 eventos selecionados; nenhum resultado adverso omitido.

## Método e contagens
Leitura de todas as células das 24 folhas dos seis anexos, incluindo capas, cabeçalhos e linhas; extração por biblioteca openpyxl do Python fornecido pelo ambiente, sem escrever nos XLSX. Registos = linhas não vazias desde a linha 3 de cada folha de dados. Linhas 1 e 2 são título e cabeçalho. Não somar as três folhas como operações distintas.

| Ano terminado em março | Períodos iniciados | Anúncios firmes | Resoluções | Unconditional/Scheme Effective | Lapsed | Withdrawn | Minoritários |
|---|---:|---:|---:|---:|---:|---:|---:|
| 2021 | 73 | 48 | 40 | 33 | 2 | 1 | 4 |
| 2022 | 72 | 60 | 57 | 43 | 10 | 1 | 3 |
| 2023 | 74 | 48 | 53 | 44 | 6 | 2 | 1 |
| 2024 | 87 | 61 | 60 | 53 | 4 | 1 | 2 |
| 2025 | 87 | 57 | 55 | 47 | 5 | 1 | 2 |
| 2026 | 84 | 60 | 64 | 52 | 7 | 2 | 3 |
| TOTAL | 477 | 334 | 329 | 272 | 34 | 8 | 15 |

São 1.140 linhas de registos em três etapas do processo, NÃO 1.140 aquisições. Os 334 anúncios referem 310 nomes de alvos distintos após trim/casefold. Não equivalem necessariamente a 334 operações independentes. Zero duplicados integrais nos anúncios e nas resoluções; isto não exclui duplicação económica.

Os 15 minoritários agregam apenas para apresentação os rótulos originais "Offer to minority" (8) e "Offer to Minority Shareholders" (7). Não foram tratados como sucesso ou falha confirmatórios. "Unconditional/Scheme Effective" não autentica recebimento do dinheiro pelo investidor. "Lapsed"/"Withdrawn" são 42 rótulos adversos brutos, não 42 perdas de posições nem 42 falhas elegíveis.

## Folhas, dimensões e campos
Todas as seis têm quatro folhas com os mesmos cabeçalhos:
- Cover Sheet: 8 linhas x 2 colunas; cinco linhas não vazias; identifica ano/âmbito e aviso de que os dados são informativos.
- Offer Periods Commencing: A=Offeree, B=ISIN, C=Offer Period Start, D=Commencement Type.
- Firm Offers Announced: A=Offeree, B=Offeror, C=Date, D=Category.
- Offers Resolved: A=Offeree, B=Offeror, C=Result Date, D=Recommendation at announcement, E=Recommendation at publication, F=Recommendation at end of offer period, G=Rule 9 at Announcement, H=Outcome.

| Ano | Dimensão períodos | Dimensão anúncios | Dimensão resoluções |
|---|---|---|---|
| 2020–21 | 75x4 | 50x4 | 42x8 |
| 2021–22 | 74x4 | 62x4 | 59x8 |
| 2022–23 | 76x4 | 50x4 | 55x8 |
| 2023–24 | 89x4 | 63x4 | 70x8 |
| 2024–25 | 89x4 | 59x4 | 65x8 |
| 2025–26 | 88x4 | 62x4 | 66x8 |

Dimensão física não é contagem de registos: há linhas vazias finais em algumas folhas.
Categorias dos anúncios: 272 Scheme e 62 Offer. Estas categorias descrevem a estrutura, não cash versus ações.

Períodos iniciados incluem negociações preliminares, processos de venda e strategic reviews, que podem não gerar acordo definitivo. Não usar a primeira folha como lista de acordos definitivos. A folha Firm Offers Announced é o ponto de partida mais próximo, sujeito a validação documental da definição do protocolo.

## Cobertura cronológica
Seis exercícios nominais consecutivos: 2020-04-01 a 2026-03-31, 72 meses.
- Anúncios observados: 2020-04-15 a 2026-03-06; há anúncios em 71 meses (abril de 2022 sem anúncios na extração). Não confundir meses sem anúncios com omissão comprovada.
- Resoluções observadas: 2020-04-03 a 2026-03-31.
- Anúncios com data no intervalo confirmatório: 262; os outros 72 são de 2025–2026 e não entram como novos anúncios confirmatórios.
- Resoluções com data até 2024-12-31: 252 = 209 unconditional/effective +26 lapsed +6 withdrawn +11 minoritários. Isto é agrupamento por data de resolução, NÃO desfechos da coorte de anúncios 2018–2024.
- Dados de 2025–2026 podem ajudar a resolver anúncios anteriores a 2025; não os descartar em bloco.
- Faltam janeiro de 2018 a março de 2020 (27 meses) na enumeração de anúncios; falta atualização de resoluções abril–19 outubro de 2026 para o corte.
- Regulação pelo Panel não prova bolsa de negociação, país de cotação ou elegibilidade. Estes ficheiros não enumeram o universo EUA e Suíça. Prefixo do ISIN não substitui mercado/listagem.
- Sete ISIN são o literal "Not traded"; existe também "Asset Match". Isto confirma que estar na fonte não prova ação listada/executável segundo o desenho.

## Reconciliação e sobrevivência
Teste diagnóstico: nomes normalizados apenas por trim/casefold e colapso de espaços; chave alvo+comprador, contra todas as resoluções dos seis ficheiros:
- 236/334 linhas de anúncios têm alguma chave correspondente (70,66%).
- 98/334 não têm correspondência exata (29,34%).
Este teste não exige sequência temporal nem unicidade e NÃO certifica 236 ligações económicas corretas; não rotula os 98 como pendentes. Existem mudanças de nomes e compradores descritos com o grupo entre parênteses nas resoluções. Não usar aproximação textual para escolher silenciosamente uma resolução.
Há duas datas de anúncio para Proactis Holdings plc/Cafe Bidco Limited (2021-04-30 e 2021-06-11, linhas 7 e 16 da folha de anúncios de 2021–22). Verificar documentos para identificar nova oferta, revisão ou outra razão; não criar dois trades automaticamente.
G4S e Codemasters têm ofertas concorrentes com desfechos diferentes. Um join só pelo alvo pode converter uma oferta caducada no sucesso de outro comprador. A granularidade inicial deve distinguir alvo, comprador, anúncio e caminho de revisões; a contabilização de posições exige evitar duplicação da mesma exposição.
Resoluções de um exercício incluem anúncios de exercícios anteriores. 329/334 não mede cobertura de desfechos; a diferença de cinco não mede pendentes.

A inclusão de anúncios e de desfechos adversos reduz o risco de seleção apenas de vencedores. Não prova completude: é necessário reconciliar por coorte de anúncio, preservar candidatos sem ligação, resolver disputas com fontes originais, documentar exclusões apenas por critérios ex-ante e identificar censoring no corte. Um fracasso de negociação preliminar não é falha de acordo definitivo elegível.

Estados:
- Concluídas: proxy regulatório explícito Unconditional/Scheme Effective.
- Retiradas: Withdrawn explícito.
- Caducadas: Lapsed explícito.
- Canceladas: não há rótulo separado Cancelled; cancelamentos podem estar noutra categoria, exigindo documento e mapeamento.
- Pendentes: nenhuma folha ou flag explícita; obter estado no corte e não inferir do fracasso de um join.

Não calcular taxa de sucesso/p(conclusão) a partir desta tabela agregada.

## Lacunas e anomalias observadas
1. 2020–21, Offer Periods Commencing!C72: Hydrogen Group plc = 2021-09-08, fora do ano terminado em março de 2021. Preservado como está, sem corrigir para uma data presumida.
2. 2024–25, Cover Sheet!B6: declara versão emendada refletida no relatório 2025–26. É uma compilação posterior; não prova informação disponível em t0. Histórico de versões não recuperado.
3. 2024–25, Offer Periods Commencing!B50/B75/B87: ISIN ausente para Brown (N.) Group, Slingsby (H.C.) e Serinus Energy.
4. Na mesma coluna existem duas strings vazias adicionais (distintas de células None), espaços iniciais e identificadores de comprimento atípico. Não aceitar a presença da célula como ISIN válido. Validar checksum e identidade em fontes oficiais antes de mapear preços; não foi feita validação completa de checksum nesta auditoria.
5. 2023–24, Offers Resolved!E3: recomendação na publicação ausente para Redx/Jounce; F58: recomendação final ausente para Kin and Carta/Kelvin.
6. Nos 334 anúncios os quatro campos estão preenchidos; nas 329 resoluções todos os campos de identidade, data e resultado estão preenchidos. Preenchimento textual não comprova exatidão/completude.
7. A ordem física não é sempre cronológica. Ordenar pelas datas preservando ficheiro/folha/linha e sem alterar fonte.
8. Os ISIN aparecem na folha de períodos, não em anúncios/resoluções. Alvo pode repetir períodos; ligação para instrumento exige validação.
9. Informação de recomendação final e outcome é posterior. Manter separada das features ex-ante. Nem recomendação inicial substitui documentação do financiamento/autorizações/voto/litígio exigidos no filtro.

## Campos ausentes e passagem aos preços
Faltam: identificador estável da operação, links de anúncio/filings, timestamps/timezones, preço/moeda/tipo de contraprestação, equity e FX ao anúncio, bolsa/ticker e histórico de símbolos, prova de controlo e ações ordinárias, acessibilidade CH, condições e aprovações até t0, data esperada conhecida até t0, revisões, dividendos, datas de liquidação/crédito de caixa e corporate actions, preços raw/bid-ask/volume, custos e fiscalidade.

| Critério congelado | Evidência nesta auditoria | Estado |
|---|---|---|
| Universo cronológico reconciliado 2018–2024 EUA/UK/CH | Fonte parcial de anúncios do Panel desde abril 2020 | Não cumprido |
| >=100 resoluções elegíveis | 329 resoluções brutas; elegibilidade não determinada | Não demonstrado |
| >=10 falhas elegíveis | 42 lapsed/withdrawn brutas, inclui concorrência/outros termos | Não demonstrado |
| >=60 meses | 72 meses nominais da fonte; apenas 57 meses nominais sobrepostos à janela de anúncios até dez.2024 | Não demonstrado para universo congelado |
| >=95% preços/fluxos por contagem e capital | Nenhuma série ou fluxo autenticado aqui; denominador elegível desconhecido | Não avaliado; não atribuir cobertura 0% à fonte de preços |
| >=20 selecionadas pelo filtro | Features necessárias ausentes | Não demonstrado |
| Todos adversos e pendentes/censura | Retiradas/caducadas explícitas; pendentes/canceladas não reconciliadas | Não cumprido |

Conclusão operacional: preservar esta fonte como inventário inicial. A próxima dependência é um ledger auditável com ligações e exclusões justificadas, incluindo os períodos/mercados ausentes e desfechos até ao corte. Não redefinir a janela para 2020–2026 nem transformar uma amostra UK num teste confirmatório do protocolo existente. Se não houver rota pública reproduzível para essas dependências, manter encerramento INCONCLUSIVO por dados; não inferir ausência de prémio económico.

## Proveniência dos anexos
Hashes SHA-256 dos bytes efetivamente lidos:
| Ficheiro | SHA-256 |
|---|---|
| 01_04_2020_to_31_03_2021.xlsx | 14d3ba0ee25379b9af6af0f19b4b57a52dd015363d02292aa601db688ce50f34 |
| 01_04_2021_to_31_03_2022.xlsx | 27d19e41d820f0244aed5e2e8647c5d783b57efb4cb5afe4f858a66c14fc7d47 |
| 01_04_2022_to_31_03_2023.xlsx | ef6ad42e08bff97f74ee26e762314140623a9f98957ae0b9aff27740d41eade0 |
| Website-Statistics-23_24.xlsx | 43b9f702b0761a76a1adf24bba352763b332812bf8d2f46a98bc51092e973e4e |
| Website-Statistics-24-25.A.xlsx | fbc1f439878360f57186b8782d40588ae2f0fe7785f31c1b0732695cad888ac9 |
| Website-Statistics-25-26.A.xlsx | 75dd0f9394fe8aa6da2214801ef7213daf9401a4054dfe833198f75855145b6d |

Origem operacional: seis anexos recuperados pela leitura do chat referenciado. Página pública transaction-statistics do Panel tentada nesta execução mas devolveu timeout; não foi usada para inferir contagens nem autenticar igualdade dos anexos com downloads atuais. Proveniência institucional é declarada nas capas; não foi afirmada validação independente do download.

## Limites e proteção
Apenas novo documento de auditoria numa nova branch derivada da branch research indicada; nenhum merge. PROTOCOL_V1.md e REPORT_PT.md preservados; main e holdouts não alterados nem holdouts consultados. Nenhum capital, conta, compra de dados ou negociação. Esta é auditoria de estrutura/cobertura, não revisão independente dos resultados económicos nem backtest.
